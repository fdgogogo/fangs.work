---
layout: post
title: "SQLAlchemy 中的混合属性 hybrid_property 与混合方法 hybird_method"
date: "2016-07-06 13:49:35 +0800"
tags: [sqlalchemy, python, flask, database]
toc: true
---

SQLAlchemy 在其 `sqlalchemy.ext` 库中提供了许多方面的ORM功能扩展，今天来介绍一下其中非常强大的 `Hybird Attributes` 特性。

> 本文代码以`Flask-SQLAlchemy`为例进行说明，原生SQLAlchemy差异不大，主要有：    
>   
> - `db.Model`约等于`sqlalchemy.ext.declarative.declarative_base`   
> - `Model.query`约等于`db.session.query(Model)`    
{: .note}

### `hybrid_property`

`@property` 装饰器是 python 中非常实用的一颗语法糖，可以有效地对外隐藏类内部的逻辑，提高代码的美观性。比如我们经常定义这样的类:

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.SmallInteger(), default=1)
    
    @property
    def disabled(self):
        return self.status == 0
```

这样当我们访问 `User().disabled` 的时候就就可以不用去关心对应`disabled`的值是多少。

但是当我们需要查询数据库的时候，依然需要知道对应的值来进行过滤，于是SQLAlchemy提供了 `hybird_property` 装饰器来解决这个问题。

我们只需要简单地把上面的代码改成这样:

```python
from sqlalchemy.ext.hybrid import hybrid_property

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.SmallInteger(), default=1)
    
    @hybrid_property
    def disabled(self):
        return self.status == 0
```

之后我们就可以使用非常简洁的语法来进行查询了， 比如这样:

```python
disabled_users = User.query.filter(User.disabled).all()
```

这其中的原理就是，在类上的 `hybrid_property` 将返回一个 `sqlalchemy.sql.elements.BinaryExpression`, 也就是一个SQL表达式, 和直接使用

```python
disabled_users = User.query.filter(User.status == 0).all()
```

是等价的，但无疑更美观也更容易维护。这也是SQLAlchemy使用”覆盖python标准运算符"的实现方式，带来的额外好处之一，Django ORM 的 `FIELD__OPERATOR=VALUE` 语法虽然初上手更简单， 但是也失去了 SQLAlchemy 里的这种面向对象特性。

### `hybrid_method`

`hybrid_property` 已经非常强大了，但SQLAlchemy中还有更为黑魔法的`hybrid_method`这个么玩意儿，就是说，你的方法同样也可以用在查询当中。

比如我们定义一个这样的函数:

```python
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

USER_STATUS = (
    (0, "disabled"),
    (1, "active")
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.SmallInteger(), default=1)

    @hybrid_property
    def disabled(self):
        return self.status == 0

    @hybrid_method
    def is_(self, status):
        return self.status == dict((y, x) for x, y in USER_STATUS)[status]
```

这里我们实现了一个最简单的 `hybrid_method` , 实际作用与上面例子中的 `hybrid_property` 相同， 只是接受一个字符串作为输入。

这个方法同样也可以同时用在查询与实例上:

```python
>>> user = query.first()
>>> print(user.is_("disabled"))
True
>>> print(User.query.filter(User.is_("disabled")).all())
[<__main__.User object at 0x10dd0f610>]
```

### 限制

前面介绍了混合属性的两种最简单的用法，但是在实际应用的时候， 这两个方法其实是比较受限的（我们当然不能指望我们在一个`hybird_method`里写上一百行代码的复杂逻辑，然后sqlalchemy就能自动把python逻辑都翻译成SQL）

其实一些读者可能已经发现了，混合属性其实没有什么特别神秘的地方，就是定义了一个同时是 classmethod 与 instancemethod 的方法而已。

在SQLAlchemy里，`Model`(`Mapper`) 类上的类属性代表的是一个字段, 而类的实例的一个属性，是这个字段对应的值。

这也就意味着， 我们的混合属性中调用的 `self` 在查询的时候就相当于 `cls`, 所以我们调用的任何一个`self`的属性及其方法，在`cls`也必须同时存在。

比如我们不能在混合属性中使用这样的写法:

```python
"peter" in self.name          # 不合法, User.name 字段不能使用 in 进行比较， 应该使用 User.name.contains()
self.name.contains("peter")   # 不合法, 实例的 name 字段为 unicode 值，没有 contains 方法
self.name.startswith("peter") # 合法, unicode 与 InstrumentedAttribute 都有 startswith 方法
```

总的来说， 同时在 `InstrumentedAttribute` 与其对应的 `python_type` 都实现的方法，一般就是那些内置方法， 比如

- `__eq__`: `self.name == "peter"` 合法
- `__gt__`: `self.id > 5` 合法

另外，位操作符(`<<`, `>>`, `&`, `|`, `~`, `^`) 也可以安全地使用，一些逻辑上判断可以处理成位操作来解决

### 突破限制

上面可以看到，如果混合属性只到此为止，还是不够灵活，实际上能用到的场合并不多，因此SQLAlchemy中也提供了一种机制， 允许用户分开定义python上的逻辑与SQL语句的生成逻辑，我们来稍微拓展一下刚才的例子:

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    @hybrid_property
    def called_jack(self):
        return "Jack" in self.name

    @called_jack.expression
    def called_jack(cls):
        return cls.name.contains("Jack")
```

这样我们就可以突破上面提到的限制了, 而且我们可以根据实际情况，把查询中使用的函数定义为数据库函数，提高查询效率

### 一点Bonus

`hybrid_property` 同样可以定义setter噢, 语法同一般的setter相同，直接搬文档上的例子:

```python
class Interval(object):
    # ...

    @hybrid_property
    def length(self):
        return self.end - self.start

    @length.setter
    def length(self, value):
        self.end = self.start + value
```

### 一点想法

说到这里，大概只介绍了混合属性一半不到的内容，后面一半是更高级的用法，比如关系的处理，自定义Comparator之类，这里我就先不展开，以后有需要再另写文章介绍。不过我的想法是，混合属性模块总体上而言是一颗语法糖，使得代码逻辑更加清晰，也更OOP，一定程度上也能起到减少代码量的效果，适合面向对象强迫症患者（比如我），不过我认为这颗语法糖也不应该被滥用，因为其自身的限制，对于过于复杂的逻辑，可能反而增加代码量并降低可读性，因此用起来还是要适度。

### 参考

- [Hybrid Attributes](http://docs.sqlalchemy.org/en/latest/orm/extensions/hybrid.html)
