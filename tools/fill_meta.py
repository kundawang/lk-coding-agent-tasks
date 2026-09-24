"""把题目元数据（任务类型/难度/语言框架/Harness 版本/操作系统/环境可复现等级/初始环境快照）
批量写进飞书表，题号 -> UID 按顺序排。

    uv run python tools/fill_meta.py --target lk2 --from 53 --to 104 --uid-start 1 --dry-run
    uv run python tools/fill_meta.py --target lk2 --from 53 --to 104 --uid-start 1
"""

import argparse
import json
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import submit  # noqa: E402
import task as task_mod  # noqa: E402


def field_types(cfg):
    f = submit.lark(["base", "+field-list", "--base-token", cfg["base_token"],
                     "--table-id", cfg["table_id"], "--format", "json"])["data"]
    out = {}
    for it in (f.get("fields") or f.get("items") or []):
        out[it.get("field_name") or it.get("name")] = it.get("type")
    return out


def rows_by_uid(cfg):
    out, offset = {}, 0
    while True:
        d = submit.lark(["base", "+record-list", "--base-token", cfg["base_token"],
                         "--table-id", cfg["table_id"], "--field-id", "UID",
                         "--limit", "200", "--offset", str(offset), "--format", "json"])["data"]
        names, rows, ids = d.get("fields") or [], d.get("data") or [], d.get("record_id_list") or []
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
    ap.add_argument("--uid-start", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = dict(submit.load_config()["targets"][args.target]
               if args.target else submit.load_config())
    types = field_types(cfg)
    table = rows_by_uid(cfg)

    def wrap(name, value):
        if not value:
            return None
        return [value] if types.get(name) == "select" else value

    plan = []
    for offset, number in enumerate(range(args.start, args.end + 1)):
        task_id = "lk-%03d" % number
        uid = str(args.uid_start + offset)
        try:
            meta = task_mod.load_meta(task_id.upper())
        except Exception:
            print(f"!! {task_id} 没有 meta.json，跳过")
            continue
        if uid not in table:
            print(f"!! UID {uid}（{task_id}）不在表里，跳过")
            continue
        init = meta.get("initial_snapshot") or {}
        fields = {
            "任务类型": wrap("任务类型", submit.norm_task_type(meta.get("task_type"))),
            "任务难度": meta.get("difficulty") or None,
            "语言/框架": submit.ascii_punct(meta.get("language_framework")) or None,
            "Harness 版本": meta.get("harness_version") or None,
            "操作系统": wrap("操作系统", meta.get("os")),
            "环境可复现等级": wrap("环境可复现等级", meta.get("env_level")),
            "初始环境快照": init.get("permalink") or None,
        }
        fields = {k: v for k, v in fields.items() if v not in (None, "", [])}
        plan.append((task_id, uid, table[uid], fields))

    print(f"准备写 {len(plan)} 行，字段类型："
          + ", ".join(f"{k}={types.get(k)}" for k in
                      ("任务类型", "任务难度", "语言/框架", "Harness 版本", "操作系统",
                       "环境可复现等级", "初始环境快照")))
    for task_id, uid, rid, fields in plan[:2]:
        print(f"  UID {uid:>3} {task_id}: " +
              json.dumps({k: (v[0] if isinstance(v, list) else v) for k, v in fields.items()},
                         ensure_ascii=False)[:220])
    if args.dry_run:
        print("\n(dry-run，没有写表)")
        return 0

    ok, failed = 0, []
    for task_id, uid, rid, fields in plan:
        try:
            submit.lark(["base", "+record-upsert", "--base-token", cfg["base_token"],
                         "--table-id", cfg["table_id"], "--record-id", rid,
                         "--json", json.dumps(fields, ensure_ascii=False)])
            ok += 1
            print(f"  ok   UID {uid}  {task_id}")
        except SystemExit as exc:
            failed.append((task_id, uid, str(exc).splitlines()[0]))
            print(f"  !!   UID {uid}  {task_id}: {str(exc).splitlines()[0][:80]}")
    print(f"\n写完 {ok} 行，失败 {len(failed)} 行")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
