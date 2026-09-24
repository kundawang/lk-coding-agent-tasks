我们用 redis-py 的多库客户端（multidb）跑事务。调用 watch/transaction 的时候，
选项被当成位置参数一路传下去，结果参数错位：transaction=True 被当成了要 watch 的 key，
事务行为完全不对、有时候还直接报错。

要求：选项要按关键字参数传，别跟 watches 混在一起；非事务的普通调用行为一点都不能变。改完补测试。
