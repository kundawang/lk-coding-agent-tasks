"""从公开仓库里挖「真实 bug」的题目：把某个修复提交的父提交做成初始环境。

思路：一个 fix 提交 = 这个 bug 的参考答案。我们取它的父提交当"有 bug 的那一版"，
修复本身不放进仓库（单独存到本机 refs 目录，事后核对用）。

用法：
    uv run python tools/import_bugfix.py --plan                 # 只看候选，不动任何东西
    uv run python tools/import_bugfix.py --take 5 --start 52    # 取 5 道，做成 lk-052 起

只处理 MIT / Apache-2.0 / BSD 这类宽松许可的仓库；GPL 或没写许可证的会跳过。
需要认证 API：从 git 凭据里取 kundawang 的 token（不会打印出来）。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tarfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import task as task_mod  # noqa: E402

API = "https://api.github.com"
OK_LICENSES = ("MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC")

# 候选仓库：都是用得比较广、许可证宽松、bug 修复提交比较规整的
CANDIDATES = [
    ("pallets/click", "Python"),
    ("psf/requests", "Python"),
    ("encode/httpx", "Python"),
    ("pallets/flask", "Python"),
    ("tqdm/tqdm", "Python"),
    ("dateutil/dateutil", "Python"),
    ("python-attrs/attrs", "Python"),
    ("pytest-dev/pytest", "Python"),
    ("jsonschema/jsonschema", "Python"),
    ("Textualize/rich", "Python"),
    ("chalk/chalk", "JavaScript"),
    ("sindresorhus/slugify", "JavaScript"),
    ("validatorjs/validator.js", "JavaScript"),
    ("moment/moment", "JavaScript"),
    ("lodash/lodash", "JavaScript"),
    ("expressjs/express", "JavaScript"),
    ("axios/axios", "JavaScript"),
    ("jashkenas/underscore", "JavaScript"),
    ("caolan/async", "JavaScript"),
    ("handlebars-lang/handlebars.js", "JavaScript"),
    ("dayjs/dayjs", "JavaScript"),
    ("brix/crypto-js", "JavaScript"),
    ("SBoudrias/Inquirer.js", "JavaScript"),
    ("remarkjs/remark", "JavaScript"),
    ("google/uuid", "Go"),
    ("spf13/cobra", "Go"),
    ("spf13/viper", "Go"),
    ("go-yaml/yaml", "Go"),
    ("stretchr/testify", "Go"),
    ("gorilla/mux", "Go"),
    ("jackc/pgx", "Go"),
    ("go-gorm/gorm", "Go"),
    ("sirupsen/logrus", "Go"),
    ("robfig/cron", "Go"),
]


def token():
    for env in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(env):
            return os.environ[env]
    result = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\nusername=kundawang\n\n",
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    match = re.search(r"^password=(.+)$", result.stdout or "", re.M)
    return match.group(1).strip() if match else ""


def curl(url, tok="", output=""):
    """这台机器上 urllib 走 api.github.com 会间歇性 SSL 失败，curl 稳。"""
    cmd = ["curl.exe", "-sS", "-L", "--max-time", "180", "-H", "User-Agent: codex-cli",
           "-H", "Accept: application/vnd.github+json"]
    if tok:
        cmd += ["-H", f"Authorization: token {tok}"]
    if output:
        cmd += ["-o", output]
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if output:
        return "" if proc.returncode == 0 else (proc.stderr or "curl failed")
    return proc.stdout or ""


def api(path, tok):
    text = curl(API + path, tok)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(f"API 返回了非 JSON: {text[:120]}")
    if isinstance(data, dict) and data.get("message"):
        raise RuntimeError(str(data["message"])[:120])
    return data


def repo_license(repo, tok):
    try:
        info = api(f"/repos/{repo}", tok)
    except Exception as exc:
        return "", f"仓库信息取不到（{exc}）"
    lic = ((info.get("license") or {}).get("spdx_id") or "").strip()
    return lic, ""


FIX_WORDS = re.compile(r"^(fix|fixed|fixes|bugfix|hotfix|patch)\b|修复|修正", re.I)
SKIP_WORDS = re.compile(r"typo|docs?\(|readme|changelog|test only|bump|release|lint|format", re.I)


def fix_candidates(repo, tok, want=40):
    """挑"像 bug 修复"的提交：消息像修复、规模适中、改动文件不多。"""
    out = []
    for page in (1, 2):
        try:
            commits = api(f"/repos/{repo}/commits?per_page=100&page={page}", tok)
        except Exception:
            break
        for item in commits:
            msg = (item["commit"]["message"] or "").split("\n")[0].strip()
            if not FIX_WORDS.search(msg) or SKIP_WORDS.search(msg):
                continue
            if len(item.get("parents") or []) != 1:
                continue
            out.append({"sha": item["sha"], "msg": msg,
                        "parent": item["parents"][0]["sha"],
                        "date": item["commit"]["author"]["date"][:10]})
        if len(out) >= want:
            break
    return out[:want]


def commit_size(repo, sha, tok):
    try:
        detail = api(f"/repos/{repo}/commits/{sha}", tok)
    except Exception:
        return None
    files = detail.get("files") or []
    changes = sum((f.get("changes") or 0) for f in files)
    return {"changes": changes, "files": len(files),
            "paths": [f["filename"] for f in files][:6],
            "message": (detail["commit"]["message"] or "")[:400]}


def issue_of(repo, message, tok):
    """提交消息里带 #123 的，去把那个 issue 的标题和正文取回来当 prompt 素材。"""
    match = re.search(r"#(\d+)", message)
    if not match:
        return None
    try:
        issue = api(f"/repos/{repo}/issues/{match.group(1)}", tok)
    except Exception:
        return None
    return {"number": match.group(1), "title": issue.get("title") or "",
            "body": (issue.get("body") or "")[:3000],
            "url": issue.get("html_url") or ""}


