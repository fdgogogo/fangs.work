---
layout: post
title: "Docker 1.12 Swarm Mode 初上手体验"
date: "2016-08-04 21:27:56 +0800"
tags: [Docker, Docker Swarm]
toc: true
---

这几天Docker释出了1.12正式版本，除了提供了正式版的Docker Native等一系列功能之外， 比较重要的一个更新就是新增加的[Swarm Mode](https://docs.docker.com/engine/swarm/), 提供了原生的集群支持。我也在第一时间进行了尝试，这里写一篇博文记录一下使用体验。

需要注意的是，虽然名字很接近，但 Swarm Mode 与 [Docker Swarm](https://docs.docker.com/swarm/) 并不是一个东西，并且并不能很好的兼容（无法无缝迁移), 他们的差别主要在于:

- `Docker Swarm` 运行于 Docker Engine 内部的一个 Container 中, 提供与标准 Docker Engine 相同的 API, 因此可以使用支持单机版 Docker 的工具进行操作 (例如 docker-compose), 
- `Swarm Mode` 直接集成于 Docker Engine 内部, 提供了原生的集群支持, 但与单机版 Docker Engine 并不兼容, 使用独立的 `docker service` 命令进行管理, 也无法使用单机版 Docker 的工具及 API

虽然文档中没有正式地提及, 但可以认为 Swarm Mode 是 Docker Swarm 的继承者与替代品, 而 Docker Swarm 应算是已经废弃了.

说起来虽然 Docker 这次显得有些不地道, 原先的 Docker Swarm 发布不过一年多, 还没有达到很稳定的程度, 就被放弃掉了, 一众追随者们应该比较郁闷(比如阿里云容器服务之类), 但是我还是认为这是一个正确的选择,
 原先的 Docker Swarm 过于执着于对单机 Docker 环境的兼容性, 而忽视了单机环境与集群环境本质上的不同(我实际用的时候踩了无数的坑), 及时废弃并为集群环境专门设计一套 API 才是正道.

### 概览

这里翻译并介绍一下主要的功能点, 并结合旧版 swarm 穿插一些我自己的评论

#### 集成于 Docker Engine 内部的集群管理系统

docker 1.12 增加了一个新的命令 `docker swarm` 用于管理集群, 并且由于内部集成了 Discovery 服务, 集群的建立变得异常简单. 基本上, 你只需要 `docker swarm init` + `docker swarm join` 就可以轻松建立一个集群, it just work (虽然目前还有一些小坑, 比如 `--listen-addr` 的问题)

#### 去中心化设计

相对于在部署时就确定节点之间的关系, 新的 Swarm Mode 选择在运行时动态地处理这些关系, 因此 manager 与 worker 的角色可以在运行时互换, 也可以动态地增加.

#### 声明式服务模型

我们可以声明一系列服务, Docker 集群负责将其中的微服务扩展至对应的状态

#### 随意控制集群规模

我们可以通过 `docker service scale` 命令轻松地增加或减少某个服务的 container 数量, 与之前的 docker-compose 命令用起来基本一样, 与单机的 compose 相比, 集群环境下的 scale 无疑要有用得多.

#### 自动状态维护

Swarm 集群会自动地维护整个服务的状态, 比如我们声明了需要10个 worker container , 在其中的一些崩溃后, docker 会创建并尝试重新分配新的 Container, 来保证 worker container 达到预期的数量

#### 跨主机网络

我们可以定义跨 host 的网络, 对于内部的容器来说这是透明的, 就好像在自己的局域网当中一样. 这个特性在 Docker Swarm 模式就已经存在了, 但 Swarm Mode 中新引进的负载均衡机制使得这个网络的用处大大地增加了.

#### 服务发现

Docker 1.12 提供了内置的 Discovery 服务, 这样集群的搭建不需要再依赖外部的 Discovery 服务, 比如 consul 或 etcd

#### 负载均衡

我想这是 Swarm Mode 中新增加的最重要的一个特性, 当我们在容器内使用内部域名访问另外一个容器的时候, 我们不再只是访问到这个服务的第一个容器, 而是访问到一个带负载均衡的虚拟 ip, 这在我们部署集群时尤其有用, 再也不用考虑诸如 n 台对外暴露端口的 nginx 容器如何分散负载到 cgi 容器之类的问题了, 而一些集群服务接入容器环境也变得容易了许多.

除了虚拟 ip (vip) 之外, docker 也提供了 DNS Round-Robin (dnsrr) 的负载均衡模式

#### 默认 TLS 加密

我想这没什么好说的

#### 滚动更新

这是另外一个重要特性, `docker service` 允许你自定义更新的间隔时间, 并依次更新你的容器, `docker service update` 允许你更新包括 image 在内的几乎任何东西, docker 会按照你设置的更新时间依次更新你的容器, 如果发生了错误, 还可以回滚到之前的状态.

### 一些使用感受

上面基本上翻译了一下官方的特性介绍, 下面我也讲一些我自己使用时的感受:

- `mode=replicated|global` 是个特别有用的参数, 默认是 replicated, 意味着这个服务可以随意 scale, docker 会自己安排这些容器运行在哪台机器上, 而 global 则可以让我们声明一个全局的服务, 亦即每台服务器一个容器, 不多, 也不少.

这意味着我们可以将我们的 cgi 容器设为 replicated ,负载能力不够的时候随时 scale , 而对外暴露端口由 global 模式的 nginx 来保证, 这样即使我们增加 worker 节点, nginx 也会自动扩展到新的机器上, 让端口立即可以访问 (并且内部还有负载均衡, 我感觉 haproxy 似乎可以不需要了)

原先的 Docker Swarm 缺乏这个模式, 是最让我不满意的一个地方, 想要保证节点中的每台机器都对外暴露相同的端口这件看起来在集群中相当基础的事情, 原先可以说是相当不容易做到.

- `-v --volume` 参数不见了, 不过不要以为挂载本地文件系统不再可能了, 只是格式变化了, 并且文档中完全没有提及, 还是在 issue 中找到的, 格式如下:

```bash
docker service create --mount type=volume,target=<container file/directory>,source=<host file/directory>,volume-driver=<driver>,volume-opts=<k0>=<v0>,volume-opts=<k1>=<v1>
```

例如挂载本地目录:

```bash
docker service create --mount type=volume,target=/container_data/,source=/host_data/,volume-driver=local
```

这里也能看出来 Docker 在更新上有点不靠谱, 大版本正式版发布, 文档还没有整的很清楚, 更新需要谨慎

同时在现在(16-08-04), 1.12版本还存在不少比较严重的 bug, 比如容器内负载均衡并不是非常可靠, 有时会访问不到容器, 特别是在使用 `docekr service scale` 命令之后, 还有原先一直可用的通过 hostname 解析 container 地址的功能也暂时不可用, 这些已经被列在1.12.1版本的 milestone 中, 等待修复.

- 现在 Swarm Mode 与 docker-compose 并不兼容, 我相信以后应该会兼容, 但现在暂时还不行, 不过大部分 swarm 的语法可以转写为 `docker service create`  的参数, docekr-compose 1.8.0 也提供了一个 `docker-compose bundle` 命令来生成 `dab` 文件, 可用于 `docker deploy` 文件进行服务发布, 但这个命令在 1.12 正式版中并没有提供, `docekr-compose bundle` 命令也还有很多语法不支持, 所以基本上处于还不能用的状态, 服务创建的命令需要自己写。 不过所幸的是我们有 `docker service update` 命令, 在服务创建之后就很少需要再次创建

- 同 Docker Swarm 一样, Swarm Mode 在使用自行编译的镜像时, 必须将镜像推送到 registry 中.
- 每次创建服务时, 每个节点都会到 registry 中检查镜像是否有更新, 哪怕 tag 相同(比如 `latest`), 没有原先 `docker-compose pull` 的困扰, 但如果你的应用没有发布版本, 而是一直使用 `latest` 的话, 使用 `docker service update --image` 时并不会有任何效果, 但有个小技巧, 我们可以在 `docker service update --image someimage` 与 `docker service update --image someimage:latest` 之前切换, 来让服务重新拉取镜像. 
- ``--env-file`` 参数目前没有支持, 需要每个环境变量通过 `-e` 参数传入, 不过这也避免了原先 Docker Swarm 中每台机器同一路径都必须要有 envfile 的麻烦
