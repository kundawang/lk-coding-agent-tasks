# querybench

本地 SQL 查询面板，网页版。把 JSONL 当成一张表，写 SQL 查它。

纯静态、无构建、无依赖。

## 目录

```
samples/orders.jsonl   一张"表"的数据（每行一个 JSON 对象）
samples/queries.sql    几条要能跑通的查询
```

## SQL 子集

要支持：

```sql
SELECT channel, COUNT(*) AS n, SUM(amount) AS total
FROM orders
WHERE created_at >= '2026-09-01' AND status <> 'cancelled'
GROUP BY channel
HAVING total > 1000
ORDER BY total DESC
LIMIT 20;
```

| 能力 | 说明 |
|---|---|
| `SELECT` | 列、`*`、表达式、`AS` 别名 |
| 函数 | `COUNT(*)`、`COUNT(col)`、`SUM`、`AVG`、`MIN`、`MAX` |
| `WHERE` | `= <> < <= > >=`、`AND` `OR` `NOT`、`IN`、`LIKE`（`%` `_`）、`IS NULL` |
| `GROUP BY` / `HAVING` | |
| `ORDER BY` | 多列，`ASC`/`DESC` |
| `LIMIT` / `OFFSET` | |

字段可能是数字、字符串、布尔或 null，比较时类型要对得上。
