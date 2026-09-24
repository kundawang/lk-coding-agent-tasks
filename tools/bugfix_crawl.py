"""批量挖「真实 bug」题目素材。

一个 fix 提交 = 这道题的参考答案。我们取它的父提交当初始环境（有 bug 的那一版），
修复本身不进仓库。每条素材写一行 JSON 到 work/bugfix-pool.jsonl，带 patch 片段，
方便后面写 prompt。

用法：
    uv run python tools/bugfix_crawl.py --want 120 --workers 8
    uv run python tools/bugfix_crawl.py --plan          # 只看仓库清单

只收 MIT / Apache-2.0 / BSD / ISC 这类宽松许可；GPL、MPL、没写许可证的都跳过。
"""

import argparse
import concurrent.futures as futures
import json
import os
import re
import subprocess
import sys
import threading
import time

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
WORK = os.path.abspath(os.path.join(REPO, "..", "..", "work"))
REPO_LIST = os.path.join(TOOLS, "bugfix_repos.txt")

API = "https://api.github.com"
OK_LICENSES = ("MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "Unlicense")
CODE_EXT = (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".java", ".kt", ".rs",
            ".cs", ".rb", ".php", ".swift", ".c", ".h", ".cpp")

FIX_WORDS = re.compile(r"^(fix|fixed|fixes|bugfix|hot\s?fix|patch|repair)\b|修复|修正", re.I)
SKIP_WORDS = re.compile(r"typo|readme|changelog|release|bump|version|lint|format|docs?\b|comment|"
                        r"whitespace|revert|merge|translation|i18n|dependabot|upgrade|"
                        r"renovate|prettier|eslint|snapshot", re.I)


def token():
    for env in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(env):
            return os.environ[env]
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\nusername=kundawang\n\n",
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout or ""
    match = re.search(r"^password=(.+)$", out, re.M)
    return match.group(1).strip() if match else ""


def curl(url, tok="", output="", timeout=30):
    cmd = ["curl.exe", "-sS", "-L", "--max-time", str(timeout),
           "-H", "User-Agent: codex-cli", "-H", "Accept: application/vnd.github+json"]
    if tok:
        cmd += ["-H", f"Authorization: token {tok}"]
    if output:
        cmd += ["-o", output]
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if output:
        return "" if proc.returncode == 0 else (proc.stderr or "curl failed")
    return proc.stdout or ""


class Client:
    def __init__(self, tok):
        self.tok = tok
        self.lock = threading.Lock()
        self.calls = 0

    def api(self, path, tries=3):
        last = ""
        for attempt in range(tries):
            with self.lock:
                self.calls += 1
            text = curl(API + path, self.tok)
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                last = "非 JSON: " + text[:80]
                time.sleep(1.5 * (attempt + 1))
                continue
            if isinstance(data, dict) and data.get("message"):
                last = str(data["message"])[:80]
                if "rate limit" in last.lower() or "abuse" in last.lower():
                    time.sleep(20 * (attempt + 1))
                    continue
                raise RuntimeError(last)
            return data
        raise RuntimeError(last or "取不到")


def first_line(text):
    return (text or "").split("\n")[0].strip()


def build_patch(detail, limit=2600):
    chunks = []
    for item in detail.get("files") or []:
        patch = item.get("patch") or ""
        head = "--- " + item["filename"] + f" (+{item.get('additions')}/-{item.get('deletions')})"
        chunks.append(head + "\n" + patch)
    return "\n".join(chunks)[:limit]


def looks_like_code(paths):
    ok = False
    for path in paths:
        low = path.lower()
        if not low.endswith(CODE_EXT):
            continue
        if re.search(r"(^|/)(tests?|spec|__tests__|fixtures?)/", low):
            continue
        if os.path.basename(low).startswith(("test_", "test-", "spec_", "spec-")):
            continue
        ok = True
    return ok


def issue_from_message(repo, message, client):
    for num in re.findall(r"#(\d+)", message or "")[:3]:
        try:
            data = client.api(f"/repos/{repo}/issues/{num}")
        except Exception:
            continue
        if data.get("pull_request"):
            continue
        body = (data.get("body") or "").strip()
        return {"number": num, "title": data.get("title") or "", "body": body[:2200],
                "url": data.get("html_url") or ""}
    return None


def pick_candidate(repo, client, min_lines, max_lines, max_files):
    info = client.api(f"/repos/{repo}")
    lic = ((info.get("license") or {}).get("spdx_id") or "").strip()
    if lic not in OK_LICENSES:
        return None, "许可证 " + (lic or "未知")
    if info.get("archived"):
        return None, "仓库已归档"
    branch = info.get("default_branch") or "main"
    stars = info.get("stargazers_count") or 0

    best = None
    checked = 0
    for page in (1, 2):
        commits = client.api(f"/repos/{repo}/commits?per_page=60&sha={branch}&page={page}")
        if not isinstance(commits, list) or not commits:
            break
        for item in commits:
            msg = first_line(item["commit"]["message"])
            if not FIX_WORDS.search(msg) or SKIP_WORDS.search(msg):
                continue
            if len(item.get("parents") or []) != 1:
                continue
            if checked >= 6:
                break
            checked += 1
            try:
                detail = client.api(f"/repos/{repo}/commits/{item['sha']}")
            except Exception:
                continue
            files = detail.get("files") or []
            changes = sum((f.get("changes") or 0) for f in files)
            paths = [f["filename"] for f in files]
            if not (min_lines <= changes <= max_lines):
                continue
            if not (1 <= len(files) <= max_files):
                continue
            if not looks_like_code(paths):
                continue
            record = {
                "repo": repo, "license": lic, "stars": stars,
                "fix_commit": item["sha"], "buggy_commit": item["parents"][0]["sha"],
                "fix_message": msg, "changes": changes, "files": paths,
                "date": (item["commit"]["author"]["date"] or "")[:10],
                "patch": build_patch(detail),
            }
            record["issue"] = issue_from_message(repo, detail["commit"]["message"], client)
            if record["issue"]:
                return record, ""
            if not best:
                best = record
        if best:
            break
    if best:
        return best, ""
    return None, f"没有 {min_lines}~{max_lines} 行 / 1~{max_files} 文件的修复"


def load_repos():
    repos, seen = [], set()
    with open(REPO_LIST, encoding="utf-8") as fh:
        for raw in fh:
            name = raw.split("#")[0].strip()
            if not name or "/" not in name or " " in name:
                continue
            if name not in seen:
                seen.add(name)
                repos.append(name)
    return repos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--want", type=int, default=120, help="至少凑够多少条")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=os.path.join(WORK, "bugfix-pool.jsonl"))
    ap.add_argument("--min-lines", type=int, default=5)
    ap.add_argument("--max-lines", type=int, default=120)
    ap.add_argument("--max-files", type=int, default=4)
    ap.add_argument("--plan", action="store_true", help="只打印仓库清单")
    args = ap.parse_args()

    repos = load_repos()
    if args.plan:
        print(f"{len(repos)} 个候选仓库")
        for name in repos:
            print("  " + name)
        return 0

    tok = token()
    if not tok:
        raise SystemExit("拿不到 GitHub 凭据")
    done = {}
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    item = json.loads(line)
                    done[item["repo"]] = item
    todo = [r for r in repos if r not in done]
    print(f"目标 {args.want} 条，已有 {len(done)} 条，待查 {len(todo)} 个仓库", flush=True)
    if len(done) >= args.want or not todo:
        return 0

    client = Client(tok)
    lock = threading.Lock()
    stop = threading.Event()
    hits = list(done.values())
    misses = []

    def work(repo):
        if stop.is_set():
            return
        try:
            record, why = pick_candidate(repo, client, args.min_lines, args.max_lines, args.max_files)
        except Exception as exc:
            record, why = None, "出错 " + str(exc)[:60]
        with lock:
            if record:
                record["slug"] = repo.split("/")[1].lower().replace(".", "")
                hits.append(record)
                with open(args.out, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(f"[{len(hits)}/{args.want}] {repo:32s} {record['changes']:4d}行/"
                      f"{len(record['files'])}文件 issue={'有' if record.get('issue') else '无'}  "
                      f"{record['fix_message'][:48]}", flush=True)
                if len(hits) >= args.want:
                    stop.set()
            else:
                misses.append((repo, why))
                print(f"        - {repo:32s} {why}", flush=True)

    with futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(work, todo))

    print(f"\n拿到 {len(hits)} 条素材 -> {args.out}（API 调用 {client.calls} 次）", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
