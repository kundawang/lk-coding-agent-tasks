# imagetool

图片批处理工具，网页版。一次拖一堆图进来，统一缩放、裁剪、加水印，打包下载。

纯静态、无构建、无依赖。

## 目录

```
samples/jobs.json    一批处理任务
```

## 任务格式

```json
{
  "output": { "format": "jpeg", "quality": 0.85, "naming": "{name}-{index}.{ext}" },
  "steps": [
    { "type": "autoOrient" },
    { "type": "resize", "mode": "fit", "width": 1280, "height": 1280 },
    { "type": "crop", "x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8 },
    { "type": "watermark", "text": "内部资料", "x": 0.02, "y": 0.96, "opacity": 0.35 }
  ],
  "concurrency": 2
}
```

| 字段 | 说明 |
|---|---|
| `mode` | `fit`（按长边缩）、`cover`（铺满裁）、`exact`（拉伸） |
| `crop` 的 x/y/w/h | 相对比例，0~1 |
| `quality` | 仅 jpeg/webp 有效 |
| `concurrency` | 同时处理几张 |

要能处理的异常：不是图片的文件、零字节文件、超大图、宽高为 0、
文件名里有重名、浏览器不支持的颜色空间。
