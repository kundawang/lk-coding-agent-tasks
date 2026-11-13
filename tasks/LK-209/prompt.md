我们在 Excalibur 里做鼠标悬停交互，场景里有多个 z-index 不同的 Actor 叠在一起。现在从底层 Actor 移到顶层 Actor 时，底层的 pointerleave 有时不触发，顶层 pointerenter 又会和底层一起响应；在 pointermove 或 pointerdown 里调用 cancel() 也挡不住后面的 Actor。结果 HUD 上一张透明卡片的点击区域会吃掉地图上的交互。

请把重叠 Actor 的指针命中顺序和事件语义修正确：每次只按最上层可命中的 Actor 派发交互，enter/leave 要随命中目标切换准确触发；事件被 cancel 后，同一轮不应继续传给下层，也不要制造重复的 leave/enter。Actor 被隐藏、销毁、移动或 z-index 运行时变化时，缓存状态不能留下幽灵 hover。

补测试覆盖两个重叠 Actor、正反向穿越、z-index 交换、移动/销毁、嵌套场景和取消事件传播，确保现有不重叠 Actor 的行为不变。直接在当前仓库完成并运行相关 pointer/input tests。
