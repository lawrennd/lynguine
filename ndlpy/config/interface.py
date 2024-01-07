import os
import numpy as np

from . import context
from ..log import Logger

from ndlpy.access.io import read_yaml_file

ctxt = context.Context()
log = Logger(
    name=__name__,
    level=ctxt._data["logging"]["level"],
    filename=ctxt._data["logging"]["filename"],
)


class _HConfig(context._Config):
    """
    Base class for a hierachical configuration which can inherit from other configurations.

    This is a base class for a hierachical configuration which can inherit from other configurations.
    """

    def __init__(self):
        raise NotImplementedError(
            "The base object _HConfig is designed to be inherited"
        )

    def __getitem__(self, key):
        """
        Return the value of the key.

        :param key: The key to be returned.
        :type key: str
        :return: The value of the key.
        :rtype: object
        """
        if key in self._data or self._parent is None:
            return self._data[key]
        else:
            return self._parent[key]

    def __setitem__(self, key, value):
        """
        Set the value of the key.

        :param key: The key to be set.
        :type key: str
        :param value: The value to be set.
        :type value: object
        :return: None
        """
        if key in self._data or self._parent is None:
            self._data[key] = value
        else:
            self._parent[key] = value

    def __delitem__(self, key):
        """
        Delete the key.

        :param key: The key to be deleted.
        :type key: str
        :return: None
        """
        if key in self._data or self._parent is None:
            del self._data[key]
        else:
            del self._parent[key]

    def __iter__(self):
        """
        Return an iterator over the keys.

        :return: An iterator over the keys.
        """
        # If there is no parent, just return the keys
        if self._parent is None:
            return iter(self._data)
        # Otherwise, create a set of the keys in the data
        set1 = set(iter(self._data))
        # Filter out elements from the second iterable that are in the set
        filtered_parent = filter(lambda x: x not in set1, iter(self._parent))
        # Chain them together
        return chain(iter(self._data), filtered_parent)

    def __len__(self):
        """
        Return the number of keys.

        :return: The number of keys.
        :rtype: int
        """
        # TODO: This isn't quite right as should filter out parents that in self._data
        if self._parent is None:
            return len(self._data)
        return len(list(self.__iter__()))

    def __contains__(self, key):
        """
        Check if the key is in the object.

        :param key: The key to be checked.
        :type key: str
        :return: True if the key is in the object, False otherwise.
        :rtype: bool
        """
        if self._parent is None:
            return key in self._data
        else:
            return key in self._data or key in self._parent

    def keys(self):
        """
        Return the keys.

        :return: The keys.
        :rtype: list
        """
        if self._parent is None:
            return self._data.keys()
        else:
            return self._data.keys() + self._parent.keys()

    def items(self):
        """
        Return the items.

        :return: The items.
        :rtype: list
        """
        if self._parent is None:
            return self._data.items()
        else:
            return self._data.items() + self._parent.items()

    def values(self):
        """
        Return the values.

        :return: The values.
        :rtype: list
        """
        if self._parent is None:
            return self._data.values()
        else:
            return self._data.values() + self._parent.values()

    def get(self, key, default=None):
        """
        Return the value of the key providing a default if the key is not found.

        :param key: The key to be returned.
        :type key: str
        :param default: The default value to be returned if the key is not found.
        :type default: object
        :return: The value of the key.
        :rtype: object
        """
        if key in self._data or self._parent is None:
            return self._data.get(key, default)
        else:
            return self._parent.get(key, default)

    def update(self, *args, **kwargs):
        """
        Update the object with the values from another object.

        :param args: The object to be updated with.
        :type args: object
        :param kwargs: The object to be updated with.
        :type kwargs: object
        :return: None
        """
        self._data.update(*args, **kwargs)

    def __str__(self):
        """
        Return a string representation of the object.

        :return: A string representation of the object.
        :rtype: str
        """
        if self._parent is None:
            return str(self._data)
        else:
            return str(self._data) + '{"parent": ' + str(self._parent) + "}"

    def __repr__(self):
        """
        Return a string representation of the object.

        :return: A string representation of the object.
        """
        return f"{self.__class__.__name__}({self._data})"

    def __iter__(self):
        """
        Return an iterator over the keys.

        :return: An iterator over the keys.
        """
        # First yield keys from the current interface
        for key in self._data.keys():
            yield key
            
        # Then, if a parent exists, yield keys from the parent
        # that are not already in the current interface
        if self._parent is not None:
            for key in self._parent:
                if key not in self._data:
                    yield key


class Interface(_HConfig):
    """
    A interface object that loads in local interface files.
    """

    def __init__(self, data=None):
        """
        Initialise the interface object.

        :param data: 
        :return: None
        """

        if data is None:
            data = {}

        self._data = data
        self._parent = None
        self._inputs = []
        self._output = []
        self._parameters = []
        self._writable = True

        if "inherit" in self._data:
            if "directory" not in self._data["inherit"]:
                raise ValueError(
                    f"Inherit specified in interface file {user_file} in directory {directory} but no directory to inherit from is specified."
                )
            else:
                directory = self._data["inherit"]["directory"]
                if "filename" not in self._data["inherit"]:
                    filename = user_file
                else:
                    filename = self._data["inherit"]["filename"]
                self._parent = Interface.from_file(user_file=filename, directory=directory)
                self._parent._writable = False
                if "writable" in self._data and self._data["inherit"]["writable"]:
                    self._parent._writable = True

        
        self._expand_vars()
        self._restructure()
        if self._parent is not None:
            self._process_parent()
        
        
    def _expand_vars(self):
        """
        Expand the environment variables in the configuration.

        :return: None
        """
        for key, item in self._data.items():
            if isinstance(item, str):
                self._data[key] = os.path.expandvars(item)
                print(self._data[key])

    def _restructure(self):
        """
        Restructure the data to be in the correct format.

        For backwards compatability, move inputs, outputs and paremeters to correct place.
        """
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
        """
        Process the parent interface file.
        """
        del self._data["inherit"]


    @classmethod
    def from_file(cls, user_file=None, directory=".", field=None):
        """
        Construct an Interface from the details in a file.

        :param user_file: The name of the user file to be loaded in.
        :type user_file: str
        :param directory: The directory to look for the user file in.
        :type directory: str
        :param field: The field to be loaded in.
        :type field: str
        
        """
        if user_file is None:
            ufile = "_" + __name__ + ".yml"
        else:
            ufile = user_file
        if type(user_file) is list:
            for ufile in user_file:
                if os.path.exists(os.path.join(os.path.expandvars(directory), ufile)):
                    break
        fname = os.path.join(os.path.expandvars(directory), ufile)
        data = {}
        if os.path.exists(fname):
            data = read_yaml_file(fname)
            if field is not None:
                if field in data:
                    data = data[field]
                else:
                    raise ValueError(
                        f'Field "{field}" specified but not found in file "{fname}"'
                    )
        if data == {}:
            log.warning(f'No configuration file found at "{user_file}".')

        interface = cls(data)
        interface._directory = directory
        interface._user_file = user_file
        
        return interface

        
