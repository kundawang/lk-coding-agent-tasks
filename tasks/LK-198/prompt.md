我们用 datasette 的自定义模板变量（extra_template_vars）塞上下文，
有些变量在特定条件下本来就应该没有值（None），希望模板里渲染成空。
现在返回 None 会直接报错，模板根本渲染不出来。

要求：extra_template_vars 返回 None 的时候按"没有值"处理（模板里为空），不要抛错；
返回正常值的行为别变。改完补测试。
