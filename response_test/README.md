# Response_test 目录文件说明
## 前期准备

先把apifox中的接口测试结果放进域名提取工具(可以去找在线的网站-->https://uutool.cn/不错)中，再写入目录下的url.txt

## 主要文件

### 1. ip2domain_test.py

功能: IP 和域名解析测试工具

读取 URL 列表进行扫描

异步并发处理请求

实时保存扫描结果到 res2.json

支持断点续传（保留之前的扫描结果）

#### 使用方法:

```
python ip2domain_test.py
```

#### 需要准备:

url.txt: 包含要扫描的 URL 列表

安装依赖: aiohttp, beautifulsoup4, lxml

```json
//扫描结果示例
"hzlqgroup.com\n": {
    "status": 200,
    "title": "杭州市路桥集团股份有限公司",
    "content": "杭州市路桥集团股份有限公司 首页 集团概况 企业介绍 组织架构 发展战略 大事历程 集团荣誉 新闻中心 集团要闻 动态 公告 产",
    "url": "http://hzlqgroup.com\n"
  },
  "www.600576.com\n": {
    "status": 200,
    "title": "首页-浙江祥源文旅股份有限公司",
    "content": "首页-浙江祥源文旅股份有限公司 目的地度假 动漫影视 文创消费 数字科技 OA 关于我们 公司简介 董高风采 企业文化 发展历程",
    "url": "http://www.600576.com\n"
  },
  "wsn.lierda.com\n": {
    "status": 200,
    "title": "首页- 利尔达科技集团股份有限公司 - 利尔达提供整套LoRaWAN系统解决方案",
    "content": "首页- 利尔达科技集团股份有限公司 - 利尔达提供整套LoRaWAN系统解决方案 首页 公司介绍 产品 5G模组 NB模组 Ca",
    "url": "http://wsn.lierda.com\n"
  },
```

### 2. web_snapshot.py

功能: 网页截图工具 （示例可见img目录下）

批量对 URL 进行网页截图

支持异步并发（默认 10 个并发）

自动调整截图尺寸

定期重启浏览器避免内存泄漏

#### 使用方法:

```
python web_snapshot.py
```

#### 需要准备:

url.txt: 包含要截图的 URL 列表

img/ 目录: 存放截图结果

安装依赖: pyppeteer

## 输入文件

### url.txt

每行一个 URL

支持 http/https URL

如果没有协议前缀，会自动添加 http://

## 输出文件

### res2.json

IP/域名扫描结果

JSON 格式，包含状态码、标题、内容等信息

累积保存所有扫描结果

### img/screenshot_[索引号].png

网页截图结果

按 URL 顺序编号

全页面截图

分辨率: 1920px 宽度，高度自适应









