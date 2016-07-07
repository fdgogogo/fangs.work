---
layout: post
title: "SQLAlchemy中的继承"
date: "2016-07-02 23:06:50 +0800"
tags: [python, sqlalchemy, database, flask]
toc: true
---

SQLAlchemy是Python下常用的ORM之一，虽然相对于Django ORM，Peewee等其他ORM而言，上手难度相对较高，但是它提供了相当丰富且灵活的高级特性，这里介绍一下模型继承方面的内容

> 本文代码以`Flask-SQLAlchemy`为例进行说明，原生SQLAlchemy差异不大，主要有：    
>   
> - `db.Model`约等于`sqlalchemy.ext.declarative.declarative_base`   
> - `Model.query`约等于`db.session.query(Model)`    
{: .note}

### 单表继承

最简单的联表形式就是单表继承, 在这种继承关系下，无论继承多少子类，数据库层面始终只有一张表，使用一个`polymorphic_identity`字段来进行区分。
显而易见，这是查询效率最高的一种继承方式。但我们无法灵活地为每个子类添加自己专有的字段。适用于各子类数据结构相同，但业务逻辑不同的场合。

比如我们有一张用户表，普通用户需要进行权限检查，但管理员用户具有一切权限, 我们当然可以用`if`进行条件判断，但在条件复杂的时候这会严重降低代码的可读性和可维护性，我们可以用更面向对象的方式来解决这个问题，比如:

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(10))

    __mapper_args__ = {
        'polymorphic_identity': 'normal',
        'polymorphic_on': user_type
    }

    def has_permission(self, permission):
        return some_permission_check_logic()


class AdminUser(User):
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

    def has_permission(self, permission):
        return True
```

这样当我们进行数据库查询的时候，ORM会自动根据`polymorphic_identity`使用不同的类映射对象，比如:

```python
>>> User.query.all()
[<User: xxx@xxx.com>, <User: xxx2@xxx.com>, <AdminUser: xxx3@xxx.com>]
```

这样还带来一个额外的好处，当我们直接创建子类对象的时候，相应的`polymorphic_identity`会自动帮我们填好:

```python
>>> admin_user = AdminUser()
>>> print(admin_user.user_type)
admin
```

#### 自动初始化子类对象

那既然创建子类会自动填入`polymorphic_identity`，那如果我对父类传入相应的值，是否能自动创建子类对象呢？

很遗憾，答案是否定的:

```python
>>> user = User(user_type='admin', email='xxx@xxx.com') 
>>> print(user)
<User: xxx@xxx.com>
>>> # 但是当我们重新从数据库取出对象的时候，可以正确的使用子类
>>> db.session.add(user)
>>> db.session.commit()
>>> user_id = user.id
>>> del user # 这里需要删除已经生成的对象, 否则sqlalchemy会自动复用已经生成的对象
>>> user = User.query.get(user_id)
>>> print(user)
<AdminUser: xxx@xxx.com>
```

如果要实现这个效果，我们可以使用元类(见参考#2)，但在这里个人不建议使用这种黑魔法，因为一是修改SQLAlchemy中已经被深度定制化的元类可能带来一些神奇的问题，二是你初始化一个类，结果初始化出来另一个类的实例，这本身也是有点奇葩的，因此个人还是使用更直接一点的classmethod的方式实现:

```python
class User(db.Model):
    # ...

    @classmethod
    def init_for(cls, user_type, **kwargs):
        """根据user_type初始化不同子类的实例"""
        children_classes = {
            x.polymorphic_identity: x.class_
            for x in cls.__mapper__.self_and_descendants
            }
        return children_classes[user_type](**kwargs)
```

注意: 单表继承不应为自类定义 `__tablename__`

### 联表继承

很多时候我们需要处理更灵活一点的情况, 子类从父类继承一些属性, 但也需要定义部分自己的属性, 联表继承可以帮我们处理这种状况, 但相应的会带来一些性能开销

顾名思义, 联表继承在hit数据库时会进行一个`JOIN`查询, 数据结构上的定义实际上是**子类的主键作为外键, 一对一关联到父类表的主键**, 子类独有的数据单独存放在一张表上

看代码：

```python
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(10))

    __mapper_args__ = {
        'polymorphic_identity': 'normal',
        'polymorphic_on': user_type
    }

class WechatUser(User):
    __tablename__ = 'user_wechat'

    # 定义一个到父类的外键
    id = db.Column(db.Integer, db.ForeignKey('user.id', primary_key=True))
    open_id = db.Column(db.String(40))
    __mapper_args__ = {
        'polymorphic_identity': 'wechat',
    }
```

#### 查询行为

我们来看下查询SQL

```python
>>> print(User.query)
```

```sql
SELECT "user".id AS user_id, "user".user_type AS user_user_type
FROM "user"
```

```python
>>> print(WechatUser.query)
```

```sql
SELECT user_wechat.id AS user_wechat_id, "user".id AS user_id, "user".user_type AS user_user_type, user_wechat.open_id AS user_wechat_open_id
FROM "user" JOIN user_wechat ON "user".id = user_wechat.id
```

可以看到，只查询父类的时候，不会查询子类的表，反之则会拼出一个`JOIN`查询, 且默认为 `INNER JOIN`, 亦即只查询子类的时候， 是不会列出父类的相关数据的。

```
>>> db.session.add(WechatUser())
>>> db.session.add(User())
>>> db.session.commit()
>>> 
>>> print(User.query.all())
>>> print(WechatUser.query.all())
[<__main__.WechatUser object at 0x1016a3e10>, <__main__.User object at 0x1016a3ed0>]
[<__main__.WechatUser object at 0x10170b510>]
```

#### 使用with_polymorphic对查询进行一些控制

在默认情况下，如果是从父类查出一个子类对象，在获取子类属性的时候会额外发起一次查询， 相当于我们正常定义的`relationship`中`lazy=True`时的行为， 例如：

代码：(测试数据中User表的第一个对象为WechatUser)

```python
user = User.query.first()
print(user.open_id)
```

查询：

```sql
SELECT user.id AS user_id, user.user_type AS user_user_type
FROM user
 LIMIT 1 OFFSET 0;
