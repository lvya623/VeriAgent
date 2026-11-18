# 实验记录

要求：每轮改动记录「假设 → 改动 → 固定评测集结果 → 结论」，结论必须能被复现。
所有指标在 `eval/dataset.jsonl` 上、同一随机种子下统计。

---

## E001  Baseline（单次检索 + 直接生成）

- 假设：单次 BM25+向量混合检索已足够支撑多跳问题。
- 改动：关闭 query 分解、证据充分性反思、Verifier 与 Checkpoint。
- 结果：见 `eval/results.json` 的 `baseline` 行。
- 结论：跨文档对比类题目证据覆盖不足，引用准确率明显偏低。
- 待验证（重要）：Baseline 单次只取 3 个候选，召回偏低可能只是候选数少，
  未必是「没有多轮编排」。E005 用等候选数对照检验这一点，别把相关性当因果。

## E002  + Agentic Search

- 假设：让模型判断「证据够不够」并改写 query 再检索，能提升跨文档覆盖。
- 改动：启用 `decompose` + `sufficiency`，最多 3 轮反思，带步数预算。
- 结果：见 `eval/results.json` 的 `+agentic_search` 行。
- 结论：证据召回提升，但冗余检索带来额外步数与时延，需要预算与重复动作检测。

## E003  + Runtime 工程化

- 假设：状态机、Checkpoint、权限与人工确认不会直接提升质量，但会让长任务可控可恢复。
- 改动：节点级 checkpoint + 幂等键 + Trace 全链路 + 步数/Token/墙钟三重预算。
- 结果：质量指标基本持平，断点恢复成功率与越权拦截率见 `runtime` 输出。
- 结论：工程化指标应单独报告，不要混进「效果提升」里讲，否则容易被追问。

## E004  + SFT / DPO / Verifier

- 假设：用达标轨迹做结构化输出训练、用 Verifier 剔除无证据陈述，可降低幻觉率。
- 改动：轨迹清洗 → SFT/DPO 数据（见 `train/`），启用 `verify` 步骤剔除无支撑 claim。
- 结果：见 `eval/results.json` 的 `+sft_dpo_verifier` 行。
- 结论：幻觉率下降，引用准确率上升；样本量小，结论只适用于本示例语料，不外推。

---

## 待办

- [ ] 换成真实语料（≥ 1000 文档）与真实模型，重跑全部四组
- [ ] 人工抽检 20% 的 LLM-as-judge 结果并报 Cohen's kappa
- [ ] 把 StateStore / Tracer 换成 MySQL，重测长任务恢复
- [ ] 用真实数据替换简历与项目文档里的所有【】占位
## E005  等候选数对照：单次检索取更多证据会怎样（我的第一次实验）

假设：Baseline 召回偏低只是因为候选数少，给够候选就能追平 Agentic Search。
改动：veriagent/runtime.py 的 search_fn，topk 3 → 6，仅此一处；Agentic 三组未动。
结果：Baseline 召回 65% → 81%（+16pt），引用 58% → 50%（-8pt），
        幻觉 40% → 33%（-7pt），完成率 83% / 步数 4.0 不变；
        Agentic 三组四项全部未变；改后 Baseline 与 +agentic_search 逐项一致。
结论：不是他更会找，是我少发了牌，真管用的只有那个查谎的。
对简历的影响：撤掉「Agentic Search 将召回 65% 提至 81%」；
        仅保留 Verifier 在等预算下把幻觉 33% → 0% 这一条。
复现：python eval/benchmark.py，对照 eval/results_基线.json（topk 改回 3 可复原）。


## E006  换成我自己看得懂的题库（大学日常）

- 动机：示例语料讲 Agent 机制，我看不懂也没法判断答案对不对；换成选课、图书馆、食堂、快递、宿舍、缓考这类日常规则，题目对不对我瞄一眼就知道。
- 改动：data/corpus.jsonl（8 篇 / 18 块）、eval/dataset.jsonl（12 题，含 2 道不可回答陷阱题）整体替换；原示例语料备份为 *_示例备份.jsonl，E005 结果备份为 results_E005.json，均保留。
- 结果（脚本实算，见 eval/results_我的题库.json）：
  - baseline: 完成率 83% / 召回 83% / 引用 42% / 幻觉 33%
  - +agentic_search: 完成率 83% / 召回 83% / 引用 42% / 幻觉 33%
  - +runtime_engineering: 完成率 83% / 召回 83% / 引用 42% / 幻觉 33%
  - +sft_dpo_verifier: 完成率 83% / 召回 83% / 引用 42% / 幻觉 0%
- 说明：E005 是**示例语料上**的历史结论，保留在上方不动；本轮是第二套独立语料，用于看同一套 Runtime 换语料后结论还成不成立。
- 复现：python eval/benchmark.py（当前默认语料已是本轮题库）。
