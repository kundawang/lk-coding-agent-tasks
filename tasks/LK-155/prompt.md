我们有一堆地方要用 notebook 的签名校验（NotebookNotary），现在的写法是手动创建、用完手动 close，
只要有一条异常路径忘了 close，就会留下没清掉的状态，排查起来很烦。

要求：支持把它当上下文管理器用（with NotebookNotary() as n: ...），退出时自动做收尾；
原来手动创建+close 的用法保持不变，签名的计算结果也不能变。改完补测试。
