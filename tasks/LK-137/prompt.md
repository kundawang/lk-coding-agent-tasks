我们用 commons-collections 的 putAll(K, Iterable) 往 map 里批量放值，
value transformer 传了 null（意思是值原样放进去，不做转换）。现在直接抛 NPE。

要求：transformer 为 null 时按"原样放入"处理；传了转换函数的行为一点都不能变。改完补测试。
