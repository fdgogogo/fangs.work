---
layout: post
title: "使用docker-compose构建自建Github-Pages环境"
date: "2016-06-27 13:41:29 +0800"
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

### 然后呢？

到现在为止，好像没有比直接`jekyll build`命令强大多少，只是省去了环境的安装？接下来我们就继续扩展我们的docker环境，加入Nginx及CI系统，使整个部署过程完全自动化，实现github pages一样的效果

