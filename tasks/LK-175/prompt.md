我们的 notebook 导出流水线用的是 nbconvert，markdown 渲染依赖 mistune。
现在 mistune 升到 3.1 之后 nbconvert 直接不兼容（插件接口对不上），导出报错，我们只能钉着老版本。

要求：支持 mistune 3.1 这一代（两者都能用，或者明确按新版本走）；
现有导出结果、以及其它渲染路径别受影响。改完补测试。
