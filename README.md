# datagen

测试数据生成器，网页版。按约束造一批假数据，同一个种子造出来的一模一样。

纯静态、无构建、无依赖。

## 目录

```
samples/spec.json   一份生成规格（表结构 + 约束）
```

## 规格格式

```json
{
  "seed": "20260924",
  "count": 300,
  "tables": {
    "users": {
      "fields": [
        { "name": "id", "type": "sequence", "start": 1 },
        { "name": "email", "type": "email", "unique": true },
        { "name": "city", "type": "enum", "values": ["上海", "北京"], "weights": [5, 3] },
        { "name": "age", "type": "int", "min": 18, "max": 65 }
      ]
    }
  }
}
```

## 字段类型

`sequence`、`name`、`email`、`enum`、`int`、`float`、`bool`、`date`、`ref`（引用另一张表的主键）。

## 要求

- 同一个 `seed` + 同一份 spec，生成的 JSONL 逐字节一致（别用 `Math.random`）
- 约束要真生效：`unique` 不重复、`ref` 指向真实存在的行、`weights` 影响分布
- 导出 JSONL 和 SQL INSERT 两种格式
- 约束冲突（比如只要 500 行却要 600 个不重复邮箱）要明确报错，不能悄悄给重复值
