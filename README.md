# swpanel

离线策略调试面板，网页版。做成一个能装到本地的页面，能看清 Service Worker 缓存了什么、命中了什么。

纯静态、无构建、无依赖（Service Worker 需要在本地起服务跑）。

## 目录

```
samples/policy.json   缓存策略：哪些资源用哪种策略
```

## 策略格式

```json
{
  "version": "v3",
  "strategies": [
    { "match": "/api/", "type": "networkFirst", "timeoutMs": 3000 },
    { "match": "/assets/", "type": "cacheFirst" },
    { "match": "/", "type": "staleWhileRevalidate" }
  ],
  "precache": ["/", "/index.html", "/app.js", "/style.css"]
}
```

## 要做的

就是一个页面，上面放几张图和一个会请求接口的按钮，重点是旁边那个**调试面板**：

- 当前 SW 状态：安装中/已激活/等待中，当前缓存版本
- 缓存里有多少条、占多大，能按 URL 列出、能单条删除、能整体清空
- 每次请求的**命中情况**：命中了缓存 / 走了网络 / 超时回落，列成一张实时表
- 点"检查更新"能看到有没有新版本，新版本处于 waiting 状态时要提示我

## 重点

- **版本升级要干净**：换成 `v4` 之后旧缓存要被清掉，不能越攒越多；升级过程中页面不能白屏
- **超时回落**：网络慢的时候要按策略里的 `timeoutMs` 回落，不能一直等
- 断网状态下刷新页面仍然能打开（precache 里那些要真的在）
- 调试面板本身不能被缓存"缓存住"（面板要始终反映最新状态）
