"""把已经分配好题号的 bug 素材正式建成题目（建工作区、铺桌面 A/B、推 base 分支）。

    uv run python tools/bugfix_batch.py --from 53 --to 65
    uv run python tools/bugfix_batch.py --ids lk-053,lk-054

依赖：
  - ~/.coding-agent-tasks/bugfix-built.json  题号 -> 仓库/工作区（由 bugfix_build.py 写）
  - work/bugfix-titles.json                  题号 -> 标题
  - work/lk-0xx-prompt.txt                   题号 -> prompt 原文
"""

import argparse
import json
import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
WORK = os.path.abspath(os.path.join(REPO, "..", "..", "work"))
sys.path.insert(0, TOOLS)

import bugfix_build as build  # noqa: E402
import task as task_mod  # noqa: E402


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def push(task_id, tries=12, delay=8.0):
    cmd = [sys.executable, os.path.join(TOOLS, "push.py"), task_id,
           "--tries", str(tries), "--delay", str(delay)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="")
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--to", dest="end", type=int, default=0)
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--only-fetch", action="store_true", help="只补齐工作区，不建题")
    args = ap.parse_args()

    state = load_json(build.STATE, {})
    titles = load_json(os.path.join(WORK, "bugfix-titles.json"), {})

    if args.ids:
        ids = [s.strip().lower() for s in args.ids.split(",") if s.strip()]
    else:
        ids = sorted(k for k in state
                     if args.start <= int(k.split("-")[1]) <= args.end)

    tok = build.token()
    for task_id in ids:
        info = state.get(task_id)
        if not info:
            print(f"?? {task_id} 还没分配")
            continue
        prompt_file = os.path.join(WORK, f"{task_id}-prompt.txt")
        record = load_json(os.path.join(build.REFS, task_id + ".json"), None)
        dest = info.get("workspace") or os.path.join(
            build.IMPORTED, f"{task_id}-{info.get('slug') or info['repo'].split('/')[1].lower()}")
        marker = os.path.join(dest, ".codex-ready")
        if not os.path.exists(marker):
            try:
                build.download(info["repo"], record["buggy_commit"], dest, tok)
                info["workspace"] = dest
                with open(build.STATE, "w", encoding="utf-8") as fh:
                    json.dump(state, fh, ensure_ascii=False, indent=2)
            except Exception as exc:
                print(f"!! {task_id} {info['repo']} 工作区下载失败：{exc}")
                continue
        if args.only_fetch:
            print(f"ok {task_id} {info['repo']} 工作区齐了")
            continue
        if not os.path.exists(prompt_file):
            print(f"!! {task_id} 还差 prompt：{prompt_file}")
            continue
        if os.path.exists(task_mod.task_dir(task_id.upper())):
            print(f"-- {task_id} 已经建过，跳过")
            continue
        title = titles.get(task_id) or f"{info['repo']} 真实 bug 修复"
        lang = f"{info['lang']}, {info['repo'].split('/')[1]}"
        # 上一次跑崩了可能把工作区留在别的分支上，先强制回到 main 再建题
        subprocess.run(["git", "checkout", "-f", "-q", "main"], cwd=build.REPO, capture_output=True)
        subprocess.run(["git", "reset", "-q", "--hard"], cwd=build.REPO, capture_output=True)
        subprocess.run(["git", "clean", "-fdq"], cwd=build.REPO, capture_output=True)
        ns = argparse.Namespace(
            id=task_id.upper(), workspace=dest, prompt_file=prompt_file, title=title,
            task_type="Bug 修复", difficulty="困难", lang=lang,
            harness="Codex CLI", harness_version="0.155.0", os="Windows",
            env_level="有外部依赖，未容器化", notes="从公开仓库的真实修复提交反推的题目",
            root="", push=False)
        try:
            task_mod.cmd_new(ns)
        except SystemExit as exc:
            print(f"!! {task_id} 建题失败：{exc}")
            # 建题中途失败会在仓库里留下半截工作区，先收拾干净，别影响后面几道
            subprocess.run(["git", "reset", "-q", "--hard"], cwd=build.REPO, capture_output=True)
            subprocess.run(["git", "clean", "-fdq"], cwd=build.REPO, capture_output=True)
            continue
        print(f"++ {task_id} {info['repo']} -> {title}")
        if not args.no_push:
            ok, out = push(task_id.upper())
            print(f"   推送 {'成功' if ok else '没成功'}  {out.strip().splitlines()[-1] if out.strip() else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
