# termcheck

术语与拼写检查，网页版。我们有自己的一套术语表，写文档的时候得按规矩来。

纯静态、无构建、无依赖。

## 目录

```
samples/terms.json     术语表：正确写法、错误写法、大小写规则
samples/doc.txt        一段故意写错的文档
```

## 术语表格式

```json
{
  "terms": [
    { "correct": "Kubernetes", "wrong": ["k8s", "k8S", "kubernetes"], "caseSensitive": true },
    { "correct": "主节点", "wrong": ["master 节点", "Master 节点"] },
    { "correct": "登录", "wrong": ["登陆"] }
  ],
  "ignoreWords": ["示例里的占位符 XXX"]
}
```

## 要做的检查

- 术语误用（命中 `wrong` 就报，并给出正确写法）
- 大小写不对（`caseSensitive` 为 true 的术语，大小写错了要报）
- 中英文之间缺空格（`中文English` 这种）
- 全角/半角混用（数字、括号、逗号）
- 重复词（`的的`、`the the`）
- 英文拼写（要有一份常见词表，别把专业名词也报出来）
