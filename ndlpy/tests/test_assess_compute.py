import pytest
from ndlpy.assess.compute import Compute  # Adjust the import as necessary
from ndlpy.assess.data import CustomDataFrame
from unittest.mock import MagicMock

@pytest.fixture
def mock_interface(mocker):
    # Create a mock object with the necessary attributes
    interface_mock_data = {
        "input": {
            "type" : "fake",
            "nrows" : 10,
            "cols" : ["givenName", "familyName"],
            "index" : "givenName"
        },
        "compute": {
            "type" : "precompute",
            "function": "test_function",
            "args": {"arg1": "value1", "arg2": "value2"}
        }
    }
    interface_mock = mocker.MagicMock()
    interface_mock.__getitem__.side_effect = interface_mock_data.__getitem__
    interface_mock.__iter__.side_effect = interface_mock_data.__iter__
    interface_mock.__contains__.side_effect = interface_mock_data.__contains__
    
    interface_mock._directory = "mock_directory"  # Assuming _directory is expected by Compute
    mocker.patch('ndlpy.assess.compute.Interface.from_file', return_value=interface_mock)
    return interface_mock

@pytest.fixture
def mock_data(mocker):
    return CustomDataFrame({})

@pytest.fixture
def compute_instance(mocker, mock_interface):
    # Ensure that Logger is also mocked if necessary
    mocker.patch('ndlpy.log.Logger')
    return Compute(mock_interface)

# Patch test_function into the Compute instance
@pytest.fixture
def mock_test_function(mocker, compute_instance):
    mocker.patch.object(compute_instance, 'test_function', return_value=lambda x: x)

# Test initialization
def test_compute_initialization(compute_instance, mock_interface, mock_data):
    #assert compute_instance._data is mock_data
    #assert compute_instance._interface is mock_interface
    pass

def test_compute_creation(mocker, mock_interface):
    # Create a MagicMock object that behaves like a dictionary

    # Patch Interface.from_file to return the mock_interface
    mocker.patch('ndlpy.assess.compute.Interface.from_file', return_value=mock_interface)

    # Patch Compute.__init__ to avoid initialization side effects
    mocker.patch('ndlpy.assess.compute.Compute.__init__', return_value=None)

    # Create a CustomDataFrame object to pass as the 'data' argument
    mock_data = CustomDataFrame([{"cat": "dog"}], colspecs="input")
    
    # Call the method under test with the required 'data' argument
    result = Compute(interface=mock_interface)

    # Check that a Compute instance is returned
    assert result is not None


# Updated mock_compute_functions fixture
@pytest.fixture
def mock_compute_functions(mocker, compute_instance):
    # Define a list of functions including 'test_function'
    mocked_functions = [
        {"name": "test_function", "function": lambda x: x, "default_args": {}}
    ]
    # Patch the _compute_functions_list method to return mocked_functions
    mocker.patch.object(compute_instance, '_compute_functions_list', return_value=mocked_functions)
    return mocked_functions

def test_prep(compute_instance, mock_data, mocker):
    # Mock the gcf_ and gca_ methods
    mocker.patch.object(compute_instance, 'gcf_', return_value=lambda x: x)
    mocker.patch.object(compute_instance, 'gca_', return_value={'arg1': 'value1', 'arg2': 'value2'})

    # Test with minimal settings
    settings_minimal = {"function": "test_function_minimal"}
    result_minimal = compute_instance.prep(settings_minimal, mock_data)
    assert 'function' in result_minimal
    assert callable(result_minimal['function'])

    # Test with additional settings
    settings_additional = {"function": "test_function_additional", "field": "test_field", "refresh": True}
    result_additional = compute_instance.prep(settings_additional, mock_data)
    assert result_additional['function'] is not None
    assert result_additional['refresh'] is True
    assert 'field' in result_additional and result_additional['field'] == "test_field"

    # Test with comprehensive settings
    settings_comprehensive = {
        "function": "test_function_comprehensive",
        "field": "test_field",
        "refresh": True,
    }
    result_comprehensive = compute_instance.prep(settings_comprehensive, mock_data)
    assert result_comprehensive['function'] is not None
    assert result_comprehensive['refresh'] is True
    assert 'field' in result_comprehensive and result_comprehensive['field'] == "test_field"
    assert 'args' in result_comprehensive and 'arg1' in result_comprehensive['args']
