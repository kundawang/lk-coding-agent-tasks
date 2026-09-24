# astsearch

代码结构搜索与重命名，网页版。按结构找代码（不是按字符串找），改完先给我看 diff。

纯静态、无构建、无依赖。

## 目录

```
samples/src/*.js       几份源码
samples/patterns.json  几条结构搜索模式和一个重命名任务
```

## 要支持的语法子集

`const/let/var`、函数声明与箭头函数、调用、成员访问、对象/数组字面量、
`if/for/while`、`return`、字符串/数字/模板串、import/export。

## 模式怎么写

```json
{ "find": "console.log($x)" }
```

`$x` 是通配符，用来匹配任意子表达式。重命名任务写成：

```json
{ "rename": { "from": "oldName", "to": "newName", "scope": "file|project" } }
```

## 要求

- 匹配要按语法结构算，不能靠文本替换 —— `oldName` 出现在字符串或注释里不能动
- 改之前先给 diff 预览，我能一条条勾选要不要应用
- 名字被当成对象属性用（`obj.oldName`）时要不要改，得按 scope 规则说清楚
