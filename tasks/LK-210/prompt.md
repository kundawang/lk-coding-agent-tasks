我们的游戏页面启用了严格 CSP，不允许 unsafe-eval，所以使用 pixi.js/unsafe-eval 走 WebGPU。最近自定义 shader 的 UniformGroup 全部变成 0，画面直接空白，但同一个框架里的普通 Graphics 还能正常显示。手动按旧的三参数形式调用底层同步函数又能得到正确数据，说明是兼容实现和调用方的参数约定没对上。

请修 UBO sync polyfill：生成函数必须与正常版本保持同一调用签名，正确应用 offset；i32 等整数 uniform 必须写入整数视图，不能把浮点 bit pattern 当成整数。WGSL 和 std140 两个布局都要覆盖，已有 uniform 顺序、对齐、padding、嵌套结构及非零 offset 的行为要一致。

补回归测试直接比较 polyfill 与 eval 版本对同一组 float/int/bool 数据生成的 buffer，并覆盖多个 UniformGroup 连续写入和 strict-CSP 路径。直接在当前仓库完成，运行相关 unsafe-eval/UBO 测试后汇报结果。
