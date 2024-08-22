# 前言

本工具的作用是实现一键包体自动上传及发布到应用市场，目前已接入 Google Play、小米、vivo、华为，接入本工具后就不再需要登录市场的后台手动上传，更加便捷和节省时间。
https://github.com/mikeFei1000/Android-Publisher

# 环境准备

```
brew install jq
python3 -m pip install crypto
python3 -m pip install pycryptodome
python3 -m pip install cryptography
python3 -m pip install requests_toolbelt
python3 -m pip install requests
python3 -m pip install google-api-python-client
python3 -m pip install oauth2client
```

jq 是一个命令行 JSON 处理器

pycryptodome、crypto、cryptography 是 Python 加解密库

requests_toolbelt 是 Python 大文件上传库

requests 是 Python 更便捷的网络库

google-api-python-client Google api 客户端库 for Python

# 接入前服务的申请

-   Vivo 操作指引 https://dev.vivo.com.cn/documentCenter/doc/326

1.  登录vivo开放平台，点击账号-账号管理-api管理，或点击产品-应用分发-开发-API接口进入
1.  点击api管理
1.  点击立即开通，开通成功vivo开放平台给开发者分配 access_key 和 access_secret

  


-   小米操作指引 https://dev.mi.com/distribute/doc/details?pId=1134

1.  登录小米开放平台，进入应用管理
1.  点击自动发布接口
1.  下载公钥、获取私钥

  


-   华为操作指引 https://developer.huawei.com/consumer/cn/doc/development/AppGallery-connect-Guides/agcapi-getstarted-0000001111845114

1.  登录[AppGallery Connect网站](https://developer.huawei.com/consumer/cn/service/josp/agc/index.html)，选择“用户与访问”。选择左侧导航栏的“API密钥 > Connect API”，点击“创建”
1.  在“名称”列输入自定义的客户端名称，“项目”保持默认值“N/A”，选择对应的“角色”，点击“确认”
1.  客户端创建成功后在客户端信息列表中记录“客户端ID”和“密钥”的值

  


-   Google Paly 操作指引 https://developers.google.com/android/management/service-account?hl=zh-cn

1.  登录 Google API 控制台。
1.  打开[“凭据”页面](https://console.developers.google.com/project/_/apiui/credential?hl=zh-cn)。如果系统提示，请选择已启用 Android Management API 的项目。
1.  点击**创建凭据** > **服务帐号密钥**。
1.  从下拉菜单中选择**新的服务帐号**。输入服务帐号的名称。
1.  选择您的首选密钥类型，然后点击**创建**。您的新公钥/私钥对已生成并下载到您的计算机，也是此密钥的唯一副本。您负责安全存储该密钥。
1.  打开 [IAM 页面](https://console.developers.google.com/iam-admin/iam?hl=zh-cn)。如果出现提示，请选择已启用 Android Management API 的项目。
1.  点击**添加**。
1.  将您刚刚创建的服务帐号添加为成员，然后选择 **Android Management User** 角色。
1.  点击**保存**。
1.  （可选，但强烈建议执行此步骤）通过向现有项目成员[授予 Owner 角色](https://cloud.google.com/iam/docs/managing-policies?hl=zh-cn#access_control_via_console)来添加其他项目所有者。

# 准备构建文件并设置参数

![](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/5a8cf1ed5d49445390f7b02fdc96908b~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1166&h=490&s=102657&e=png&b=3c4042)

```
config.json 的结构
{
  "appName": "",
  "packageName": "",
  "appgallery": {
    "appId": "",
    "client_id": "",
    "client_secret": "",
    "releaseType": 1
  },
  "xiaomi": {
    "user_name": "",
    "private_key": ""
  },
  "vivo": {
    "access_key": "",
    "access_secret": ""
  }
}
```

release-note-zh-CN.txt 、release-note-zh-HK.txt、release-note-en-US.txt 对应语言的新版本简介

dev.api.public.cer 小米公钥文件

# 使用介绍

```
. appgallery-publisher.sh $apk_filepath
python3 mi-publisher.py $apk_filepath
python3 vivo-publisher.py $apk_filepath
python3 google-publisher-service-account.py -apk_file $apk_filepath
```

# 配合 CI/CD-Jenkins 工具

![](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/27816dd10f0448bcadb793d47b618cc5~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1514&h=1538&s=176461&e=png&b=ffffff)

# Api 官方文档

> [小米应用自动发布接口](https://dev.mi.com/distribute/doc/details?pId=1134)
>
> [华为更新在架应用详情](https://developer.huawei.com/consumer/cn/doc/development/AppGallery-connect-Guides/agcapi-updateappinfo-0000001158245317)
>
> [vivoAPI接口传包](https://dev.vivo.com.cn/documentCenter/doc/327)
>
> [Google Play Developer API](https://developers.google.com/android-publisher?hl=zh-cn)

# 问题 QA

# [AttributeError: module 'time' has no attribute 'clock' in Python 3.8](https://stackoverflow.com/questions/58569361/attributeerror-module-time-has-no-attribute-clock-in-python-3-8)

```
检查您是否正在使用 PyCrypto，如果是，请将其卸载并安装PyCryptodome，它是 PyCrypto 的一个分支
正如项目问题页面上提到的，PyCrypto 已死
由于这两个库可以共存，因此这也可能是一个问题
pip3 uninstall PyCrypto
pip3 install -U PyCryptodome
```
