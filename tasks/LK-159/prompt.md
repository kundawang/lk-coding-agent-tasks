我们写 markdown-it 的插件，需要用到它内部那些类（Token、Ruler、各种 Parser/State、Renderer）。
现在只能按内部文件路径去 import，它一调整目录结构我们的插件就崩，已经踩过好几次。

要求：把这些类作为静态属性暴露在 MarkdownIt 上供外部使用（名字和行为按现有实现来）；
渲染/解析行为一点都不能变。改完补测试。
