我们在网关里用 Netty 把 HTTP/2 请求转换成 HTTP/1.1 后交给后面的业务 handler。最近安全测试发现一个很危险的情况：用默认的 InboundHttp2ToHttpAdapterBuilder 构链路时，一个 x-test 头只要带上 CR/LF，仍然会被转换成 FullHttpRequest 并继续往下游送；如果业务层顺手把这个值写回响应头，就会变成 header injection / response splitting 的入口。显式打开校验的转换路径能拦住，但默认适配器不该要求每个调用方自己记得开开关。

你帮忙把转换前的校验补齐：HTTP/2 的普通字段和伪头值都要按 RFC 9113 8.2 判成 malformed，不能只依赖最终构造 HTTP/1 消息时顺便抛错。合法的值、合法的 HTAB 边界、现有 cookie、authority/host 处理和不启用非法输入时原有的行为都不要被改坏；显式配置 validateHttpHeaders 的兼容语义也要想清楚。改完补测试，覆盖默认 adapter 路径、CR、LF、其他禁止控制字符、伪头非法值，以及正常请求。

直接在当前仓库里完成，最后运行 codec-http2 相关测试，把实际命令和结果留在回复里。
