import pandas as pd

from ..log import Logger
from ..config.context import Context

ctxt = Context()
log = Logger(
    name=__name__,
    level=ctxt._data["logging"]["level"],
    filename=ctxt._data["logging"]["filename"],
)

class WidgetCluster:
    """
    A class to hold a cluster of widgets.
    """
    def __init__(self, name, parent, viewer=False, **kwargs):
        self._widget_dict = {}
        self._widget_list = []
        self._name = name
        self._viewer = viewer
        self._parent = parent
        log.debug(f"Setting cluster name to \"{name}\".")
        self.add(**kwargs)

    def clear_children(self):
        self.close()
        self._widget_dict = {}
        self._widget_list = []

    def close(self):
        for entry in self._widget_list:
            if isinstance(entry, WidgetCluster):
                entry.close()
            else:
                self._widget_dict[entry].close()
                
    def has(self, key):
        return key in self.to_dict()

    def get(self, key):
        return self.to_dict()[key]

    def refresh(self):
        log.debug(f"Widget list is currently \"{self._widget_list}\"")
        for entry in self._widget_list:
            if isinstance(entry, WidgetCluster):
                log.debug(f"Refreshing widget cluster \"{entry._name}\"")
                entry.refresh()
            elif isinstance(entry, str):
                log.debug(f"Refreshing widget \"{entry}\"")                
                self._widget_dict[entry].refresh()
            else:
                errmsg = f"Invalid entry type \"{type(entry)}\"."
                log.error(errmsg)
                raise KeyError(errmsg)
        log.debug(f"Finished refreshing")
        
    def add(self, cluster=None, **kwargs):
        if cluster is not None:
            cluster.add(**kwargs)
            self._widget_list.append(cluster)
        else:
            if kwargs:
                self._widget_list.extend(list(kwargs.keys()))
                self._widget_dict.update(kwargs)
        
    def update(self, **kwargs):
        for key, item in kwargs.items():
            if key in self._widget_dict:
                self._widget_dict[key] = item
            else:
                raise ValueError(f"Attempt to update widget \"{key}\" when it doesn't exist.")

    def to_markdown(self, skip=[]):
        text = ""
        for entry in self._widget_list:
            if isinstance(entry, WidgetCluster):
                text += entry.to_markdown(skip=skip)
            else:
                if isinstance(entry, str):
                    entry = [entry]
                for key in entry:
                    if key not in skip:
                        text += self._widget_dict[key].to_markdown()
                        if text:
                            text += "\n\n"
        return text
            
    def to_dict(self):
        widgets = {}
        for entry in self._widget_list:
            if isinstance(entry, WidgetCluster):
                widgets.update(entry.to_dict())
            else:
                if isinstance(entry, str):
                    widgets[entry] = self._widget_dict[entry]
                else:
                    for key in entry:
                        widgets[key] = self._widget_dict[key]
        return widgets

    def display(self):
        for entry in self._widget_list:
            if isinstance(entry, WidgetCluster):
                entry.display()
            else:
                self._widget_dict[entry].display()


class DisplaySystem:
    def __init__(self, index=None, data=None, interface=None, system=None):
        self._data = data
        self._interface = interface
        self._system = system
        self._widgets = WidgetCluster(name="parent", parent=self)
        self._downstream_displays = []

        if index is not None and data is not None:
            self._data.set_index(index)

    @property
    def index(self):
        return self._data.index if self._data is not None else None

    def get_index(self):
        return self._data.get_index() if self._data is not None else None

    def set_index(self, value: str) -> None:
        if self._data is not None:
            old_val = self.get_index()
            if old_val != value:
                self._data.set_index(value)
                self.populate_display()
                for ds in self._downstream_displays:
                    ds.set_index(value)

    def get_value(self):
        return self._data.get_value() if self._data is not None else None

    def get_value_by_element(self, element):
        return self._data.get_value_by_element(element) if self._data is not None else None

    def set_value_by_element(self, value, element, trigger_update=True):
        if self._data is not None:
            old_value = self.get_value_by_element(element)
            if value != old_value:
                self._data.set_value_by_element(value, element)
                if trigger_update:
                    self.value_updated()

    def set_value(self, value, trigger_update=True):
        if self._data is not None:
            old_value = self.get_value()
            if value != old_value:
                self._data.set_value(value)
                if trigger_update:
                    self.value_updated()

    def get_column(self) -> str:
        return self._data.get_column() if self._data is not None else None

    def set_column(self, column) -> None:
        if self._data is not None:
            self._data.set_column(column)

    def get_indices(self) -> pd.Index:
        return self._data.index if self._data is not None else None

    def add_downstream_display(self, display):
        self._downstream_displays.append(display)

    def load_flows(self, reload: bool = False) -> None:
        if self._data is not None:
            self._data.load_flows()
        self.populate_display()

    def save_flows(self) -> None:
        if self._data is not None:
            self._data.save_flows()
        for ds in self._downstream_displays:
            ds.load_flows()
            ds.set_index(self.get_index())
            ds.populate_display()

    def load_input_flows(self) -> None:
        if self._data is not None:
            self._data.load_input_flows()

    def load_output_flows(self) -> None:
        if self._data is not None:
            self._data.load_output_flows()

    def populate_display(self) -> None:
        self._widgets.refresh()

    def value_updated(self):
        pass
