---
author: Noel
pubDatetime: 2022-09-25T23:42:31.000+08:00
modDatetime: 2022-09-25T23:42:31.000+08:00
title: 常见WIFI攻击
featured: false
draft: false
tags:
  - Redteam
  - 网络安全
  - phishing
  - Wifi
description: 
   本篇文章主要记录有关 **WIFI** 的部分概念以及其相关的攻击向量.
---

# 前言

本篇文章主要记录有关 **WIFI** 的部分概念以及其相关的攻击向量.

> Notice: This passage is for educational and informational purposes only.

<!-- more -->

# 正文

## 概念

**AP or Access Point**
无线接入点,他是一个转发器.或许你对他的另一个名字: 路由器 更为熟悉.

**STD(Station)**

站点,也就是客户端.所有连接到 AP 的终端设备都可以称之为 station.

**SSID or Service Set Identifier**

服务集标识.你可以将他理解为无线网络的名称.

**网络标准**

2.4G 5G以及新出的6G(WIFI 6). WiFi网络初期使用的 2.4GHz频段,但由于设备越来越多,设备间互相干扰就越来越严重.因此,5G频段成为新的传输频段.

根据初中初中物理,波长表达式
$$
λ波长=u波速/f频率
$$
频率越高,穿透性越弱.

> 误区: 这里的 G并不是 generation 的意思.他表示的频段,单位为Hz

![image-20220926105155840](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220926105155840.png)



**Channel 信道**

可以理解为传送无线信号的通道。信道的主要作用就是为了避免信号之间的相关干扰。

**WPS or WIFI Protected Setup**

简化用户链接无线网络的一种加密。也就是常说的采用PIN码登录。 用户只需要按一下路由器上的 wps 按键，就能完成无线网络的连接。

**WPA/WAP2/WAP-PSK/WAP2-PSK**

WPA: Wi-Fi Protected Access

WPA的出现是为了解决 WEP 不安全加密的缺陷。 而WPA2是WPA的升级版本，它增强了AES加密方式。

WPA-PSK  WPA2-PSK(pre-shared key)

WPA和WPA需要使用专用的 Radius 认证服务器。由于其价格昂贵，因此对于普通用户而言，使用 wap 的简化版本，使用共享密钥进行加密，在避免昂贵的设备费用外，也能保证安全性。

WPA/WPA2混合加密方式兼具了WPA2的安全性，也具备WPA的广泛兼容性，可以根据设备支持的情况自动选择WPA或WPA2加密机制，适用性较好。

![image-20220917215235164](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220917215235164.png)



## 常见攻击向量

### PIN码爆破

简述下WPS加密的漏洞

> WPS的PIN码一共由 8 位组成，其中第八位是校验位，因此理论上的最大爆破次数为 10 的 7 次方.
>
> 但是,在实际的认证过程中,PIN会把认证分为两部分,前4位和后3位.只有当前4位正确时,才会对后3位进行校验.因此,最大爆破次数又从最初的 10 的 7 次方减少至 10 的 4 次方 + 10 的 3 次方,也就是最多尝试 11000 次 就能得到结果.

不过目前现在大多数的路由器都存在防PIN功能.如果恶意攻击者尝试暴力攻击破解PIN一段时间后,路由器将会自动锁定 PIN 功能.

工具推荐: https://github.com/derv82/wifite2

### WPA/WPA2爆破

首先我们需要对 WPA/WPA2 的认证方式或者说工作原理有一定的了解,为了简化,以家用WPA-PSK/WPA2-PSK认证过程为例：

1. AP会定期向外广播Beacon帧(携带自身关联 的SSID),无线终端通过侦听Beacon帧来发现网络
2. 线终端通过发送Probe Request帧来请求加入网络,AP收到无线终端发送的请求帧后,会发送Probe Respnse帧做出相应.
3. 无线终端通过发生Authentication Request帧向指定AP请求认证;AP收到后会发送Authentcation Response帧做出相应
4. 无线终端发送association request帧向指定AP请求关联,AP收到后会发送association response帧做出回应.
5. 关联完成之后,STA与AP会进行四步握手协议交互过程.这个过程的目的是通过STA和AP都有的主秘钥,协商出一个对会话信息进行加密的会话密钥.我们破解WPA2加密的无线网络,主要是为了对这四步握手进行解析和暴力破解.

