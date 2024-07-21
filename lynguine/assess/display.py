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
    A class to hold and manage a cluster of widgets.
    """

    def __init__(self, name, parent, viewer=False, **kwargs):
        """
        Initialize a WidgetCluster.

        :param name: The name of the widget cluster
        :type name: str
        :param parent: The parent object of this cluster
        :type parent: object
        :param viewer: Whether this cluster is a viewer, defaults to False
        :type viewer: bool, optional
        :param kwargs: Additional widgets to add to the cluster
        """
        self._widget_dict = {}
        self._widget_list = []
        self._name = name
        self._viewer = viewer
        self._parent = parent
        log.debug(f"Setting cluster name to \"{name}\".")
        self.add(**kwargs)

    def clear_children(self):
        """
        Clear all child widgets from the cluster.
        """
        self.close()
        self._widget_dict = {}
        self._widget_list = []

    def close(self):
        """
        Close all widgets in the cluster.
        """
        for entry in self._widget_list:
            if isinstance(entry, WidgetCluster):
                entry.close()
            else:
                self._widget_dict[entry].close()
                
    def has(self, key):
        """
        Check if the widget cluster contains a specific widget.

        :param key: The key of the widget to check for
        :type key: str
        :return: True if the widget exists in the cluster, False otherwise
        :rtype: bool
        """
        return key in self.to_dict()

    def get(self, key):
        """
        Get a specific widget from the cluster.

        :param key: The key of the widget to retrieve
        :type key: str
        :return: The requested widget
        :rtype: object
        """
        return self.to_dict()[key]

    def refresh(self):
        """
        Refresh all widgets in the cluster.
        """
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
        """
        Add widgets or a sub-cluster to this cluster.

        :param cluster: A WidgetCluster to add as a sub-cluster, defaults to None
        :type cluster: WidgetCluster, optional
        :param kwargs: Widgets to add to the cluster
        """
        if cluster is not None:
            cluster.add(**kwargs)
            self._widget_list.append(cluster)
        else:
            if kwargs:
                self._widget_list.extend(list(kwargs.keys()))
                self._widget_dict.update(kwargs)
        
    def update(self, **kwargs):
        """
        Update existing widgets in the cluster.

        :param kwargs: The widgets to update, with their new values
        :raises ValueError: If attempting to update a non-existent widget
        """
        for key, item in kwargs.items():
            if key in self._widget_dict:
                self._widget_dict[key] = item
            else:
                raise ValueError(f"Attempt to update widget \"{key}\" when it doesn't exist.")

    def to_markdown(self, skip=[]):
        """
        Convert the widget cluster to markdown format.

        :param skip: List of widget keys to skip in the conversion, defaults to []
        :type skip: list, optional
        :return: Markdown representation of the widget cluster
        :rtype: str
        """
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
        """
        Convert the widget cluster to a dictionary.

        :return: Dictionary representation of the widget cluster
        :rtype: dict
        """
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
        """
        Display all widgets in the cluster.
        """
        for entry in self._widget_list:
            if isinstance(entry, WidgetCluster):
                entry.display()
            else:
                self._widget_dict[entry].display()


class DisplaySystem:
    """
    A class to manage the display system for data visualization and interaction.
    """

    def __init__(self, index=None, data=None, interface=None, system=None):
        """
        Initialize a DisplaySystem.

        :param index: The index to set for the data, defaults to None
        :type index: str, optional
        :param data: The data to display, defaults to None
        :type data: object, optional
        :param interface: The interface to use, defaults to None
        :type interface: object, optional
        :param system: The system to use, defaults to None
        :type system: object, optional
        """
        self._downstream_displays = []
        if interface is None:
            raise TypeError("The interface argument is missing in DisplaySystem.")
        else:
            self._interface = interface

        if system is None:
            raise TypeError("The system argument is missing in DisplaySystem.")
        else:
            self._system = system

        if data is None:
            raise TypeError("The data argument is missing in DisplaySystem.")
        else:
            self._data = data

        
        self._widgets = WidgetCluster(name="parent", parent=self)
        self._downstream_displays = []

        if index is not None:
            # Widget isn't created yet so set index in data only.
            self._data.set_index(index)

    @property
    def index(self):
        """
        Get the current index of the data.

        :return: The current index
        :rtype: pd.Index or None
        """
        return self._data.index if self._data is not None else None

    def get_index(self):
        """
        Get the current index of the data.

        :return: The current index
        :rtype: object or None
        """
        return self._data.get_index() if self._data is not None else None

    def set_index(self, value: str) -> None:
        """
        Set the index of the data.

        :param value: The new index value
        :type value: str
        """
        if self._data is not None:
            old_val = self.get_index()
            if old_val != value:
                self._data.set_index(value)
                self.populate_display()
                for ds in self._downstream_displays:
                    ds.set_index(value)

    def get_value(self):
        """
        Get the current value of the data.

        :return: The current value
        :rtype: object or None
        """
        return self._data.get_value() if self._data is not None else None

    def get_value_by_element(self, element):
        """
        Get a specific element's value from the data.

        :param element: The element to retrieve
        :type element: object
        :return: The value of the specified element
        :rtype: object or None
        """
        return self._data.get_value_by_element(element) if self._data is not None else None

    def set_value_by_element(self, value, element, trigger_update=True):
        """
        Set the value of a specific element in the data.

        :param value: The new value to set
        :type value: object
        :param element: The element to update
        :type element: object
        :param trigger_update: Whether to trigger an update after setting the value, defaults to True
        :type trigger_update: bool, optional
        """
        if self._data is not None:
            old_value = self.get_value_by_element(element)
            if value != old_value:
                self._data.set_value_by_element(value, element)
                if trigger_update:
                    self.value_updated()

    def set_value(self, value, trigger_update=True):
        """
        Set the current value of the data.

        :param value: The new value to set
        :type value: object
        :param trigger_update: Whether to trigger an update after setting the value, defaults to True
        :type trigger_update: bool, optional
        """
        if self._data is not None:
            old_value = self.get_value()
            if value != old_value:
                self._data.set_value(value)
                if trigger_update:
                    self.value_updated()

    def get_column(self) -> str:
        """
        Get the current column of the data.

        :return: The current column
        :rtype: str or None
        """
        return self._data.get_column() if self._data is not None else None

    def set_column(self, column) -> None:
        """
        Set the current column of the data.

        :param column: The new column to set
        :type column: str
        """
        if self._data is not None:
            self._data.set_column(column)

    def get_indices(self) -> pd.Index:
        """
        Get all indices of the data.

        :return: All indices
        :rtype: pd.Index or None
        """
        return self._data.index if self._data is not None else None

    def add_downstream_display(self, display):
        """
        Add a downstream display to update when this display updates.

        :param display: The downstream display to add
        :type display: DisplaySystem
        """
        self._downstream_displays.append(display)

    def load_flows(self, reload: bool = False) -> None:
        """
        Load data flows.

        :param reload: Whether to force a reload, defaults to False
        :type reload: bool, optional
        """
        if self._data is not None:
            self._data.load_flows()
        self.populate_display()

    def save_flows(self) -> None:
        """
        Save data flows and update downstream displays.
        """
        if self._data is not None:
            self._data.save_flows()
        for ds in self._downstream_displays:
            ds.load_flows()
            ds.set_index(self.get_index())
            ds.populate_display()

    def load_input_flows(self) -> None:
        """
        Load input data flows.
        """
        if self._data is not None:
            self._data.load_input_flows()

    def load_output_flows(self) -> None:
        """
        Load output data flows.
        """
        if self._data is not None:
            self._data.load_output_flows()

    def populate_display(self) -> None:
        """
        Populate the display with current data.
        """
        self._widgets.refresh()

    def value_updated(self):
        """
        Handle updates when a value changes.
        """
        pass
