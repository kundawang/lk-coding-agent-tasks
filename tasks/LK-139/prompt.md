我们在 Windows 上构建 kotlinx.coroutines，配置里 kotlin_repo_url 指向本地目录（Windows 路径）。
现在构建直接失败，报的是 URI 解析不了这种路径；改成正常 URL 就好了。

要求：本地路径和 URL 两种写法都要能用；其它构建行为别动。改完补测试。
