---
layout: post
title: 使用docker-compose编译静态文件
---

许多项目部署的时候需要执行许多工具命令，比如通过`gulp`/`grunt`压缩静态文件，还有 `compass` 编译之类，
这些工具在Docker部署的时候可能会遇到一些麻烦，因为通常情况下单个image只有一种服务。

有些人会使用一些集成的image，也有人的人会选择 `apt-get update && apt-get install` 相关的环境，但这样要写比较复杂的Dockerfile，build时间会大幅延长，也会把单个image弄的很臃肿，不怎么docker。

我们可以使用 `docker-compose` 的 `volumes_from` 参数来简化这一过程：

> *volumes_from*
> Mount all of the volumes from another service or container, optionally specifying read-only access(ro) or read-write(rw).

## 环境

我们的示例环境大概长这样：

- `python` (主项目)
- `node` (`npm`, `bower`, `grunt`)
- `ruby` (`compass`)

## 编译文件
##＃ 结构

```
├── Dockerfile
├── DockerfileNode
├── DockerfileRuby
├── requirements.txt
├── bower.json
├── package.json
├── config.rb
├── static
│   ├── src
│   ├── dist
│   ├── ...
├── app
│   ├── ...
```

### Dockerfile (python)
python正常编译，不添加node及ruby环境
``` Dockerfile
FROM python
ADD . code/
RUN pip install -r requirements.txt

# 暴露4000端口给其他container
EXPOSE 4000

CMD gunicorn --chdir /code -w 4 -b 0.0.0.0:4000 apps:app
```
### Dockerfile (node)
```
FROM node

ADD . /code
WORKDIR /code

RUN npm install -g bower grunt-cli
RUN bower install --allow-root

RUN npm install

# 暴露 /code 目录给其他container， 要使用volumes_from必须加上这个命令
VOLUME /code
CMD grunt
```
这里使用node image安装node相关环境， 并将code目录标记为volume

### Dockerfile (ruby)

```
FROM ruby
ADD ./config.rb /config.rb
RUN gem install compass
CMD compass compile
```
这里使用ruby image安装compass环境

### docker-compose.yml

``` yaml

app:
  build: .

node:
  build: .
  dockerfile: ./DockerfileNode

compass:
  build: .
  dockerfile: ./DockerfileRuby
  # 这里从node container中挂出 code 目录, 进行编译
  volumes_from:
    - node

nginx:
  image: nginx
  volumes:
    - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
  links:
    - app
  ports:
    - 80:80
  # app(python) container不再挂载静态文件，静态文件目录直接挂给nginx来serve
  volumes_from:
    - node
```

这个compose定义了4个服务:

- app
  - 主服务
- node
  - 包含 bower_components
  - 包含 node_modules
  - 在运行时进行grunt编译， 完成后container自动停止
  - container内的`/code`目录暴露给其他container挂载
- ruby
  - 包含 `compass` 工具
  - 从 `node` container 挂入 `/code` 目录， 运行时进行相关编译
- nginx
  - 从 `node` container 挂入 `/code` 目录, 该目录文件已经过 `grunt` 及 `compass` 编译， 由nginx直接serve

大致就是这样的一个流程，在这里编译命令是作为CMD写在Dockerfile里面的，这样才能在container运行时进行编译，对于 `compass` 镜像来说这是必须的, 但对于node镜像而言也可以在Dockerfile里面写成RUN，根据具体需要决定。
