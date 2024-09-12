---
author: Noel
pubDatetime: 2024-08-01T23:42:31.000+08:00
modDatetime: 2024-08-01T23:42:31.000+08:00
title: JSHunter-一款针对于前端的未授权访问扫描工具
featured: true
draft: false
tags:
  - 网络安全
  - Coding
  - Golang
description: 
   从JSHunter探究 AI辅助挖掘+前端未授权扫描... 文章首发于公众号https://mp.weixin.qq.com/s/heHRbbemwVAMcEYX2NhQuQ
---


很早之前挖的一个坑,到目前也算是初步填坑了，分享一下开发背景和过程。

⚠️文章篇幅偏长，建议摸🐟时阅读。

# 背景

开发这款工具主要有以下两点背景:

1. 渗透测试中遇到的webpack场景越来越多。
2. JSFinder类工具的瓶颈。

请允许我娓娓道来…

## 背景一：webpack场景越来越多

背景一：Webpack场景越来越多

随着前端技术的快速发展，React、Vue、Angular等前端框架逐渐成为主流，前端框架的普及在为开发人员提供了更高效、更便捷开发体验的同时，也随之带来了新的安全问题。其中最典型的问题两个问题：Webpack打包类网站中的1.信息泄漏 2.接口泄漏。

针对 `信息泄漏和接口泄漏` 问题, 已经出现了很多优秀的开源工具解决方案,比如：[https://github.com/rtcatc/Packer-Fuzzer。](https://github.com/rtcatc/Packer-Fuzzer%E3%80%82)

除此之外，在前端框架还面临另一个问题：路由缺失。这也算是一种未授权访问漏洞，通过访问未做限制的路由，攻击者可以访问任意功能页面，进一步根据页面加载的请求进行挖掘。

**本工具的首要目标就是自动化的去寻找当前目标网页中的路由，并尝试从中寻找出的未授权访问(路由守卫缺失)的地址。**

## 背景二：JSFinder类工具的瓶颈

随便在GitHub上找一款javascript相关的安全工具，我们都能在其中看到JSFinder的影子，这从侧面也体现了JSFinder这款工具的优秀。

然而，这么久以来好像JSFinder类的工具仍然停留在仅仅寻找在接口地址上。结合背景一的场景会发现：随着前端场景的变化,仅仅通过正则去匹配接口地址可能已经无法满足现在的需求, 现在更希望的是能在匹配接口地址的同时, 还能够构造该接口所需要的参数，这有进一步加强了对接口的挖掘深度。

然而构造参数并非想象中那么简单。奈何本人编程技术比较菜, 又恰巧AI盛行, 不如就让数据解析和构造参数这一步繁琐的逻辑放手交给AI去做,看看在AI的赋能下, 是否能将前面的愿景变为现实。

# 详细设计

简单画了一个图来帮助各位理解 `JSHunter`的工作流程和逻辑，如下图所示：

![Untitled](../../assets/images/JSHunter-%E4%B8%80%E6%AC%BE%E9%92%88%E5%AF%B9%E4%BA%8E%E5%89%8D%E7%AB%AF%E7%9A%84%E6%9C%AA%E6%8E%88%E6%9D%83%E8%AE%BF%E9%97%AE%E6%89%AB%E6%8F%8F%E5%B7%A5%E5%85%B7%20236b362ffa194821a51da5f243a6ecf5/26211743-67f6-46c8-9a6d-0a4e42a1d3d8.png)

根据前面的背景主要将该工具设计为两个模块：

1. VueRouter 模块
2. Endpoint 模块

## VueRouter 模块

既然要进行路由检测, 那第一步自然就得拿到该页面(尽可能多)的路由.最开始设想了两种提取路由的方法：1.通过正则去提取 2.通过JS去提取。

如何通过正则去提取?

根据测试经验, 一般在翻JS的过程中，出了接口地址我更关心其中的 `path`关键字,比如下面这段js代码片段,那我们要找的路由自然就是 `/about`

```json
{
	"path": "/about",
	"name": "About",
	"component": "xxx",
}
```

但实际上， 除了上诉结构之外还有其他结构的路由形式， 如下面这段js：

```json
{
	"path": "/account",
	"name": "account",
	"redirect": "account/info"
	"component": "",
	"meta": {
		"requiresRole": 1
	},
	"children": [
		{
			"component": "",
			"path": "info"
		},
		{
			"component": "",
			"path": "bills"
		},
		{
			"component": "",
			"path": "littlecard"
		}
	],
}
```

这种形式，我们需要提取的路由就是 `/accout/info` `/account/bills` `/account/littlecard`。

由此可见，使用正则匹配需要极度依靠正则表达式的准度，同时不同匹配内容还得使用不同的处理方法。**简而言之,使用正则匹配要考虑的数据结构太多了, 这种方法不太稳定。**

于是就去寻找第二种方法，尝试通过 js本身去提取到相关路由。通过一番检索，发现了P神的 [vueinfo](https://github.com/phith0n/vueinfo) 项目，非常符合我想要的效果, 关键是使用起来也比较简单，于是敲定了这种提取方式。

在获取到所有路由路径之后，还有一个需要处理的难点：**如何判断该路由是否存在未授权访问?**

由于页面都是通过javascript动态渲染而成, 所以直接通过页面特征进行判断不太现实.不过通过观察，我发现了以下两种场景能够判断不存在未授权访问：

场景一：

一些登陆页面, 在访问一些路由后,会跳转到首页并携带 redirect参数。

比如某网站的登陆首页的地址为:

```json
http://example.com/#/index
```

如果我们去访问从JS中获得的路由信息:

```json
http://example.com/#/accout/info
```

最后会发现网页又跳转会登陆首页，且URL会出现如下形式

```json
http://example.com/#/index?redirect=%2Faccout%2Finfo
```

场景二:

访问路由前、后的地址相同，即访问构造后的路由就完全跳回之前的地址

比如某网站首页地址为：

```
http://example.com/index
```

访问

```
http://example.com/accout/info
```

跳转到

```
http://example.com/index
```

> 注意：这里并不是忘记加锚点,而是表示 加锚点和不加锚点两种方式处理逻辑都是相通的
> 

于是我通过以上两种逻辑来判断网站不存在未授权访问漏洞。

但只通过以上述方式去判断是存在未授权漏洞是否存在在问题？答案是肯定的，因为有些类似于资源展示类相关的路由虽然能访问，但是其本质上就是静态页面，不存在敏感信息，这时使用上述的逻辑去判断显然是符合未授权访问的, 但实际上这一判断是错误的。

因此如果想要仅仅依靠程序逻辑去判断该路由是否未授权访问漏洞是一种不太好的策略，于是我的解决方案是对所有判定为未授权访问的路由地址的网页进行截图保存，输出报告，随后配合人工审查。这是我目前来说能想到的比较折中的方案。

## Endpoint 模块

该模块参考了https://github.com/rtcatc/Packer-Fuzzer中提取接口地址的正则表达式,用来提取相关接口及其涉及到的参数:

以如下匹配到的结果为例：

```json
i.get("/api/public/staff/get/full").
i.get("/api/public/trainingcard/type/get",{ids:C.product_id}).
i.get("/api/homepage/get",{id:t}).
i.post("/api/utils/file/get_list",{origin_type:"homepage"}).
```

针对以上第一个匹配结果，很容易能判断请求接口地址为 `/api/public/staff/get/full` ，请求方法为`GET`;

同样针对第二个目标，能确定其请求的模版为 `"/api/public/trainingcard/type/get?id=xxx`即该接口是带有请求参数的，请求方法也是`GET`，第三个同理;

而第四个则是需要使用post去请求 `/api/utils/file/get_list` 并且其请求体中带有参数 `{"origin_type":"homepage"}`.

这些匹配结果通过人工还是很容判断，但是如果要手动去解析每个匹配结果的话逻辑比较复杂(懒狗一个), 于是趁着AI的热度，利用AI做一下解析和参数填充，返回如下的JSON格式：

```json
{
"path": "xxxx",
"method": "GET/POST",
"query": "xxxxx"
"data": "data"
}
```

比如针对:`i.get("/api/public/trainingcard/type/get",{ids:C.product_id}).`就能解析为

```json
{
"path": "/api/public/trainingcard/type/get",
"method": "GET",
"query": "id=1231233123"
"data": ""
}
```

针对: `i.post("/api/utils/file/get_list",{origin_type:"homepage"}).`能够解析为：

```json
{
"path": "/api/utils/file/get_list",
"method": "POST",
"query": ""
"data": "{\"origin_type\":\"homepage\"}"
}
```

于是再根据解析的结构构造相应的请求进行发送即可。

关于未授权的判断上并没有采取单一的通过请求状态码的形式进行判断，因为考虑到有写接口访问即使是404的情况，返回内容有时也会存在类似于 “缺少xxx参数” 等相关信息，

于是采取的策略为将所有的请求信息记录，最后统一输出到md中，配合人工审查漏洞挖掘。

**目前该功能还属于测试阶段**，原因如下：

1. Prompt不够准确
2. LLM经常抽风

### 关于敏感信息提取

因为是JS分析, 涉及到JS分析的话顺便检查一下JS里面是否存在敏感信息也是很轻易想到的一个事，但从开发背景上来看该功能属于是越写越偏了。

关于敏感信息提取功能的本省，我希望在判断敏感信息之外还有一种更灵活的方式，即除了使用正则匹配外还有一些其他的逻辑来处理相关提取到的内容，而不是仅仅依靠单一的正则，但是Go又不太支持插件式加载，于是采用了一种比较low的方式进行加载。如果你感兴趣，可以参考 `pkg/extracter/extractor/api_key/key.go` 的编写模式，才了解我的实现过程。

# 使用方法

使用方法放仓库了：

[https://github.com/N0el4kLs/JSHunter](https://github.com/N0el4kLs/JSHunter)

# 最后

非常感谢🙏各位师傅能看到最后，祝各位师傅们身体健康，生活愉快，多赚💰。