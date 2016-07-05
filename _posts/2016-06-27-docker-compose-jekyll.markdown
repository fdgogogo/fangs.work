---
layout: post
title: "使用docker-compose构建自建Github-Pages环境"
date: "2016-06-27 13:41:29 +0800"
tags: [docker, docker-compose, jekyll]
toc: true
---

开新博客的时候，尝试了一下github-pages, 方便是很方便，但是还是有几个地方不能满足，比如插件受限，不支持自定义域名https等，正好手上一台服务器闲着也是闲着，决定自建一个，也作学习。

### Jekyll

Jekyll在Dockerhub有提供官方镜像，因此搭建环境非常简单方便。一开始我还不打算添加自定义插件，因此先从尽可能接近github环境的 `jekyll/builder:pages` 镜像开始

首先创建或编辑我们的docker-compose.yml文件, 加入docker镜像

```yaml
jekyll:
  image: jekyll/builder:pages
  volumes:
    - .:/srv/jekyll
  command: jekyll build
```

然后使用 `docker-compose up` 命令即可编译静态文件，生成后的文件在当前目录的 `_site/` 底下，和直接使用 `jekyll build` 效果一样

### Nginx

然后我们还需要配置Nginx来serve我们的静态文件, 这一步比较简单:

在docker-compose.yml中添加nginx配置:

如果不需要使用https, 则只需要简单挂载一下镜像即可:

```yaml
nginx:
  image: nginx
  volumes:
    - ./_site:/usr/share/nginx/fangs.work:ro
  ports:
    - 80:80
```

然后直接`docker-compose up -d`即可在80端口serve你的jekyll站点了

如果需要更进阶一点的设置，比如 https, vhost 等， 可以建立自己的配置文件和证书路径，然后将其挂载到容器内, 例如:

```yaml
nginx:
  image: nginx
  volumes:
    - ./_site:/usr/share/nginx/fangs.work:ro
    - ./_docker/nginx/certs:/certs:ro # 证书文件， 不在repo中
    - ./_docker/nginx/conf.d:/etc/nginx/conf.d:ro
  ports:
    - 80:80
    - 443:443
```

