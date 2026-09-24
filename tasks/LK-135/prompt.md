我们的命令行工具要交叉编译到 WebAssembly（GOOS=js），用的 mattn/go-isatty 做终端判断。
现在 go build 直接失败，说这个包在 js 平台下没有实现。

要求：js 这个目标平台也要能编译通过（终端判断返回 false 就行）；其它平台的实现别动。改完补测试。
