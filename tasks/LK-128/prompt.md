我们用 chalk 控制 CI 输出的颜色，用 FORCE_COLOR 指定级别（比如 FORCE_COLOR=3 想要 256 色）。
现在发现它把任何数字都当成"要彩色"，级别没生效：FORCE_COLOR=3 和 FORCE_COLOR=2 输出一模一样。

要求：数字要当精确级别用，超出 0~3 范围的当没设置；FORCE_COLOR 为空/true、以及 NO_COLOR 的行为别变。
改完补测试。
