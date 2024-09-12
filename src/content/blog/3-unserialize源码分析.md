---
author: Noel
pubDatetime: 2023-11-18T23:42:31.000+08:00
modDatetime: 2023-11-18T23:42:31.000+08:00
title: unserialize 源码调试
featured: false
draft: false
tags:
  - 网络安全
  - PHP
description: 
   本文尝试通过调试 unserialize 源码来理解PHP FAST GC的原理...
---


# PHP GC

全称`Garbage Collection`, 垃圾回收. 我们都知道 `PHP` 的底层是使用`C`语言实现的. 在C语言中的内存申请与释放都需要编程者手动的实现. 如果未将没有使用的空间释放`free()`掉, 就会出现内存泄露的问题.

在PHP中, 没有出现类似于 `malloc` 以及 `free` 的主动申请和释放的相关函数, 那他是怎么实现的呢?

那就是垃圾回收.

> 垃圾回收时一种自动的内存管理机制,当一个变量在程序中不在被需要时,应该予以释放,这种内存资源管理称为垃圾回收.

其中, 判断程序是否不再需要,是通过一个叫 `引用计数器`实现的.当某个变量的引用计数器为零, 则认为该对象以及被抛弃而应该释放其所占有的内存.

简单看下其相关数据结构. 引用计数器则为`zend_refcounted_h.refcount`.

```c
typedef struct _zend_refcounted_h {
    uint32_t         refcount;          /* 引用计数 */
    union {
        struct {
            ZEND_ENDIAN_LOHI_3(
                zend_uchar    type,     
                zend_uchar    flags,    /* 字符串的类型 */
                uint16_t      gc_info   /* 垃圾回收信息 */
            )
        } v;
        uint32_t type_info;
    } u;
} zend_refcounted_h;
```

可以前往这边文章快速了解引用计数的工作方式: [浅析PHP GC垃圾回收机制及常见利用方式](https://xz.aliyun.com/t/11843#toc-0)



# Fast Destruct 分析

上一篇对`Fast Destruct ` 进行学习后,得到了一个猜想:

> 猜测很有可能是因为反序列化函数`unserialize`的底层代码中的逻辑造成的: 如果序列化字符格式存在错误, 会通过类似于`catch` 的错误捕获对变量进行了释放操作.

因此这篇文章主要是针对猜想进行分析:

首先定位 `unserialize`函数位置, 全局搜索 `PHP_FUNCTION(unserialize)`.

找到位置后,熟悉下正常反序列化字符串以及错误反序列字符串的代码流程.

之后通过不断地对比, 发现正常的反序列化字符串和错误的反序列化字符串会在`Zend/zend_execute_API.c` 的`第44行`出现分歧：

![image-20221122180440585](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221122180440585.png)

去百度了一下,这个函数的大致功能为:

> `zval_ptr_dtor`首先会将它的`refcount`减一，如果减一后`refcount`为0了，便会再调用`zval_dtor`把`tmp->value`给释放掉，然后再调用`efree_rel()`函数把自己`tmp`所指的`zval类型结构体`所占的内存空间给释放掉。
>
> 如果减一后不为0,那`zval_ptr_dtor`便不会释放`tmp->value`和`tmp`1本身，而是通知一下GC垃圾回收器，然后返回.



对比了正常反序列化代码和错误反序列化代码在此处的相关变量 ，发现正常反序列化字符串：

![image-20221124153514618](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221124153514618.png)

错误反序列化字符串：

![image-20221124153748017](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221124153748017.png)

可以看到区别在于正常反序列化字符到此处的 `ref_count=2`, 而错误的反序列化字符串到此处的`ref_count=1`. 

为什么错误序列化字符的引用计数器的回事`1`? 继续往前下断点分析.

在 `ext\standard\var.c` 的 `第1121行`, 在此处已经出现了 `refcount`的差异.

![image-20221127122601202](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221127122601202.png)

![image-20221127122456305](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221127122456305.png)



继续向上跟踪,在 `ext\standard\var.c` 的`第1110行` 发现正常序列化字符串与错误序列化字符串会出现此处的判断语句中进入不同逻辑语句:

错误序列化字符串会进入 `if`逻辑分支:

![image-20221127230740226](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221127230740226.png)

而正常序列化字符串则会进入 `else`逻辑分支:

![image-20221127230613863](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221127230613863.png)

步进`else` 分支, 发现正常序列化字符串的 `refcount` 会在 `第1118行` 加一.

![image-20221127230146683](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221127230146683.png)

跟进`ZVAL_COPY` 函数, 可以看到在 `872`行存在一个自增操作,也就是在这个地方,对`refcount` 进行加1.

![image-20221127231403594](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221127231403594.png)

到目前为止,可以得出结论:

> 如果序列化正确,  refcount=2,  序列化错误, refcount=1



那么接下里就去分析序列化是怎样发生错误的.

# Unserialize 语法分析

关键函数在于 `ext\standard\var.c` 的`第1110行` 的 `php-var_unserialize` 函数, 继续跟进, 到 `ext\standard\var_unserializer.c` 的`第550`行的 `php_var_unsrialize_internal` 函数, 其函数体在 `ext\standard\var_unserializer.c` 的`第572行`,在此函数内, 主要针对传入的序列化字符串进行语法分析,如果语法解析成功返回 `1` , 否则返回 `0`:

![image-20221127231945878](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221127231945878.png)

![image-20221127232205158](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221127232205158.png)



语法分析函数大概过一遍,要求总结如下:

1. 类名正确(包括序列化字符串类名前面的数字), 以确保能够查找以及初始化该类.
2. 破坏类中属性的字符数(如：原来是 `1`, 修改为`11`),影响类属性的解析.
3. 破坏类中属性结构.
4. 将 序列化字符中的对象 `O` 改为`C` 也可以.
5. 破坏类中属性的个数.(没找到,但是确实能实现)



# 总结

这次代码分析还是一次挺大的挑战, 对`C`语言不熟悉, 对数据结构不熟悉,再加之分析之初方法不对,导致绕了很多弯路. 后面不断去了解了相关底层代码的数据结构, 函数作用,以及修改思路不断回溯, 最终找到问题所在的关键代码.

简单总结下吧:

1. PHP 中的内置函数在 `C`中都是以 `PHP_FUNCTION(function_name)`定义的.
2. PHP 中 `zval` 以及 `gc` 相关的数据结构.



# 参考

[浅析PHP GC垃圾回收机制及常见利用方式](https://xz.aliyun.com/t/11843#toc-0)

[PHP 核心开发者博客](https://www.laruence.com/php-internal)