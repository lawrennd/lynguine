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
    """
    The Compute class handles computation operations on data frames.
    
    This class is responsible for executing various computation operations specified
    in an interface configuration. It supports precomputation, computation, and
    post-computation operations, along with liquid template rendering.
    
    The computation operations are specified in the interface using a dictionary or list
    of dictionaries with fields like 'function', 'field', 'args', etc.
    
    Attributes:
        _computes (dict): Dictionary of computation operations divided by type
            ('precompute', 'compute', 'postcompute').
        _liquid_env: The liquid template environment for rendering templates.
        logger: Logger instance for logging messages.
    """
    
    def __init__(self, interface):
        """Initialize the compute object.

        Creates a new Compute object with the specified interface, setting up
        computation operations, liquid environment, and logger.

        :param interface: The interface to be used for computation operations.
        :type interface: lynguine.config.interface.Interface or dict
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
        Setup the logger for the Compute class.
        
        Initializes the logger with the appropriate name, log level, and output file
        based on the context configuration.

        :return: None
        """
        self.logger = Logger(
            name=__name__,
            level=cntxt["logging"]["level"],
            filename=cntxt["logging"]["filename"],
        )
        

    @property
    def computes(self):
        """
        Return the compute operations.

        :return: The list of compute operations defined in the interface.
        :rtype: list
        """
        return self._computes["compute"]

    @property
    def precomputes(self):
        """
        Return the precompute operations.
        
        These operations are executed before the main compute operations.

        :return: The list of precompute operations defined in the interface.
        :rtype: list
        """
        return self._computes["precompute"]

    @property
    def postcomputes(self):
        """
        Return the postcompute operations.
        
        These operations are executed after the main compute operations.

        :return: The list of postcompute operations defined in the interface.
        :rtype: list
        """
        return self._computes["postcompute"]
    
        
    def prep(self, settings : dict, data : "CustomDataFrame" or pd.DataFrame) -> dict:
        """
        Prepare a compute entry for use.
        
        Processes the settings dictionary to create a standardized compute entry
        with function, arguments, and refresh flag.

        :param settings: The settings to be used for the computation.
        :type settings: dict
        :param data: The data to be used in the computation.
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

    def gca_(self, function, field=None, refresh=False, args={}, row_args={}, view_args={}, function_args={}, subseries_args={}, column_args={}, mode=None, separator=None):
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
        
        Creates and returns a function to be used for computation based on the
        function name specified. The returned function will access values from
        the data object according to the argument specifications.

        :param function: The name of the function to be used.
        :type function: str
        :param data: The data object to be used in the function.
        :type data: lynguine.assess.data.CustomDataFrame
        :return: The compute function that will be executed.
        :rtype: function
        :raises ValueError: If the specified function is not found in the list of available functions.
        """
        list_function = next((f for f in self._compute_functions_list() if f["name"] == function), None)
        if not list_function:
            raise ValueError(f"Function \"{function}\" not found in list_functions.")
        

        def compute_function(data, args={}, subseries_args={}, column_args={}, row_args={}, view_args={}, function_args = {}, default_args={}):
            """
            Compute a function using arguments found in subseries, columns, or the same row.
            
            This function applies the computation with arguments that can come from
            different sources in the data frame:
            - subseries: Values from a sub-series specified by a column and value
            - columns: Values from entire columns
            - rows: Values from the current row
            - direct args: Values provided directly in the args dictionary
            - function args: Values produced by other compute functions
            
            :param data: The data frame to operate on.
            :type data: lynguine.assess.data.CustomDataFrame
            :param args: Direct arguments to be used in the function, defaults to {}.
            :type args: dict, optional
            :param subseries_args: Arguments to extract from subseries, defaults to {}.
            :type subseries_args: dict, optional
            :param column_args: Arguments to extract from columns, defaults to {}.
            :type column_args: dict, optional
            :param row_args: Arguments to extract from the current row, defaults to {}.
            :type row_args: dict, optional
            :param view_args: Arguments for view operations, defaults to {}.
            :type view_args: dict, optional
            :param function_args: Arguments that are themselves functions, defaults to {}.
            :type function_args: dict, optional
            :param default_args: Default arguments for the function, defaults to {}.
            :type default_args: dict, optional
            :return: The result of the computation.
            :rtype: Any
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
                    # Check if column is actually a valid key/index
                    if isinstance(column, str) and column in data:
                        kwargs[key] = data[column]
                    else:
                        # column is not a valid key - this is likely a parameter value
                        # that should be passed directly, not treated as a column name
                        available_keys = list(data.keys()) if isinstance(data, dict) else list(data.index)
                        errmsg = f"Invalid key '{column}' in row_args for key '{key}' when data is {type(data).__name__}. Available keys: {available_keys}. If '{column}' is meant to be a parameter value, it should not be in row_args."
                        self.logger.error(errmsg)
                        raise ValueError(errmsg)
                else:
                    # Check if column is actually a valid column name
                    if isinstance(column, str) and column in data.columns:
                        kwargs[key] = data.get_value_column(column)
                    else:
                        # column is not a valid column name - this is likely a parameter value
                        # that should be passed directly, not treated as a column name
                        errmsg = f"Invalid column name '{column}' in row_args for key '{key}'. Available columns: {list(data.columns)}. If '{column}' is meant to be a parameter value, it should not be in row_args."
                        self.logger.error(errmsg)
                        raise ValueError(errmsg)
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
        Run the compute operations on the data.
        
        This method executes the compute operations specified in the interface on the data.
        First it runs any precompute operations, then the main compute operations,
        and finally any postcompute operations.
        
        For each compute operation, it:
        1. Prepares the operation with the settings and data
        2. Gets the current value for the target field
        3. Determines whether to compute (based on refresh flag and existing value)
        4. Computes the new value and sets it in the data frame
        
        :param data: The data to be processed.
        :type data: lynguine.assess.data.CustomDataFrame
        :param interface: The interface defining the compute operations.
        :type interface: lynguine.config.interface.Interface or dict
        :return: None
        :raises ValueError: If a compute operation is missing required fields.
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
            column_output = False
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
            
            # Get mode parameter early to determine if we need to run compute
            mode = compute.get("mode", "replace")
            
            # If we're not refreshing, need to determine which columns aren't set so they can be refreshed.
            missing_vals = []
            if not refresh:
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
            else:
                # When refreshing, treat all columns as if they need updating
                missing_vals = [True] * len(columns)

            # Append/prepend modes must always run to read existing content
            should_run = refresh or any(missing_vals) or mode in ["append", "prepend"]
            
            if should_run:
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

            # Get separator parameter for write operation (mode was retrieved earlier)
            separator = compute.get("separator", "\n\n---\n\n")
            
            # Distribute the updated values to the columns
            for column, new_val, missing_val in zip(columns, new_vals, missing_vals):
                if column == "_":
                    continue
                # Always write for append/prepend modes, respect refresh/missing_val for replace
                should_write = (
                    (mode in ["append", "prepend"]) or  # Accumulating modes always write
                    refresh or                           # Explicit refresh requested
                    missing_val                          # Field is empty
                )
                
                if should_write and data.ismutable(column):
                    # Apply write mode logic
                    if mode == "append" or mode == "prepend":
                        # Read current value for append/prepend modes
                        try:
                            current_val = data.get_value_column(column)
                            # Check if current value is non-empty
                            if current_val and not isna(current_val) and str(current_val).strip():
                                if mode == "append":
                                    # Append: current + separator + new
                                    new_val = str(current_val) + separator + str(new_val)
                                    self.logger.debug(f"Appending to column \"{column}\" with separator.")
                                elif mode == "prepend":
                                    # Prepend: new + separator + current
                                    new_val = str(new_val) + separator + str(current_val)
                                    self.logger.debug(f"Prepending to column \"{column}\" with separator.")
                        except (KeyError, AttributeError):
                            # Column doesn't exist yet, just use new value
                            pass
                    elif mode != "replace":
                        errmsg = f"Invalid mode '{mode}' specified for compute operation. Valid modes are: 'replace', 'append', 'prepend'."
                        self.logger.error(errmsg)
                        raise ValueError(errmsg)
                    
                    self.logger.debug(f"Setting column \"{column}\" in data structure to value \"{new_val}\" from compute (mode: {mode}).")
                    data.set_value_column(new_val, column)

        

    def preprocess(self, data : "CustomDataFrame", interface : Interface) -> None:
        """
        Run preprocessing operations on the data.
        
        Executes the precompute operations specified in the interface on the data.
        These operations are run before the main compute operations.
        
        Similar to run(), but only processes the 'precompute' operations.
        
        :param data: The data to be preprocessed.
        :type data: lynguine.assess.data.CustomDataFrame
        :param interface: The interface defining the precompute operations.
        :type interface: lynguine.config.interface.Interface or dict
        :return: None
        :raises ValueError: If a precompute operation is missing required fields.
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
        Run compute operations when a specific cell changes.
        
        This method is used to run compute operations when a specific cell in the
        data frame changes. It checks if the changed cell is used as an argument
        in any compute operation and runs those operations if needed.
        
        :param data: The data frame containing the changed cell.
        :type data: lynguine.assess.data.CustomDataFrame
        :param index: The index of the changed cell.
        :type index: object
        :param column: The column of the changed cell.
        :type column: str
        :return: None
        """
        self.logger.debug(f"Running onchange for {column} at index {index} (not yet implemented).")

        
    def run_all(self, data : "CustomDataFrame", interface : Interface) -> None:
        """
        Run compute operations on all indices in the data frame.
        
        Iterates through all indices in the data frame and runs the compute
        operations for each index. This is useful for batch processing the
        entire data set.
        
        :param data: The data to process.
        :type data: lynguine.assess.data.CustomDataFrame
        :param interface: The interface defining the compute operations.
        :type interface: lynguine.config.interface.Interface or dict
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
        List of available compute functions.
        
        Returns a list of dictionaries, each containing information about an available
        compute function, including its name, default arguments, and the actual function
        object.
        
        Each dictionary has the following structure:
        - 'name': The name of the function
        - 'function': The actual function object
        - 'default_args': Default arguments for the function
        
        :return: List of available compute functions.
        :rtype: list[dict]
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
        Apply filters to the data based on the interface.
        
        This method applies filters to the data frame based on filter specifications
        in the interface. It can select or exclude rows based on column values.
        
        :param data: The data to filter.
        :type data: lynguine.assess.data.CustomDataFrame
        :param interface: The interface defining the filters.
        :type interface: lynguine.config.interface.Interface or dict
        :return: None
        :raises ValueError: If a filter operation is invalid.
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
        """
        Initialize the liquid template environment.
        
        Sets up the liquid template rendering environment with custom filters
        and configurations from the interface.
        
        :param interface: The interface containing liquid configuration.
        :type interface: lynguine.config.interface.Interface or dict
        :return: None
        """
        self._liquid_env = lq.Environment(
            tolerance=lq.Mode.LAX  # Use Mode.LAX instead of the non-existent constants
        )
        self._liquid_env.add_filter("url_escape", url_escape)
        self._liquid_env.add_filter("markdownify", markdownify)
        self._liquid_env.add_filter("relative_url", relative_url)
        self._liquid_env.add_filter("absolute_url", absolute_url)
        self._liquid_env.add_filter("to_i", to_i)


    def add_liquid_filters(self):
        """
        Add custom filters to the liquid environment.
        
        This method can be extended to add additional custom filters
        to the liquid template environment.
        
        :return: None
        """
        pass

        
    @classmethod
    def from_flow(cls, interface):
        """
        Create a Compute instance from an interface.
        
        Factory method to create a Compute instance from an interface specification,
        which can be either an Interface object or a dictionary.
        
        :param interface: The interface to create the Compute from.
        :type interface: lynguine.config.interface.Interface or dict
        :return: A new Compute instance.
        :rtype: Compute
        """
        if not isinstance(interface, (dict, Interface)):
            raise ValueError("Interface must be a dictionary or of type Interface.")
        return cls(interface)
       
    # Render a string output
    def __str__(self):
        """
        Return a string representation of the Compute object.
        
        :return: String representation of the object.
        :rtype: str
        """
        return f"Compute({self._computes})"
        
    def _liquid_render(self, template, **kwargs):
        """
        Render a liquid template with the given arguments.
        
        This is a utility method used by the compute functions to render
        liquid templates.
        
        :param template: The liquid template to render.
        :type template: str
        :param kwargs: Arguments to pass to the template.
        :return: The rendered template.
        :rtype: str
        """
        try:
            return self._liquid_env.from_string(template).render(**kwargs)
        except Exception as e:
            self.logger.error(f"Error rendering liquid template '{template}': {e}")
            return f"Error rendering template: {e}"
            
    def _today(self, format="%Y-%m-%d"):
        """
        Return today's date as a formatted string.
        
        :param format: The format to use for the date string, defaults to "%Y-%m-%d".
        :type format: str, optional
        :return: Today's date as a string.
        :rtype: str
        """
        return datetime.datetime.now().strftime(format)
        
    def _identity(self, value):
        """
        Return the input value unchanged.
        
        This is a utility function that simply returns its input, useful
        when you need a pass-through function.
        
        :param value: The value to return.
        :return: The same value.
        """

        return value
