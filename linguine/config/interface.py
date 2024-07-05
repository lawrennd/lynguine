import os
import numpy as np

from . import context
from ..log import Logger

from linguine.access.io import read_yaml_file

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
            if self._parent is not None:
                if key in self._parent:
                    del self._parent[key]
        else:
            self._parent[key] = value

    def __delitem__(self, key):
        """
        Delete the key.

        :param key: The key to be deleted.
        :type key: str
        :return: None
        """
        if key not in self.keys():
            raise KeyError(f"Key {key} not found in object.")
        
        if key in self._data:
            del self._data[key]
        if self._parent is not None and key in self._parent:
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
        return len(self.keys())

    def __contains__(self, key):
        """
        Check if the key is in the object.

        :param key: The key to be checked.
        :type key: str
        :return: True if the key is in the object, False otherwise.
        :rtype: bool
        """
        return key in self.keys()

    def keys(self):
        """
        Return the keys.

        :return: The keys.
        :rtype: list
        """
        if self._parent is None:
            return self._data.keys()
        else:
            tmp_dict = {}
            for key in self._data:
                tmp_dict[key] = None
            for key in self._parent:
                if key not in tmp_dict:
                    tmp_dict[key] = None
            return tmp_dict.keys()

    def items(self):
        """
        Return the items.

        :return: The items.
        :rtype: list
        """
        for key in self.keys():
            yield (key, self[key])

    def values(self):
        """
        Return the values.

        :return: The values.
        :rtype: list
        """
        if self._parent is None:
            return self._data.values()
        else:
            tmp_dict = {}
            for key in self.keys():
                tmp_dict[key] = self[key]
            return tmp_dict.values()
                
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
        if key in self.keys():
            return self.__getitem__(key)
        else:
            return default

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
        # Create a string representation similar to a regular dictionary
        items_str = ', '.join([f"{repr(key)}: {repr(self[key])}" for key in self])
        return f"{{{items_str}}}"

    def __repr__(self):
        """
        Return a string representation of the object.

        :return: A string representation of the object.
        """
        # More formal representation, typically used for debugging
        class_name = self.__class__.__name__
        items_repr = ', '.join([f"{repr(key)}: {repr(self[key])}" for key in self])
        return f"{class_name}({{{items_repr}}})"

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
    """A interface object that loads in local interface files.

    The interface can be hierarchical in that one interface can
    inherit from another interface where typically outputs from that
    interface are used as inputs to the current interface. The
    interface can also append to the parent interface values.
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
                    f"Inherit specified in interface file {self._user_file} in directory {directory} but no directory to inherit from is specified."
                )
            else:
                directory = self._data["inherit"]["directory"]
                if "filename" not in self._data["inherit"]:
                    # assume default file name
                    filename = self.__class__.default_config_file()
                else:
                    filename = self._data["inherit"]["filename"]
                self._parent = Interface.from_file(user_file=filename, directory=directory)
                self._parent._writable = False
                if "writable" in self._data and self._data["inherit"]["writable"]:
                    self._parent._writable = True
                if "ignore" not in self._data["inherit"]:
                    self._data["inherit"]["ignore"] = []
                if "append" not in self._data["inherit"]:
                    self._data["inherit"]["append"] = []
        
        self._expand_vars()
        self._restructure()
        if self._parent is not None:
            self._process_parent()
        

    def __getitem__(self, key):
        """
        Get an item from the interface. If an item is not found,
        search the parent. If an item is specified in "inherit",
        "ignore" then ignore it in the parent. If an item is specified
        in "inherit:append" then append it to the parent values.

        :param key: The key to be returned.
        :type str:
        :return value: The value of the key.
        :rtype: object

        """

        if self._parent is None:
            if key in self._data:
                return self._data[key]
            else:
                raise ValueError(
                    f"Key {key} not found in Interface object. Available keys are \"{', '.join(self._data.keys())}\""
                )
        else:
            if key in self._data:
                # Check if key is also in parent and is listed as an append key.
                if key in self._parent and key in self._data["inherit"]["append"]:
                    # Key should be appended to parent values
                    val = self._data[key]
                    par_val = self._parent[key]
                    if isinstance(par_val, dict):
                        tmp = par_val.copy()
                        tmp.update(val)
                        return tmp
                    elif isinstance(par_val, list):
                        return par_val + val
                    else:
                        raise ValueError(
                            f"Key {key} specified in inherit append list, but entry is not of type \"dict\" or type \"list\" so appending doesn't make sense. Type of entry is \"{type(val)}\"."
                        )
                else:
                    return self._data[key]
            elif key in self._parent: # key not in data, but is in parent.
                return self._parent[key]
            else:
                # Key is not in parent or data.
                raise ValueError(
                    f"Key {key} is not found in the Interface or its parents. Available keys are \"{', '.join(self.keys())}. The following keys are explicitly ignored in inherited Interfaces \"{', '.join(self._data['inherit']['ignore'])}\"."
                    )

    def get_output_columns(self):
        """
        Return the output columns.

        :return: The output columns.
        :rtype: list
        """
        if "output" in self._data and "columns" in self._data["output"]:
            return self._data["output"]["columns"]
        else:
            columns = []
            if "compute" in self._data:
                for comp in self._data["compute"]:
                    if "field" in comp and comp["field"][0] != "_":
                        columns.append(comp["field"])
            if "review" in self._data:
                for rev in self._data["review"]:
                    if "field" in rev and rev["field"][0] != "_":
                        columns.append(rev["field"])
        if len(columns) > 0:
            return columns
        else:
            log.warning(
                f'No output columns specified in interface file.'
            )
            return []

    def get_cache_columns(self):
        """
        Return the cache columns.

        :return: The cache columns.
        :rtype: list
        """
        if "cache" in self._data and "columns" in self._data["cache"]:
            return self._data["cache"]["columns"]
        else:
            columns = []
            if "compute" in self._data:
                for comp in self._data["compute"]:
                    if "field" in comp and comp["field"][0] == "_":
                        columns.append(comp["field"])
                    elif "cache" in comp:
                        columns.append(comp["cache"])
        if len(columns) > 0:
            return columns
        else:
            log.warning(
                f'No cache columns specified in interface file.'
            )
            return []
    
    def _expand_vars(self):
        """
c        Expand the environment variables in the configuration.

        :return: None
        """
        for key, item in self._data.items():
            if isinstance(item, str):
                self._data[key] = os.path.expandvars(item)

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
        delete_keys = []
        if self._parent is not None:
            for key in self._data["inherit"]["ignore"]:
                if key in self._parent._data.keys():
                    delete_keys.append(key)
        for key in delete_keys:
            del self._parent._data[key]

    @classmethod
    def default_config_file(cls):
        """
        Default name of the interface configuration file.
        """
        return "_linguine.yml"
    
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
            ufile = cls.default_config_file()
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

        
