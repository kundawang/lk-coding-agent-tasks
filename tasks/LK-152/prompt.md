我们用 async 的 timeout(fn, ms, info) 给异步操作加超时，info 传的是 falsy 值（空字符串这种）。
现在超时之后 info 丢了，拿不到我们标记的上下文信息；传非空字符串是正常的。

要求：只要 info 不是 undefined 就要保留下来（falsy 也算传了）；没传 info 的行为别变。改完补测试。
