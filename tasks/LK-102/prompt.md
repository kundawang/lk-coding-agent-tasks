我们把 freezegun 升到 1.5.3 之后，pytest 里那些用 yield 的 fixture 全坏了：
fixture 的 setup 部分跑完就报错，用例直接挂掉。退回 1.5.2 是正常的。项目里这种 fixture 一大堆，
不可能一个个改。

要求：被冻结时间装饰的类/函数里，生成器形式的 fixture 要照常工作，setup 和 teardown 都要跑到；
其它时间冻结行为别动。改完补上这种 fixture 的测试。
