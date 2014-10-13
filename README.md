**lazyjson** is a module for Python 3.2 or higher that provides lazy JSON I/O.

This is `lazyjson` version 1.2.0 ([semver](http://semver.org/)). The versioned API is described below, in the section *API*.

Usage
=====

First you need a lazyjson object, which can represent a JSON formatted file on the file system:

```python
>>> import lazyjson
>>> f = lazyjson.File('example-file.json')
```

or even a remote file:

```python
>>> import lazyjson, paramiko.util, os.path
>>> host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
>>> f = lazyjson.SFTPFile('example.com', 22, '/foo/bar/example-file.json', username='me', pkey=paramiko.RSAKey.from_private_key_file(os.path.expanduser('~/.ssh/id_rsa')), hostkey=host_keys['example.com'][host_keys['example.com'].keys()[0]])
```

You can then use the `File` object like a regular `dict`:

```python
>>> print(f)
{'someKey': ['a', 'b', 'c']}
```

Okay, so far so good. But why not just use [`json.load`](https://docs.python.org/3/library/json.html#json.load)? Well, this is where the “lazy” part comes in. Let's say some other program modifies our `example-file.json`. Let's do the same call again, still on the same `File` object:

```python
>>> print(f['someKey'])
['a', 'b', 'c', 'd']
```

The result has magically changed, because the file is actually read each time you get data from it. If you have write permission, you can also modify the file simply by changing the values from the `File` object:

```python
>>> f['someKey'] += ['e', 'f']
>>> with open('example-file.json') as text_file:
...     print(text_file.read())
... 
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

Lazyjson 2 provides the `BaseFile` ABC and two concrete subclasses: `File` and `SFTPFile`.

BaseFile
--------

`BaseFile` inherits from `Node`, and represents its own root node (see below).

It has 2 abstract methods:

*   `set`: write the JSON value passed as argument to the file.
*   `value`: read the JSON value from the file.

Both methods should handle native Python objects, as used in the [`json`](docs.python.org/3/library/json.html) module.

It also has an `__init__` method that takes no arguments and must be called from subclasses' `__init__`.

File
----

When instantiating a `File`, the single argument must be one of the following:

*   a valid single argument to the built-in function [`open`](http://docs.python.org/3/library/functions.html#open),
*   an open [file object](https://docs.python.org/3/glossary.html#term-file-object),
*   or an [instance](http://docs.python.org/3/library/functions.html#isinstance) of [`pathlib.Path`](http://docs.python.org/3/library/pathlib.html#pathlib.Path).

Note that constructing a `File` from a file object may result in unexpected behavior, as lazyjson uses `.read` on the file every time a value is accessed, and `.write` every time one is changed. The file object must also support [`str`](https://docs.python.org/3/library/stdtypes.html#str) input for changes to succeed.

MultiFile
---------

A `MultiFile` represents a stack of JSON files, with values higher up on the stack extending or overwriting those below them.

The constructor takes a variable number of positional arguments, which should all be instances of `BaseFile` subclasses. These will become the file stack, listed from top to bottom.

When reading a `MultiFile`, a single file representation is created by recursively merging/overriding the values in the file stack. Two objects are merged into one, and all other types of JSON values, as well as an object and a different value, overwrite each other.

When writing to a `MultiFile`, only the topmost file is ever modified. It will be modified in such a way that using the reading algorithm on the multifile will have the intended effect. The only exception is deleting pairs from a JSON object, which is undefined behavior.

**Note:** the exact writing behavior of `MultiFile` is undefined and may change at any point without requiring a major release.

PythonFile
----------

This class makes a lazyjson file out of a native Python object, as defined by the `json` module. It can be used in a `MultiFile` to provide a fallback value.

SFTPFile
--------

The `SFTPFile` class uses [paramiko](https://github.com/paramiko/paramiko) to represent a JSON file accessed via SFTP (FTP over SSH).

The constructor takes the following required positional-only arguments:

*   the hostname
*   the port (usually 22)
*   the remote path/filename

Any keyword arguments are passed to [`connect`](http://docs.paramiko.org/en/1.15/api/transport.html#paramiko.transport.Transport.connect) on the [`paramiko.Transport`](http://docs.paramiko.org/en/1.15/api/transport.html#paramiko.transport.Transport) object.

The file is fetched from the SFTP connection on each read, no caching is performed.

Node
----

A node represents a JSON value, such as an entire file (the root node), or a value inside an array inside an object inside the root node.

Nodes have a method `value`, which returns the JSON value of the node as a native Python object, similar to [`json.load`](https://docs.python.org/3/library/json.html#json.load).

Nodes representing JSON arrays or objects can mostly be used like Python `list`s and `dict`s, respectively: they can be indexed, sliced, and iterated over as usual. Some of these operations may return nodes, or succeed even for missing keys. Trying this on primitive nodes (numbers, strings, booleans, or null) is undefined behavior.

Under the hood, the `Node` object only holds a reference to its file (`BaseFile` subclass instance), and its key path. All data is lazily read from, and immediately written to the file each time it is accessed. This means that you can have `Node` objects representing nonexistent nodes. This will become apparent when calling `value` on this node raises an exception.
