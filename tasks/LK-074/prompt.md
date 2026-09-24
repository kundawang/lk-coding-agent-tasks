我们用 sqlalchemy 连 postgres，面板里要列出库里的 schema，用的 get_schema_names()。
结果我们自己的 schema 不见了——名字是 pgdata、pgms 这种，pg 开头但后面不是下划线，
系统 schema 明明只有 pg_catalog、pg_toast 那几个。

换成别的名字（比如 mydata）就能列出来，所以是它过滤条件写得太宽了。

要求：只过滤真正的系统 schema，用户自己建的不要误伤；
过滤条件别的行为（排序、返回值类型）别动。改完补测试。
