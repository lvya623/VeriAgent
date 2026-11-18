# 一键演示：编排 -> 人工确认 -> Checkpoint 恢复 -> 权限拦截 -> Trace -> 消融评测。
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from veriagent.llm import MockLLM
from veriagent.skills import SkillRegistry
from veriagent.mcp_client import MCPClient, MCPServer, LocalTransport
from veriagent.search import load_corpus
from veriagent.state import StateStore, TaskState
from veriagent.trace import Tracer
from veriagent.runtime import AgentRuntime
from eval.benchmark import main as benchmark_main

ROOT = Path(__file__).resolve().parent
QUESTION = "对比 短期记忆 与 长期记忆 在长任务编排中的表现与适用条件"


def line(title):
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def main():
    index = load_corpus(ROOT / "data" / "corpus.jsonl")
    print("VeriAgent 最小可运行骨架 | 语料块:", len(index["chunks"]))

    line("1. 结构化编排 + 人工确认闸门")
    store, tracer = StateStore(), Tracer()
    rt = AgentRuntime(MockLLM(), SkillRegistry(),
                      MCPClient(LocalTransport(MCPServer(index))), index,
                      store=store, tracer=tracer,
                      config=dict(agentic=True, checkpoint=True,
                                  verifier=True, strict_write=True),
                      auto_approve=False, authorized_exec=False)
    print("MCP 工具发现:", rt.tool_names)
    r1 = rt.start(QUESTION)
    print("状态:", r1.state)
    print("待确认动作:", json.dumps(
        {"skill": r1.pending_action["skill"], "node": r1.pending_action["node_id"],
         "permission": "write"}, ensure_ascii=False))
    print("Checkpoint 数:", r1.checkpoints)
    for e in tracer.events(r1.task_id):
        if e.kind in ("plan", "await_human", "search_round", "skill_call"):
            print(f"  trace | {e.kind:14s} | {e.node_id}")

    line("2. 从 Checkpoint 恢复并完成（幂等键防重复执行）")
    r2 = rt.approve(r1.task_id)
    print("状态:", r2.state)
    print("结论:", r2.report.conclusion if r2.report else "N/A")
    print("有效结论数:", len(r2.report.claims) if r2.report else 0)
    print("证据块数:", len(r2.evidences))
    print("Agentic Search 轮次:", [(x["round"], x["sufficient"]) for x in r2.search_log])
    print("Trace 汇总:", json.dumps(r2.trace_summary, ensure_ascii=False))
    print("Checkpoint 数:", r2.checkpoints)
    print("状态迁移终点:", store.state(r1.task_id).value)

    line("3. 权限控制：未授权的 exec 调用被拦截")
    rt3 = AgentRuntime(MockLLM(), SkillRegistry(),
                       MCPClient(LocalTransport(MCPServer(index))), index,
                       config=dict(agentic=False, checkpoint=True, verifier=True),
                       auto_approve=True, authorized_exec=False)
    from veriagent.schemas import Plan
    p = Plan.from_dict({"goal": "演示越权", "steps": [
        {"skill": "run_calculation", "args": {"expression": "3-1", "a": 3, "b": 1},
         "reason": "测试 exec 权限"}],
        "stop_condition": "完成"})
    # 直接调用注册表校验路径，观察拦截事件
    tid = "perm-demo"
    rt3.store.transition(tid, TaskState.PLANNING)
    rt3._sessions[tid] = {"question": "演示", "plan": p.to_dict(), "cursor": 0,
                          "evidences": [], "report": None, "facts": [],
                          "seen_actions": [], "t0": time.time()}
    rt3.store.transition(tid, TaskState.RUNNING)
    res3 = rt3._run(tid)
    blocked = [e for e in rt3.tracer.events(tid) if e.kind == "blocked"]
    print("拦截事件:", json.dumps([b.payload for b in blocked], ensure_ascii=False))
    print("结论: exec 权限未授权时直接拒绝并写 Trace 告警")

    line("4. 固定评测集消融 Benchmark（指标为脚本真实计算）")
    benchmark_main()

    line("5. 导出 SFT / DPO 训练数据")
    import train.build_sft as bs
    bs.build()

    line("完成")
    print("下一步：把 MockLLM 换成真实模型、StateStore 换成 MySQL、")
    print("用你自己的语料与评测集重跑，再用真实数字替换简历中的【】占位。")


if __name__ == "__main__":
    main()
