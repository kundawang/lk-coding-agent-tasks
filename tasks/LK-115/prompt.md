我们 pre-commit 里配了 language: node 的钩子，而且钩子仓库里带 build 脚本。
npm 升到 11 之后这些钩子装不上了（从 git 依赖安装全局包的行为变了），CI 直接红，
同一条配置在 npm 10 的机器上是好的。

要求：npm 11 下这种钩子也要能正常安装运行；老版本 npm、以及别的 language 的钩子别受影响。改完补测试。
