# statemap

状态机可视化编辑器，网页版。画状态和转移，顺便把画错的地方揪出来。

纯静态、无构建、无依赖。

## 目录

```
samples/machine.json   一个订单状态机（里面故意留了几个问题）
```

## 状态机格式

```json
{
  "id": "order",
  "initial": "created",
  "finals": ["closed"],
  "states": [
    { "id": "created", "name": "已创建", "x": 80, "y": 120 },
    { "id": "paid", "name": "已支付", "x": 320, "y": 120 }
  ],
  "transitions": [
    { "from": "created", "to": "paid", "event": "pay", "guard": "amount > 0" }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `initial` | 初始状态 id |
| `finals` | 终止状态 id 列表 |
| `guard` | 转移条件，纯文本展示用，不要求解析 |

## 要能查出来的问题

- 有状态从初始状态**不可达**
- 有非终止状态**出不去**（死锁：没有任何出边）
- 有事件名对不上（同一个 `from` 上同名事件指向了两个不同的 `to`）
- 引用了不存在的状态
