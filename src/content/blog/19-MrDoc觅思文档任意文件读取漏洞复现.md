---
author: Noel
pubDatetime: 2024-10-14T21:54:11.000+08:00
modDatetime: 2024-10-14T21:54:11.000+08:00
title: MrDoc觅思文档任意文件读取漏洞复现
featured: false
draft: false
tags:
  - 漏洞复现
  - 漏洞分析
  - 网络安全
description: |
    MrDoc觅思文档任意文件读取漏洞复现。文章首发于先知社区 https://xz.aliyun.com/t/14089
---

MrDoc觅思文档任意文件读取漏洞复现。文章首发于先知社区 https://xz.aliyun.com/t/14089

## Table of contents

## 影响版本:

commit提交记录是2月一号，但是最近一次 release版本时 2个月前v0.9.2,大概 v0.9.2以下的版本都存在漏洞.

## Commit记录：

[https://gitee.com/zmister/MrDoc/commit/b634cf84eedb669fc1f11ce87558b0b045301af1](https://gitee.com/zmister/MrDoc/commit/b634cf84eedb669fc1f11ce87558b0b045301af1)

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232147588-7e297.png)

## 漏洞分析:

通过commit记录可以看到是对变量 `media_filename` 进行了处理, 那么感觉问题就出现在 `media_filename` 这个变量，

我们下载下项目，切换到修复前的版本：

```bash
git clone https://gitee.com/zmister/MrDoc.git
git checkout d1ce
```

定位一下漏洞位置 `app_doc/report_utils.py#152`：

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221122-f6c9a.png)

这段代码就是从markdown文件中去查找静态资源,然后对查找到的每个静态资源进行路径处理，最后移动到一个文件中进行下载。

先来看第一个正则表达式：`pattern = r"\!\[.*?\]\(.*?\)"`，他是用来匹配

```bash
![]()
```

格式的字符串, 当然如果你对正则不熟悉，直接去问AI也行：

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-de5af.png)

接着会从匹配到的每个字符串中取出括号() 中的内容, 并进行资源目录查找，其中主要球了这个资源地址是以 `/media` 开头就行, 到这里基本上都能猜到payload的形式了, 无非就是  `/media/../../../xxx` ,

先吧这个函数取出来测试一下, 其中`self.media_path` 等一些路径变量我就先随便模拟了：

```python
import re
import os
import pathlib
from urllib.parse import unquote

md_content = '''
![example_image](/media/../requirements.txt)
'''
pattern = r"\!\[.*?\]\(.*?\)"
media_list = re.findall(pattern, md_content)
print(media_list)
for media in media_list:
    try:
        media_filename = media.replace('//', '/').split("(")[-1].split(")")[0]  # 媒体文件的文件名
        print(media_filename)
    except:
        continue
        # 对本地静态文件进行复制
    if media_filename.startswith("/media"):
        # print(media_filename)
        sub_folder = "/" + media_filename.split("/")[2]  # 获取子文件夹的名称
        # print(sub_folder)
        print("sub_folder is", sub_folder)
        is_sub_folder = os.path.exists("/Users/shaw/language/python_floder/MrDoc/media/reportmd_temp"
                                       + sub_folder)
        # 替换MD内容的静态文件链接
        md_content = md_content.replace(media_filename, "." + media_filename)
        # 复制静态文件到指定文件夹
        new_file_path = pathlib.Path("/Users/shaw/language/python_floder/", unquote(media_filename)[1:])
        print("new_file_path is", new_file_path)
```

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-5e85b.png)

可以看到解析的路径是可以存在 `../` 路径穿越的，随后就使用 `shutil.copy` 对这个资源进行的复制操作.

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-87673.png)

## 漏洞复现：

接下来我们去找漏洞出发点,调用栈如下：

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-2feca.png)

最后找到是在这个地方，根据注释 `导出文集MD文件` ,去官网找一下这个功能：

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-c18b3.png)

搜索结果如下：[https://doc.mrdoc.pro/doc/45554/](https://doc.mrdoc.pro/doc/45554/)

那我们就去试一下：

先注册账号编辑一便文章，资源路径为 `![example_image](/media/../requirements.txt)`,然后保存到文集下面，这里我的文集是test2:

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-b4264.png)

