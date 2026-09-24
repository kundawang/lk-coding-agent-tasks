# eventsrc

事件溯源 + 时间旅行调试，网页版。所有状态都是事件算出来的，能倒回任意时刻看当时长什么样。

纯静态、无构建、无依赖。

## 目录

```
samples/events.jsonl   一串事件（含重复投递、乱序、非法事件）
samples/snapshots.json 两个快照点
```

## 事件格式

```json
{ "seq": 3, "type": "OrderPaid", "at": 1789700010000, "payload": { "orderId": "o-1", "amount": 128.5 } }
```

`seq` 是全局递增序号，`type` 决定怎么改状态，`payload` 是内容。

## 要支持的事件

`OrderCreated`、`OrderPaid`、`OrderShipped`、`OrderCancelled`、`ItemAdded`、`ItemRemoved`、`NoteUpdated`。

## 重点

- 状态只由事件算出来：重放同一串事件必须得到同一个状态
- 拖时间轴能看到任意 seq 时的完整状态；快照只是加速手段，有没有快照结果必须一致
- 同一个 `seq` 来了两次只能生效一次（幂等）
- `seq` 比当前小的迟到事件要按序号插回去重算，或者明确报冲突（你自己定，但要说清楚）
- 非法事件（类型不认识、payload 缺字段、状态不允许的转移）要跳过并记录，界面上单独列出来
