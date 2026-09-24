# textcore

代码编辑器的内核，网页版。打开大文件、输入不卡、撤销要能走成树。

纯静态、无构建、无依赖。

## 目录

```
samples/lang.json    一门小语言的词法规则（关键字、注释、字符串）
samples/sample.js    拿它当打开的文件
samples/edits.json   一串编辑操作，用来验证撤销/重做
```

## 语言定义

```json
{
  "name": "minijs",
  "keywords": ["const", "let", "function", "return", "if", "else"],
  "lineComment": "//",
  "blockComment": ["/*", "*/"],
  "strings": ["\"", "'"],
  "numbers": true
}
```

## 编辑操作格式

```json
{ "ops": [
  { "type": "insert", "at": [1, 5], "text": "hello" },
  { "type": "delete", "start": [2, 0], "end": [2, 3] }
] }
```

`at` / `start` / `end` 是 `[行号, 列号]`，都从 1 开始。