def download(repo, sha, dest, tok):
    if os.path.isdir(dest) and os.listdir(dest):
        return True
    os.makedirs(dest, exist_ok=True)
    url = f"https://codeload.github.com/{repo}/tar.gz/{sha}"
    tar_path = os.path.join(os.path.dirname(dest), os.path.basename(dest) + ".tar.gz")
    err = curl(url, tok, tar_path)
    if err or not os.path.exists(tar_path) or os.path.getsize(tar_path) == 0:
        raise RuntimeError(err or "下载到空文件")
    with tarfile.open(tar_path) as tar:
        root = os.path.commonpath([m.name.split("/")[0] for m in tar.getmembers() if m.name])
        for member in tar.getmembers():
            if member.name == root:
                continue
            member.name = member.name[len(root) + 1:] or ""
            if not member.name or ".." in member.name.split("/"):
                continue
            tar.extract(member, dest, filter="data")
    os.remove(tar_path)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="只列候选，不动任何东西")
    ap.add_argument("--take", type=int, default=0, help="实际做几道")
    ap.add_argument("--start", type=int, default=52, help="从 lk-0xx 开始编号")
    ap.add_argument("--min-lines", type=int, default=5, help="改动行数下限")
    ap.add_argument("--max-lines", type=int, default=120, help="改动行数上限（中等难度）")
    args = ap.parse_args()

    tok = token()
    if not tok:
        raise SystemExit("拿不到 GitHub 凭据")
    work = os.path.join(REPO, "..", "..", "work", "imported")
    refs = os.path.join(os.path.expanduser("~"), ".coding-agent-tasks", "refs")
    found, skipped = [], []

    for repo, lang in CANDIDATES:
        lic, err = repo_license(repo, tok)
        if err or lic not in OK_LICENSES:
            skipped.append(f"{repo}: 许可证 {lic or '未知'}，跳过")
            continue
        picked = None
        for cand in fix_candidates(repo, tok):
            size = commit_size(repo, cand["sha"], tok)
            if not size:
                continue
            if not (args.min_lines <= size["changes"] <= args.max_lines):
                continue
            if not (1 <= size["files"] <= 4):
                continue
            picked = {**cand, **size, "license": lic, "repo": repo, "lang": lang}
            break
        if picked:
            found.append(picked)
        else:
            skipped.append(f"{repo}: 没找到合适规模（{args.min_lines}~{args.max_lines} 行）的修复提交")

    print(f"可用仓库 {len(found)} 个，跳过 {len(skipped)} 个\n")
    for item in found:
        print(f"  {item['repo']:28s} {item['license']:12s} {item['changes']:4d} 行 / {item['files']} 文件")
        print(f"      {item['sha'][:8]}  {item['msg'][:70]}")
        print(f"      改的是: {', '.join(item['paths'])}")
    if skipped:
        print("\n跳过：")
        for line in skipped:
            print("  " + line)
    if args.plan or not args.take:
        print("\n（--plan 模式，没有落盘。确认后加 --take N 真正建题）")
        return 0

    os.makedirs(refs, exist_ok=True)
    for index, item in enumerate(found[:args.take]):
        task_id = "lk-%03d" % (args.start + index)
        slug = item["repo"].split("/")[1].lower()
        dest = os.path.join(work, task_id + "-" + slug)
        print(f"\n=== {task_id}  {item['repo']}  ({item['sha'][:8]}) ===")
        try:
            download(item["repo"], item["parent"], dest, tok)
        except Exception as exc:
            print(f"  下载失败，跳过：{exc}")
            continue
        issue = issue_of(item["repo"], item["message"], tok)
        detail = {"task_id": task_id, "repo": item["repo"], "license": item["license"],
                  "fix_commit": item["sha"], "buggy_commit": item["parent"],
                  "fix_message": item["message"], "files": item["paths"],
                  "issue": issue, "workspace": dest}
        with open(os.path.join(refs, task_id + ".json"), "w", encoding="utf-8") as fh:
            json.dump(detail, fh, ensure_ascii=False, indent=2)
        print(f"  初始环境（有 bug 的那版）: {dest}")
        print(f"  参考答案（不进仓库）: {os.path.join(refs, task_id + '.json')}")
        if issue:
            print(f"  关联 issue #{issue['number']}: {issue['title'][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
