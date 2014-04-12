**lazyjson** is a module for Python 3.2 or higher that provides lazy JSON I/O.

This is `lazyjson` version 1.1.0 ([semver](http://semver.org/)). The versioned API is described below, in the section *API*.

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

API
===

When instantiating a `File`, the single argument must be one of the following:

*   a valid single argument to the built-in function [`open`](http://docs.python.org/3/library/functions.html#open),
*   an open [file object](https://docs.python.org/3/glossary.html#term-file-object),
*   or an [instance](http://docs.python.org/3/library/functions.html#isinstance) of [`pathlib.Path`](http://docs.python.org/3/library/pathlib.html#pathlib.Path).

The `File` object can then be used like a dict object. All data is lazily read from, and immediately written to the file each time it is accessed.

Note that constructing a `File` from a file object may result in unexpected behavior, as lazyjson uses `.read` on the file every time a value is accessed, and `.write` every time one is changed. The file object must also support [`str`](https://docs.python.org/3/library/stdtypes.html#str) input for changes to succeed.
