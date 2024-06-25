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

    def prep(self, settings : dict, data : CustomDataFrame ) -> dict:
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

    def run(self, data : CustomDataFrame, interface : Interface) -> None:
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
             
    def filter(self, data : CustomDataFrame, interface : Interface) -> None:
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
       
