# 游戏领域 Bugfix 短周期方案

## 范围

本批只保留“游戏、图形与多媒体”领域，共三道 Bugfix：

| 题号 | 题目 | 难度 | 上游 |
|---|---|---|---|
| LK-204 | PixiJS 隐藏 masked object 后 stencil mask 污染无关几何 | 地狱 | <https://github.com/pixijs/pixijs/issues/12295> |
| LK-206 | Excalibur 圆形碰撞体射线背向命中 | 困难 | <https://github.com/excaliburjs/Excalibur/issues/3895> |
| LK-207 | KAPLAY SAT 分离轴选择了较远位移 | 困难 | <https://github.com/kaplayjs/kaplay/issues/1194> |

## 为什么周期较短

- 三题都是真实开源仓库中已经定位到现象或根因路径的 Bugfix，不需要从功能想法开始设计。
- 每题都已建立并推送独立的 `base` 初始快照，下一轮可以直接从固定 SHA 开始。
- 三题都可依靠仓库现有测试体系做确定性验证，不需要外部账号、数据库或线上服务。
- 按当前单轮规则，每题只执行一次首轮: 一个 SessionID、一份轨迹、一份产物快照和一段不超过 90 秒的运行录屏。
- 不采用 A/B 双跑和 GSB 对比；这样可以减少一轮模型执行和一次结果比较。

## 执行建议

1. 先执行 LK-206 或 LK-207，二者问题边界更窄，适合验证当天的环境和流程。
2. 再执行 LK-204；该题涉及 RenderGroup、stencil mask 和 WebGL graphics batch，耗时预期最长。
3. 每题只贴一次完整 Prompt，模型回答后立即结束，不追问、不纠错。
4. 运行录屏重点展示修复前后的可观察结果即可；不要录整个安装或长时间构建过程。
5. 若当天时间不足，只交付 LK-206 和 LK-207 两条，优先保证数据完整而不是追求数量。

## 初始快照

- LK-204: `296c243a78499c54fa188e47d2b13ba300bba0e4`
- LK-206: `fdf3b2247bcdd87f4216fb80c0cc8166b17f5788`
- LK-207: `f17dc914295fafe7350529ba38b84a07fb277f1c`
