我们用 plotly express 画柱状图，y 轴那列是 pandas 的 uint32（从 parquet 读出来就是无符号整数）。
结果 px.bar 把它当分类轴画了，柱子的顺序和高度都不对；把这列 astype 成 int64 就正常。

要求：无符号整数列也要按数值轴处理，跟普通整数一样；其它 dtype（分类、字符串、时间）的行为别动。
改完补测试。
