我们项目用 guice 做依赖注入，并且已经迁到 jakarta 那套注解上了。
现在发现自定义作用域没生效：扫描的时候只认 javax.inject.Scope，用 jakarta.inject.Scope 标的类被忽略了，
跟别的地方（其它注解已经兼容两套）不一致。

要求：javax 和 jakarta 两套注解都要认；其它扫描、绑定行为一点都不能变。改完补测试。
