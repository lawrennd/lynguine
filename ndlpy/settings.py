import os
import numpy as np

from . import context 
from .log import Logger

from .access import read_yaml_file

ctxt = context.Context()
log = Logger(
    name=__name__,
    level=ctxt._data["logging"]["level"],
    filename=ctxt._data["logging"]["filename"],
)

class _HConfig(context._Config):
    """Base class for a hierachical configuration which can inherit from other configurations."""
    def __init__(self):
        raise NotImplementedError("The base object _HConfig is designed to be inherited")

    def __getitem__(self, key):
        if key in self._data or self._parent is None:
            return self._data[key]
        else:
            return self._parent[key]

    def __setitem__(self, key, value):
        if key in self._data or self._parent is None:
            self._data[key] = value
        else:
            self._parent[key] = value

    def __delitem__(self, key):
        if key in self._data or self._parent is None:
            del self._data[key]
        else:
            del self._parent[key]

    def __iter__(self):
        if self._parent is None:
            return iter(self._data)
        set1 = set(iter(self._data))        
        # Filter out elements from the second iterable that are in the set
        filtered_parent = filter(lambda x: x not in set1, iter(self._parent))
        # Chain them together
        return chain(iter(self._data), filtered_parent)

    def __len__(self):
        # This isn't quite right as should filter out parents that in self._data
        if self._parent is None:
            return len(self._data)
        return len(list(self.__iter__()))

    def __contains__(self, key):
        if self._parent is None:
            return key in self._data
        else:
            return key in self._data or key in self._parent

    def keys(self):
        if self._parent is None:
            return self._data.keys()
        else:
            return self._data.keys() + self._parent.keys()

    def items(self):
        if self._parent is None:
            return self._data.items()
        else:
            return self._data.items() + self._parent.items()

    def values(self):
        if self._parent is None:
            return self._data.values()
        else:
            return self._data.values() + self._parent.values()

    def get(self, key, default=None):
        if key in self._data or self._parent is None:
            return self._data.get(key, default)
        else:
            return self._parent.get(key, default)

    def update(self, *args, **kwargs):
        self._data.update(*args, **kwargs)
        
    def __str__(self):
        if self._parent is None:
            return str(self._data)
        else:
            return str(self._data) + "{\"parent\": " + str(self._parent) + "}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self._data})"

    def __iter__(self):
        return self._data.__iter__()
    

class Settings(_HConfig):
    """A settings object that loads in local settings files."""
    def __init__(self, user_file=None, directory=".", field=None):
        if user_file is None:
            ufile = "_" + __name__ + ".yml"
        else:
            ufile = user_file
        if type(user_file) is list:
            for ufile in user_file:
                if os.path.exists(os.path.join(os.path.expandvars(directory), ufile)):
                    break
        self._user_file = ufile
        self._directory = directory
        fname = os.path.join(os.path.expandvars(directory), ufile)
        self._filename = fname
        self._data = {}
        if os.path.exists(self._filename):
            data = read_yaml_file(self._filename)
            if field is None:
                self._data = data
            elif field in data:
                self._data = data[field]
            else:
                raise ValueError(f"Field \"{field}\" specified but not found in file \"{fname}\"")

        self._inputs = []
        self._output = []
        self._parameters = []
        self._writable = True
        
        self._parent = None
        if "inherit" in self._data:
            if "directory" not in self._data["inherit"]:
                raise ValueError(f"Inherit specified in settings file {user_file} in directory {directory} but no directory to inherit from is specified.")
            else:
                directory = self._data["inherit"]["directory"]
                if "filename" not in self._data["inherit"]:
                    filename = user_file
                else:
                    filename=self._data["inherit"]["filename"]
                self._parent = Settings(user_file=filename, directory=directory)
                self._parent._writable = False
                if "writable" in self._data and self._data["inherit"]["writable"]:
                    self._parent._writable = True
        if self._data=={}:
            log.warning(f"No configuration file found at {user_file}.")

        self._expand_vars()
        self._restructure()
        if self._parent is not None:
            self._process_parent()
        
    def _expand_vars(self):
        for key, item in self._data.items():
            if item is str:
                self._data[key] = os.path.expandvars(item)

    def _restructure(self):
        """For backwards compatability, move inputs, outputs and paremeters to correct place. """
        for key, item in self._data.items():
            if key in self._inputs:
                if "inputs" not in self._data:
                    self._data["inputs"] = {}
                self._data["inputs"][key] = item
            if key in self._output:
                if "output" not in self._data:
                    self._data["output"] = {}
                self._data["output"][key] = item
            if key in self._parameters:
                if "parameters" not in self._data:
                    self._data["parameters"] = {}
                self._data["parameters"][key] = item
                    
    def _process_parent(self):
        del self._data["inherit"]

    
