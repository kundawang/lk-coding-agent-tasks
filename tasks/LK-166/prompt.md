我们用 aiohttp 抓一些老站点，它们的 Content-Type 里没有 charset 参数，
但首页 meta 里写的是 GBK。现在 aiohttp 只能按默认编码解，中文全乱码，
我们只能拿原始 bytes 自己手动 decode。

要求：请求的时候能指定文本编码（text_charset 这类参数），指定了就按它解码响应文本；
不指定的时候行为完全不变（包括自动从 header 里取编码的逻辑）。改完补测试。
