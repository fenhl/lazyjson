import json
import threading

__version__ = '0.1.0'

class Node:
    def __init__(self, root, key_path=None):
        if not isinstance(root, File):
            root = File(root)
        self.root = root
        self.key_path = [] if key_path is None else key_path[:]
    
    def __deepcopy__(self, memodict={}):
        return self.value()
    
    def __str__(self):
        return str(self.value())
    
    def __repr__(self):
        return 'lazyjson.Node(' + repr(self.root.file_info) + ', ' + repr(self.key_path) + ')'
    
    def value(self):
        return self.root.value_at_key_path(self.key_path)

class Dict(Node, dict):
    def __getitem__(self, key):
        if isinstance(self.value()[key], dict):
            return Dict(self.root, self.key_path + [key])
        elif isinstance(self.value()[key], list):
            return List(self.root, self.key_path + [key])
        else:
            return self.value()[key]
    
    def __setitem__(self, key, value):
        if isinstance(value, Node):
            value = value.value()
        self.root.set_value_at_key_path(self.key_path + [key], value)

class List(Node, list):
    def __getitem__(self, key):
        if isinstance(self.value()[key], dict):
            return Dict(self.root, self.key_path + [key])
        elif isinstance(self.value()[key], list):
            return List(self.root, self.key_path + [key])
        else:
            return self.value()[key]
    
    def __iadd__(self, other):
        self.root.set_value_at_key_path(self.key_path, self.value() + other)
        return self
    
    def __setitem__(self, key, value):
        if isinstance(value, Node):
            value = value.value()
        self.root.set_value_at_key_path(self.key_path + [key], value)

class File(Dict):
    def __init__(self, file_info):
        self.file_info = file_info
        self.lock = threading.Lock()
        super().__init__(self)
    
    def set(self, value):
        if isinstance(value, Node):
            value = value.value()
        with self.lock:
            with open(self.file_info, 'w') as json_file:
                json.dump(value, json_file, sort_keys=True, indent=4, separators=(',', ': '))
    
    def set_value_at_key_path(self, key_path, value):
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
        with open(self.file_info) as json_file:
            ret = json.load(json_file)
        for key in key_path:
            ret = ret[key]
        return ret