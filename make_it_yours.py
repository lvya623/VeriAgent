# -*- coding: utf-8 -*-
"""
第 1 步：把这套骨架登记成「你的项目」。
运行：python make_it_yours.py
作用：改 README 标题、写署名与 LICENSE、建 git 首次提交（留下属于你的提交历史）。
不改动 veriagent/ 里的任何代码，不碰语料与评测集，安全可重复运行。
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def ask(label, default=""):
    s = input(label + ("（直接回车用「%s」）: " % default if default else ": ")).strip()
    return s or default


def run(cmd, cwd=ROOT):
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", "command not found"
    except Exception as e:
        return 1, "", str(e)


def main():
    print("=" * 60)
    print("把项目变成你的 · 第 1 步")
    print("=" * 60)
    print("只做三件事：署名 / 展示名 / 首次提交。代码逻辑一行都不动。\n")

    author = ask("你的姓名或 ID（会出现在署名和 git 提交里）", "【你的名字】")
    display = ask("项目展示名（README 大标题，包名 veriagent 保持不变）", "VeriAgent")
    email = ask("git 提交用邮箱（不推 GitHub 也可以随便填）", "me@localhost")
    github = ask("GitHub 用户名（没有就回车跳过）", "")

    # 1. README 标题
    readme = ROOT / "README.md"
    if readme.exists():
        lines = readme.read_text(encoding="utf-8").splitlines()
        if lines and lines[0].startswith("# "):
            lines[0] = "# " + display
        readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("[ok] README 标题 ->", display)

    # 2. 署名文件
    today = date.today().isoformat()
    (ROOT / "AUTHORS.md").write_text(
        "# 作者与来源\n\n"
        "- 实现与维护：%s\n"
        "- 起始日期：%s\n"
        "- 代码基线：一套最小 Agent Runtime 参考骨架；本项目在其上完成\n"
        "  语料与评测集替换、参数实验、消融复跑与实验记录。\n"
        "- 说明：`veriagent/` 为 Python 包名，保持一致以免破坏 import；\n"
        "  对外展示名为「%s」。\n" % (author, today, display),
        encoding="utf-8")
    print("[ok] 生成 AUTHORS.md")

    # 3. LICENSE
    (ROOT / "LICENSE").write_text(
        "MIT License\n\nCopyright (c) %s %s\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        "of this software and associated documentation files (the \"Software\"), to deal\n"
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n\n"
        "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE.\n" % (today[:4], author),
        encoding="utf-8")
    print("[ok] 生成 LICENSE（MIT）")

    gi = ROOT / ".gitignore"
    if not gi.exists():
        gi.write_text("__pycache__/\n*.pyc\n.venv/\nvenv/\n.idea/\n.vscode/\n",
                      encoding="utf-8")
        print("[ok] 生成 .gitignore")

    # 4. 一分钟讲法顶部插一行归属
    card = ROOT / "一分钟讲法.md"
    if card.exists():
        txt = card.read_text(encoding="utf-8")
        mark = "> 维护："
        if mark not in txt:
            head, sep, rest = txt.partition("\n")
            card.write_text(head + "\n\n" + mark + author + " · " + display + sep + rest,
                            encoding="utf-8")
            print("[ok] 一分钟讲法.md 加入归属")

    # 5. git 首次提交
    print("\n--- git 提交 ---")
    if not (ROOT / ".git").exists():
        code, out, err = run(["git", "init"])
        if code == 0:
            print("[ok] git init")
        else:
            print("[skip] git 不可用或初始化失败：", err or out)
            print("      不影响后面步骤，跳过提交即可。")
            finish(author, display, github)
            return
    else:
        print("[ok] 已是 git 仓库，跳过 init")

    run(["git", "add", "-A"])
    code, out, err = run(["git", "-c", "user.name=" + author,
                          "-c", "user.email=" + email, "commit",
                          "-m", "Initial commit: " + display + " by " + author])
    if code == 0:
        print("[ok] 首次提交完成")
    else:
        print("[skip] 提交未成功：", (err or out)[:200])
    code, out, _ = run(["git", "log", "--oneline", "-1"])
    if code == 0 and out:
        print("      ", out)
    finish(author, display, github)


def finish(author, display, github):
    print("\n" + "=" * 60)
    print("第 1 步完成 ✅")
    print("=" * 60)
    print("现在把这个文件里的输出整段贴给我，我们走第 2 步：")
    print("  1) 打开 我的第一次实验.md，改一个参数、重跑、记录前后差异")
    print("  2) 告诉我你想换成哪个领域，我陪你把 12 道示例题改成你自己的题")
    if github:
        print("\n推到你的 GitHub（可选，等第 2 步做完再推更合适）：")
        print("  git remote add origin https://github.com/%s/%s.git" % (github, display))
        print("  git branch -M main && git push -u origin main")
    print("\n注意：这一步只是登记归属，简历里的数字仍来自示例语料。")
    print("      第 2 步跑出你自己的结果后，才算真正能写进简历。")


if __name__ == "__main__":
    main()
