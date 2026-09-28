"""往飞书表里批量新建行。

    uv run python tools/new_rows.py --target lk3 --json-file work\\feature-rows.json --dry-run
    uv run python tools/new_rows.py --target lk3 --json-file work\\feature-rows.json

--json-file 是 JSON 数组，每个元素是一条记录的字段表：
    [{"UID": "48", "User Prompt": "...", "原仓库地址": "https://github.com/x/y"}, ...]
"""

import argparse
import json
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

import submit  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="lk3")
    ap.add_argument("--json-file", required=True)
    ap.add_argument("--batch", type=int, default=25)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = dict(submit.load_config()["targets"][args.target]
               if args.target else submit.load_config())
    with open(args.json_file, encoding="utf-8") as fh:
        rows = json.load(fh)
    if not isinstance(rows, list) or not rows:
        raise SystemExit("json 文件要是一个非空数组")

    print(f"准备新建 {len(rows)} 行到 {cfg['table_id']}")
    for row in rows[:3]:
        brief = {k: (str(v)[:26] + "…" if len(str(v)) > 26 else v) for k, v in row.items()}
        print("   " + json.dumps(brief, ensure_ascii=False)[:140])
    if len(rows) > 3:
        print(f"   …… 后面 {len(rows) - 3} 行同理")
    if args.dry_run:
        print("\n(dry-run，没有建行)")
        return 0

    created, failed = 0, []
    for start in range(0, len(rows), args.batch):
        chunk = rows[start:start + args.batch]
        payload = json.dumps({"create_records": chunk}, ensure_ascii=False)
        try:
            data = submit.lark(["base", "+record-batch-create",
                                "--base-token", cfg["base_token"],
                                "--table-id", cfg["table_id"],
                                "--json", payload])["data"]
            ids = data.get("record_id_list") or data.get("records") or []
            created += len(chunk)
            count = len(ids) if isinstance(ids, list) else "?"
            print(f"  ok   UID {chunk[0].get('UID')}~{chunk[-1].get('UID')}（{len(chunk)} 行），返回 {count} 个 id")
        except SystemExit as exc:
            failed.append((chunk[0].get("UID"), str(exc).splitlines()[0]))
            print(f"  !!   UID {chunk[0].get('UID')} 起这批失败：{str(exc).splitlines()[0][:90]}")
    print(f"\n共新建 {created} 行，失败 {len(failed)} 批")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