SELECT user_wechat.open_id AS user_wechat_open_id;
```

当我们获取子类属性次数较少的时候，这样的查询是完全可以接受的，但是当我们预计会频繁调用子类属性的时候，这么做会带来大量的查询，这时候将所有表`JOIN`进来会是更好的选择

幸运的是，SQLAlchemy同样提供了这种支持:

```python
>>> mixed = db.with_polymorphic(User, [User, WechatUser])
>>> # 也可以写作 mixed = db.with_polymorphic(User, '*') join所有的子表
>>> query = db.session.query(mixed)
>>> print(query)
SELECT "user".id AS user_id, "user".user_type AS user_user_type, user_wechat.id AS user_wechat_id, user_wechat.open_id AS user_wechat_open_id
FROM "user" LEFT OUTER JOIN user_wechat ON "user".id = user_wechat.id
>>> query.all()
[<__main__.WechatUser object at 0x1016a3e10>, <__main__.User object at 0x1016a3ed0>]
```

`with_polymorphic` 同样提供了对过滤的支持, 

```python
>>> print(db.session.query(mixed).filter(mixed.WechatUser.open_id.is_(None)))
SELECT "user".id AS user_id, "user".user_type AS user_user_type, user_wechat.id AS user_wechat_id, user_wechat.open_id AS user_wechat_open_id
FROM "user" LEFT OUTER JOIN user_wechat ON "user".id = user_wechat.id
WHERE user_wechat.open_id IS NULL
```

文档中还提供了一些更精细化的控制查询的手段，比如 `of_type`, 自定义的 `Join`, 还有 `.options()` 与 `joinedload` 策略, 本文在此暂不展开, 有需要请参考文档

### 实体继承

SQLAlchemy还提供了一种继承方法，称为`concrete` 继承, 姑且翻译为实体继承

在这种继承关系中，父类及其每个子类都具有一张完整的表, 表与表之间在数据库层面可以没有任何关系, 甚至我们在python中每个子类都必须**完整地定义每个字段，这些字段并不会从父类继承**

因为每个子类都有一张完全独立的表, 因此并不像前两种继承关系一样，需要一个`polymorphic_identity`来区分每个子类, 也避免了JOIN和遇到查询字段时需要额外产生一个请求的问题

但是代价就是，因为每个类都是一张独立的表，因此当我们想要从父类查询子类的时候，就必须`UNION`所有的表，所以子类不宜过多，否则性能开销是很恐怖的

(所以说实话，个人并不是非常理解这种继承关系存在的意义。)

类定义如下:

```python
from sqlalchemy.ext.declarative import ConcreteBase

class User(ConcreteBase, db.Model):  # 注意: 此处应继承ConcreteBase
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

class WechatUser(User):
    __tablename__ = 'user_wechat'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))  # 注意: 子类必须重新定义字段
    open_id = db.Column(db.String(40))

    __mapper_args__ = {
        'concrete': True
    }
```

查询:

```python
print(User.query)
```

```sql
SELECT pjoin.id AS pjoin_id, pjoin.name AS pjoin_name, pjoin.type AS pjoin_type, pjoin.open_id AS pjoin_open_id
FROM (SELECT "user".id AS id, "user".name AS name, CAST(NULL AS VARCHAR(40)) AS open_id, 'normal' AS type
FROM "user" UNION ALL SELECT user_wechat.id AS id, user_wechat.name AS name, user_wechat.open_id AS open_id, 'wechat' AS type
FROM user_wechat) AS pjoin
```

```python
print(WechatUser.query)
```

```sql
SELECT pjoin.id AS pjoin_id, pjoin.name AS pjoin_name, pjoin.open_id AS pjoin_open_id, pjoin.type AS pjoin_type
FROM (SELECT user_wechat.id AS id, user_wechat.name AS name, user_wechat.open_id AS open_id, 'wechat' AS type
FROM user_wechat) AS pjoin
```

可以看到，这里的查询动用了 `UNION` `CAST`, 形成了比较复杂的查询， 而且随着子类的增多，查询上的复杂性会快速增加，个人没有在生产环境中用过这种继承类型（不敢， 而且感觉没有必要）

如果谁有这种继承关系适用的场合希望能够指出，一起学习。

### 代码

本文相关代码可参考 [gist](https://gist.github.com/fdgogogo/65666e58e2e860619c640b7215c4ccd9)

### 参考

1. [Mapping Class Inheritance Hierarchies](http://docs.sqlalchemy.org/en/latest/orm/inheritance.html)
2. [Add child classes in SQLAlchemy session using parent constructor](http://stackoverflow.com/questions/30518484/add-child-classes-in-sqlalchemy-session-using-parent-constructor)
