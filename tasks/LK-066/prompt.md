我们的构建机是 Debian 系的，打包的时候用 pip install --prefix=/opt/ourpkg 装到自己的目录里。
最近发现东西根本没进 /opt/ourpkg，全跑到 /usr/local 下面去了，装完还得手动搬。

debug 日志里能看到它选的 scheme 是 posix_local 那套。不指定 --prefix 的时候（系统包管理器那种用法）
是正常的，只有自己指定 prefix 才跑偏。

要求：显式给了 --prefix 的时候装到自己指定的前缀里去；没给 prefix 的场景保持原样别动；
各个平台（包括 Windows/macOS）的路径规则都不能被改坏。改完补上对应的测试。
