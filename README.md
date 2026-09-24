# ruleform

表单校验引擎，网页版。校验规则用配置写，不写死在代码里。

纯静态、无构建、无依赖。

## 目录

```
samples/rules.json    一份校验规则
samples/data.json     一份填错的数据
```

## 规则格式

```json
{
  "fields": {
    "name": { "rules": [{ "type": "required" }, { "type": "length", "min": 2, "max": 20 }] },
    "email": { "rules": [{ "type": "required" }, { "type": "email" }] },
    "age": { "rules": [{ "type": "range", "min": 18, "max": 65 }] },
    "phone": { "rules": [{ "type": "pattern", "regex": "^1\\d{10}$", "message": "手机号格式不对" }] },
    "confirm": { "rules": [{ "type": "sameAs", "field": "password" }] },
    "age2": { "rules": [{ "type": "requiredIf", "field": "vip", "equals": true }] },
    "code": { "rules": [{ "type": "unique", "url": "local" }] }
  }
}
```

## 要支持的规则

`required`、`length`、`range`、`pattern`、`email`、`url`、`sameAs`、`requiredIf`、
`unique`（本地假装有一个已占用列表）。

## 重点

- **异步校验的竞态**：`unique` 是异步的。用户连续改三次，先发的那次后回来，
  不能把后发的结果覆盖掉——旧结果要丢弃
- **报错定位到字段**，界面上对应输入框要标红并显示消息
- **校验顺序**：必填不过就不该再跑后面的规则，但**所有字段的错误要一次全给出来**，不能只报第一个
- 规则配置写错（未知规则类型、缺参数）要在加载时明确报出来
