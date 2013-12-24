**lazyjson** is a Python 3 module providing lazy JSON I/O.

This is `lazyjson` version 0.1.0 ([semver](http://semver.org/)).

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
