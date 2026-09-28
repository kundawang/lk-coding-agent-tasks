我们用 anyio 的 Condition 做线程间的等待/通知。为了保证原子性，我们会在外面先把底层锁
手动 acquire 住再操作，这时候调 condition.notify() 会被拒绝（说当前没持锁）。

要求：底层锁是被当前任务直接持有时，notify 也要能正常发通知（按文档语义来）；
正常 with condition 用的路径、以及 notify_all 的行为别动。改完补测试。
