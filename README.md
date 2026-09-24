# tzlab

时区与夏令时转换器，网页版。算时间别再看错一天。

纯静态、无构建、无依赖，**不要引任何时区库**，规则自己带。

## 目录

```
samples/zones.json    要支持的时区与它们相对 UTC 的规则
samples/cases.json    一组转换用例（含夏令时边界）
```

## 时区规则

```json
{
  "zones": [
    { "id": "Asia/Shanghai", "name": "中国标准时间", "utcOffsetMinutes": 480, "dst": null },
    { "id": "America/New_York", "name": "美国东部时间", "utcOffsetMinutes": -300,
      "dst": { "offsetMinutes": -240, "start": { "month": 3, "week": 2, "weekday": 0, "hour": 2 },
               "end": { "month": 11, "week": 1, "weekday": 0, "hour": 2 } } }
  ]
}
```

`week` 是"这个月第几个"，`weekday` 0 是周日。夏令时开始的那一刻时钟往前跳一小时，结束的时候往后跳。

## 用例

```json
{ "from": "America/New_York", "to": "Asia/Shanghai", "at": "2026-03-08 02:30", "expect": "??" }
```

## 重点

- **切换那一小时的边界**：春季跳过去的那一小时（02:00~03:00）在本地时间上是不存在的、
  秋季重复的那一小时是有歧义的——这两种情况要给明确结论，不能算出一个不存在的时间还装作没事
- 跨日期、跨年、闰年 2 月 29 日都要对
- 时间戳与本地时间双向转换要能互推（转过去再转回来必须一样）
- 用例文件里每条都要跑出和 `expect` 一致的结果
