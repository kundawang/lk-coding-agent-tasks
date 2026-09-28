我们的配置文件是 Windows 上编辑器存的，开头带了 UTF-8 BOM（.prettierrc / prettier.config.js 都有）。
prettier 读这种配置直接报解析错误，同事改配置都得先手动去 BOM，很折腾。

要求：读配置的时候把 BOM 去掉再解析；不带 BOM 的文件、以及配置解析结果别有任何变化。改完补测试。
