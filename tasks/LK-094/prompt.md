我们用 mistune 的 create_markdown，renderer 是自己写的（继承了它的 HTML renderer），
并且显式传了 escape 开关。结果这个开关被忽略：该转义的地方没转义，输出里直接是原始 HTML。
不传自定义 renderer 的时候是正常的。

要求：传了自定义 renderer 也要让显式给的 escape 生效；没显式传的时候保持 renderer 自己的设置，
默认 renderer 的行为别动。改完补测试。
