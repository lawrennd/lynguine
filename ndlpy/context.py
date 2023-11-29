# This file loads configurations that are specific to the context
import os
import yaml
from itertools import chain

class _Config(object):
    """Base class for context and settings objects."""
    def __init__(self):
        raise NotImplementedError("The base object _Config is designed to be inherited")
    
    def __getitem__(self, key):
        return self._data[key]            

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data 

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def update(self, *args, **kwargs):
        self._data.update(*args, **kwargs)
        
    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._data})"

    def __iter__(self):
        return iter(self._data)
    

class Context(_Config):
    """Load in some default configuration from the context."""
    def __init__(self, name=None):        
        self._default_file = os.path.join(os.path.dirname(__file__), "defaults.yml")
        self._local_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "machine.yml"))

        if name is None:
            name = __name__
        self._name = name
        self._data = {}

        if os.path.exists(self._default_file):
            with open(self._default_file) as file:
                self._data.update(yaml.load(file, Loader=yaml.FullLoader))

        if os.path.exists(self._local_file):
            with open(local_file) as file:
                self._data.update(yaml.load(file, Loader=yaml.FullLoader))

        if self._data=={}:
            raise ValueError(
                "No configuration file found at either "
                + self._local_file
                + " or "
                + self._default_file
                + "."
            )
        self._expand_vars()
        self._add_logging_defaults()

    def _expand_vars(self):
        """Deal with any enviornment variables."""
        for key, item in self._data.items():
            if item is str:
                self._data[key] = os.path.expandvars(item)

    def _add_logging_defaults(self):
        """If there's no logging information in files, add some default info."""
        default_log = self._name + ".log"
        if "logging" in self._data:
            if not "level" in self._data["logging"]:
                self._data["logging"]["level"] = 20
                
            if not "filename" in self._data["logging"]:
                self._data["logging"]["filename"] = default_log
        else:
            self._data["logging"] = {"level": 20, "filename": default_log}


    
