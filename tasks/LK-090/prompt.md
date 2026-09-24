我们用 pyjwt 解 token，调用方统一 except 它自己的 InvalidTokenError。
最近有人拿嵌套特别深的 payload 来打，解码时抛出来的却是 RecursionError，直接穿透了我们的 except，
整个请求 500。

要求：这种畸形/恶意的 payload 也要归到「token 无效」这一类错误里，别把递归错误漏给调用方；
正常 token 的解析结果一点都不能变。改完补测试。
