"""把 work/bugfix-pool.jsonl 里的素材做成题目：下载初始环境 + 打印写 prompt 所需的材料。

    uv run python tools/bugfix_build.py --take 10 --start 53

每道题：
  1. 从 codeload 下载「有 bug 的那一版」（fix 的父提交）到 work/imported/<题号>-<slug>
  2. 把参考答案（fix 提交 + diff + issue 原文）写到 ~/.coding-agent-tasks/refs/<题号>.json
  3. 在屏幕上打印写 prompt 需要的材料（改了哪些文件、diff 的增删行、issue 标题）
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
WORK = os.path.abspath(os.path.join(REPO, "..", "..", "work"))
POOL = os.path.join(WORK, "bugfix-pool.jsonl")
IMPORTED = os.path.join(WORK, "imported")
REFS = os.path.join(os.path.expanduser("~"), ".coding-agent-tasks", "refs")
STATE = os.path.join(os.path.expanduser("~"), ".coding-agent-tasks", "bugfix-built.json")

EXT_LANG = [
    (".py", "Python", "python", 0),
    (".js", "JavaScript", "node", 1),
    (".mjs", "JavaScript", "node", 1),
    (".cjs", "JavaScript", "node", 1),
    (".ts", "TypeScript", "node", 1),
    (".tsx", "TypeScript", "node", 1),
    (".go", "Go", "go", 2),
    (".java", "Java", "java", 3),
    (".kt", "Kotlin", "kotlin", 3),
    (".rs", "Rust", "rust", 4),
    (".cs", "C#", "dotnet", 5),
    (".rb", "Ruby", "ruby", 6),
    (".php", "PHP", "php", 6),
]


def token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\nusername=kundawang\n\n",
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout or ""
    match = re.search(r"^password=(.+)$", out, re.M)
    return match.group(1).strip() if match else ""


def lang_of(record):
    counts = {}
    for path in record["files"]:
        low = path.lower()
        for ext, name, key, rank in EXT_LANG:
            if low.endswith(ext):
                counts[(name, key, rank)] = counts.get((name, key, rank), 0) + 1
    if not counts:
        return "Unknown", "unknown", 9
    name, key, rank = max(counts, key=lambda k: counts[k])
    return name, key, rank


def is_test(path):
    low = path.lower()
    if re.search(r"(^|/)(tests?|spec|__tests__|fixtures?)/", low):
        return True
    return os.path.basename(low).startswith(("test_", "test-", "spec_", "spec-"))


def long_path(path):
    """Windows 上仓库里有超长路径，加 \\\\?\\ 前缀才能写进去。"""
    if os.name != "nt":
        return path
    absolute = os.path.abspath(path)
    return "\\\\?\\" + absolute if not absolute.startswith("\\\\?\\") else absolute


def download(repo, sha, dest, tok):
    """下载某个提交的源码快照。先解到 .part 目录，成功了再换过去，免得失败把旧内容清空。"""
    marker = os.path.join(dest, ".codex-ready")
    if os.path.exists(marker):
        with open(marker, encoding="utf-8") as fh:
            if fh.read().strip() == f"{repo} {sha}":
                return dest
    staging = dest + ".part"
    if os.path.isdir(staging):
        shutil.rmtree(long_path(staging), ignore_errors=True)
    os.makedirs(staging, exist_ok=True)
    url = f"https://codeload.github.com/{repo}/tar.gz/{sha}"
    tar_path = staging + ".tar.gz"
    cmd = ["curl.exe", "-sS", "-L", "--max-time", "300", "-H", "User-Agent: codex-cli"]
    if tok:
        cmd += ["-H", f"Authorization: token {tok}"]
    cmd += ["-o", tar_path, url]
    for attempt in range(3):
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0 and os.path.exists(tar_path) and os.path.getsize(tar_path) > 0:
            break
        time.sleep(4 * (attempt + 1))
        if attempt == 2:
            shutil.rmtree(long_path(staging), ignore_errors=True)
            raise RuntimeError((proc.stderr or "下载失败")[:100])
    skipped = 0
    target = long_path(staging)
    with tarfile.open(tar_path) as tar:
        members = [m for m in tar.getmembers() if m.name]
        root = os.path.commonpath([m.name.split("/")[0] for m in members])
        for member in members:
            if member.name == root:
                continue
            member.name = member.name[len(root) + 1:]
            if not member.name or ".." in member.name.split("/"):
                continue
            if len(member.name) > 200:
                skipped += 1
                continue
            try:
                tar.extract(member, target, filter="data")
            except (OSError, ValueError):
                skipped += 1
    os.remove(tar_path)
    with open(os.path.join(staging, ".codex-ready"), "w", encoding="utf-8") as fh:
        fh.write(f"{repo} {sha}\n")
    if os.path.isdir(dest):
        shutil.rmtree(long_path(dest), ignore_errors=True)
    os.rename(long_path(staging), long_path(dest))
    if skipped:
        print(f"   （{repo}: 跳过 {skipped} 个超长路径/特殊文件）")
    return dest


def compact_diff(record, max_lines=22, width=150):
    """只留主代码文件的增删行，去掉上下文，够看懂 bug 就行。"""
    blocks = re.split(r"^--- ", record["patch"], flags=re.M)[1:]
    chosen = None
    for block in blocks:
        head = block.split("\n")[0]
        name = head.split(" ")[0]
        if not is_test(name) and not is_doc(name):
            chosen = (name, block)
            break
    if not chosen:
        for block in blocks:
            head = block.split("\n")[0]
            name = head.split(" ")[0]
            if not is_doc(name):
                chosen = (name, block)
                break
    if not chosen:
        head = blocks[0].split("\n")[0] if blocks else ""
        chosen = (head.split(" ")[0], blocks[0] if blocks else "")
    name, block = chosen
    out = []
    for line in block.split("\n")[1:]:
        if line.startswith("+++") or line.startswith("@@") or line.startswith("-") or \
                line.startswith("+"):
            if line.startswith("@@"):
                continue
            out.append(line[:width])
        if len(out) >= max_lines:
            break
    return name, "\n".join(out)


DOC_EXT = (".rst", ".md", ".txt", ".toml", ".cfg", ".ini", ".yaml", ".yml", ".json", ".pot")


def is_doc(path):
    low = path.lower()
    if low.endswith(DOC_EXT):
        return True
    return bool(re.search(r"(^|/)(docs?|changelog|news)/", low)) or \
        os.path.basename(low).startswith(("changes", "changelog", "history", "news"))


def print_material(task_id, record):
    lang, _, _ = lang_of(record)
    name, diff = compact_diff(record)
    issue = record.get("issue") or {}
    print(f"\n=== {task_id}  {record['repo']}  ({lang})  {record['changes']}行/"
          f"{len(record['files'])}文件 ===")
    print(f"  文件: {', '.join(record['files'])}")
    print(f"  提交: {record['fix_message']}")
    if issue:
        body = re.sub(r"\s+", " ", issue.get("body") or "")[:420]
        print(f"  issue #{issue.get('number')}: {issue.get('title')}")
        if body:
            print(f"    {body}")
    print(f"  主文件 {name}:")
    for line in diff.split("\n"):
        print("    " + line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", type=int, default=10)
    ap.add_argument("--start", type=int, default=53)
    ap.add_argument("--offset", type=int, default=0, help="从排好序的第几条开始取")
    ap.add_argument("--print-only", action="store_true", help="只打印，不下载")
    ap.add_argument("--assign-only", action="store_true", help="只分配题号并写 refs，不下载")
    ap.add_argument("--fetch", action="store_true", help="把已分配但还没下载好的工作区补齐")
    ap.add_argument("--show", default="", help="打印已分配题目的材料：如 lk-056,lk-057 或 all")
    ap.add_argument("--drop", default="", help="撤掉几个题号（素材不合适时用），如 lk-054,lk-055")
    ap.add_argument("--only", default="", help="只从这些仓库里取（逗号分隔，按给定顺序）")
    args = ap.parse_args()

    with open(POOL, encoding="utf-8") as fh:
        pool = [json.loads(line) for line in fh if line.strip()]
    pool.sort(key=lambda r: (lang_of(r)[2], r["repo"].lower()))

    state = {}
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            state = json.load(fh)

    skip_path = os.path.join(WORK, "bugfix-skip.txt")
    skipped = set()
    if os.path.exists(skip_path):
        with open(skip_path, encoding="utf-8") as fh:
            skipped = {line.split("#")[0].strip() for line in fh if line.split("#")[0].strip()}

    if args.show:
        names = sorted(state) if args.show == "all" else [s.strip() for s in args.show.split(",")]
        for name in names:
            ref_file = os.path.join(REFS, name + ".json")
            if not os.path.exists(ref_file):
                print(f"!! {name} 没有 refs")
                continue
            with open(ref_file, encoding="utf-8") as fh:
                print_material(name, json.load(fh))
        return 0

    if args.drop:
        for name in [s.strip() for s in args.drop.split(",") if s.strip()]:
            info = state.pop(name, None)
            ref_file = os.path.join(REFS, name + ".json")
            if os.path.exists(ref_file):
                os.remove(ref_file)
            if info:
                dest = info.get("workspace") or ""
                if dest and os.path.isdir(dest) and os.path.abspath(dest).startswith(IMPORTED):
                    shutil.rmtree(long_path(dest), ignore_errors=True)
                print(f"撤掉 {name}  {info['repo']}")
            else:
                print(f"撤掉 {name}（本来就没分配）")
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2)
        return 0

    if args.fetch:
        tok = token()
        pending = 0
        for name in sorted(state):
            info = state[name]
            dest = info.get("workspace") or os.path.join(
                IMPORTED, f"{name}-{info.get('slug') or info['repo'].split('/')[1].lower()}")
            marker = os.path.join(dest, ".codex-ready")
            if os.path.exists(marker):
                continue
            pending += 1
            record = None
            ref_file = os.path.join(REFS, name + ".json")
            if os.path.exists(ref_file):
                with open(ref_file, encoding="utf-8") as fh:
                    record = json.load(fh)
            if not record:
                continue
            try:
                download(record["repo"], record["buggy_commit"], dest, tok)
                info["workspace"] = dest
                print(f"{name}  {record['repo']}  ok")
            except Exception as exc:
                print(f"{name}  {record['repo']}  下载失败：{exc}")
            with open(STATE, "w", encoding="utf-8") as fh:
                json.dump(state, fh, ensure_ascii=False, indent=2)
        if not pending:
            print("所有工作区都齐了")
        return 0

    used_repos = {v["repo"] for v in state.values()}
    free = [r for r in pool if r["repo"] not in used_repos and r["repo"] not in skipped]
    if args.only:
        wanted = [s.strip() for s in args.only.split(",") if s.strip()]
        by_repo = {r["repo"]: r for r in free}
        free = [by_repo[name] for name in wanted if name in by_repo]

    used_ids = set()
    for key in state:
        try:
            used_ids.add(int(key.split("-")[1]))
        except (IndexError, ValueError):
            pass

    def alloc_id():
        number = args.start
        while number in used_ids:
            number += 1
        used_ids.add(number)
        return "lk-%03d" % number

    batch = free[args.offset:args.offset + args.take]
    if not batch:
        print("没有更多素材了")
        return 0

    tok = "" if args.assign_only else token()
    os.makedirs(REFS, exist_ok=True)
    for index, record in enumerate(batch):
        slug = record.get("slug") or record["repo"].split("/")[1].lower()
        lang, lang_key, _ = lang_of(record)
        task_id = ""
        if not args.print_only:
            task_id = alloc_id()
            dest = os.path.join(IMPORTED, f"{task_id}-{slug}")
            with open(os.path.join(REFS, task_id + ".json"), "w", encoding="utf-8") as fh:
                json.dump(record, fh, ensure_ascii=False, indent=2)
            state[task_id] = {"repo": record["repo"], "slug": slug, "lang": lang,
                              "lang_key": lang_key, "workspace": dest,
                              "files": record["files"], "changes": record["changes"]}
            with open(STATE, "w", encoding="utf-8") as fh:
                json.dump(state, fh, ensure_ascii=False, indent=2)
            if not args.assign_only:
                try:
                    download(record["repo"], record["buggy_commit"], dest, tok)
                except Exception as exc:
                    print(f"!! {task_id} {record['repo']} 下载失败：{exc}")
        if not task_id:
            task_id = f"(未建) {record['repo']}"

        print_material(task_id, record)
    return 0


if __name__ == "__main__":
    sys.exit(main())
