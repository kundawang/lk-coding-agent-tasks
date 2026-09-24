# offlinebook

离线优先的笔记应用，网页版。断网照样能写，联网了也不丢东西。

纯静态、无构建、无依赖（用 Service Worker + 浏览器本地存储）。

## 目录

```
samples/notes.json   几篇初始笔记
```

## 笔记格式

```json
{
  "id": "n-001",
  "title": "开会记录",
  "body": "……",
  "updatedAt": 1789700005000,
  "rev": 3,
  "deleted": false
}
```

| 字段 | 说明 |
|---|---|
| `updatedAt` | 毫秒时间戳 |
| `rev` | 每编辑一次加一，用来判断谁更新 |
| `deleted` | 软删除，删除也当成一次修改，不能直接抹掉（不然合并会复活） |
