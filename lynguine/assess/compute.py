import os
import datetime
import pandas as pd
import liquid as lq

from ..config.context import Context
from ..log import Logger

from ..config.interface import Interface

from ..util.text import render_liquid
from ..util.misc import isna

from ..util.liquid import url_escape, markdownify, relative_url, absolute_url, to_i

cntxt = Context(name="lynguine")
           

class Compute():
    def __init__(self, interface):
        """Initialize the compute object.

        :param interface: The interface to be used.
        :type interface: lynguine.config.interface.Interface
        :return: None
        """

        self._computes = {}
        for comptype in ["precompute", "compute", "postcompute"]:
            if comptype in interface:
                if isinstance(interface[comptype], dict):
                    interface[comptype] = [interface[comptype]]
                    self._computes[comptype]=interface[comptype]
                elif isinstance(interface[comptype], list):
                    self._computes[comptype]=interface[comptype]
            else:
                self._computes[comptype] = []
        self.load_liquid(interface)
        self.add_liquid_filters()

        self.setup_logger()

    def setup_logger(self):
        """
        Setup the logger.

p        :return: None
        """
        self.logger = Logger(
            name=__name__,
            level=cntxt["logging"]["level"],
            filename=cntxt["logging"]["filename"],
        )
        

    @property
    def computes(self):
        """
        Return the computes.

        :return: The computes.
        :rtype: list
        """
        return self._computes["compute"]

    @property
    def precomputes(self):
        """
        Return the precomputes.

        :return: The precomputes.
        :rtype: list
        """
        return self._computes["precompute"]

    @property
    def postcomputes(self):
        """
        Return the post computes.

        :return: The post computes.
        :rtype: list
        """
        return self._computes["postcompute"]
    
        
    def prep(self, settings : dict, data : "CustomDataFrame" or pd.DataFrame) -> dict:
        """
        Prepare a compute entry for use.

        :param settings: The settings to be used.
        :type settings: dict
        :param data: The data to be used.
        :type data: lynguine.assess.data.CustomDataFrame or pandas.DataFrame
        :return: The prepared compute entry.
        :rtype: dict

        """
        self.logger.debug(f"Preparing compute entry with settings \"{settings}\".")
        compute_prep = {
            "function": self.gcf_(function=settings["function"], data=data),
            "args" : self.gca_(**settings),
            "refresh" : "refresh" in settings and settings["refresh"],
        }
        if "field" in settings:
            compute_prep["field"] = settings["field"]
        return compute_prep

    def gca_(self, function, field=None, refresh=False, args={}, row_args={}, view_args={}, function_args={}, subseries_args={}, column_args={}):
        """
        Args generator for compute functions.

        :param function: The name of the function to be used.
        :type function: str
        :param field: The field to be used.
        :type field: str
        :param refresh: Whether to refresh the field.
        :type refresh: bool
        :param args: The arguments to be used.
        :type args: dict
        :param row_args: The row arguments to be used.
        :type row_args: dict
        :param view_args: The view arguments to be used.
        :type view_args: dict
        :param function_args: The function arguments to be used.
        :type function_args: dict
        :param subseries_args: The subseries arguments to be used.
        :type subseries_args: dict
        :param column_args: The column arguments to be used.
        :type column_args: dict
        :return: The arguments to be used.
        :rtype: dict
        """

        found_function = False
        for list_function in self._compute_functions_list():
            if list_function["name"] == function:
                found_function = True
                break
        if not found_function:
            errmsg = f"Function \"{function}\" not found in list_functions."
            self.logger.error(errmsg)
            raise ValueError(errmsg)
        return {
            "subseries_args" : subseries_args,
            "column_args" : column_args,
            "row_args" : row_args,
            "view_args" : view_args,
            "function_args" : function_args,
            "args" : args,
            "default_args" : list_function["default_args"],
        }


    def gcf_(self, function, data):
        """
        Function generator for compute functions.

        :param function: The name of the function to be used.
        :type function: str
        :param data: The data to be used.
        :type data: lynguine.assess.data.CustomDataFrame
        :return: The function to be used.
        """
        list_function = next((f for f in self._compute_functions_list() if f["name"] == function), None)
        if not list_function:
            raise ValueError(f"Function \"{function}\" not found in list_functions.")
        

        def compute_function(data, args={}, subseries_args={}, column_args={}, row_args={}, view_args={}, function_args = {}, default_args={}):
            """
            Compute a function using arguments found in subseries (column of sub-series specified by value in dictionary), or columns (full column specified by value in dictionary) or the same row (value from row as specified in the dictionary).
            :param args: The arguments to be used.
            :type args: dict
            :param subseries_args: The subseries arguments to be used.
            :type subseries_args: dict
            :param column_args: The column arguments to be used.
            :type column_args: dict
            :param row_args: The row arguments to be used.
            :type row_args: dict
            :param view_args: The view arguments to be used.
            :type view_args: dict
            :param function_args: The function arguments to be used.
            :type function_args: dict
            :param default_args: The default arguments to be used.
            :type default_args: dict
            :return: The result of the computation.
            """

            kwargs = default_args.copy()
            kwargs.update(args)
            for key, value in function_args.items():
                kwargs[key] = self.gcf_(value, data)
            for key, column in column_args.items():
                if otherdf is None:
                    orig_col = data.get_column()
                    data.set_column(column)
                if key in kwargs:
                    self.logger.warning(f"No key \"{key}\" already column_args found in kwargs.")
                kwargs[key] = data.get_column_values()
                data.set_column(orig_col)
                
            for key, column in subseries_args.items():
                orig_col = data.get_column()
                data.set_column(column)
                if key in kwargs:
                    self.logger.warning(f"No key \"{key}\" from subseries_args already found in kwargs.")   
                kwargs[key] = data.get_subseries_values()
                data.set_column(orig_col)

            ## Arguments based on liquid, or format, or join.
            for key, view in view_args.items():
                orig_col = data.get_column()
                kwargs[key] = data.view_to_value(view)
                data.set_column(orig_col)
                
            for key, column in row_args.items():
                if key in kwargs:
                    self.logger.warning(f"No key \"{key}\" from row_args already found in kwargs.")
                # if it's a series or a dictionary return element
                if isinstance(data, (pd.Series, dict)):
                    kwargs[key] = data[column]
                else:
                    kwargs[key] = data.get_value_column(column)
            # kwargs.update(remove_nan(data.mapping(args)))
            self.logger.debug(f"The keyword arguments for the compute function are {kwargs}.")
            if "context" in list_function and list_function["context"]:# if the compute context is required
                return list_function["function"](self, **kwargs)
            return list_function["function"](**kwargs)

        compute_function.__name__ = list_function["name"]
        if "docstr" in list_function:
            compute_function.__doc__ = list_function["docstr"]
        return compute_function

    def run(self, data : "CustomDataFrame", interface : Interface) -> None:
        """
        Run computations on all rows of the data.

        :param data: The data to be updated.
        :type data: lynguine.assess.data.CustomDataFrame
        :param interface: The interface to be used.
        :type interface: lynguine.config.interface.Interface
        :return: None
        """

        if "compute" not in interface:
            msg = f"Interface does not contain a compute section."
            self.logger.info(msg)
            return

        computes = interface["compute"]
        if not isinstance(computes, list):
            computes = [computes]

        index = data.get_index()
        
        for compute in computes:
            # Some computes return multiple outputs, in which case field is a list of columns
            multi_output = False 
            
            if "field" in compute:
                columns = compute["field"]
                if isinstance(columns, list):
                    multi_output = True
                else:
                    columns = [columns]
            else:
                columns = None

            # Check if we need to refresh the data    
            if "refresh" in compute:
                refresh = compute["refresh"]
            else:
                refresh = False
                
            compute_prep = self.prep(compute, data)
            fname = compute_prep["function"].__name__
            fargs = compute_prep["args"]
            if columns is None: # No fields to update, just run the compute
                self.logger.debug(f"Running compute function \"{fname}\" with no field(s) stored for index=\"{index}\" with refresh=\"{refresh}\" and arguments \"{fargs}\".")
                compute_prep["function"](data, **fargs)
                continue
            
            # If we're not refreshing, need to determine which columns aren't set so they can be refreshed.
            if not refresh:
                missing_vals = []
                for column in columns:
                    if column not in data.columns:
                        missing_vals.append(True)
                        continue
                    if column == "_": # If the column is called "_" then ignore that argument
                        missing_vals.append(False)
                        continue
                    val = data.get_value_column(column)
                    if not isinstance(val, list) and isna(val): 
                        missing_vals.append(True) # The value is missing.
                    else:
                        missing_vals.append(False)

            if refresh or any(missing_vals):
                # Compute the function and get the new values  
                self.logger.debug(f"Running compute function \"{fname}\" storing in field(s) \"{columns}\" with index=\"{index}\" with refresh=\"{refresh}\" and arguments \"{fargs}\".")
                    
                new_vals = compute_prep["function"](data, **fargs)
            else:
                continue
                   
            if multi_output:
                if not isinstance(new_vals, tuple):
                    errmsg = f"Multiple columns provided for return values of \"{fname}\" but return value given is not a tuple."
                    log.error(errmsg)
                    raise ValueError(errmsg)
            
                new_vals = [*new_vals]
            else:
                new_vals = [new_vals]

            # Distribute the updated values to the columns
            for column, new_val, missing_val in zip(columns, new_vals, missing_vals):
                if column == "_":
                    continue
                if refresh or missing_val and data.ismutable(column):
                    self.logger.debug(f"Setting column \"{column}\" in data structure to value \"{new_val}\" from compute.")
                    data.set_value_column(new_val, column)

        

    def preprocess(self, data : "CustomDataFrame", interface : Interface) -> None:
        """
        Run all compute computations inside the data frame.

        :param data: The data to be updated.
        :type data: lynguine.assess.data.CustomDataFrame
        :param interface: The interface to be used.
        :type interface: lynguine.config.interface.Interface
        :return: None
        """
        if "compute" not in interface:
            msg = f"Interface does not contain a compute section."
            self.logger.info(msg)
            return
        else:
            computes = interface["compute"]
            for compute in computes:
                compute_prep = self.prep(compute, data)
                fargs = compute_prep["args"]
                if "field" in compute:
                    data[compute["field"]] = compute_prep["function"](data, **fargs)
                else:
                    compute_prep["function"](data, **fargs)

    def run_onchange(self, data : "CustomDataFrame", index : object, column : str) -> None:
        """
        Run any computations that are triggered by a change in the data.

        :param data: The data to be updated.
        :type data: lynguine.assess.data.CustomDataFrame
        :param index: The index to be used.
        :type index: object
        :param column: The column to be used.
        :type column: str
        :return: None
        """
        self.logger.debug(f"Running onchange for {column} at index {index} (not yet implemented).")

        
    def run_all(self, data : "CustomDataFrame", interface : Interface) -> None:
        """
        Run any computation elements on the data frame.

        :param data: The CustomDataFrame to be used.
        :type data: lynguine.assess.data.CustomDataFrame
        :param interface: The interface to be used.
        :type interface: lynguine.config.interface.Interface
        :return: None
        """

        current_index = data.get_index()
        self.logger.debug(f"Current index is {current_index}.")
        for index in data.index:
            self.logger.debug(f"Running all computations for index {index}.")
            data.set_index(index)
            self.run(data, interface)

        self.logger.debug(f"Resetting index to {current_index}.")
        data.set_index(current_index)
        
    def _compute_functions_list(self) -> list[dict]:
        """
        Return a list of compute functions.

        :return: A list of compute functions.
        :rtype: list
        """
        return [
            {
                "name" : "render_liquid",
                "function" : render_liquid,
                "context" : True, # compute context required for liquid_env
                "default_args" : {
                },
                "docstr": "Render a liquid template.",
            },
            {
                "name" : "today",
                "function" : datetime.datetime.now().strftime,
                "context" : False, # no compute context required
                "default_args": {
                    "format": "%Y-%m-%d",
                },
                "docstr" : "Return today's date as a string.",
            },
        ]
    
    def filter(self, data : "CustomDataFrame", interface : Interface) -> None:
        """
        Filter the data based on the interface. The filter allows
        removal of rows from the data.

        :param data: The data to be updated.
        :type data: lynguine.assess.data.CustomDataFrame
        :param interface: The interface to be used.
        :type interface: lynguine.config.interface.Interface
        :return: None
        """
        
        if "filter" not in interface:
            self.logger.info(msg)
            return
        
        filters = interface["filter"]
        if not isinstance(filters, list):
            filters = [filters]

        filt = pd.Series(True, index=data.index)
        for filter in filters:
            filter_prep = self.prep(filter)
            fargs = filter_prep["args"]
            newfilt = filter_prep["function"](data, **fargs)
            filt = (filt & newfilt)
        data.filter_row(filt)
            
    def load_liquid(self, interface):
        """Load the liquid environment."""
        loader = None
        if "liquid" in interface:
            if "templates" in interface["liquid"]:
                if "dir" in interface["liquid"]["templates"]:
                    templates_path = [os.path.abspath(interface["liquid"]["templates"])]
                else:
                    template_path = [
                        os.path.join(os.path.dirname(__file__), "templates"),
                    ]

                    if "ext" in interface["liquid"]:
                        ext = interface["liquid"]["ext"]
                        loader = lq.loaders.FileExtensionLoader(search_path=template_path, ext=ext)
                    else:
                        loader = lq.FileSystemLoader(template_path)
            elif "dict" in interface["liquid"]["templates"]:
                loader = lq.loaders.DictLoader(interface["liquid"]["templates"]["dict"])
        self._liquid_env = lq.Environment(loader=loader)


    def add_liquid_filters(self):
        """Add liquid filters to the liquid environment."""
        self._liquid_env.add_filter("url_escape", url_escape)
        self._liquid_env.add_filter("markdownify", markdownify)
        self._liquid_env.add_filter("relative_url", relative_url)
        self._liquid_env.add_filter("absolute_url", absolute_url)
        self._liquid_env.add_filter("to_i", to_i)
        

    @classmethod
    def from_flow(cls, interface):
        """
        Construct a Compute object from a interface object.

        :param interface: Interface object.
        :return: A Compute object.
        """
        if not isinstance(interface, (dict, Interface)):
            raise ValueError("Interface must be a dictionary or of type Interface.")
        return cls(interface)
       
    # Render a string output
    def __str__(self):
        """
        Create a string version of the object for printing.
        :return: A string version of the object.
        """
        val = ""
        for comptype in ["precompute", "compute", "postcompute"]:
            if comptype in self._computes and len(self._computes[comptype])>0:
                val += f"{comptype}: {self._computes[comptype]}\n"
            else:
                val += f"{comptype}: None\n"

        return val
