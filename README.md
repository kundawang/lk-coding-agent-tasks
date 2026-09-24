# textbreak

中英文混排断行引擎，网页版。我们自己排版，不用浏览器默认的那套。

纯静态、无构建、无依赖。

## 目录

```
samples/paragraphs.json   几段要排的文本
samples/rules.json        断行与标点规则
```

## 规则

```json
{
  "font": "16px sans-serif",
  "width": 320,
  "lineHeight": 26,
  "rules": {
    "noLineStart": "，。、；：？！）」』】》",
    "noLineEnd": "（「『【《",
    "hyphenateEnglish": true,
    "squeezePunctuation": true,
    "maxSqueezeRatio": 0.5
  }
}
```

## 要实现

- **禁用行首标点**：行尾放不下的标点不能挪到下一行开头（要么挤上去，要么把前一个字拉下来）
- **禁用行尾标点**：开括号类不能留在行尾
- **标点挤压**：连续标点（`。」`）要能压缩到半个字宽，压缩有上限
- **中英混排**：英文按单词断，放不下就整体换行；超长单词要能强制断开
- **英文连字符断词**（`hyphenateEnglish` 为真时）
- 每行都要给出行宽、用了多少次挤压，我要能看到排版是不是"刚刚好"

## 要顶住的情况

- 超长不可断串（一长串 `AAAAAAAA...`）、单个宽度超过整行的字、空段落
- 换字号/换宽度之后重新排版，结果必须是确定的（同样的输入换两次结果一致）
