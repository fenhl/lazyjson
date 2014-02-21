**lazyjson** is a module for Python 3.2 or higher that provides lazy JSON I/O.

This is `lazyjson` version 1.0.2 ([semver](http://semver.org/)).

The versioned API is simple: when instantiating a `File`, the single argument must be a valid single argument to the built-in function [`open`](http://docs.python.org/3/library/functions.html#open). The object can then be used like a dict object. All data is lazily read from, and immediately written to the file using `open` on each call.

Usage
=====

First you need a lazyjson object, which represents a JSON formatted file on the file system:

```python
>>> import lazyjson
>>> f = lazyjson.File('example-file.json')
```

You can then use the `File` object like a regular `dict`:

```python
>>> print(f)
{'someKey': ['a', 'b', 'c']}
```

Okay, so far so good. But why not just use `json.load`? Well, this is where the “lazy” part comes in. Let's say some other program modifies our `example-file.json`. Let's do the same call again, still on the same `File` object:

```python
>>> print(f['someKey'])
['a', 'b', 'c', 'd']
```

The result has magically changed, because the file is actually read each time you get data from it. If you have write permission, you can also modify the file simply by changing the values from the `File` object:

```python
>>> f['someKey'] += ['e', 'f']
>>> with open('example-file.json') as text_file:
...     print(text_file.read())
{
    "someKey": [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f"
    ]
}
```
