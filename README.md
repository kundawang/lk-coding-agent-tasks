# html2md

HTML 转 Markdown，网页版。我们文档站的存量内容都是 HTML，想转成 Markdown 迁移过去。

纯静态、无构建、无依赖。

## 目录

```
samples/articles/*.html   几篇真实文章（含表格、代码块、嵌套列表、图片）
samples/golden/*.md       期望的转换结果（用来对照）
```

## 要转换的元素

`h1~h6`、`p`、`strong/b`、`em/i`、`code`、`pre`（带语言标注）、`ul/ol/li`（嵌套）、
`blockquote`、`a`、`img`、`hr`、`table`、`br`、`del`。

## 重点

- 表格要转成 Markdown 表格，单元格里有多行/竖线的要转义，表头缺失也要能处理
- 代码块 `pre > code` 之间的内容**原样保留**（缩进、空行、反引号），
  内容里有三个反引号时要换成长一点围栏
- 嵌套列表的缩进要正确（Markdown 对缩进敏感），有序列表起始序号不是 1 的要写出来
- 加粗和斜体嵌套、代码里的星号不能被当成强调
- 文本里的 Markdown 特殊字符要转义，不然转出来格式就乱了

## 验收

把这些 Markdown 再渲染回 HTML，语义结构要和原 HTML 对得上
（不用逐字节相同，但标题层级、列表层级、链接、代码内容必须一致）。

自己写解析，别引 html 解析库，也别用 innerHTML 拼。
