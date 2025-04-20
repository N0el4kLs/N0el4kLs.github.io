---
author: Noel
pubDatetime: 2025-04-20T09:00:11.000+08:00
modDatetime: 2025-04-20T09:00:11.000+08:00
title: MCP自动化扫描思考以及mcp-scan源码阅读
featured: false
draft: false
tags:
  - AI
  - MCP
description: |
   上周慢雾科技发布了一个MCP-Security-Checklist,刚好最近在公众号中提到了MCP的安全问题。当时在公众号中只局限了未授权发访问这一部分。而慢雾这篇总结就非常全面了，大佬牛皮。
---



上周慢雾科技发布了一个[MCP-Security-Checklist](https://github.com/slowmist/MCP-Security-Checklist/blob/main/README_CN.md),刚好最近在公众号中提到了MCP的安全问题。当时在公众号中只局限了未授权发访问这一部分。而慢雾这篇总结就非常全面了，大佬牛皮。

既然指导方针有了，那能不能写个自动化脚本，来参考MCP-Security-Checklist实现一部分自动化检查呢？

![mcp_risk_points_cn](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250420150748908-a7062.png)



## Table of Contents

## MCP自动扫描实现分析以及困难点

**Server 身份验证与授权**：这部分包含了上次我在微信文章中提到的未授权部分。关于身份验证和未授权，我感觉是设计架构上的缺陷，如果能在后面将MCP的SSE与Web框架相结合，这个问题应该可以很好解决。另外这方面能不能存在自动化检测呢？当然可以，本质上就是MCP客户端去链接Sever。哪又如何判断是否属于未授权呢？这得配合MCP背后的Tool才能判断。如果Tool是直接简单的数据展示，那就不存在未授权；如果是能执行系统命令/执行SQL语句，那就可以认定是未授权。

**后台持久性控制**、**部署与运行时安全**、**监控与日志记录**、**AI 控制与监控**：这部分是在使用过程中的问题，理论上是得从MCP Client架构上考虑的。这里暂时忽略

**供应链安全**：这个和pip一样，本质上得靠第三方维护数据源的平台。这里暂时忽略。

...

分析来分析去，目前能做的就是处理**MCP Tools 与 Servers 管理**这个部分，而这个部分中整个难点主要是围绕提示词注入(Prompt Injection)展开的，包括：

1. **MCP工具命名控制**
2. **恶意MCP检测**
3. **MCP工具验证**
4. **安全更新**
5. **函数名校验**



上面列举的这些问题本质上这些问题都是有提示词注入导致的，比如，攻击者可能在 Tool 描述中伪装使用**本地已存在工具**的描述，从而实现描述覆盖，影响工具的优先级判断；或者直接在工具描述中嵌入对其他本地 MCP 工具的调用，造成意图外的行为触发.

上面提到的问题几乎都与“工具描述”有关，也就是提示词本身。那么，是否可以直接在客户端获取这些工具描述，并进行分析呢？

当然可以。但问题在于：提示词本质上是自然语言，具有高度的灵活性和模糊性，**静态分析很容易被绕过**。理想的解决方案是，在 MCP Client 与 MCP Server 之间引入一个“中间人”组件，**动态监测工具调用过程**，从行为层面识别和拦截异常，从而有效规避提示词注入带来的风险。



## MCP-Scan 阅读

[MCP-Scan](https://github.com/invariantlabs-ai/mcp-scan)是用于检查本地MCP是否存在漏洞的一个扫描工具，其主要用于监测提示词注入、工具劫持和Rug Pull(中文名不知道怎么翻译). 带着上面的疑问，来看看这个工具是怎么进行相关问题的监测，是否能解答我的疑问。

> Rug pull: a malicious server can change the tool description after the client has already approved it.



### 提示词注入检测

关键函数`verify_server` 位于 `MCPScanner.py:168`:

``` python
def verify_server(tools, prompts, resources, base_url):
    if len(tools) == 0:
        return []
    messages = [
        {
            "role": "system",
            "content": f"Tool Name:{tool.name}\nTool Description:{tool.description}",
        }
        for tool in tools
    ]
    url = base_url + "/api/v1/public/mcp"
    headers = {"Content-Type": "application/json"}
    data = {
        "messages": messages,
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
     ...
```

将工具描述上传到远程进行分析。远程大概率也是调用AI Provider的API进行分析的。简单尝试了两个案例，如下图哦所示。 总的来说，还是属于最简单粗暴的检测方式。

![image-20250420141001948](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20250420150748908-c039d.png)



### Rug Pull检测

关键代码位于：`MCPScanner.py:480`

```python
for tool, verified in zip(tools, verification_result):
    changed, prev_data = self.storage_file.check_and_update(
        server_name, tool, verified.value
    )
    additional_text = None
    if changed.value is True:
       	...
```

```python
# MCPScanner.py:331 check_and_update function
def check_and_update(self, server_name, tool, verified):
    key = f"{server_name}.{tool.name}"
    hash = self.compute_hash(tool)
    new_data = {
        "hash": hash,
        "timestamp": datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
        "description": tool.description,
    }
    changed = False
    message = None
    prev_data = None
    if key in self.data:
        prev_data = self.data[key]
        changed = prev_data["hash"] != new_data["hash"]
        if changed:
            message = (
                "tool description changed since previous scan at "
                + prev_data["timestamp"]
            )
	...
```

通过计算Tool的hash是否改变，来判断工具的提示词(工具的完整性)是否被动态修改，来判断是否存在Rug Pull漏洞。这个方法能够有效工具恶意修改的问题，但是距离工具劫持，感觉还差点意思



## 最后

至于效果整么样，师傅们自行评价吧。

BTW，mcp-scan的代码写得很优雅。