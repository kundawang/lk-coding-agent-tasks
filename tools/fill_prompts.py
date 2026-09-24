"""只把 prompt 原文回填到飞书表里的空行（其它字段不动）。

    uv run python tools/fill_prompts.py --target lk2 --from 95 --to 104 --uid-start 43 --dry-run
    uv run python tools/fill_prompts.py --target lk2 --from 95 --to 104 --uid-start 43

题号 -> UID 直接按顺序排：第一个题号填 uid-start，往后依次 +1。
"""

import argparse
import json
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
WORK = os.path.abspath(os.path.join(REPO, "..", "..", "work"))
sys.path.insert(0, TOOLS)

import submit  # noqa: E402


def read_prompt(task_id):
    path = os.path.join(WORK, f"{task_id}-prompt.txt")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read().strip()


def rows_by_uid(cfg):
    out, offset = {}, 0
    while True:
        d = submit.lark([
            "base", "+record-list",
            "--base-token", cfg["base_token"],
            "--table-id", cfg["table_id"],
            "--field-id", "UID",
            "--limit", "200",
            "--offset", str(offset),
            "--format", "json",
        ])["data"]
        names = d.get("fields") or []
        rows = d.get("data") or []
        ids = d.get("record_id_list") or []
        idx = names.index("UID") if "UID" in names else None
        for i, rid in enumerate(ids):
            row = rows[i] if i < len(rows) else []
            uid = str(row[idx] or "").strip() if idx is not None and idx < len(row) else ""
            if uid:
                out[uid] = rid
        if not d.get("has_more") or not ids:
            break
        offset += len(ids)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="lk2")
    ap.add_argument("--from", dest="start", type=int, required=True)
    ap.add_argument("--to", dest="end", type=int, required=True)
    ap.add_argument("--uid-start", type=int, required=True, help="第一个题号对应的 UID")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg_all = submit.load_config()
    cfg = dict(cfg_all["targets"][args.target] if args.target else cfg_all)
    table = rows_by_uid(cfg)
    print(f"表里 {len(table)} 行")

    plan = []
    for offset, number in enumerate(range(args.start, args.end + 1)):
        task_id = "lk-%03d" % number
        uid = str(args.uid_start + offset)
        prompt = read_prompt(task_id)
        if not prompt:
            print(f"!! {task_id} 没有 prompt 文件，跳过")
            continue
        if uid not in table:
            print(f"!! UID {uid}（{task_id}）在表里不存在，跳过")
            continue
        plan.append((task_id, uid, table[uid], prompt))

    print(f"准备写入 {len(plan)} 行：")
    for task_id, uid, rid, prompt in plan:
        print(f"  UID {uid:>3}  {task_id}  {rid}  {prompt.replace(chr(10), ' ')[:44]}…")
    if args.dry_run:
        print("\n(dry-run，没有写表)")
        return 0

    ok, failed = 0, []
    for task_id, uid, rid, prompt in plan:
        try:
            submit.lark([
                "base", "+record-upsert",
                "--base-token", cfg["base_token"],
                "--table-id", cfg["table_id"],
                "--record-id", rid,
                "--json", json.dumps({"User Prompt": prompt}, ensure_ascii=False),
            ])
            ok += 1
            print(f"  ok   UID {uid}  {task_id}")
        except SystemExit as exc:
            failed.append((task_id, uid, str(exc).splitlines()[0]))
            print(f"  !!   UID {uid}  {task_id}")
    print(f"\n写完 {ok} 行，失败 {len(failed)} 行")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
