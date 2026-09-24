我们埋点和订单数据现在都躺在 JSONL 文件里，查点东西就得写个一次性脚本，太慢了。
想让你做个网页版的查询面板：把 JSONL 当一张表，写 SQL 查它。

样例数据在 samples/orders.jsonl（160 行，就是一张订单表），要能跑通的查询写在 samples/queries.sql 里，
字段含义 README 里有，别改这两个文件。

想要的：

上面写 SQL，下面出结果表格。要支持 SELECT / WHERE / GROUP BY / HAVING / ORDER BY / LIMIT / OFFSET，
还有 COUNT、SUM、AVG、MIN、MAX 这几个函数和 AS 别名。具体列在 README 里。

三件我比较在意的事：

一是SQL 得自己解析。别用 eval、别用正则硬切，我要能看到一句 SQL 被拆成了什么。
加个"解释"面板，把解析出来的结构显示出来（选了什么列、条件是什么、按什么分组、怎么排序），
我说不清哪里写错的时候能对着看。

二是类型要处理好。金额是数字、时间是字符串、note 有的行是 null。
比大小的时候不能把 "9" 和 "100" 按字符串比（那会得到错误答案），null 也不能当成 0 或者空串。
`IS NULL`、`LIKE` 里的 `%` 和 `_` 都要对。

三是报错要说人话。SQL 写错了要告诉我错在第几个字符、期待什么，
比如 `SELECT FROM orders` 这种缺列的，别只弹一句 "syntax error"。

结果表格要能排序、能看出来多少行命中；数据换成几万行的 JSONL 也不能卡死。

别引库、别 npm、别构建，原生 ES module。README 里写清楚支持哪些语句、
解析器是怎么做的、null 和类型比较的规则。
