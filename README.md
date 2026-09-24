# lk-coding-agent-tasks

本机（lk 线）跑出的 Coding Agent 题目库。

每道题一条 pair-wise 数据：**一个初始环境快照 + A / B 两次跑的产物快照 + 两条轨迹**。

## 结构

```
main                        台账：题目信息、prompt、轨迹
├── tasks/LK-xxx/           每道题一个目录
│   ├── prompt.md           发给模型的 prompt 原文
│   ├── meta.json           提交表字段（机器可读）
│   └── trajectories/       A / B 轨迹 jsonl
├── tools/                  自动化脚本
│   ├── task.py             建题 / 铺工作区 / 清理 / 记账 / 出字段
│   ├── ready.py            巡检：两轮跑完就自动回填提交表
│   ├── submit.py           把字段（含附件）推到飞书提交表
│   ├── push.py             带重试的推送（HTTPS 不通自动走 SSH）
│   └── find_trajectory.py  按 SessionID 找轨迹
└── docs/                   项目文档、字段口径、GSB 写法、雷同题黑名单

lk-xxx/base                 初始环境快照（这道题的工作区代码）
├── lk-xxx/a                A 跑完后的产物快照（parent = base）
└── lk-xxx/b                B 跑完后的产物快照（parent = base）
```

代码放在按题命名的分支上（`lk-xxx/base|a|b`），台账放在 `main`。
这样模型跑题时工作区里只有这一题的代码，不会被别的题干扰。

## 怎么用

完整流程见 **[docs/怎么用这套作业-lk线.md](docs/怎么用这套作业-lk线.md)**。

常用命令（仓库根目录下）：

```bat
t list                        :: 列出所有题目和状态
t report lk-006               :: 输出这道题要填的字段 + 可点击的轨迹文件
t new lk-012 --workspace <起始环境> --prompt-file p.txt ...
t prep  lk-012                :: 铺出桌面工作区 A / B + 启动器
t cycle lk-012 --side a       :: 存档上一轮 + 把 A 清成全新
t record lk-012 a --side a --session <SessionID>
push                          :: 推送（带重试；HTTPS 不通自动走 SSH）
submit lk-012 --uid 14X       :: 上传提交表（默认 dry-run）
uv run python tools\ready.py --submit   :: 巡检 + 自动回填
```

## 硬性约束

- 两次跑必须是**完全相同的 prompt**、同一个 Harness 和版本、同一台机器、同一套配置
- **只跑首轮**：模型答完就结束，不追问、不纠错
- A / B 产物快照的父提交必须是同一个初始环境快照
- 记录过的 SHA 不要 amend / rebase / force-push
- **禁止用 AI 工具分析轨迹和产物，禁止 AI 代写 GSB 理由**
- 只用 40 位完整 SHA，不要用短 SHA、分支名或 tag 代替
