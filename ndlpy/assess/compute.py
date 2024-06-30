import os
import datetime
import pandas as pd
import liquid as lq

from ..config.context import Context
from ..log import Logger

from ..config.interface import Interface

from ..util.text import render_liquid

from ..util.liquid import url_escape, markdownify, relative_url, absolute_url, to_i

cntxt = Context(name="ndlpy")
           
log = Logger(
    name=__name__,
    level=cntxt["logging"]["level"],
    filename=cntxt["logging"]["filename"],
    
)

class Compute():
    def __init__(self, interface):
        """Initialize the compute object.

        :param interface: The interface to be used.
        :type interface: ndlpy.config.interface.Interface
        :return: None
        """

        self._computes = {}
        for comptype in ["precompute", "compute", "postcompute"]:
            self._computes[comptype]=[]
        self.load_liquid(interface)
        self.add_liquid_filters()

    def prep(self, settings : dict, data : "CustomDataFrame" ) -> dict:
        """
        Prepare a compute entry for use.

        :param settings: The settings to be used.
        :type settings: dict
        :param data: The data to be used.
        :type data: ndlpy.assess.data.CustomDataFrame
        :return: The prepared compute entry.
        :rtype: dict

        """
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
            log.error(errmsg)
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
        :type data: ndlpy.assess.data.CustomDataFrame
        :return: The function to be used.
        """
        found_function = False
        for list_function in self._compute_functions_list():
            if list_function["name"] == function:
                found_function = True
                break
        if not found_function:
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
                    log.warning(f"No key \"{key}\" already column_args found in kwargs.")
                kwargs[key] = data.get_column_values()
                data.set_column(orig_col)
                
            for key, column in subseries_args.items():
                orig_col = data.get_column()
                data.set_column(column)
                if key in kwargs:
                    log.warning(f"No key \"{key}\" from subseries_args already found in kwargs.")   
                kwargs[key] = data.get_subseries_values()
                data.set_column(orig_col)

            ## Arguments based on liquid, or format, or join.
            for key, view in view_args.items():
                orig_col = data.get_column()
                kwargs[key] = data.view_to_value(view)
                data.set_column(orig_col)
                
            for key, column in row_args.items():
                if key in kwargs:
                    log.warning(f"No key \"{key}\" from row_args already found in kwargs.")
                kwargs[key] = data.get_value_column(column)
            # kwargs.update(remove_nan(data.mapping(args)))
            log.debug(f"The keyword arguments for the compute function are {kwargs}.")
            return list_function["function"](**kwargs)

        compute_function.__name__ = list_function["name"]
        if "docstr" in list_function:
            compute_function.__doc__ = list_function["docstr"]
        return compute_function

    def run(self, data : "CustomDataFrame", interface : Interface) -> None:
        """
        Run computations on all rows of the data.

        :param data: The data to be updated.
        :type data: ndlpy.assess.data.CustomDataFrame
        :param interface: The interface to be used.
        :type interface: ndlpy.config.interface.Interface
        :return: None
        """
        if "compute" not in interface:
            msg = f"Interface does not contain a compute section."
            log.info(msg)
            return
        
        computes = interface["compute"]
        if not isinstance(computes, list):
            computes = [computes]
        
        for compute in computes:
            compute_prep = self.prep(compute)
            fargs = compute_prep["args"]
            if "field" in compute: # if field is in compute, then we are computing or updating a new field
                data[compute["field"]] = compute_prep["function"](data, **fargs)
            else:
                compute_prep["function"](data, **fargs)

    def preprocess(self, data, interface):
        """
        Run all preprocess computations.

        :return: None
        """
        pass

    def run_all(self, data, df=None, index=None, pre=False, post=False):
        """
        Run any computation elements on the data frame.

        :param df: The data frame to be used.
        :type df: pandas.DataFrame or ndlpy.assess.data.CustomDataFrame
        :param index: The index to be used.
        :type index: object
        :param pre: Whether to run precomputes.
        :type pre: bool
        :param post: Whether to run postcomputes.
        :type post: bool
        :return: None
        """
        pass

    
    def filter(self, data : "CustomDataFrame", interface : Interface) -> None:
        """
        Filter the data based on the interface. The filter allows
        removal of rows from the data.

        :param data: The data to be updated.
        :type data: ndlpy.assess.data.CustomDataFrame
        :param interface: The interface to be used.
        :type interface: ndlpy.config.interface.Interface
        :return: None
        """
        
        if "filter" not in interface:
            log.info(msg)
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
       
