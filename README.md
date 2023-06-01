<img src="resources/icon.jpeg" alt="icon" style="zoom: 20%;" />

<h1 align="center">GhostKiller</h1>

<center>邮件追踪器，支持查看用户在邮件页面停留的时间
<center>NKU 数据库系统 2023 Spring 课程项目

## 原理

在邮件中嵌入一个对肉眼不可见的 1*1 大小图片，图片URL指向受控服务器。

对于需要查看用户留存时间的追踪器，对图片URL的请求会**在一定时间后**返回一个302跳转，跳转目标依然在受控服务器。多次跳转后，我们可以通过比较第一次访问时间和最后一次访问时间的到存留时间。
