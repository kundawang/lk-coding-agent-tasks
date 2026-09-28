我们的代码里要模拟"网络层直接失败"这种情况，浏览器里的 fetch 有 Response.error() 可以造一个，
node-fetch 上没有，只能在测试里自己拼一个对象，类型判断到处对不上。

要求：加上 Response.error()，返回一个 type 为 "error" 的响应对象（按 fetch 规范的语义来）；
其它响应的行为别动。改完补测试。