> 来自： [无线WiFi接入、干扰、爆破过程分析-(二)](https://canbaoafeizai.github.io/2020/02/04/%E6%97%A0%E7%BA%BFWiFi%E6%8E%A5%E5%85%A5%E3%80%81%E5%B9%B2%E6%89%B0%E3%80%81%E7%88%86%E7%A0%B4%E8%BF%87%E7%A8%8B%E5%88%86%E6%9E%90-(%E4%BA%8C)/)

因此,爆破WPA加密的关键在于获取 Station 和 AP连接前的认证信息包,也就是 **握手包**.

实验测试: 使用aircrack-ng 工具套件爆破WPA密码

查看扩展网卡

```
sudo airmon-ng
```

开启网卡监听模式

```
sudo airmon-ng start <网卡名称>
```

确实是否已经开启监听模式

```
iwconfig
```

![image-20220922121342735](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220922121342735.png)

> 开启监听模式后无线网卡无法继续连接 wifi，如需使用WIFI, 在使用后需要关闭监听模式即可.

扫描附近的无线网络信号

```
sudo airodump-ng <网卡名称>
```

![image-20220922121729163](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220922121729163.png)

对上述命令显示的部分字段进行说明:

```
BSSID:AP的mac地址
PWR: 无线网络的信号,强信号约为-40。平均一个约为-55，一个弱的开始在-70左右。Wi-Fi适配器下限（又称接收灵敏度）通常约为-80/-90。
#Data: 捕获的数据包
ENC: 加密方式
MB: AP支持的最大传输速率
CH: 传输信道
ESSID: 无线网络名称
https://www.aircrack-ng.org/doku.php?id=airodump-ng
```

抓取WiFi认证握手包(关键步骤)

```shell
sudo airodump-ng -c channel -w write_path --bssid ap_mac <网卡名称>
```

当出现 `WPA handshake `字样时,表示已经成功抓取到认证握手包.

![image-20220922135445384](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220922135445384.png)

握手包会以 `.cap` 后缀结尾,保存在你所指定的目录,如下:

![image-20220922135958559](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220922135958559.png)

为了快速获取握手包,我们可以使用 `aireplay-ng` 工具向 station 发送 `Deauthentication` 数据包,将在线用户进行强制下线处理:

```
sudo aireplay-ng -0 0 -a ap_mac -c station_mac <网卡名称>
参数说明:
-0 表示使用 Deauthentication 取消认证攻击,后面跟的 0 表示把发送数据包的数量, 0 表示不断发送
-a 表示 ap 的mac 地址,我们就输入前面 airdump-ng --bssid 指定的 ap地址
-c 表示要攻击取消认证的station, 在左边可以看到又两个 station, 这里我们选择测试机 AC:... 作为受害者,进行 deauthentication 攻击

详细描述:https://www.aircrack-ng.org/doku.php?id=aireplay-ng
```

![image-20220922143240568](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220922143240568.png)



在获取到握手包后,就可以通过字典进行密码爆破操作:

```
sudo aircrack-ng -w dict_path demo.cap
```

如果字典中存在该SSID所对应的密码,您将会得到以下结果.

![image-20220922140922662](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220922140922662.png)

其中, `KEY FOUND! [****]` 中方括号`[`中的内容就是该 WIFI 的密码

本实验使用的是 `aircrack-ng套件`,当然你也可以使用[fluxion](),通过更简单引导操作来达到相同的攻击效果,或者使用其他你喜欢的工具.

### AP 攻击

**Authentication Flood Attack**

认证洪水攻击:

> 攻击者向AP发送大量伪造的身份验证请求帧，当AP收到大量伪造的身份验证请求而超过所能承受的能力时，它将断开其他无线服务连接。 该攻击也是无线网络拒绝服务的一种形式。

**Deauthentication Flood Attack**

取消认证洪水攻击

> 该攻击方式主要是通过伪造AP向客户端单播地址发送取消身份验证帧，将客户端转为未关联/未认证的状态。该攻击也是无线网络拒绝服务攻击的一种。其也被称为Deauth攻击。

**Fake Beacon**

假信标攻击

> 这是一种伪AP攻击的攻击。Beacon就是AP的无线型号， Fake Beacon 攻击就是攻击者模拟AP向无线信道中发送大量的虚假SSID来充斥客户端，使客户端找不到真正的AP。

工具推荐：mdk3

为了更好的理解这里提到的几种攻击AP的方式, 读者可以尝试使用 Wireshark 进行数据包监听,来查看具体的流量包.

### 客户端攻击

`evil twin attack`

伪AP攻击

原理：

> 攻击者会克隆出一个和目标AP拥有完全相同的 SSID名称, 工作信道,加密方式等的假AP, 如果此时我们让真正的AP 下线,让用户进行重新链接的话,由于我们克隆的AP信号比较前强,用户会自动连接到我们创建的虚假AP上,因此就能捕获客户端发送的信息.

使用 `fluxion` 进行 `evil twin attack`:

参考连接:

https://blog.csdn.net/CrotZZ/article/details/122363374

注意:再 **为目标跟踪选择无线接口时**, 选择 跳过:

![image-20220925205332599](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220925205332599.png)

踩坑:

我在使用`fluxion`进行测试的时候,在最后一步时出现了以下报错

```
Cannot find device fluxwl0v.
```

我在原项目也发现了同样的 [issue](https://github.com/FluxionNetwork/fluxion/issues/864).

也尝试了重启, 以及使用 `sudo airmon-ng check kill` 命令,但都未能得到解决方案.

最后看到一个回复,其关键内容为 ` you may just be better off using a dedicated hacking OS that has the proper settings for wifi hacking like Kali or Parrot OS`.由于我的操作系统时`Ubuntu`,猜测可能时这个问题,因此又去装了个 `parrot OS`,装好之后发现虚拟机不能接受网卡, 于是我有下载了`Kali`, 最终完美解决了这个问题.推荐在kali下使用该工具.



**MITM Attack**

中间人攻击时局域网中攻击最常见的一种攻击，其中最常见的是 ARP欺骗攻击。

工具推荐：

[ettercap](https://salsa.debian.org/pkg-security-team/ettercap)

实验测试, 使用 ettercap 进行中间人攻击

参考连接:

https://www.youtube.com/watch?v=ogtWS6MfiWM

https://www.itggg.cn/xuexi/270.html

踩坑：

对 ettercap 中的 target 1 和 target 2 一直没有概念，看到很多文章都说的是 taget 1 选择 网关地址， target 2 选择目标地址，但是我添加之后，没办法捕获到 http 的请求。

查看一下帮助手册.

![image-20220925200516347](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220925200516347.png)

翻译过来大概意思是： 

> 这两个目标旨在过滤一个从一个到另一个目标的流量，反之亦然

意思是主要选择两个目标地址就行了?



## 参考

[本机号码一键登录的安全分析](https://mabin004.github.io/2020/02/20/%E6%9C%AC%E6%9C%BA%E5%8F%B7%E7%A0%81%E4%B8%80%E9%94%AE%E7%99%BB%E5%BD%95%E7%9A%84%E5%AE%89%E5%85%A8%E5%88%86%E6%9E%90/)

[aircrack-ng toolkit](https://www.aircrack-ng.org/doku.php?id=airodump-ng)

[无线WiFi接入、干扰、爆破过程分析-(二)](https://canbaoafeizai.github.io/2020/02/04/%E6%97%A0%E7%BA%BFWiFi%E6%8E%A5%E5%85%A5%E3%80%81%E5%B9%B2%E6%89%B0%E3%80%81%E7%88%86%E7%A0%B4%E8%BF%87%E7%A8%8B%E5%88%86%E6%9E%90-(%E4%BA%8C)/)

[使用fluxion进行钓鱼](https://blog.csdn.net/CrotZZ/article/details/122363374)



**本文所提到的所有开源项目的地址**

[wifipumpkin3](https://github.com/P0cL4bs/wifipumpkin3)

[fluxion](https://github.com/FluxionNetwork/fluxion)

[wifite2](https://github.com/derv82/wifite2)

[ettercap](https://salsa.debian.org/pkg-security-team/ettercap) kali自带

[aircrack-ng](https://salsa.debian.org/pkg-security-team/aircrack-ng) kali自带