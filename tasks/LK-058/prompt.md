我们用 starlette 的 URL 类在一堆地方拼链接、改端口。配置里除了正常的完整地址，
还有一些没有 authority 的写法（只有路径、或者 mailto: 这种）。

只要对这类地址调 URL.replace()，直接抛 IndexError: string index out of range，
连抛在哪个分支我们都看不出来。完整的 http://host:port/... 就没这问题。

要求：这种没有 host 的 URL 调 replace 不要崩，能拼出来的部分照常拼；
原来有 host 的地址，输出要跟现在一模一样，一个字节都别变。改完补测试。
