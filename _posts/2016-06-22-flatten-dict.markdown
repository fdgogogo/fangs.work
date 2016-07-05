---
layout: post
title: "Python摊平与反向组合字典"
date: "2016-06-22 00:42:46 +0800"
tags: [python]

---

我们经常会处理或者构造一些较为复杂的多层嵌套字典数据，这虽然不难，但经常是个比较麻烦的事情，比如我们需要一个这样的数据

```yaml
types:
  typeA:
    items:
      - item1
      - item2
  typeB:
    items:
      - item1
  typeN:
    # ...
```

最初级的写法：

```python
data = {'types': {}}
def append(_type, item):
    global data
    if _type not in data['types']:
        data['types'][_type] = []
    data['types'].append(item)
```

简化这个写法，我们可以使用 `dict.setdefault` 方法:

```python
data = {'types': {}}
def append(_type, item):
    global data
    data['types'].setdefault(_type, []).append(item)
```

但是在更复杂的场景下，要不断嵌套`setdefault`方法，还是太麻烦了一些, 而且一些动态的场景下，我们需要能够通过生成的字符串来对程序行为做一些控制，这时我们可以选择把字典摊平再组合（代码见后文）:

```python
>>> example = {'a': 1, 'b': {}, 'c': {'d': [], 'e': {'f': 0, 'h': u'xxx', 'i': {'j'}, 'k': object()}}}
>>> flatten_dict(example) # doctest: +ELLIPSIS
{'a': 1, 'b': {}, 'c.d': [], 'c.e.k': <object object at ...>, 'c.e.i': set(['j']), 'c.e.h': u'xxx', 'c.e.f': 0}
```

这样如果我们需要对层级对象进行一些控制就会变得更加方便:

```python
def set_data(obj, user, data):
    flatted_data = flatten_dict(data)
    for key, value in tuple(flatted_data.items()):
        if key in get_readonly_fields(user):
            del flatted_data[key]
    obj.data = nestify_dict(flatted_data)

def get_readonly_fields(user):
    if user.is_superuser:
        return []
    return ['c.d', 'c.e.h']
```

我们也可以通过这种方式方便地构造上面例子中的数据(当然这个例子可能不够复杂）:

```python
data = {}
def append(key_as_string, item):
    global data
    flatted_data = flatten_dict(data)
    flatted_data.setdefault('types.' + key_as_string, []).append(item)
    data = nestify_dict(flatted_data)

```

示例:

```
In [4]: append('a.b.c.d', 'itemA')

In [5]: data
Out[5]: {'types': {'a': {'b': {'c': {'d': ['itemA']}}}}}

In [6]: data
Out[6]: {'types': {'a': {'b': {'c': {'d': ['itemA']}}}}}

In [7]: append('a.b.c.d', 'itemA')

In [8]: data
Out[8]: {'types': {'a': {'b': {'c': {'d': ['itemA', 'itemA']}}}}}

In [9]: append('a.b.c.d', 'itemA')

In [10]: data
Out[10]: {'types': {'a': {'b': {'c': {'d': ['itemA', 'itemA', 'itemA']}}}}}

In [11]: append('a.b.c.x', 'itemA')

In [12]: data
Out[12]:
{'types': {'a': {'b': {'c': {'d': ['itemA', 'itemA', 'itemA'],
     'x': ['itemA']}}}}}
```

### 代码

[gist](https://gist.github.com/fdgogogo/b04340b649b055243a5c)

```python

""" Flatten dict and vice versa
    Authored by: Fang Jiaan (fduodev@gmail.com)
    Example:
    >>> example = {'a': 1, 'b': {}, 'c': {'d': [], 'e': {'f': 0, 'h': u'xxx', 'i': {'j'}, 'k': object()}}}
    >>> flatten_dict(example) # doctest: +ELLIPSIS
    {'a': 1, 'b': {}, 'c.d': [], 'c.e.k': <object object at ...>, 'c.e.i': set(['j']), 'c.e.h': u'xxx', 'c.e.f': 0}
    >>> assert nestify_dict(flatten_dict(example)) == example
    >>> assert 'c.e.h' in flatten_dict(example)
    >>> assert flatten_dict(example)['c.e.h'] == example['c']['e']['h']
    >>> example2 = {'x.y': 1}
    >>> flatten_dict(example2) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ValueError: Separator . already in key, this may lead unexpected behaviour, choose another.
"""
import collections


def flatten_dict(d, parent_key='', sep='.', quiet=False):
    items = []
    for k, v in d.items():

        if not quiet and sep in k:
            raise ValueError('Separator "%(sep)s" already in key, '
                             'this may lead unexpected behaviour, '
                             'choose another.' % dict(sep=sep))

        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
            if not v:  # empty dict
                items.append((new_key, v))
        else:
            items.append((new_key, v))
    return dict(items)


def nestify_dict(d, sep='.'):
    ret = {}
    for k, v in d.items():
        if sep in k:
            keys = k.split(sep)
            target = ret

            while len(keys) > 1:
                current_key = keys.pop(0)
                target = target.setdefault(current_key, {})
            else:
                assert len(keys) == 1
                target[keys[0]] = v
        else:
            ret[k] = v
    return ret
```
