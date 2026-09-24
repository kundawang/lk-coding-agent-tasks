"""往飞书表的某一段 UID 行里写同一个值（默认写「原仓库地址」= 本仓库地址）。

    uv run python tools/fill_field.py --target lk2 --field 原仓库地址 --repo-url --uid-from 43 --uid-to 52
    uv run python tools/fill_field.py --target lk2 --field 备注 --value "xxx" --uid-from 1 --uid-to 5
"""

import argparse
import json
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

import submit  # noqa: E402


def rows_by_uid(cfg, field):
    out, offset = {}, 0
    while True:
        d = submit.lark([
            "base", "+record-list",
            "--base-token", cfg["base_token"],
            "--table-id", cfg["table_id"],
            "--field-id", "UID",
            "--field-id", field,
            "--limit", "200",
            "--offset", str(offset),
            "--format", "json",
        ])["data"]
        names = d.get("fields") or []
        rows = d.get("data") or []
        ids = d.get("record_id_list") or []
        iu = names.index("UID") if "UID" in names else None
        iv = names.index(field) if field in names else None
        for i, rid in enumerate(ids):
            row = rows[i] if i < len(rows) else []
            uid = str(row[iu] or "").strip() if iu is not None and iu < len(row) else ""
            old = row[iv] if iv is not None and iv < len(row) else ""
            if isinstance(old, list):
                old = "".join(s.get("text", "") + (s.get("link") or "")
                              for s in old if isinstance(s, dict))
            if uid:
                out[uid] = (rid, (old or "").strip())
        if not d.get("has_more") or not ids:
            break
        offset += len(ids)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="lk2")
    ap.add_argument("--field", required=True)
    ap.add_argument("--value", default="")
    ap.add_argument("--repo-url", action="store_true", help="用本仓库的 GitHub 地址当值")
    ap.add_argument("--uid-from", type=int, required=True)
    ap.add_argument("--uid-to", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    value = args.value or (submit.repo_url() if args.repo_url else "")
    if not value:
        raise SystemExit("要么给 --value，要么加 --repo-url")

    cfg = dict(submit.load_config()["targets"][args.target]
               if args.target else submit.load_config())
    table = rows_by_uid(cfg, args.field)
    plan = []
    for uid in range(args.uid_from, args.uid_to + 1):
        key = str(uid)
        if key not in table:
            print(f"!! UID {key} 不在表里，跳过")
            continue
        plan.append((key, *table[key]))

    print(f"字段「{args.field}」<- {value}")
    print(f"要写 {len(plan)} 行，写之前的值：")
    for key, rid, old in plan[:4]:
        print(f"  UID {key:>3}  {rid}  原值: {old[:50] or '(空)'}")
    if len(plan) > 4:
        print(f"  …… 后面 {len(plan) - 4} 行同理")
    if args.dry_run:
        print("\n(dry-run，没有写表)")
        return 0

    ok, failed = 0, []
    for key, rid, _old in plan:
        try:
            submit.lark([
                "base", "+record-upsert",
                "--base-token", cfg["base_token"],
                "--table-id", cfg["table_id"],
                "--record-id", rid,
                "--json", json.dumps({args.field: value}, ensure_ascii=False),
            ])
            ok += 1
        except SystemExit as exc:
            failed.append((key, str(exc).splitlines()[0]))
            print(f"  !! UID {key}: {str(exc).splitlines()[0][:80]}")
    print(f"\n写完 {ok} 行，失败 {len(failed)} 行")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
