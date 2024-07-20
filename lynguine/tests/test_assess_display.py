# File: tests/test_display.py

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from lynguine.assess.display import DisplaySystem, WidgetCluster

# WidgetCluster Tests

@pytest.fixture
def widget_cluster():
    return WidgetCluster(name="test_cluster", parent=None)

def test_widget_cluster_init(widget_cluster):
    assert widget_cluster._name == "test_cluster"
    assert widget_cluster._parent is None
    assert not widget_cluster._viewer
    assert isinstance(widget_cluster._widget_dict, dict)
    assert isinstance(widget_cluster._widget_list, list)

def test_widget_cluster_add():
    wc = WidgetCluster(name="test", parent=None)
    mock_widget = Mock()
    wc.add(test_widget=mock_widget)
    assert "test_widget" in wc._widget_list
    assert wc._widget_dict["test_widget"] == mock_widget

def test_widget_cluster_to_dict():
    wc = WidgetCluster(name="test", parent=None)
    mock_widget1 = Mock()
    mock_widget2 = Mock()
    wc.add(widget1=mock_widget1, widget2=mock_widget2)
    result = wc.to_dict()
    assert result == {"widget1": mock_widget1, "widget2": mock_widget2}

def test_widget_cluster_refresh(widget_cluster):
    mock_widget = Mock()
    widget_cluster.add(test_widget=mock_widget)
    widget_cluster.refresh()
    mock_widget.refresh.assert_called_once()

# DisplaySystem Tests

@pytest.fixture
def mock_data():
    return Mock()

@pytest.fixture
def display_system(mock_data):
    return DisplaySystem(data=mock_data, interface=Mock(), system=Mock())

def test_display_system_init(display_system):
    assert display_system._data is not None
    assert display_system._interface is not None
    assert display_system._system is not None
    assert isinstance(display_system._widgets, WidgetCluster)
    assert display_system._downstream_displays == []

def test_display_system_index(display_system, mock_data):
    mock_data.index = pd.Index([1, 2, 3])
    assert display_system.index.equals(pd.Index([1, 2, 3]))

def test_display_system_get_index(display_system, mock_data):
    mock_data.get_index.return_value = 'test_index'
    assert display_system.get_index() == 'test_index'

def test_display_system_set_index(display_system, mock_data):
    with patch.object(display_system, 'populate_display') as mock_populate_display:
        display_system.set_index('new_index')
        mock_data.set_index.assert_called_once_with('new_index')
        mock_populate_display.assert_called_once()

def test_display_system_get_value(display_system, mock_data):
    mock_data.get_value.return_value = 'test_value'
    assert display_system.get_value() == 'test_value'

def test_display_system_set_value(display_system, mock_data):
    with patch.object(display_system, 'value_updated') as mock_value_updated:
        display_system.set_value('new_value')
        mock_data.set_value.assert_called_once_with('new_value')
        mock_value_updated.assert_called_once()

def test_display_system_get_column(display_system, mock_data):
    mock_data.get_column.return_value = 'test_column'
    assert display_system.get_column() == 'test_column'

def test_display_system_set_column(display_system, mock_data):
    display_system.set_column('new_column')
    mock_data.set_column.assert_called_once_with('new_column')

def test_display_system_get_indices(display_system, mock_data):
    mock_data.index = pd.Index([1, 2, 3])
    assert display_system.get_indices().equals(pd.Index([1, 2, 3]))

def test_display_system_add_downstream_display(display_system):
    mock_display = Mock()
    display_system.add_downstream_display(mock_display)
    assert mock_display in display_system._downstream_displays

def test_display_system_load_flows(display_system, mock_data):
    with patch.object(display_system._widgets, 'refresh') as mock_refresh:
        display_system.load_flows()
        mock_data.load_flows.assert_called_once()
        mock_refresh.assert_called_once()

def test_display_system_save_flows(display_system, mock_data):
    mock_downstream = Mock()
    display_system._downstream_displays = [mock_downstream]
    display_system.save_flows()
    assert mock_data.save_flows.called
    assert mock_downstream.load_flows.called
    assert mock_downstream.set_index.called
    assert mock_downstream.populate_display.called

def test_display_system_load_input_flows(display_system, mock_data):
    display_system.load_input_flows()
    assert mock_data.load_input_flows.called

def test_display_system_load_output_flows(display_system, mock_data):
    display_system.load_output_flows()
    assert mock_data.load_output_flows.called

def test_display_system_populate_display(display_system):
    with patch.object(display_system._widgets, 'refresh') as mock_refresh:
        display_system.populate_display()
        assert mock_refresh.called

def test_display_system_value_updated(display_system):
    # This method is empty in the base class, so we just ensure it doesn't raise an exception
    display_system.value_updated()
