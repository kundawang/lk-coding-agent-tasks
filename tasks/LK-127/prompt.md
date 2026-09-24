我们用 axios，有段代码为了清掉拦截器，把 instance.interceptors.request.handlers 直接置成 null。
现在一发请求就抛 TypeError（说是读 length 出错），以前这么写是能跑过去的。

要求：没有拦截器（handlers 为 null/空）的情况要当空栈处理，别崩；正常注册拦截器的行为一点别动。
改完补测试。
