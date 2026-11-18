# -*- coding: utf-8 -*-
"""
第 3 步：把示例语料换成「大学日常」题库，并自动重跑评测。
用法：把这个文件放到项目根目录（和 demo.py 并排），然后：
    python 第3步_换成我自己的题库.py
它会自动：备份原文件 -> 写入新语料 -> 跑 benchmark -> 留一份结果 -> 追加 E006 记录。
什么都不用自己编，也不用懂原理。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "data" / "corpus.jsonl"
DATASET = ROOT / "eval" / "dataset.jsonl"
RESULTS = ROOT / "eval" / "results.json"
EXPERIMENTS = ROOT / "EXPERIMENTS.md"

# ---------------- 8 篇文档 / 18 个分块：都是大学日常，谁都看得懂 ----------------
DOCS = [
    {"doc_id": "d01", "title": "校历与选课", "sections": [
        {"chunk_id": "c1", "path": "选课/开放时间",
         "text": "每学期选课系统在第 1 周周一 9 点开放，第 2 周周五 17 点关闭。预选阶段不限制人数，正选阶段按先到先得，名额满即止。"},
        {"chunk_id": "c2", "path": "选课/补退选",
         "text": "补退选仅在第 3 周开放，逾期不再受理。退选后已缴学分费不予退还，补选只能在仍有余量的课程里进行。"},
        {"chunk_id": "c3", "path": "选课/学分上限",
         "text": "本科生每学期修读学分上限为 28 学分，超过需院系审批；下限 12 学分，低于下限会触发学业预警并通知辅导员。"},
    ]},
    {"doc_id": "d02", "title": "图书馆借阅", "sections": [
        {"chunk_id": "c1", "path": "借阅/数量与借期",
         "text": "本科生可借 10 册，借期 30 天；研究生可借 20 册，借期 60 天。工具书和当期期刊一律不外借。"},
        {"chunk_id": "c2", "path": "借阅/续借与逾期",
         "text": "每册可在到期前续借 1 次，续借期 30 天。逾期按每册每天 0.1 元计费，逾期未还期间暂停全部借阅权限，缴清后恢复。"},
        {"chunk_id": "c3", "path": "空间/研讨间",
         "text": "研讨间须提前在馆内系统预约，每次最长 4 小时且最少 2 人使用。爽约 2 次后暂停预约权限 30 天。"},
    ]},
    {"doc_id": "d03", "title": "食堂与校园卡", "sections": [
        {"chunk_id": "c1", "path": "校园卡/充值与挂失",
         "text": "校园卡可通过校内 App 或食堂一楼自助机充值。丢失后先在 App 挂失，挂失前 24 小时内产生的消费由持卡人承担，补卡需带学生证。"},
        {"chunk_id": "c2", "path": "食堂/营业时间",
         "text": "第一食堂早餐 6 点 30 至 9 点、午餐 11 点至 13 点 30、晚餐 17 点至 19 点 30。节假日仅第二食堂一层开放，各餐结束时间提前 1 小时。"},
    ]},
    {"doc_id": "d04", "title": "宿舍与水电", "sections": [
        {"chunk_id": "c1", "path": "宿舍/门禁与晚归",
         "text": "宿舍楼门禁为 23 点至次日 6 点，晚归需刷卡登记。连续 3 次晚归会通知辅导员，并计入社区表现记录。"},
        {"chunk_id": "c2", "path": "宿舍/报修与用电",
         "text": "水电故障在后勤系统报修，一般 24 小时内响应。宿舍禁止使用大功率电器，违规一次没收并通报，造成损失的照价赔偿。"},
    ]},
    {"doc_id": "d05", "title": "快递驿站", "sections": [
        {"chunk_id": "c1", "path": "取件/取件码与代取",
         "text": "包裹入库后短信发送 6 位取件码，凭取件码或校园卡取件。代取需出示双方证件照片并登记，未登记不予放行。"},
        {"chunk_id": "c2", "path": "取件/保管期限",
         "text": "包裹免费保管 3 天，超期每天 0.5 元，超过 7 天退回寄件方。大件物品仅当日保管，当日未取即安排退回。"},
    ]},
    {"doc_id": "d06", "title": "考试与成绩", "sections": [
        {"chunk_id": "c1", "path": "考试/缓考",
         "text": "因病缓考须在考前提交校医院证明和缓考申请，考后补交一律不受理。缓考成绩按实际卷面记载，不额外扣分。"},
        {"chunk_id": "c2", "path": "成绩/查分与绩点",
         "text": "成绩在考后 10 个工作日内发布，复核申请限发布后 5 个工作日内提出。绩点按四分制换算，重修成绩覆盖原成绩但标注重修。"},
    ]},
    {"doc_id": "d07", "title": "请假与校医院", "sections": [
        {"chunk_id": "c1", "path": "请假/审批流程",
         "text": "请假 3 天以内由辅导员审批，超过 3 天需院系盖章并提交说明材料。销假须在返校当日完成，未销假按缺勤处理。"},
        {"chunk_id": "c2", "path": "校医院/转诊与报销",
         "text": "校医院门诊需先刷校园卡挂号。转诊至校外医院须持转诊单，无转诊单不予报销；报销单在每月 1 至 5 日集中受理。"},
    ]},
    {"doc_id": "d08", "title": "体育馆与社团", "sections": [
        {"chunk_id": "c1", "path": "体育馆/场地预约",
         "text": "羽毛球和乒乓球场地提前 2 天在体育系统预约，每人每天限 1 场 1 小时。预约后 15 分钟未到场视为放弃，累计 3 次暂停预约 1 周。"},
        {"chunk_id": "c2", "path": "社团/招新",
         "text": "社团招新集中在开学第 2 周，每名学生最多加入 3 个社团。新社团成立需 20 名发起人并提交章程，逾期不受理当学年申请。"},
    ]},
]

# ---------------- 12 道题：10 道有答案 + 2 道故意问不到的陷阱题 ----------------
RUBRIC = {"correctness": 2, "evidence": 2, "citation": 2, "structure": 2, "efficiency": 2}

QUESTIONS = [
    ("q01", "对比 选课开放 与 补退选 在时间窗口和逾期后果上的区别", True,
     [["d01", "c1"], ["d01", "c2"], ["d01", "c3"]], ["开放第1至2周", "补退选仅第3周", "学分下限触发预警"]),
    ("q02", "校园卡挂失 与 快递代取 各自需要什么凭证", True,
     [["d03", "c1"], ["d05", "c1"]], ["App挂失与补卡证件", "取件码或校园卡", "代取双方证件"]),
    ("q03", "续借 与 逾期 分别怎么影响图书馆借阅权限", True,
     [["d02", "c1"], ["d02", "c2"]], ["到期前可续借1次", "逾期按天计费", "未还期间暂停借阅"]),
    ("q04", "晚归登记 与 违规用电 在宿舍管理里分别触发什么处理", True,
     [["d04", "c1"], ["d04", "c2"]], ["23点门禁登记", "3次通知辅导员", "大功率电器没收通报"]),
    ("q05", "超期保管 与 大件物品 在快递驿站的时限规定有何不同", True,
     [["d05", "c1"], ["d05", "c2"]], ["免费3天", "超期每天0.5元", "大件仅当日"]),
    ("q06", "缓考申请 与 成绩复核 各自的截止时间", True,
     [["d06", "c1"], ["d06", "c2"]], ["缓考须考前提交", "考后补交不受理", "复核限发布后5个工作日"]),
    ("q07", "请假超过 3 天 与 校医院转诊 分别需要什么额外材料", True,
     [["d07", "c1"], ["d07", "c2"]], ["院系盖章与说明", "转诊单", "无转诊单不报销"]),
    ("q08", "场地预约 与 社团招新 在时间窗口上有什么共同限制", True,
     [["d08", "c1"], ["d08", "c2"]], ["提前2天预约", "招新集中第2周", "逾期不受理"]),
    ("q09", "选课学分上限 与 成绩绩点 分别由哪条规则约束", True,
     [["d01", "c3"], ["d06", "c2"]], ["上限28学分", "下限12学分预警", "绩点四分制"]),
    ("q10", "节假日食堂 与 大件快递 在时限上缩短了哪些", True,
     [["d03", "c2"], ["d05", "c2"]], ["仅二层一层开放", "各餐提前1小时", "大件当日退回"]),
    ("q11", "学校 2027 年未公开的宿舍空调内部定价是多少", False,
     [], ["语料中无此信息", "应拒答"]),
    ("q12", "请给出没有任何公开资料支持的某社团内部经费精确数额", False,
     [], ["语料中无此信息", "应拒答"]),
]


def backup(src, suffix):
    dst = src.with_name(src.stem + suffix + src.suffix)
    if not dst.exists():
        shutil.copy2(src, dst)
        print("  备份 ->", dst.name)


def main():
    print("第 3 步：换成「大学日常」题库\n")
    print("[1/5] 备份原来的示例语料和 E005 结果（只备份一次，不会覆盖你的提交历史）")
    backup(CORPUS, "_示例备份")
    backup(DATASET, "_示例备份")
    backup(RESULTS, "_E005")

    print("[2/5] 写入 8 篇文档 / 18 个分块")
    CORPUS.write_text(
        "\n".join(json.dumps(d, ensure_ascii=False) for d in DOCS) + "\n",
        encoding="utf-8")

    print("[3/5] 写入 12 道题（含 2 道故意问不到的陷阱题）")
    rows = []
    for qid, q, answerable, gold, points in QUESTIONS:
        rows.append({
            "id": qid, "question": q,
            "difficulty": "multi_hop" if answerable else "unanswerable",
            "answerable": answerable,
            "gold_evidence": gold, "key_points": points, "rubric": RUBRIC,
        })
    DATASET.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8")

    print("[4/5] 重跑四组消融（数字由脚本实算，不是我编的）\n")
    subprocess.run([sys.executable, str(ROOT / "eval" / "benchmark.py")],
                   cwd=str(ROOT), check=True)

    print("\n[5/5] 留证")
    shutil.copy2(RESULTS, ROOT / "eval" / "results_我的题库.json")
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    lines = []
    for m in data["metrics"]:
        lines.append(
            f"{m['config']}: 完成率 {m['task_completion_rate']:.0%} / "
            f"召回 {m['evidence_recall_at5']:.0%} / "
            f"引用 {m['citation_precision']:.0%} / "
            f"幻觉 {m['hallucination_rate']:.0%}")
    note = (
        "\n\n## E006  换成我自己看得懂的题库（大学日常）\n\n"
        "- 动机：示例语料讲 Agent 机制，我看不懂也没法判断答案对不对；换成选课、图书馆、"
        "食堂、快递、宿舍、缓考这类日常规则，题目对不对我瞄一眼就知道。\n"
        "- 改动：data/corpus.jsonl（8 篇 / 18 块）、eval/dataset.jsonl（12 题，含 2 道"
        "不可回答陷阱题）整体替换；原示例语料备份为 *_示例备份.jsonl，E005 结果备份为 "
        "results_E005.json，均保留。\n"
        "- 结果（脚本实算，见 eval/results_我的题库.json）：\n"
        + "\n".join("  - " + x for x in lines) + "\n"
        "- 说明：E005 是**示例语料上**的历史结论，保留在上方不动；本轮是第二套独立语料，"
        "用于看同一套 Runtime 换语料后结论还成不成立。\n"
        "- 复现：python eval/benchmark.py（当前默认语料已是本轮题库）。\n"
    )
    with EXPERIMENTS.open("a", encoding="utf-8") as f:
        f.write(note)

    print("  已写 eval/results_我的题库.json")
    print("  已在 EXPERIMENTS.md 追加 E006")
    print("\n=== 你这套题库跑出来的四行（把这段整段贴给我）===")
    for x in lines:
        print(x)
    print("\n完成。原示例语料和 E005 数字都还在备份里，没丢。")


if __name__ == "__main__":
    main()
