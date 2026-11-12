我们在 Prefect 里跑数据流水线。有个客户端提交了一个参数嵌套很深的 FlowRun，服务端返回 500，但记录还是写进数据库了；之后只要 /flow_runs/filter 或 /paginate 的结果页碰到这条记录，所有客户端都会继续 500，除非人工把那条 run 删掉。lone surrogate 和 labels 里的 NaN/Infinity 也能把服务打坏，Deployment 和 WorkPool 列表也遇到过同类问题，看起来不是某一个 endpoint 的偶发异常。

我希望从输入边界就把这类值拦住：创建/更新接口应当明确返回 422 且不落库，不能让半条坏记录留在事务里。对历史上已经存在的异常记录，读取侧也不能因为一行序列化失败就让整页失败，至少要保证其他行仍可查询，并给出可诊断的错误，不要无差别吞掉真实数据库错误。现有的合法 parameters、labels、datetime、None、Unicode 和正常深度嵌套必须保持兼容。

请补测试覆盖 flow run、deployment、work pool 的深嵌套、lone surrogate、NaN/Infinity，以及脏行存在时筛选和分页仍能返回其他记录。直接在当前仓库完成并运行相关 server tests，回复时给出改动范围和实际测试命令。
