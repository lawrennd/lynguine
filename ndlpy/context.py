# This file loads configurations that are specific to the context
import os
import yaml

class Context():
    """Load in some default configuration from the context."""
    def __init__(self):        
        self._default_file = os.path.join(os.path.dirname(__file__), "defaults.yml")
        self._local_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "machine.yml"))

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
        default_log = __name__ + ".log"
        if "logging" in self._data:
            if not "level" in self._data["logging"]:
                self._data["logging"]["level"] = 20
                
            if not "filename" in self._data["logging"]:
                self._data["logging"]["filename"] = default_log
        else:
            self._data["logging"] = {"level": 20, "filename": default_log}


    