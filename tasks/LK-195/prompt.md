我们用 redis-py 的连接池，代码里要确保用完一定把连接还回去。
现在只能手动 try/finally，漏一次就把池子占死，我们希望池子本身能当上下文管理器用。

要求：ConnectionPool 支持 with 用法，进入时给出可用的连接、退出时自动归还；
原来手动 get_connection/release 的行为一点都不能变。改完补测试。
