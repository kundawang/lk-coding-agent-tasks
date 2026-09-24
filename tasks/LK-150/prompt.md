我们用 ava 的 t.throws(fn, {any: true}) 断言"只要抛异常就行"。如果 fn 里抛的是 falsy 值
（比如 throw undefined、throw 0），断言反而失败，说没抛出；抛真实的 Error 就正常。

要求：any: true 的时候，只要有抛出（不管抛什么）就算通过；其它断言形式的行为别变。改完补测试。
