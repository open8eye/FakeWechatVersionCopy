# FakeWechatVersion

虚拟windows微信版本，解决微信弹窗 "当前客户端版本过低,请前往应用商店升级到最新版本客户端后再登录"

## 用法：

### 1. 源码运行:
```shell
git clone https://github.com/ThinkerWen/FakeWechatVersion.git
cd FakeWechatVersion
python -m pip install pymem
# c为当前微信版本，t为目标微信版本
python fake_wechat_version.py c=3.9.6.33 t=3.9.12.51
```

### 2. 编译版运行
再 [Release](https://github.com/ThinkerWen/FakeWechatVersion/releases) 页面下载最新版fake_wechat.exe，执行：
```shell
fake_wechat.exe c=3.9.6.33 t=3.9.12.51
```