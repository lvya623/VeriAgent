# -*- coding: utf-8 -*-
"""
第 0 步（先跑这个）：修掉一个会让评测数字自己漂移的 bug。
运行：python 第0步_修可复现性.py
背景：veriagent/search.py 的向量索引用了 Python 内置 hash()，
      它每次启动进程会随机化，导致同一份评测集两次跑分不一致。
      改成确定性 crc32 后，seed=42 才名副其实，单变量实验才做得下去。
只改一行索引逻辑，不动任何算法与评测口径。
"""
import filecmp
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "veriagent" / "search.py"
RESULTS = ROOT / "eval" / "results.json"
OLD = "v[hash(g) % 512] += 1"
NEW = 'v[zlib.crc32(g.encode("utf-8")) % 512] += 1'
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def run_bench():
    r = subprocess.run([sys.executable, "eval/benchmark.py"], cwd=str(ROOT),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    if r.returncode != 0:
        print("[error] benchmark 没跑通：", (r.stderr or r.stdout)[-400:])
        return False
    return True


def main():
    print("=" * 60)
    print("第 0 步 · 修可复现性")
    print("=" * 60)
    if not TARGET.exists():
        print("[error] 找不到 veriagent/search.py，请确认本脚本放在项目根目录。")
        return
    src = TARGET.read_text(encoding="utf-8")

    if "zlib.crc32" in src:
        print("[ok] 已是修复版，跳过改动。")
    elif OLD in src:
        if "import zlib" not in src:
            src = src.replace("import re\n", "import re\nimport zlib\n", 1)
        src = src.replace(OLD, NEW, 1)
        TARGET.write_text(src, encoding="utf-8")
        print("[ok] 已把 hash(g) 换成 zlib.crc32 确定性哈希。")
    else:
        print("[warn] 没找到预期代码行，可能你已改过 search.py。")
        print("       请手动确认 _vectorize 里用的是确定性哈希，然后继续。")

    print("\n--- 连跑两次，比对结果文件 ---")
    if not run_bench():
        return
    a = ROOT / "eval" / "_run1.json"
    a.write_text(RESULTS.read_text(encoding="utf-8"), encoding="utf-8")
    if not run_bench():
        return
    same = filecmp.cmp(str(a), str(RESULTS), shallow=False)
    a.unlink(missing_ok=True)
    if same:
        print("[ok] 两次 eval/results.json 逐字节一致 ✅ 可复现了")
    else:
        print("[fail] 两次结果仍不一致，把本段输出贴给我，我接着查。")
        return

    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    print("\n--- 修复后的稳定基线（这就是你第 2 步的对照值）---")
    for m in data["metrics"]:
        print("  %-22s 完成 %3d%%  召回 %3d%%  引用 %3d%%  幻觉 %3d%%" % (
            m["config"], round(m["task_completion_rate"] * 100),
            round(m["evidence_recall_at5"] * 100),
            round(m["citation_precision"] * 100),
            round(m["hallucination_rate"] * 100)))
    print("\n把这四行抄下来，然后打开 跟我做_三步.md 从第 1 步开始。")
    print("（第 2 步的「改之前」就用这四行，不用再备份一次。）")


if __name__ == "__main__":
    main()
