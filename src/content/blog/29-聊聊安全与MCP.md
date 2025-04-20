---
author: Noel
pubDatetime: 2025-04-06T09:00:11.000+08:00
modDatetime: 2025-04-06T09:00:11.000+08:00
title: 聊聊安全与MCP
featured: false
draft: false
tags:
  - AI
  - MCP
description: |
   文章首发与微信公众号: https://mp.weixin.qq.com/s/8ylk996b2b3wBw3ehI7XbA
---



最近MCP热度有点高了,并且实际开发上手后，挺有感触的。往好的说，能够显著提升工作效率；往坏了的说，xxx又要失业了。

借这个机会，来谈谈对MCP相关的一些内容。



## Table of Contents

## MCP是什么

网上已经有很多且很详细的关于MCP是什么的介绍了，同样的内容这里就不在赘述了。作为一个门外汉，笔者就个人经验而言，谈谈对MCP的理解。

MCP(Model Context Protocol)是一个协议，但是我更愿意将它***误认为***是提供给大预言模型(LLM)的一个抽象API。通过这个API，LLM能够访问和操作各种外部"资源"，实现与外部世界的交互。

既然作为API，MCP继承了传统API的诸多优势,如：

1. **服务抽象化**：将数据和服务通过统一API暴露给调用者，使得交互逻辑更加清晰。
2. **高度可扩展性**：可以集成更多的API，轻松地拓展新的功能和资源。

除此之外，相较于传统的API，现在的MCP(理论上)甚至不需要用户填充任何API参数。在使用体验上，即使是不了解AI的用户，也只需使用简单统一的命令(如：npx -y xxx),就能让自己想要的服务或功能接入大模型模型，极大降低了使用门槛。

前面提到了：“LLM能够访问和操作各种外部‘**资源**’”, 这里的**“资源”**又是指什么呢？答案：**数据源**。

数据源有很多表现形式：比如本地的文件、本地的数据库服务，远程的API等等。

官方中还提到了`MCP 提供了一种将 AI 模型连接到不同数据源和工具的标准化方式`,那工具(“Tool”)呢？

这里的“工具”并不是传统意义上的某个应用程序。而是访问数据源的一个行为，一个动作，就如AI Agent中的概念：

> An Agent is a system that leverages an AI model to interact with its environment in order to achieve a user-defined objective.It combines reasoning, planning, and the execution of actions (often via external tools) to fulfill tasks.

`提供了一个与外界环境交互的方式，从而完成指定的任务`。而“工具”，是实现这个任务中的一个动作。其本质还是对数据的操作。比如最近比较火的例子：GhidraMCP。其原理不是简单地将Ghidra软件暴露给模型，而是将Ghidra中的反编译能力、代码分析功能等抽象为一系列操作，让模型能够有目的地获取和处理二进制分析数据。

除了GhidraMCP，这里也介绍一下最近我们自己写的MCP工具：

[inject-mcp](https://github.com/Joe1sn/inject-mcp)：使用模型上下文协议完成多种 DLL Shellcode 的注入。

[BurpMCP](https://github.com/N0el4kLs/BurpMCP)：允许LLMs从Burp Suite代理历史记录中检索数据, 从而帮助研究人员和渗透测试人员更有效地进行安全测试和分析。



## MCP对网络安全带来的可能

笔者主要从渗透测试的角度进行切入，谈谈MCP可能在渗透测试方向的潜力。

前面提到“工具”本身是一个动作，其背后本质是对数据的操作。在网络安全里面，这个“工具”（双冠一下）可太多了，毕竟网络安全里面还有个专门的名词，“脚本小子”。

对于大多数渗透场景中，信息收集等前期工作往往需要耗费大量时间和精力，且流程相对固定，也算是公式化了，比如扫资产->扫指纹,再到后面的每个功能点测试SQL等等.如果MCP能够实现多工具的联动,在未来，无疑会将单兵作战的能力再突破一个层次。



## MCP暴露的安全问题

或许读者已经使用过MCP，可能已经发现一个问题：在填写MCP配置时，如果是调用外部的SSE服务，在使用时只需要填写一个地址就好了，基本没有任何认证信息要求。开始介绍MCP的时候提到过，MCP就像是API，既然是API，<u>理论上就应该存在访问控制的机制</u>，但这也只是理论上，并非所有开发者一开始就会考虑到安全问题。

![image-20250406200735269](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250406233055237-7e640.png)



现在来假设一个认证不足导致的危险案例：

[Filesystem MCP Serve](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)是一个可以用于操作本地文件的MCP，通过这个MCP，可以实现对本地文件的读写/增删文件/查询。虽然官方实现仅支持Stdio传输（限制在本地访问），但不排除在未来，许多开发者为了方便，可能会开发支持SSE的版本,用于管理服务器上的文件资源文件。当这类高危操作暴露在互联网中，且同时没有设置恰当的访问权限时(比如安全目录，白名单IP)，这将引发一个怎么的灾难？



### 实验

实验了一下：用nmap和http简单扫了一下对应端口的SSE特征，使用Quake空间引擎搜了一下`http_path:"/sse"and response:"text/event-stream"`，还是能发现可以直接使用的SSE服务,至少理论行得通。感兴趣的师傅可以深入挖掘一下其他方法：

![image-20250406180036728](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250406233055238-b93fb.png)

![image-20250406180015925](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250406233055238-1eb92.png)

![image-20250406180157972](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250406233055238-b81bb.png)

### 如何保护

当然，上述案例并非鼓励大家去利用他人的MCP服务，而是希望提醒使用或开发MCP服务的读者，了解所使用工具可能存在的安全风险。除了前面提到的问题，[Anthropic](https://modelcontextprotocol.io/docs/concepts/architecture#security-considerations) 官网还详细阐述了针对“Resource（资源）”“Tool（工具）”和“Prompt（提示）”的其他安全风险。感兴趣的读者可以前往官网深入了解相关内容。

![image-20250406180836477](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250406233055238-d882f.png)



