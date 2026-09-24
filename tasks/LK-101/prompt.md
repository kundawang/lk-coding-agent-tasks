我们把 sqlite-utils 升到 4.2，装完之后连 --help 都跑不起来，报
ModuleNotFoundError: No module named 'typing_extensions'。我们是不想为了跑个命令行工具
再额外装一堆依赖。

要求：这个包不该在缺少这个模块的时候直接崩掉（能用标准库实现的地方就别依赖它）；
其它功能行为一点都不能变。改完补测试。
