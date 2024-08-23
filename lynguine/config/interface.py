import os
import numpy as np

import yaml

from . import context
from ..log import Logger


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
    interface are used as input to the current interface. The
    interface can also append to the parent interface values.
    """
    @classmethod
    def default_config_file(cls):
        """
        Return the default configuration file name
        """
        return "_linguine.yml"

    def __init__(self, data : dict=None, directory : str=None, user_file : str=None) -> None:
        """
        Initialise the interface object.

        :param data: dictionary containing the information for the flows
        :type data: dict
        :param directory: directory where the flow infomration was loaded from
        :type directory: str
        :param user_file: file name of the user file.
        :type user_file: str
        :return: None
        """
        log.debug(f"Initialising lynguine.assess.Interface object.")
        if data is None:
            data = {}
        self._data = data

        if directory is None:
            errmsg = f"A directory must be provided when initialising an Interface object."
            log.error(errmsg)
            raise ValueError(errmsg)

        if user_file is None:
            errmsg = f"A user_file must be provided when initialising an Interface object."
            log.error(errmsg)
            raise ValueError(errmsg)

        self.directory = directory
        self.user_file = user_file
        
        self._parent = None
        self._input = []
        self._output = []
        self._parameters = []
        self._writable = True
        self._inherited = False

        if "inherit" in self._data:
            if "directory" not in self._data["inherit"]:
                raise ValueError(
                    f"Inherit specified in interface file {self._user_file} in directory {directory} but no directory to inherit from is specified."
                )
            else:
                log.debug(f"Inheriting another Interface.")
                inherit_directory = os.path.expandvars(self._data["inherit"]["directory"])
                if not os.path.isabs(inherit_directory):
                    inherit_directory = os.path.join(self.directory, inherit_directory)
                if "filename" not in self._data["inherit"]:
                    # assume default file name
                    filename = self.__class__.default_config_file()
                    log.debug(f"No filename specified in inherit section of interface file. Using default file name \"{filename}\"")
       
                else:
                    filename = self._data["inherit"]["filename"]
                log.debug(f"Inheriting parent Interface \"{filename}\" from directory \"{inherit_directory}\".")

                # Establish if path is relative from curent directory.
                self._parent = self.__class__.from_file(user_file=filename, directory=inherit_directory)
                self._parent._writable = False
                if "writable" in self._data and self._data["inherit"]["writable"]:
                    self._parent._writable = True
                if "ignore" not in self._data["inherit"]:
                    self._data["inherit"]["ignore"] = []
                if "append" not in self._data["inherit"]:
                    self._data["inherit"]["append"] = []
        
        self._expand_vars()
        #self._restructure()
        if self._parent is not None:
            log.debug(f"Processing parent.")
            if "output" in self._parent:
                log.debug(f"Output is there.")
            if "input" not in self._parent:
                log.debug(f"Input is not there.")
            self._process_parent()
            if "output" not in self._parent:
                log.debug(f"Output is not there.")
            if "input" in self._parent:
                log.debug(f"Input is there")

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
            if key == "input":
                if "input" not in self._parent:
                    return self._data["input"]
                elif "input" not in self._data:
                    return self._parent["input"]
                
                log.debug(f"Appending contents of parent input to input.")
                # stack the input horizontally.
                mapping = {}
                if "mapping" in self._parent["input"]:
                    mapping.update(self._parent["input"]["mapping"])
                if "mapping" in self._data["input"]:
                    mapping.update(self._data["input"]["mapping"])
                if self._parent["input"]["type"] == "hstack" and self._data["input"]["type"] == "hstack":
                    

                    return {
                        "type" : "hstack",
                        "index" : self._parent["input"]["index"],
                        "mapping" : mapping,
                        "specifications" : self._parent["input"]["specifications"] + self._data["input"]["specifications"]
                    }
                elif self._parent["input"]["type"] == "hstack":
                    return {
                        "type" : "hstack",
                        "index" : self._parent["input"]["index"],
                        "mapping" : mapping,
                        "specifications" : self._parent["input"]["specifications"] + [self._data["input"]]
                    }
                elif self._data["input"]["type"] == "hstack":
                    return {
                        "type" : "hstack",
                        "index" : self._parent["input"]["index"],
                        "mapping" : mapping,
                        "specifications" : [self._parent["input"]] + self._data["input"]["specifications"]
                    }
                else:
                    return {
                        "type" : "hstack",
                        "index" : self._parent["input"]["index"],
                        "mapping" : mapping,
                        "specifications" : [
                            self._parent["input"],
                            self._data["input"],
                        ]
                    }

            elif key == "constants":
                if "constants" not in self._parent:
                    return self._data["constants"]
                elif "constants" not in self._data:
                    return self._parent["constants"]
                
                log.debug(f"Appending contents of parent constants to constants.")
                # stack the constants horizontally.
                if self._parent["constants"]["type"] == "hstack" and self._data["constants"]["type"] == "hstack":
                    return {
                        "type" : "hstack",
                        "specifications" : self._parent["constants"]["specifications"] + self._data["constants"]["specifications"]
                    }
                elif self._parent["constants"]["type"] == "hstack":
                    return {
                        "type" : "hstack",
                        "specifications" : self._parent["constants"]["specifications"] + [self._data["constants"]]
                    }
                elif self._data["constants"]["type"] == "hstack":
                    return {
                        "type" : "hstack",
                        "specifications" : [self._parent["constants"]] + self._data["constants"]["specifications"]
                    }
                else:
                    return {
                        "type" : "hstack",
                        "specifications" : [
                            self._parent["constants"],
                            self._data["constants"],
                        ]
                    }
                
            if key in self._data:
                # Check if key is also in parent and is listed as an append key.
                if key in self._parent and key in self._data["inherit"]["append"]:
                    log.debug(f"Appending contents of parent key \"{key}\" to child.")
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
                        errmsg = f"Key {key} specified in inherit:append list, but entry is not of type \"dict\" or type \"list\" so appending doesn't make sense. Type of entry is \"{type(val)}\"."
                        log.error(errmsg)
                        raise ValueError(errmsg)
                else:
                    return self._data[key]
            elif key in self._parent: # key not in data, but is in parent.
                if key in self._data["inherit"]["ignore"]:
                    errmsg = f"Key \"{key}\" is not in current data and is specified in the inherit:ignore list."
                    log.error(errmsg)
                    raise KeyError(errmsg)
                else:
                    return self._parent[key]
            else:
                # Key is not in parent or data.
                errmsg = f"Key {key} is not found in the Interface or its parents. Available keys are \"{', '.join(self.keys())}. The following keys are explicitly ignored in inherited Interfaces \"{', '.join(self._data['inherit']['ignore'])}\"."
                log.error(errmsg)
                raise KeyError(errmsg)       

    @property
    def user_file(self):
        """
        Return the user file.

        :return: The user file.
        :rtype: str
        """
        return self._user_file

    @user_file.setter
    def user_file(self, value):
        """
        Set the user file.

        :param value: The user file.
        :type value: str
        :return: None
        """
        self._user_file = value

    @property
    def directory(self):
        """
        Return the directory.

        :return: The directory.
        :rtype: str
        """
        return self._directory

    @directory.setter
    def directory(self, value):
        """
        Set the directory.

        :param value: The directory.
        :type value: str
        :return: None
        """
        self._directory = value
        
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


    def _process_parent(self):
        """
        Process the parent interface file.
        """
        delete_keys = []
        if self._parent is not None:
            for key in self._data["inherit"]["ignore"]:
                if key in self._parent:
                    delete_keys.append(key)
            # Output from parents shouldn't be modified, they become parts of the input.      
            if "output" in self._parent and "output" not in self._data["inherit"]["ignore"]:
                # Inherited outputs become input.
                log.debug(f"Inheriting parent output as input.")
                if "input" not in self._parent:
                    self._parent["input"] = self._parent["output"]
                else:
                    if self._parent["input"]["type"] == "hstack":
                        self._parent["input"]["specifications"].append(self._parent["output"])
                    else:
                        self._parent["input"] = {
                            "type" : "hstack",
                            "index" : self._parent["input"]["index"],
                            "mapping" : {},
                            "specifications" : [self._parent["input"], self._parent["output"]]
                        }
                    if "mapping" in self._parent["output"]:
                        if "mapping" in self._parent["input"]:
                            self._parent["input"]["mapping"].update(self._parent["output"]["mapping"])
                        else:
                            self._parent["input"]["mapping"] = self._parent["output"]["mapping"]
                        
                delete_keys.append("output")
                
            # Series from parents should be converted to type series and added to input.    
            if "series" in self._parent and "series" not in self._data["inherit"]["ignore"]:
                series = {"type" : "series", "specifications" : self._parent["series"]}
                # Inherited series become input.
                if "input" not in self._parent:
                    self._parent["input"] = series
                elif self._parent["input"]["type"] == "hstack":
                    self._parent["input"]["specifications"].append(series)
                else:
                    self._parent["input"] = {
                        "type" : "hstack",
                        "index" : self._parent["input"]["index"],
                        "specifications" : [self._parent["input"], series]
                    }
                if "mapping" in series:
                    if "mapping" in self._parent["input"]:
                        self._parent["input"]["mapping"].update(series["mapping"])
                    else:
                        self._parent["input"]["mapping"] = series["mapping"]
                    for entry in self._parent["input"]["specifications"]:
                        if "mapping" in entry:
                            del entry["mapping"]
                delete_keys.append("series")

            # Parameters from parents shouldn't be modifled, they become constants.
            if "parameters" in self._parent:
                log.debug(f"Inheriting parent parameters as constants.")
                if "constants" not in self._data:
                    self._parent["constants"] = self._parent["parameters"]
                elif self._parent["constants"]["type"] == "hstack":
                    self._parent["constants"]["specifications"].append(self._parent["parameters"])
                else:
                    self._parent["constants"] = {
                        "type" : "hstack",
                        "specifications" : [self._parent["constants"], self._parent["parameters"]]
                    }
                delete_keys.append("parameters")
                
        for key in delete_keys:
            del self._parent._data[key]

    def _extract_review_write_fields(self, data=None):
        """
        Extract fields from the "review" entry that need to be written to in the output file.

        :return: The fields that need to be written to in the output file.
        :rtype: list

        """
        if data is None:
            if self._data is not None:
                data = self._data
            else:
                errmsg = "No data provided to extract fields from."
                log.error(errmsg)
                raise ValueError(errmsg)
        if "review" in data:
            return self._extract_fields(data["review"])
        else:
            return []


    def _extract_fields(self, entries):
        """
        Extract fields from the entries.

        :param entries: The entries to extract fields from.
        :type entries: list
        :return: The fields.
        :rtype: list
        """
        fields = []
        if not isinstance(entries, list):
            entries = [entries]
        for rev in entries:
            if "field" in rev:
                field = rev["field"]
                if field not in fields:
                    fields.append(field)
            elif "entries" in rev:                
                new_fields = self._extract_fields(rev["entries"])
                for field in new_fields:
                    if field not in fields:
                        fields.append(field)
        return fields

    @classmethod
    def default_config_file(cls):
        """
        Default name of the interface configuration file.
        """
        return "_lynguine.yml"
    
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
        log.debug(f"Attempting to open file \"{fname}\".")
        if os.path.exists(fname):
            with open(fname, "r") as stream:
                try:
                    log.debug(f'Reading yaml file "{fname}"')
                    data = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    errmsg = f'Error reading yaml file "{fname}", error: {exc}'
                    log.error(errmsg)
                    raise ValueError(errmsg)
                    
                    data = {}
            if field is not None:
                if field in data:
                    data = data[field]
                else:
                    raise ValueError(
                        f'Field "{field}" specified but not found in file "{fname}"'
                    )
        if data == {}:
            log.warning(f'No configuration file found at "{fname}".')

        interface = cls(data, directory=directory, user_file=ufile)
        
        return interface

        
    @classmethod
    def from_yaml(cls, text : str) -> "Interface":
        """
        Read an interface from yaml text.

        :param text: yaml text of interface.
        :type text: str
        :return: A lynguine.config.interface.Interface object.
        """
        input_dict = yaml.safe_load(text)
        return cls(input_dict, directory=".", user_file=cls.default_config_file())

    def to_yaml(self) -> str:
        """
        Write the interface to yaml text.

        :return: yaml text of interface.
        :rtype: str
        """
        return yaml.dump(self._data)
