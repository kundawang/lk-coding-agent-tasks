我们在 PixiJS 里做一个 HUD 退场动画：有个 Graphics 填充挂在带圆角的父容器里，旁边还有个 Graphics stencil mask。动画开始时把填充的 visible 设成 false，父容器继续移动和淡出，结果后面的 MeshPlane 偶尔出现白色三角条纹，还会和别的批次串到一起。现在临时绕法是同时把已经用不到的 mask 也设成 false，但业务代码不该为了规避渲染器内部状态去手动配对隐藏对象。

现象只在 WebGL、父容器继续变换、并且隐藏的是被 mask 的对象时出现；把同一帧的状态强制重建 instruction set 后画面又恢复正常。我们怀疑重建后 mask 的旧 batch 位置被其他 graphics 复用，但后面父节点变换仍然往旧位置更新 mask 数据；具体路径你自己查。请修到“隐藏 masked object”本身不会影响任何无关几何，同时不要破坏仍然可见的 mask、嵌套 mask 和正常 RenderGroup 重建。

补一个回归测试，至少覆盖隐藏 fill 后连续移动父节点、同场景重建前后像素一致、无关 Mesh/Virtual 图形不受污染，以及重新显示 fill 后 mask 仍然可用。完成后运行相关 unit/visual 测试，记录实际命令和结果。
