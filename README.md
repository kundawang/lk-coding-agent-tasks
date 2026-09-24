# a11ycheck

可访问性审计面板，网页版。把一段 HTML 贴进来（或打开样例页），跑一遍规则，出一份能照着改的报告。

纯静态、无构建、无依赖。

## 目录

```
samples/page.html   一个有各种问题的页面
samples/rules.json  规则清单与参数
```

## 规则清单

```json
{
  "rules": [
    { "id": "img-alt", "enabled": true, "level": "error" },
    { "id": "label-for", "enabled": true, "level": "error" },
    { "id": "contrast", "enabled": true, "level": "warn", "minRatio": 4.5 },
    { "id": "heading-order", "enabled": true, "level": "warn" },
    { "id": "tabindex-positive", "enabled": true, "level": "warn" },
    { "id": "dup-id", "enabled": true, "level": "error" }
  ]
}
```

`level` 是 `error` 或 `warn`。`enabled` 为 false 的规则跳过。
