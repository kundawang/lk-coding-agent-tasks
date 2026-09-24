我们用 tortoise-orm 做多对多查询，distinct() 之后调 count()，返回的是 join 出来的总行数，
不是去重之后的数量。同一份条件我们手写 count(distinct ...) 算出来才是对的。

要求：distinct() 之后再 count 要按去重后的结果算；不带 distinct 的 count、
以及 distinct() 直接取数据的行为都别动。改完补测试。
