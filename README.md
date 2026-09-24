# motionlab

关键帧动画编辑器，网页版。拖关键帧、调缓动、预览播放、导出成能直接用的东西。

纯静态、无构建、无依赖。

## 目录

```
samples/scene.json   一个场景：元素、属性轨道、关键帧、缓动
```

## 场景格式

```json
{
  "id": "intro",
  "durationMs": 3000,
  "fps": 60,
  "elements": [
    {
      "id": "card",
      "name": "卡片",
      "tracks": {
        "x": [
          { "t": 0, "v": 0, "easing": "linear" },
          { "t": 800, "v": 320, "easing": "easeOutCubic" }
        ],
        "opacity": [
          { "t": 0, "v": 0, "easing": "linear" },
          { "t": 400, "v": 1, "easing": "easeOutQuad" },
          { "t": 2600, "v": 1, "easing": "linear" },
          { "t": 3000, "v": 0, "easing": "easeInQuad" }
        ]
      }
    }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `t` | 毫秒 |
| `v` | 该时刻的值 |
| `easing` | 从**这个关键帧开始**到下一个关键帧之间用的缓动 |

要支持的缓动：`linear`、`easeInQuad`、`easeOutQuad`、`easeInOutQuad`、`easeInCubic`、`easeOutCubic`、`easeInOutCubic`。
