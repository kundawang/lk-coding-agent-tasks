# pastesafe

富文本粘贴清洗，网页版。从网页或 Word 里复制一段内容粘进来，留下该留的，其余全扔掉。

纯静态、无构建、无依赖。

## 目录

```
samples/allowlist.json   允许保留的标签和属性
samples/dirty.html       一段从别处复制来的脏 HTML
```

## 白名单

```json
{
  "tags": {
    "p": [],
    "b": [], "strong": [], "i": [], "em": [],
    "ul": [], "ol": [], "li": [],
    "a": ["href", "title"],
    "h1": [], "h2": [], "h3": [],
    "blockquote": [], "code": [], "pre": []
  },
  "urlSchemes": ["http", "https", "mailto"]
}
```

不在白名单里的标签：要么整段丢掉，要么把里面的文字留下、标签扔掉（你自己定，但要一致）。

## 要处理的脏东西

内联 style 和 class、`<font>`、Word 的 `<!--[if ...]-->` 注释、`data-*` 与 `mso-*` 属性、
`javascript:` 链接、重复嵌套的空标签、表格结构、图片（白名单里没有 img，按规则处理）。
