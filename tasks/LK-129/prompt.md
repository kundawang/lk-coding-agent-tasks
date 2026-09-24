我们用 express 的 res.send 返回 JSON，同时手动带上 Transfer-Encoding（流式场景）。
发现这种情况下响应里没有 ETag 了，客户端缓存全部失效，只有不带 Transfer-Encoding 的时候才有。

要求：加 Content-Length 的那段逻辑不要影响 ETag 的生成（有 Transfer-Encoding 时不加 Content-Length 就行）；
正常响应的头别变。改完补测试。
