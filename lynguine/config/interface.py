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
    """A hierarchical interface configuration for data-oriented architecture.
    
    The Interface class manages configuration for data flows within the lynguine 
    data-oriented architecture. It provides a mechanism for defining inputs, outputs,
    computations, parameters, and other components of a data processing pipeline.
    
    Key features:
    - Hierarchical inheritance: An interface can inherit from a parent interface,
      allowing for composition and reuse of configurations.
    - Input/output management: Defines how data is read from and written to various sources.
    - Computation specification: Defines computations to be performed on the data.
    - Parameter handling: Manages configuration parameters that control processing.
    
    The interface can be loaded from YAML files, with support for environment variable
    expansion and directory-relative paths. When inheriting from another interface,
    the child can specify which elements to ignore or append from the parent.
    
    Inheritance is particularly useful when outputs from a parent interface are used
    as inputs to the child interface, creating a processing pipeline.
    """
    @classmethod
    def default_config_file(cls):
        """
        Return the default configuration file name
        """
        return "_linguine.yml"

    @classmethod
    def _extract_mapping_columns(self, data):
        """
        Extract mapping and columns from data.

        :param data: The data to be processed.
        :type data: dict
        :return: The mapping and columns.
        :rtype: tuple
        """
        mapping = {}
        columns = []
        if "mapping" in data:
            mapping = data["mapping"].copy()
            del data["mapping"]
        if "columns" in data:
            columns = data["columns"].copy()
            del data["columns"]
        return mapping, columns
                
    
    def __init__(self, data : dict=None, directory : str=None, user_file : str=None) -> None:
        """
        Initialize a new Interface instance with the provided configuration data.
        
        This constructor sets up the interface configuration, processes inheritance if specified,
        and expands environment variables in the configuration values.
        
        The initialization process:
        1. Validates required arguments (directory and user_file)
        2. Stores configuration data, directory, and filename
        3. Sets up parent interface if inheritance is specified
        4. Processes parent interface (resolving inheritance relationships)
        5. Expands environment variables in configuration values
        
        When inheritance is specified, the parent interface is loaded using the directory 
        and filename provided in the "inherit" section of the configuration. The parent's
        attributes can be selectively ignored or appended to the child interface using
        the "ignore" and "append" lists in the "inherit" section.
        
        :param data: Dictionary containing the configuration for the interface
        :type data: dict or None
        :param directory: Directory where the configuration file was loaded from 
                         (used for resolving relative paths)
        :type directory: str
        :param user_file: Filename of the configuration file
        :type user_file: str
        :return: None
        :raises ValueError: If required arguments are missing or if inheritance configuration is invalid
        """

        # Add base_directory and user_file to data if not already present.
        if directory is not None:
            if "base_directory" not in data:
                data["base_directory"] = directory
        if user_file is not None:
            if "user_file" not in data:
                data["user_file"] = user_file

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
            log.debug(f"Inheriting another Interface.")
            if "directory" not in self._data["inherit"]:
                raise ValueError(
                    f"Inherit specified in interface file {self._user_file} in directory {directory} but no directory to inherit from is specified."
                )

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

            # TK Establish if path is relative from current directory and set it to relative location.
            
            # Load parent interface
            self._parent = self.__class__.from_file(user_file=filename, directory=inherit_directory)
            
            # Set it not to be writable (convert output to input,
            # series to input, parameters to constants))
            self._parent._writable = False
            if "writable" in self._data and self._data["inherit"]["writable"]:
                self._parent._writable = True

            
            if "ignore" not in self._data["inherit"]:
                self._data["inherit"]["ignore"] = []
            if "append" not in self._data["inherit"]:
                self._data["inherit"]["append"] = []

            self._process_parent()
        self._expand_vars()

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
        Process the parent interface to establish inheritance relationships.
        
        This method handles the transformation of a parent interface's components when they
        are inherited by a child interface. It implements the lynguine inheritance model where:
        
        1. Parent outputs become child inputs - This enables pipeline processing where one
           interface's outputs feed into another's inputs.
        2. Parent series become child inputs - Series data from the parent is made available
           as input in the child.
        3. Parent parameters become child constants - Parameters that were configurable in the
           parent become fixed constants in the child.
           
        The method also handles keys that should be ignored based on the "ignore" list in the
        inheritance configuration, removing them from the parent before applying inheritance.
        
        This is a critical part of the hierarchical interface system, allowing for composition
        of data processing pipelines and reuse of configuration.
        
        :return: None
        """

        delete_keys = [] # Keys to be removed from the parents
        for key in self._data["inherit"]["ignore"]:
            if key in self._parent:
                delete_keys.append(key)


        # TK: Big similarities for code for "output, "series", and "parameters", consider using a helper function for all three
        
        # Output from parents shouldn't be modified, they become
        # parts of the input.
        if not self._parent._writable and "output" in self._parent._data and "output" not in delete_keys:

            mapping, columns = self._extract_mapping_columns(self._parent._data["output"])

            # Inherited outputs become input.
            log.debug(f"Inheriting parent output as input.")
            if "input" not in self._parent._data:
                self._parent._data["input"] = self._parent._data["output"]
            else:
                if self._parent._data["input"]["type"] == "hstack":
                    self._parent._data["input"]["specifications"].append(self._parent._data["output"])
                else:
                    self._parent._data["input"] = {
                        "type" : "hstack",
                        "index" : self._parent._data["input"]["index"],
                        "specifications" : [self._parent._data["input"], self._parent._data["output"]],
                        "mapping" : self._parent._data["input"]["mapping"],
                    }
            if "mapping" in self._parent._data["input"]:
                self._parent._data["input"]["mapping"].update(mapping)
            else:
                self._parent._data["input"]["mapping"] = mapping

            if "columns" in self._parent._data["input"]:
                self._parent._data["input"]["columns"] += columns
            else:
                self._parent._data["input"]["columns"] = columns

            delete_keys.append("output")

        # Series from parents should be converted to type series
        # and added to input.
        if "series" in self._parent._data and "series" not in self._data["inherit"]["ignore"]:
            mapping, columns = self._extract_mapping_columns(self._parent._data["series"])

            series = {
                "type" : "series",
                "index" : self._parent._data["series"]["index"],
                "specifications" : self._parent._data["series"]
            }
            # Inherited series become input.
            if "input" not in self._parent._data:
                self._parent._data["input"] = series
            elif self._parent._data["input"]["type"] == "hstack":
                self._parent._data["input"]["specifications"].append(series)
            else:
                self._parent._data["input"] = {
                    "type" : "hstack",
                    "index" : self._parent._data["input"]["index"],
                    "specifications" : [self._parent._data["input"], series]
                }
            if "mapping" in self._parent._data["input"]:
                self._parent._data["input"]["mapping"].update(mapping)
            else:
                self._parent._data["input"]["mapping"] = mapping

            if "columns" in self._parent._data["input"]:
                self._parent._data["input"]["columns"] += columns
            else:
                self._parent._data["input"]["columns"] = columns

            delete_keys.append("series")

        # Parameters from parents shouldn't be modifled, they become constants.
        if "parameters" in self._parent:
            mapping, columns = self._extract_mapping_columns(self._parent._data["parameters"])
            
            log.debug(f"Inheriting parent parameters as constants.")
            if "constants" not in self._data:
                self._parent._data["constants"] = self._parent._data["parameters"]
            elif self._parent._data["constants"]["type"] == "hstack":
                self._parent._data["constants"]["specifications"].append(self._parent._data["parameters"])
            else:
                self._parent._data["constants"] = {
                    "type" : "hstack",
                    "specifications" : [self._parent._data["constants"], self._parent._data["parameters"]]
                }

            if "mapping" in self._parent._data["constants"]:
                self._parent._data["cosntants"]["mapping"].update(mapping)
            else:
                self._parent._data["constants"]["mapping"] = mapping

            if "columns" in self._parent._data["constants"]:
                self._parent._data["constants"]["columns"] += columns
            else:
                self._parent._data["constants"]["columns"] = columns
                
                
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
    def from_file(cls, user_file=None, directory=".", field=None, raise_error_if_not_found=True):
        """
        Construct an Interface instance by loading configuration from a YAML file.
        
        This factory method creates an Interface object by reading a YAML configuration file.
        It handles file path resolution, YAML parsing, and hierarchical interface loading if 
        inheritance is specified in the configuration.
        
        The configuration file should be in YAML format and can include interface specifications
        for inputs, outputs, computations, and other configuration.
        
        :param user_file: The name of the configuration file to load, or a list of filenames 
                         to try in order (first existing file will be used). If None, the 
                         default config filename will be used.
        :type user_file: str or list[str] or None
        :param directory: The directory to look for the configuration file in, defaults to current directory.
        :type directory: str
        :param field: Optional specific field to extract from the loaded YAML (for when the interface
                     is nested within a larger configuration file).
        :type field: str or None
        :param raise_error_if_not_found: Whether to raise an error if the file is not found or empty,
                                        defaults to True. If False, an empty interface will be created.
        :type raise_error_if_not_found: bool
        :return: A new Interface instance loaded from the specified file.
        :rtype: Interface
        :raises ValueError: If the file is not found or empty (and raise_error_if_not_found is True),
                           or if the YAML cannot be parsed, or if a specified field is not found.
        """
        
        if user_file is None:
            ufile = cls.default_config_file()
        else:
            ufile = user_file
            
        expanded_directory = os.path.expandvars(directory)
        # If the user_file is a list, check existence of each file in order.
        if type(user_file) is list:
            for ufile in user_file:
                if os.path.exists(os.path.join(expanded_directory, ufile)):
                    break
        fname = os.path.join(expanded_directory, ufile)
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
        else:
            errmsg = f'No configuration file found at "{fname}".'
            if raise_error_if_not_found:
                log.error(errmsg)
                raise ValueError(errmsg)
            else:
                log.info(f'{errmsg} creating empty interface.')
        
        if data == {} and raise_error_if_not_found:
            errmsg = f'No data found in "{fname}".'
            log.error(errmsg)
            raise ValueError(errmsg)
        
        
        interface = cls(data, directory=expanded_directory, user_file=ufile)
        
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