然后来到 `我的文集----文集管理----选择文集----批量导出`

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-94ad2.png)

然后下载压缩包，解压就能发现里面有requirements.txt

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-bdf1f.png)

除此之外 img标签也是可以的
`<img src="/media/../../../etc/passwd"/>`

自此，漏洞复现结束

## 一次失败的尝试

既然这个地方的文件导出功能存在问题，那类似的，其他markdown的导出是否也存在同样的问题呢？带着这个疑问，我尝试去找了下类似于Mrdoc的其他开源在线文档系统，找到了一个用go语言写的mm-wiki:[https://github.com/phachon/mm-wiki](https://github.com/phachon/mm-wiki)

跳过环境搭建，先来黑盒测试一下功能，我先上传了一张照片，按照同样的逻辑加入了一个带有穿越路径的资源，如下，接着导出：

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-86514.png)

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-1f60c.png)

结果并没有出现类似的问题，我们再去看看相关的处理代码逻辑`app/controllers/page.go:367` ,发现打包的图片附件地址是从数据库检索的，然后使用了 `filepath.Join` 来拼接，那如果我们`attachment[”path”]` 是存在 `../` 这种穿越字符，那就能够造成目录穿越.因此接下来去查看下上传图片这个逻辑。

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-fb2f0.png)

图片上传的代码位于 `app/controllers/image.go:23` 

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-7872c.png)

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-c5d54.png)

可以看到, 在上传处使用了 `path.Join` 直接将上传的文件名进行了，因此在此处是存在目录穿越的，但是由于在保存文件之前进行了文件是否存在校验，所以及时存在目录穿越漏洞，也无法进行文件覆盖，从而也不能将数据插入到数据库中

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-d0dea.png)

所以最后该项目不存在类似的漏洞.

这里只列举了一个类似的网站，感兴趣的师傅可以利用相同的思路，去找找其他相关项目的再测测，说不定会有什么发现。

## 关于Markdown的一些漏洞

既然遇到Markdown了，那就顺带回顾一下关于markdown的一些常见漏洞吧.

历史上, markdown 出现最多的问题就是HTML渲染导致的XSS漏洞,这里举一些案例：

typora:

[Typora XSS 到 RCE (上)-安全客 - 安全资讯平台](https://www.anquanke.com/post/id/170665)

[Typora XSS 到 RCE (上)-安全客 - 安全资讯平台](https://www.anquanke.com/post/id/170665)

[CVE-2023-2317：Typora MD编辑器命令执行漏洞分析与复现](https://www.wevul.com/2386.html)

[Typora XSS Vulnerability](https://c0olw.github.io/2023/07/31/Typora-XSS-Vulnerability/)

[Typora XSS to Code Execution](https://blog.splitline.tw/typora-xss-to-code-execution/)

[https://github.com/typora/typora-issues/issues/2959](https://github.com/typora/typora-issues/issues/2959)

以及开源markdwon编辑器[https://pandao.github.io/editor.md/](https://pandao.github.io/editor.md/)的一些xss

[https://github.com/pandao/editor.md/issues?q=xss](https://github.com/pandao/editor.md/issues?q=xss)

但是，上面大部分的xss都是基于源码去分析了程序逻辑而找到xss漏洞，那平时的黑盒测试我们应该如何去找到markdown中的xss问题呢？

个人的理解：就是多尝试一些比较少见的标签去测试，举些例子：

```python
<iframe src=javascript://%0aalert('iframe')>
<embed src="https://c0olw.github.io/pic/1.html">
<audio src=x onerror=confirm("casrc")> //从xmind那抄来的
```

以一个在线网站网站为例，尝试最简单的payload都没啥反应

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-fc2d8.png)

换了个 `embed`  `iframe` 一下就出了，当然这个反射性没啥用，只是给各位平时做漏洞挖掘起到一点启发。

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-2b114.png)

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-4fa16.png)

当然mm-wiki上也是存在xss的,

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-7dbe6.png)

![Untitled](https://particles.oss-cn-beijing.aliyuncs.com/blog_img/20241014232221123-4e656.png)