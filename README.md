# VeriAgent

**一个能在本地跑通、能复现、并且被自己的实验推翻过一句结论的 Agent Runtime 最小实现。**

> 面向岗位：大模型应用开发实习生（Agent Runtime / Agentic Search 方向）
> 实验记录与讲法在本仓库内（`EXPERIMENTS.md`、`一分钟讲法.md`）；简历与技术报告随投递材料另附，不入代码仓库。

---

## 30 秒跑起来

零第三方依赖，Python 3.10+，不用 API key、不用数据库、不用起服务：

```bash
cd VeriAgent
python demo.py
```

`demo.py` 一次跑完：结构化编排 → WAITING_HUMAN 人工确认 → 从 Checkpoint 断点恢复
（幂等键防重复执行）→ 越权 `exec` 拦截 → 全链路 Trace → 四组配置消融 → 导出 SFT / DPO 数据。

```bash
python eval/benchmark.py        # 单独重跑四组消融
```

Windows PowerShell 里直接在项目根目录敲 `python demo.py` 即可；中文脚本名可打 `python 第` 按 Tab 补全。

---

## 它解决什么

输入一个开放的多跳调研问题，输出**带逐条引用的结构化报告**，全程可观测、可中断恢复、可评测：

| 层 | 实现 |
| --- | --- |
| Runtime | 结构化 Planning（`Plan` / `Report` / `SkillSpec` 均过 Schema 校验）→ Skill 注册表 → 最小 MCP 客户端（`initialize` → `tools/list` → `tools/call`）→ Plan-Act-Observe 主循环 |
| 长任务 | 显式状态机 `PENDING / PLANNING / RUNNING / WAITING_HUMAN / RECOVERING / DONE / FAILED`、节点级 Checkpoint、幂等键、read/write/exec 权限分级、步数 / Token / 墙钟三重预算 |
| Agentic Search | 结构感知分块保留 section 路径 → BM25 倒排 + 轻量向量双索引 RRF 融合 → Query 分解 → 证据充分性自反思（跨文档数 / 命中块数，上限 3 轮）→ 带引用生成 → Verifier 句子级校验 |
| 评测闭环 | 固定评测集 + 5 维 rubric + 四组消融 + 全链路 Trace → 轨迹清洗后导出 SFT / DPO 偏好对 |

---

## 这两个实验，才是这个仓库的重点

### E005 — 亲手推翻自己写进简历的那句结论

第一套示例语料上，Baseline（`topk=3`）召回 65%，`+agentic_search`（`topk=8`，多轮）召回 81%，
看起来是「多轮编排带来 +16pt」。

**只改一个变量**：把 `veriagent/runtime.py` 的 `search_fn` 里 `topk=3` 改成 `topk=6`，Agentic 三组不动。重跑：

| 配置 | 完成率 | 召回 | 引用 | 幻觉 |
| --- | --- | --- | --- | --- |
| Baseline（topk=3，改前） | 83% | 65% | 58% | 40% |
| Baseline（topk=6，改后） | 83% | 81% | 50% | 33% |
| +agentic_search | 83% | 81% | 50% | 33% |
| +sft_dpo_verifier | 83% | 81% | 50% | **0%** |

改后 Baseline 与 `+agentic_search` **四项逐项一致**。

> **结论：不是他更会找，是我少发了牌，真管用的只有那个查谎的。**
> 那 16pt 来自检索预算不对等，不是多轮编排。简历里「Agentic Search 提升召回」那句已主动撤下；
> 唯一与检索预算无关的增益是 Verifier 把幻觉率 33% → 0%（规则层剔除无引用陈述，口径如实写明）。

### E006 — 换一套自己看得懂的语料再验一遍

原示例语料讲 Agent 机制，我自己判断不了答案对不对。于是整体换成**大学日常规则**
（选课 / 图书馆 / 食堂 / 校园卡 / 快递 / 宿舍 / 缓考 / 体育馆）：
`data/corpus.jsonl` 8 篇 / 18 分块，`eval/dataset.jsonl` 12 题（含 2 道故意问不到的陷阱题）。

