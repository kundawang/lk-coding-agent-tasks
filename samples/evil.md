# 安全样例

<script>alert(1)</script>

<img src=x onerror="alert(2)">

<iframe src="https://evil.example"></iframe>

[点我](javascript:alert(3))

[另一个](data:text/html;base64,PHNjcmlwdD5hbGVydCg0KTwvc2NyaXB0Pg==)

<!-- <script>alert(5)</script> -->

**没闭合的粗体

<div class="x" onclick="alert(6)">

<b>没闭合的标签

> 引用里塞一个 <a href="javascript:alert(7)">链接</a>
