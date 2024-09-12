---
author: Noel
pubDatetime: 2022-06-13T23:42:31.000+08:00
modDatetime: 2022-06-13T23:42:31.000+08:00
title: 搭建属于自己的RSS
featured: false
draft: false
tags:
  - Rss
  - 折腾
description: 
   和大多数人一样，使用 `RSS` 的原因是为了从如今信息爆炸的网络媒体中脱离出来。
---

> 看见好玩儿的东西就想折腾折腾

# 前言

和大多数人一样，使用 `RSS` 的原因是为了从如今信息爆炸的网络媒体中脱离出来。

# 正文

在 `Google` 了一段内容后,我发现 `Tiny Tiny RSS + fever api + RSSHub` 这一套组合能够满足我的需求.动手开干!

## `TT RSS + fever`

现在的 `Web 应用` 基本上都提供了 `docker 部署` 的方式, `ttrss` 也不例外.

`TT RSS`一款基于 PHP 的免费开源 RSS 聚合阅读器,`Awesome TTRSS`提供一个 「一站式容器化」 的 Tiny Tiny RSS 解决方案，通过提供简易的部署方式以及一些额外插件，以提升用户体验

项目地址: [Awesome TTRSS](https://ttrss.henry.wang/zh/#%E9%80%9A%E8%BF%87-docker-compose-%E9%83%A8%E7%BD%B2)


这里我选择使用 `docker-compose` 的方式进行部署.
先用以下命令将 `docker-compose.yml` 文件拉取到本地
```
wget https://raw.githubusercontent.com/HenryQW/Awesome-TTRSS/main/docker-compose.yml
```

拉取之后,我们需要对其中的进行一部分的更改,
```
SELF_URL_PATH=http://localhost:181/ # please change to your own domain
需要将这里的地址设置为你 vps 的地址.

- DB_PASS=ttrss # use the same password defined in `database.postgres`

environment:
  - POSTGRES_PASSWORD=ttrss # feel free to change the password
为了安全性,这两处的密码也需要进行更改, 注意 这两处的密码需要一致.


volumes:
      - ~/postgres/data/:/var/lib/postgresql/data # persist postgres data to ~/postgres/data/ on the host
这里我将 `~/postgres/data/` 改成了 `./postgres/data/`, 防止目录结构混乱
```

修改保存后,直接使用 `docker-compose up -d` 启动就好了. 随后访问 vps 的 `181` 端口就好了.

登录的默认账户和密码为 `admin` 和 `password`.进去之后记得修改密码.

如何启动 `fever api` 在 [`Awesome TTRSS` 项目](https://ttrss.henry.wang/zh/#fever-api)中也进行了说明. 

前往 `/prefs.php` 的偏好设置开启 `允许外部客户端通过 API 来访问该账户`

![20220601170644](http://particles.oss-cn-beijing.aliyuncs.com/img%5C1dc0223e14c111523ade8ecd8f6a68ed.png)

点击保存后,接着在 `Fever Emulation`,设置访问 `API` 的密码即可. 
![20220601170737](http://particles.oss-cn-beijing.aliyuncs.com/img%5Ced1eb5819442599c3b8eb349fc62b6a1.png)

接着使用客户端,比如 `Fluent Reader` 订阅地址 `/plugins/fever/` 就好了

![20220601171027](http://particles.oss-cn-beijing.aliyuncs.com/img%5C8b2979bfceaebfd45694b1eab0c10770.png)

## RSSHub 搭建

RSSHUB搭建已经有一段时间了，操作可以参考如下：

`RSSHub` 的搭建也很简单,你可以选择使用 `docker-compose` ,`Heroku` 或者 `Google App Engine` 等方式.更多部署方式你可以前往[rsshub的主页进行查看](https://docs.rsshub.app/install/)

这里我选择使用 `Heroku` 进行搭建.

先到 [`Heroku` 官网](https://dashboard.heroku.com/)进行注册一个账号,好像邮箱只能使用国外的, 好久之前部署的,有点忘记了.

然后前往这个[地址](https://dashboard.heroku.com/new?template=https%3A%2F%2Fgithub.com%2FDIYgod%2FRSSHub), 一直下一步,就能成功搭建了.



## RSS 推荐

[公众号转RSS订阅](https://github.com/zhengjim/Chinese-Security-RSS)

[网络安全资讯的RSS](https://github.com/ttttmr/wechat2rss)

[网络安全相关的RSS](https://github.com/zer0yu/CyberSecurityRSS)

