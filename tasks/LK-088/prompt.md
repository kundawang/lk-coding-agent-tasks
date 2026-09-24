我们有个 bottle 写的老服务接了 sentry 的 bottle 集成，同时开了 attach_stacktrace=True。
现在请求处理到一半就整个卡住，进程还在、CPU 也不高，看起来像卡在某个循环里，
把 attach_stacktrace 关掉或者把 sentry 集成摘掉就正常。

要求：这个开关打开也不能卡死，事件该上报的还是照常上报，别的配置行为别动。改完补测试。