| 配置 | 完成率 | 召回 | 引用 | 幻觉 |
| --- | --- | --- | --- | --- |
| baseline | 83% | 83% | 42% | 33% |
| +agentic_search | 83% | 83% | 42% | 33% |
| +runtime_engineering | 83% | 83% | 42% | 33% |
| +sft_dpo_verifier | 83% | 83% | 42% | **0%** |

E005 结论在第二套独立语料上依然成立；引用准确率 42% 低于第一套的 50%，
**作为跨语料差异如实记录，不强行解释**。

完整假设—改动—结果—结论见 [`EXPERIMENTS.md`](EXPERIMENTS.md)，
原始数字见 `eval/results_基线.json`、`eval/results_E005.json`、`eval/results_我的题库.json`。

---

## 可复现性

向量索引原先误用 Python 内置 `hash()`，受进程级随机化影响，同一评测集两次跑分会在
65%~69% 间漂移 —— 那样「改参数前后对比」根本没有意义。已改为确定性 `crc32`，
连跑两次 `eval/results.json` **逐字节一致**。单变量实验建立在这个前提上才成立。

口径说明：所有百分比都是脚本在本仓库小型自建语料（12 题 / 8 篇 / 18 分块、`MockLLM`、`seed=42`）
上实算的结果，用于证明**评测闭环与工程取舍**，**不代表生产系统指标**，也不外推到真实业务。

---

## 目录

    veriagent/schemas.py     结构化输出 schema 与校验
    veriagent/state.py       状态机 / Checkpoint / 幂等键 / 内存 StateStore
    veriagent/trace.py       全链路 Trace（span / token / 耗时 / 成本）
    veriagent/skills.py      Skill 注册表、权限、人工确认声明
    veriagent/mcp_client.py  最小 MCP JSON-RPC client + 本地 server
    veriagent/search.py      分块、双索引、RRF 融合、证据充分性自反思
    veriagent/runtime.py     Plan-Act-Observe 主循环、恢复、防循环
    veriagent/llm.py         可插拔 LLM adapter（默认 MockLLM）
    eval/                    评测集、benchmark、各轮结果备份
    train/                   轨迹 → SFT / DPO / Verifier 数据管线
    EXPERIMENTS.md           E005 / E006 实验记录
    一分钟讲法.md            30 秒开场与现场演示顺序
    schema.sql               MySQL 建表语句（生产替换点）

## 换成真实组件

| 当前 | 生产替换点 |
| --- | --- |
| `MockLLM` | `OpenAICompatibleLLM`（填 `VERIAGENT_API_BASE` / `KEY` / `MODEL`） |
| `LocalTransport` | stdio / SSE 子进程，三步握手不变 |
| 内存 `StateStore` | MySQL，DDL 见 `schema.sql` |
| 哈希 n-gram 向量 | 真实 embedding，只换 `search.py:_vectorize` |
| 可选 torch 脚本 | 真实 SFT / DPO，先把数据管线跑通再谈训练规模 |

## 与岗位的对应

| JD 关键词 | 代码位置 |
| --- | --- |
| Agent Runtime / Skill / Tool / MCP 编排 | `runtime.py`、`skills.py`、`mcp_client.py` |
| 长任务状态管理 / 人工确认 / 异常恢复 / 权限控制 | `state.py`、`runtime.py` |
| 运行观测 / 效果评测 | `trace.py`、`eval/benchmark.py` |
| 知识库与 Agentic Search / 数据关联 / 问答优化 | `search.py`、`data/` |
| 结构化流程 / 评测集 / Benchmark | `schemas.py`、`eval/` |
| 训练数据构建清洗 / SFT / 偏好优化 / Verifier | `train/` |
| Python / Git / Linux / MySQL | 全仓库 + `schema.sql` |

---

## 诚实声明

这是一套**可复现的实现骨架，不是已上线的业务系统**：没有真实模型、没有真实 embedding、
没有真训完的 SFT/DPO、没有生产数据库，语料只有 8 篇文档。
本仓库的价值在于：编排链路完整可跑、每个指标都能由脚本重算、
**每一轮改动都有留证，包括一条被自己实验推翻的结论**。
