我们用 gson 处理 JSON，会把 JsonPrimitive 放进 HashSet、也当 HashMap 的 key 用。
现在发现 `42` 和 `42.0` 这两个 primitive 用 equals 判是相等的，但 hash 不一样，
放进集合之后 contains 查不到、去重也去不掉。

要求：equals 判定相等的 JsonPrimitive，hashCode 也必须一致（遵守 equals/hashCode 契约）；
不相等的值不要凑到一起，其它类型的 hash 行为别动。改完补测试。
