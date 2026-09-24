# i18nextract

文案提取与 i18n 校验工具，网页版。扫源码把要翻译的文案挑出来，顺手把多语言文件的毛病查一遍。

纯静态、无构建、无依赖。

## 目录

```
samples/src/          几份源码（js + html）
samples/locales/zh.json   中文词条
samples/locales/en.json   英文词条（故意留了问题）
```

## 从源码里挑什么

- `t('key')` / `t("key")` 这种调用里的 key
- html 里 `data-i18n="key"` 的属性
- 代码里的中文串（要给出建议的 key，命名规则见下）

建议 key 的命名：`页面.模块.意思`，比如 `order.list.empty`。

## 校验规则

- 源码用了、语言包里没有的 key
- 语言包里有、源码里没人用的 key
- 中英文语言包 key 对不上的
- 词条值是空串、或者还留着中文的英文词条
