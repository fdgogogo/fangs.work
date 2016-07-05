---
layout: post
title: "SQLAlchemy中的继承"
date: "2016-07-02 23:06:50 +0800"
tags: [python, sqlalchemy, database]
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
        'polymorphic_on': user_type
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
>>> user = User.query.get(user.id)
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

### 联表继承

### 实体继承

### 参考

1. [Mapping Class Inheritance Hierarchies](http://docs.sqlalchemy.org/en/latest/orm/inheritance.html)
2. [Add child classes in SQLAlchemy session using parent constructor](http://stackoverflow.com/questions/30518484/add-child-classes-in-sqlalchemy-session-using-parent-constructor)
