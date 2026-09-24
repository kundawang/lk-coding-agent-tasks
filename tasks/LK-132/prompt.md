我们用 uuid 生成 v1 UUID，没有传 node（让它自己随机生成）。按 RFC 规范，
这种自生成的 node 必须把 multicast 位置上，现在没置，导致我们下游有些系统认为这个 UUID 不合法。

要求：随机生成的 node 要按规范置上 multicast 位；显式传入 node 的时候行为保持不变。改完补测试。
