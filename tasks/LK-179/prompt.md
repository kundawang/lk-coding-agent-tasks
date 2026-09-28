我们用 marshmallow 校验用户填的网站地址。国际化域名（中文域名、带 Unicode 的域名）现在一律被判非法，
用户只能填 punycode 形式，体验很差。

要求：URL 校验要支持 IDN（Unicode 域名要能通过，必要时内部转成 punycode 再校验）；
原来合法的 ASCII 域名、以及明显非法的输入结果都不能变。改完补测试。
