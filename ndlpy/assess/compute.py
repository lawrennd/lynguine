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
       
