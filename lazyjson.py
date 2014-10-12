import abc
try:
    import collections.abc as collectionsabc
except ImportError:
    import collections as collectionsabc
import io
import json
import threading

__version__ = '1.2.0'

try:
    import builtins
    import pathlib
except ImportError:
    pass
else:
    def open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        if isinstance(file, pathlib.Path):
            return file.open(mode=mode, buffering=buffering, encoding=encoding, errors=errors, newline=newline)
        else:
            return builtins.open(file, mode=mode, buffering=buffering, encoding=encoding, errors=errors, newline=newline, closefd=closefd, opener=opener)

class Node(collectionsabc.MutableMapping, collectionsabc.MutableSequence):
    def __contains__(self, item):
        if isinstance(item, Node):
            item = item.value()
        return item in self.value()
    
    def __deepcopy__(self, memodict={}):
        return self.value()
    
    def __delitem__(self, key):
        self.root.delete_value_at_key_path(self.key_path + [key])
    
    def __getitem__(self, key):
        return Node(self.root, self.key_path + [key])
    
    def __init__(self, root, key_path=None):
        if not isinstance(root, BaseFile):
            root = File(root)
        self.root = root
        self.key_path = [] if key_path is None else key_path[:]
    
    def __iter__(self):
        return self.value().__iter__()
    
    def __len__(self):
        return len(self.value())
    
    def __str__(self):
        return str(self.value())
    
    def __repr__(self):
        return 'lazyjson.Node(' + repr(self.root) + ', ' + repr(self.key_path) + ')'
    
    def __setitem__(self, key, value):
        if isinstance(value, Node):
            value = value.value()
        self.root.set_value_at_key_path(self.key_path + [key], value)
    
    def insert(self, key, value):
        self.root.insert_value_at_key_path(self.key_path + [key], value)
    
    def value(self):
        return self.root.value_at_key_path(self.key_path)

class BaseFile(Node, metaclass=abc.ABCMeta):
    """ABC for lazyjson files (root values)."""
    def __init__(self):
        super().__init__(self)
    
    def delete_value_at_key_path(self, key_path):
        json_value = self.value()
        item = json_value
        if len(key_path) == 0:
            json_value = None
        else:
            for key in key_path[:-1]:
                item = item[key]
            del item[key_path[-1]]
        self.set(json_value)
    
    def insert_value_at_key_path(self, key_path, value):
        json_value = self.value()
        item = json_value
        if len(key_path) == 0:
            json_value = value
        else:
            for key in key_path[:-1]:
                item = item[key]
            item.insert(key_path[-1], value)
        self.set(json_value)
    
    @abc.abstractmethod
    def set(self, new_value):
        pass
    
    def set_value_at_key_path(self, key_path, new_value):
        json_value = self.value()
        item = json_value
        if len(key_path) == 0:
            json_value = new_value
        else:
            for key in key_path[:-1]:
                item = item[key]
            item[key_path[-1]] = new_value
        self.set(json_value)
    
    @abc.abstractmethod
    def value(self, new_value):
        pass
    
    def value_at_key_path(self, key_path):
        ret = self.value()
        for key in key_path:
            ret = ret[key]
        return ret

class File(BaseFile):
    """A file based on a file-like object, a pathlib.Path, or anything that can be opened."""
    def __init__(self, file_info, file_is_open=None):
        super().__init__()
        self.file_is_open = isinstance(file_info, io.IOBase) if file_is_open is None else bool(file_is_open)
        self.file_info = file_info
        self.lock = threading.Lock()
    
    def __repr__(self):
        return 'lazyjson.File(' + repr(self.file_info) + ('' if self.file_is_open and isinstance(self.file_info, io.IOBase) or (not self.file_is_open) and not isinstance(self.file_info, io.IOBase) else ', file_is_open=' + repr(self.file_is_open)) + ')'
    
    def set(self, new_value):
        if isinstance(new_value, Node):
            value = value.value()
        json.dumps(new_value) # try writing the value to a string first to prevent corrupting the file if the value is not JSON serializable
        with self.lock:
            if self.file_is_open:
                json.dump(new_value, self.file_info, sort_keys=True, indent=4, separators=(',', ': '))
                print(file=self.file_info) # json.dump doesn't end the file in a newline, so add it manually
            else:
                with open(self.file_info, 'w') as json_file:
                    json.dump(new_value, json_file, sort_keys=True, indent=4, separators=(',', ': '))
                    print(file=json_file) # json.dump doesn't end the file in a newline, so add it manually
    
    def value(self):
        if self.file_is_open:
            return json.load(self.file_info)
        else:
            with open(self.file_info) as json_file:
                return json.load(json_file)

class PythonFile(BaseFile):
    """A file based on a Python object. Can be used with MultiFile to provide fallback values."""
    def __init__(self, value=None):
        super().__init__()
        self._value = value
    
    def __repr__(self):
        return 'lazyjson.PythonFile(' + repr(self._value) + ')'
    
    def set(self, new_value):
        json.dumps(new_value) # try writing the value to a string first to make sure it is JSON serializable
        self._value = new_value
    
    def value(self):
        return self._value

class SFTPFile(BaseFile):
    def __init__(self, host, port, path, **kwargs):
        super().__init__()
        self.hostname = host
        self.port = port
        self.remote_path = path
        self.connection_args = kwargs
    
    def __repr__(self):
        return 'lazyjson.SFTPFile(' + repr(self.hostname) + ', ' + repr(self.port) + ', ' + repr(self.remote_path) + ''.join(', {}={}'.format(k, repr(v)) for k, v in self.connection_args.items()) + ')'
    
    def set(self, new_value):
        import paramiko
        
        with paramiko.Transport((self.hostname, self.port)) as transport:
            transport.connect(**self.connection_args)
            with transport.open_sftp_client().file(self.remote_path, 'w') as sftp_file:
                json_string = json.dumps(new_value, sort_keys=True, indent=4, separators=(',', ': '))
                sftp_file.write(json_string.encode('utf-8') + b'\n')
    
    def value(self):
        import paramiko
        
        with paramiko.Transport((self.hostname, self.port)) as transport:
            transport.connect(**self.connection_args)
            with transport.open_sftp_client().file(self.remote_path) as sftp_file:
                return json.loads(sftp_file.read().decode('utf-8'))
