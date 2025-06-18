# FakeWechatVersionCopy

复制的 [FakeWechatVersion](https://github.com/ThinkerWen/FakeWechatVersion/)项目 
只是做了简单的修改用来增加易用性，如果安装了wx就会自动去注册表获取安装路径和版本号，
剩下的只需要在config.json中设置版本号，双击运行即可
在此十分感谢ThinkerWen

## 用法：

### 1. 源码运行:
```shell
git clone https://github.com/open8eye/FakeWechatVersionCopy.git
cd FakeWechatVersion
pip install -r requirements.txt
# c为当前微信版本，t为目标微信版本
python fake_wechat_version.py c=3.9.6.33 t=3.9.12.51
# 如果 安装了微信 可以直接运行
python fake_wechat_version.py 
```

### 2. 打包版运行
在 dist/[fake_wechat_version.exe](dist/fake_wechat_version.exe)目录里下载fake_wechat_version.exe，在根目录里下载[config.json](config.json)
将两个文件放在同一文件夹下，双击fake_wechat_version.exe运行

### 3. 配置
config.json 文件里的version表示替换后的版本号
### 4. 感谢
[FakeWechatVersion](https://github.com/ThinkerWen/FakeWechatVersion/)
