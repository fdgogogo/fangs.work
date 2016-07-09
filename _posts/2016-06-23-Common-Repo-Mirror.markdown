---
layout: post
title: "常用开发工具源国内镜像"
date: "2016-06-23 22:46:42 +0800"
tags: [Python, Docker, Ruby, Node]
category: [程序, 杂项]
toc: true
---

因为一些众所周知的原因，国内访问国外网站一直比较慢，而很多开发中会用到的包管理软件都会访问国外的源，经常慢的抓狂。收集了一些常用的镜像，放在这里备查。

### pip

#### 临时使用

复制命令后在后面加包名或其他参数

```bash
# 清华源， 支持https，速度尚可
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple
# 阿里源， 速度较快（特别是阿里云），不支持https
pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

#### 固化配置

创建或编辑`~/.pip/pip.conf`

[清华源](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/)

```bash
# 命令会覆盖原有pip配置
mkdir -p ~/.pip
echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple" > ~/.pip/pip.conf
```

阿里源

```bash
# 命令会覆盖原有pip配置
mkdir -p ~/.pip
echo "[global]\nindex-url = http://mirrors.aliyun.com/pypi/simple/\n[install]\ntrusted-host = mirrors.aliyun.com" > ~/.pip/pip.conf
```

### pyenv

我用七牛的镜像功能自建了一个mirror
安装时使用

```
export PYTHON_BUILD_MIRROR_URL="http://pyenv.qiniudn.com/pythons/"
```

再 `pyenv install VERSION` 即可，不过现在官方似乎不再提供大多数的预编译包，多数版本需要下载源代码安装，并且源代码的地址是写死的，暂时无法加速，只能手动修改`python-build`的相关文件实现

安装前可以先打开 [http://pyenv.qiniudn.com/pythons/](http://pyenv.qiniudn.com/pythons/) 确认要安装的版本是否已有编译好的包


### Docker

#### Docker Engine

从官方安装Docker Engine速度相当感人，这里可以使用[DaoCloud](http://daocloud.io)提供的安装镜像:

```
curl -sSL https://get.daocloud.io/docker | sh
```

#### Docker Registry

安装好Docker后， pull镜像依然很慢，daocloud的加速服务个人使用起来感觉不是非常快，我还是用阿里云最近推出的[开发者平台](https://dev.aliyun.com/search.html)的镜像功能

进入[开发者平台](https://dev.aliyun.com/search.html)

点左侧加速器, 找到自己专属的加速器地址，该页也有安装说明，一般是编辑`/etc/default/docker`文件， 在`DOCKER_OPTS`里面加入`--registry-mirror=https://XXXXXXXXX.mirror.aliyuncs.com`

`XXXXXXXXX`是你自己的镜像地址

#### Docker Machine

如果使用[docker-machine](https://docs.docker.com/machine/)创建机器的话，可以在安装时同时配置好registry镜像

```bash
docker-machine create \
--driver generic \
--generic-ip-address=MACHINE_IP \
--engine-install-url=https://get.daocloud.io/docker \
--engine-registry-mirror="https://XXXXXXXXX.mirror.aliyuncs.com" \
MACHINE_NAME
```

### NPM

因为npm自身的坑爹原因，哪怕是使用镜像，安装仍然算不上快，还要加上一些hack， 比如关闭进度条等， 因此建议直接使用阿里提供的cnpm进行安装

安装[cnpm](https://npm.taobao.org/)

#### 临时使用

```bash
npm install --registry=https://registry.npm.taobao.org
```

#### 固化配置

```bash
npm install -g cnpm --registry=https://registry.npm.taobao.org
```

之后使用 

```bash
cnpm install
```

进行安装

### Ruby Gem

使用[淘宝源](https://ruby.taobao.org/)

```bash
gem sources --add https://ruby.taobao.org/ --remove https://rubygems.org/
# 如果使用bundle
bundle config mirror.https://rubygems.org https://ruby.taobao.org
```
