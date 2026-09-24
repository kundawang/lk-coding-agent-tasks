# schemacheck

JSON Schema 校验器子集，网页版。给一份 schema 和一份数据，把不合规的地方一条条列出来。

纯静态、无构建、无依赖。

## 目录

```
samples/schema.json    一份用上各种关键字的 schema
samples/data-bad.json  一份故意写坏的数据
samples/data-good.json 一份正常数据
```

## 要支持的关键字

| 关键字 | 说明 |
|---|---|
| `type` | `object` `array` `string` `number` `integer` `boolean` `null` |
| `properties` / `required` / `additionalProperties` | 对象 |
| `items` / `minItems` / `maxItems` / `uniqueItems` | 数组 |
| `minLength` / `maxLength` / `pattern` / `format` | 字符串，`format` 支持 `email` `date` `uri` |
| `minimum` / `maximum` / `multipleOf` | 数字 |
| `enum` / `const` | 通用 |
| `anyOf` / `oneOf` / `allOf` / `not` | 组合 |
| `$ref` | 只要求支持 `#/definitions/xxx` 这种本文件内引用 |

## 报错要给到什么程度

每条要带出错位置（像 `items[2].price` 这样，能一路点到具体字段）和为什么。
`oneOf` 失败时要把它逐个分支的失败原因也列出来，不然没法改。
