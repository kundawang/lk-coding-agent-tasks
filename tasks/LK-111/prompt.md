我们用 authlib 做 OIDC，生成 id_token 的时候，如果授权码里没有 nonce 或者 auth_time，
它现在照样把这两个 claim 写进去、值是 null。有些客户端拿到 null 校验直接失败，
还有的把 null 当字符串处理，接入方一直在找我们。

要求：值为空的时候就不要带这个 claim（完全没有这个字段），有值的时候照常写；
其它 claim 的行为一点都不能变。改完补测试。
