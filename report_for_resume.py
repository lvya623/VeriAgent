# -*- coding: utf-8 -*-
"""
第 2/3 步跑完后运行：python report_for_resume.py
读 eval/results.json，生成「简历项目段_我的数据.md」。
纯标准库、零依赖。把这个 .md 发我，我出可投的 docx 终版。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RES = ROOT / "eval" / "results.json"
OUT = ROOT / "简历项目段_我的数据.md"


def pct(x):
    return "%d%%" % round(x * 100)


def diff(a, b):
    raw = (b - a) * 100
    d = int(raw + 0.5) if raw >= 0 else int(raw - 0.5)
    return ("+%dpt" % d) if d > 0 else ("%dpt" % d if d < 0 else "0pt")


def main():
    if not RES.exists():
        print("找不到 eval/results.json，先跑一次：python eval\\benchmark.py")
        return
    data = json.loads(RES.read_text(encoding="utf-8"))
    ms = {m["config"]: m for m in data["metrics"]}
    base = ms.get("baseline") or list(ms.values())[0]
    agentic = ms.get("+agentic_search") or base
    final_conf = "+sft_dpo_verifier"
    final = ms.get(final_conf) or list(ms.values())[-1]

    ds = ROOT / "eval" / "dataset.jsonl"
    corpus = ROOT / "data" / "corpus.jsonl"
    n_q = sum(1 for l in ds.read_text(encoding="utf-8").splitlines() if l.strip()) if ds.exists() else "N"
    docs, chunks = set(), 0
    if corpus.exists():
        for l in corpus.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            d = json.loads(l)
            docs.add(d["doc_id"])
            chunks += len(d["sections"])

    recall_delta = diff(base["evidence_recall_at5"], agentic["evidence_recall_at5"])
    if recall_delta == "0pt":
        ablation = (
            "等候选数对照实证：把 Baseline 单次检索候选数调至与 Agentic Search 相当后，"
            "两组证据召回同为 %s、提升归零，说明当前最小语料规模下「多轮编排带来召回提升」"
            "不成立，收益主要来自证据池变大而非编排本身；引用准确率 %s → %s，"
            "接入 Verifier 后幻觉率 %s → %s。每轮假设—改动—结论写入 EXPERIMENTS.md。"
            % (pct(agentic["evidence_recall_at5"]),
               pct(base["citation_precision"]), pct(agentic["citation_precision"]),
               pct(base["hallucination_rate"]), pct(final["hallucination_rate"])))
    else:
        ablation = (
            "消融实证：Agentic Search 将证据召回从 %s 提至 %s（%s）；引用准确率由 %s 变为 %s（%s）。"
            "接入 Verifier 后幻觉率由 %s 降至 %s（%s）。任务完成率 %s → %s，"
            "每轮假设—改动—结论写入 EXPERIMENTS.md。"
            % (pct(base["evidence_recall_at5"]), pct(agentic["evidence_recall_at5"]), recall_delta,
               pct(base["citation_precision"]), pct(agentic["citation_precision"]),
               diff(base["citation_precision"], agentic["citation_precision"]),
               pct(base["hallucination_rate"]), pct(final["hallucination_rate"]),
               diff(base["hallucination_rate"], final["hallucination_rate"]),
               pct(base["task_completion_rate"]), pct(final["task_completion_rate"])))

    lines = [
        "# 简历项目段 · 我的实跑数据",
        "",
        "数据来源：eval/results.json（本仓库脚本实算，seed=%s，评测集 %s 条，"
        "语料 %s 篇 / %s 分块）" % (data.get("seed", "?"), n_q, len(docs), chunks),
        "",
        "## 可直接替换进简历的量化 bullet",
        "",
        "自建 %s 条多跳评测集（含不可回答陷阱题）与 5 维 rubric，固定切分、seed=%s，"
        "以 %s 篇文档 / %s 个分块的最小语料做四组消融；指标覆盖任务完成率、证据召回、"
        "引用准确率、幻觉率、平均 Skill 调用数，结果落 eval/results.json 一键复现。"
        % (n_q, data.get("seed", "?"), len(docs), chunks),
        "",
        ablation,
        "",
        "## 四组配置全量结果",
        "",
        "| 配置 | 完成率 | 证据召回 | 引用准确率 | 幻觉率 | 平均 Skill 调用 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for m in data["metrics"]:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            m["config"], pct(m["task_completion_rate"]),
            pct(m["evidence_recall_at5"]), pct(m["citation_precision"]),
            pct(m["hallucination_rate"]), m["avg_skill_calls"]))
    lines += [
        "",
        "## 口径说明（简历脚注用）",
        "",
        "上述百分比为自建最小示例评测集上脚本实算结果，用于证明评测闭环与工程取舍，"
        "不代表生产系统指标；MockLLM、无 API key、纯标准库可复现。",
        "",
        "把这个文件发我，我据此生成可投的 docx 终版。",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("[ok] 生成", OUT.name)
    print("-" * 56)
    print("\n".join(lines[4:12]))
    print("-" * 56)


if __name__ == "__main__":
    main()
