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

## 运行

纯静态、无依赖、无构建，但浏览器不允许 `file://` 页面 fetch 本地文件，
所以要在项目目录起一个静态服务器：

```bash
python3 -m http.server 8000
# 打开 http://localhost:8000
```

打开后自动加载 `samples/orders.jsonl`。也可以点「换数据」选自己的
`.jsonl` 文件（每行一个 JSON 对象），表名取文件名。

页面分三块：上面写 SQL（Ctrl+Enter 运行），右边「解释」面板显示解析出的
结构，下面是结果表格（点表头排序，标题旁显示命中行数）。

## 支持的语句

```
SELECT 列 | * | 函数(列) [AS 别名], ...
FROM 表名
[WHERE 条件]
[GROUP BY 列, ... [HAVING 条件]]
[ORDER BY 列|别名 [ASC|DESC], ...]
[LIMIT n] [OFFSET n]
```

- 条件：`= <> < <= > >=`、`AND` `OR` `NOT`、括号、`IN (...)`、
  `LIKE '模式'`（`%` 任意串、`_` 单字符）、`IS [NOT] NULL`
- 函数：`COUNT(*)`、`COUNT(列)`、`SUM(列)`、`AVG(列)`、`MIN(列)`、`MAX(列)`
- 别名：`AS` 可省略（`SELECT amount total`）；`HAVING`、`ORDER BY` 里可以用别名
- 字符串用单引号（`''` 表示一个引号），双引号是标识符，支持 `--` 行注释
- 一次执行一条语句，末尾分号可有可无

## 解析器是怎么做的

手写、零依赖，分两步（`js/lexer.js` → `js/parser.js`），不用 eval、不用正则切语句：

1. **词法分析**：把 SQL 字符串扫成 token 序列（关键字、标识符、数字、
   字符串、运算符、标点）。每个 token 记下在源串中的字符下标。
2. **递归下降解析**：按优先级逐层消费 token——
   `OR` < `AND` < `NOT` < 谓词（比较 / `IS NULL` / `IN` / `LIKE` / 括号），
   产出 AST（查询列、WHERE 树、GROUP BY、HAVING、ORDER BY、LIMIT/OFFSET）。
3. **执行**（`js/engine.js`）：过滤 → 分组聚合 → HAVING → 排序 → LIMIT/OFFSET。

报错会带**字符位置**和**期待的内容**，页面在出错行下面画 `^` 指给你看。
例如 `SELECT FROM orders` 会提示「SELECT 后面缺少要查询的列」，
而不是一句干巴巴的 syntax error。

## null 和类型比较规则

- **不做隐式类型转换**。数字和数字按数值比（`9 < 100` 成立），字符串和
  字符串按字典序比，布尔和布尔比。跨类型比较不会报错，按固定的类型顺序
  `null < 数字 < 字符串 < 布尔` 给出确定结果。
- **null 是「未知」，不是 0 也不是空串**。`null` 和任何值比较（包括
  `null = null`）结果都是未知；`WHERE`/`HAVING` 只保留条件为真的行，
  所以 `note = NULL` 永远查不到东西——查空值请用 `IS NULL`。
- 聚合跳过 null：`SUM`/`AVG`/`MIN`/`MAX` 不算 null 行，`COUNT(列)` 只数
  非 null 行，`COUNT(*)` 数所有行。一组里全是 null 时 `SUM`/`AVG` 返回 null。
- `LIKE` 只作用于字符串；`note` 为 null 的行不会被任何 `LIKE` 命中
  （包括 `LIKE '%'`）。
- 排序时 null 一律排在最后。

## 测试

```bash
node test/run-tests.mjs   # 32 个断言：样例查询、类型/null 语义、报错、5 万行性能
```
