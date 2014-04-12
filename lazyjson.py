try:
    import collections.abc as collectionsabc
except ImportError:
    import collections as collectionsabc
import io
import json
import threading

__version__ = '1.1.0'

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

class Node:
    def __deepcopy__(self, memodict={}):
        return self.value()
    
    def __init__(self, root, key_path=None):
        if not isinstance(root, File):
            root = File(root)
        self.root = root
        self.key_path = [] if key_path is None else key_path[:]    
    
    def __str__(self):
        return str(self.value())
    
    def __repr__(self):
        return 'lazyjson.Node(' + repr(self.root.file_info) + ', ' + repr(self.key_path) + ')'
    
    def value(self):
        return self.root.value_at_key_path(self.key_path)

class Dict(Node, collectionsabc.MutableMapping):
    def __delitem__(self, key):
        self.root.delete_value_at_key_path(self.key_path + [key])
    
    def __getitem__(self, key):
        if isinstance(self.value()[key], dict):
            return Dict(self.root, self.key_path + [key])
        elif isinstance(self.value()[key], list):
            return List(self.root, self.key_path + [key])
        else:
            return self.value()[key]
    
    def __iter__(self):
        for key in self.value():
            yield key
    
    def __len__(self):
        return len(self.value())
    
    def __setitem__(self, key, value):
        if isinstance(value, Node):
            value = value.value()
        self.root.set_value_at_key_path(self.key_path + [key], value)

class List(Node, collectionsabc.MutableSequence):
    def __delitem__(self, key):
        self.root.delete_value_at_key_path(self.key_path + [key])
    
    def __getitem__(self, key):
        if isinstance(self.value()[key], dict):
            return Dict(self.root, self.key_path + [key])
        elif isinstance(self.value()[key], list):
            return List(self.root, self.key_path + [key])
        else:
            return self.value()[key]
    
    def __len__(self):
        return len(self.value())
    
    def __setitem__(self, key, value):
        if isinstance(value, Node):
            value = value.value()
        self.root.set_value_at_key_path(self.key_path + [key], value)
    
    def insert(self, index, value):
        self.root.insert_value_at_key_path(self.key_path + [index], value)

class File(Dict):
    def __init__(self, file_info, file_is_open=None):
        self.file_is_open = isinstance(file_info, io.IOBase) if file_is_open is None else file_is_open
        self.file_info = file_info
        self.lock = threading.Lock()
        super().__init__(self)
    
    def delete_value_at_key_path(self, key_path):
        if self.file_is_open:
            json_dict = json.load(self.file_info)
        else:
            with open(self.file_info) as json_file:
                json_dict = json.load(json_file)
        item = json_dict
        if len(key_path) == 0:
            json_dict = {}
        else:
            for key in key_path[:-1]:
                item = item[key]
            del item[key_path[-1]]
        self.set(json_dict)
    
    def insert_value_at_key_path(self, key_path, value):
        if self.file_is_open:
            json_dict = json.load(self.file_info)
        else:
            with open(self.file_info) as json_file:
                json_dict = json.load(json_file)
        item = json_dict
        if len(key_path) == 0:
            json_dict = value
        else:
            for key in key_path[:-1]:
                item = item[key]
            item.insert(key_path[-1], value)
        self.set(json_dict)
    
    def set(self, value):
        if isinstance(value, Node):
            value = value.value()
        with self.lock:
            if self.file_is_open:
                json.dump(value, self.file_info, sort_keys=True, indent=4, separators=(',', ': '))
                print(file=self.file_info) # json.dump doesn't end the file in a newline, so add it manually
            else:
                with open(self.file_info, 'w') as json_file:
                    json.dump(value, json_file, sort_keys=True, indent=4, separators=(',', ': '))
                    print(file=json_file) # json.dump doesn't end the file in a newline, so add it manually
    
    def set_value_at_key_path(self, key_path, value):
        if self.file_is_open:
            json_dict = json.load(self.file_info)
        else:
            with open(self.file_info) as json_file:
                json_dict = json.load(json_file)
        item = json_dict
        if len(key_path) == 0:
            json_dict = value
        else:
            for key in key_path[:-1]:
                item = item[key]
            item[key_path[-1]] = value
        self.set(json_dict)
    
    def value_at_key_path(self, key_path):
        if self.file_is_open:
            ret = json.load(self.file_info)
        else:
            with open(self.file_info) as json_file:
                ret = json.load(json_file)
        for key in key_path:
            ret = ret[key]
        return ret
