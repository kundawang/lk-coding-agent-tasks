我们用 jsdom 跑前端单测，代码里大量使用 document.forms.login、document.images.logo 这种
按 name（或 id）直接取元素的写法——浏览器是支持的，jsdom 里拿到的是 undefined，
一堆老测试跑不过，只能一个个改成 querySelector。

要求：实现 Document 的 named properties 访问（forms、images、embeds、以及带 name 的表单控件这些），
行为要跟 HTML 规范一致（同名多个元素时返回集合、找不到返回 undefined 之类）。
现有 API 的行为别动。改完补测试。
