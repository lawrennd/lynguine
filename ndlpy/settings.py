import os
import numpy as np

from .context import Context
from .log import Logger

from .access import read_yaml_file

ctxt = Context()
log = Logger(
    name=__name__,
    level=ctxt._data["logging"]["level"],
    filename=ctxt._data["logging"]["filename"],
)

class Settings(object):
    """A settings object that loads in local settings files."""
    def __init__(self, user_file=None, directory="."):
        if user_file is None:
            user_file = "_" + __name__ + ".yml"
        
        self._filename = os.path.join(os.path.expandvars(directory), user_file)
        self._data = {}
        if os.path.exists(user_file):
            self._data = read_yaml_file(user_file)

        self._inputs = []
        self._outputs = []
        self._parameters = []
        
        self._parent = {}
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

        if self._data=={}:
            log.warning(f"No configuration file found at {user_file}.")

        self._expand_vars()
        
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
        pass
