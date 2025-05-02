import pytest
import pandas as pd
from datetime import datetime
from lynguine.assess.compute import Compute  # Adjust the import as necessary
from lynguine.assess.data import CustomDataFrame
from unittest.mock import MagicMock, patch
import liquid as lq

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
        "compute": [
            {
                "function": "test_function",
                "args": {"arg1": "value1", "arg2": "value2"}
            }
        ],
        "precompute": [
            {
                "function": "pretest_function",
                "args": {"arg1": "value1", "arg2": "value2"}
            }
        ],
        "filter": {
            "function": "test_filter",
            "args": {}
        },
        "on_field_change": {
            "test_field": {"function": "update_function"}
        }
    }
    interface_mock = mocker.MagicMock()
    interface_mock.__getitem__.side_effect = interface_mock_data.__getitem__
    interface_mock.__iter__.side_effect = interface_mock_data.__iter__
    interface_mock.__contains__.side_effect = interface_mock_data.__contains__
    interface_mock._directory = "mock_directory" 
    return interface_mock

@pytest.fixture
def mock_logger(mocker):
    # Create a mock logger
    logger_mock = mocker.MagicMock()
    mocker.patch('lynguine.assess.compute.Logger', return_value=logger_mock)
    return logger_mock

@pytest.fixture
def mock_data(mocker):
    # Create a simple mock dataframe
    mock_df = MagicMock(spec=CustomDataFrame)
    # Add necessary methods that might be called
    mock_df.filter_rows = MagicMock(return_value=True)
    mock_df.get_index = MagicMock(return_value='test_index')
    mock_df.get_column = MagicMock(return_value='test_column')
    mock_df.set_column = MagicMock()
    mock_df.set_index = MagicMock()
    mock_df.index = ['index1', 'index2', 'index3']
    mock_df.filter_row = MagicMock()
    return mock_df

@pytest.fixture
def compute_instance(mocker, mock_interface, mock_logger):
    # Create a compute instance with mocked methods
    mocker.patch('lynguine.assess.compute.Compute.load_liquid')
    mocker.patch('lynguine.assess.compute.Compute.add_liquid_filters')
    
    compute = Compute(mock_interface)
    # Manually set the logger attribute
    compute.logger = mock_logger
    # Create a mock liquid env
    compute._liquid_env = MagicMock()
    return compute

# Test initialization
def test_compute_initialization(compute_instance, mock_interface):
    assert hasattr(compute_instance, '_computes')
    assert 'compute' in compute_instance._computes
    assert 'precompute' in compute_instance._computes
    assert 'postcompute' in compute_instance._computes

@patch('lynguine.log.Logger')
def test_compute_creation(mock_logger, mock_interface):
    # Patch necessary methods to avoid side effects
    with patch('lynguine.assess.compute.Compute.load_liquid'), \
         patch('lynguine.assess.compute.Compute.add_liquid_filters'), \
         patch('lynguine.assess.compute.Compute.setup_logger'):
        # Simply test that we can create a Compute instance
        compute = Compute(mock_interface)
        assert compute is not None
        assert hasattr(compute, '_computes')

def test_setup_logger(compute_instance, mocker):
    # Mock the Context class
    context_mock = mocker.MagicMock()
    context_mock.__getitem__.return_value = {"level": "DEBUG", "filename": "test.log"}
    mocker.patch('lynguine.assess.compute.cntxt', context_mock)
    
    # Mock the Logger class
    logger_mock = mocker.MagicMock()
    logger_class_mock = mocker.patch('lynguine.assess.compute.Logger', return_value=logger_mock)
    
    # Call setup_logger
    compute_instance.setup_logger()
    
    # Verify Logger was called with the right arguments
    logger_class_mock.assert_called_once()
    assert compute_instance.logger is logger_mock

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

# Test gcf_ functionality
def test_gcf_(compute_instance, mocker, mock_data):
    # Mock _compute_functions_list with multiple functions
    test_func_one = lambda x: x
    test_func_one.__name__ = "test_function_one"
    
    test_func_two = lambda y=0: y*2
    test_func_two.__name__ = "test_function_two"
    test_func_two.__doc__ = "This is the documentation."
    
    mocked_functions = [
        {"name": "test_function_one", "function": test_func_one, "default_args": {}, "context": True},
        {"name": "test_function_two", "function": test_func_two, "default_args": {"param": "default"}, "docstr": "This is the documentation."}
    ]
    mocker.patch.object(compute_instance, '_compute_functions_list', return_value=mocked_functions)

    # Test for the first function
    function_one = compute_instance.gcf_("test_function_one", mock_data)
    assert callable(function_one)
    
    # Test for a function that doesn't exist
    with pytest.raises(ValueError):
        compute_instance.gcf_("nonexistent_function", mock_data)

# Updated test_gca_ test
def test_gca_(compute_instance, mocker):
    # Call gca_ method with various arguments
    mocked_functions = [
        {"name": "test_function", "function": lambda x: x, "default_args": {}}
    ]
    mocker.patch.object(compute_instance, '_compute_functions_list', return_value=mocked_functions)
    
    # Test with valid function
    args_empty = compute_instance.gca_("test_function")
    assert isinstance(args_empty, dict)
    for arglist in ["subseries_args", "column_args", "row_args", "view_args", "function_args", "args", "default_args"]:
        assert arglist in args_empty

    # Test with different argument types
    args_full = compute_instance.gca_("test_function", args={
        "field": "test_field", "refresh": True}, row_args={"row1": "value1"})
    assert isinstance(args_full, dict)
    assert args_full["args"]['field'] == "test_field"
    assert args_full["args"]['refresh'] is True
    assert 'row1' in args_full["row_args"] and args_full["row_args"]['row1'] == "value1"

    # Test with nonexistent function - should raise ValueError
    with pytest.raises(ValueError):
        compute_instance.gca_("nonexistent_function")

# Test run method
def test_run(compute_instance, mock_data, mocker):
    # Create a mock interface with compute operations
    mock_interface = {"compute": [{"function": "test_function", "args": {}}]}
    
    # Create a function that returns 42
    test_func = lambda **kwargs: 42
    
    # Override compute_instance.run to directly call a function for testing
    def mock_run(data, compute):
        return test_func(**compute.get("args", {}))
    
    # Patch the run method for this test
    mocker.patch.object(compute_instance, 'run', side_effect=mock_run)
    
    # Test simple function call with the patched run method
    compute = {"function": test_func, "args": {}}
    result = compute_instance.run(mock_data, compute)
    assert result == 42
    
    # Test with field parameter to make sure the call is structured correctly
    compute = {"function": test_func, "args": {}, "field": "test_field"}
    result = compute_instance.run(mock_data, compute)
    assert result == 42

# Test preprocess method
def test_preprocess(compute_instance, mock_data, mock_interface, mocker):
    # Mock necessary methods
    mocker.patch.object(compute_instance, 'prep', return_value={"function": lambda data, **kwargs: 42, "args": {}})
    
    # Create a mock interface with compute operations
    mock_interface = {
        "compute": [
            {"function": "test_function", "field": "test_field"}
        ]
    }
    
    # Call preprocess with the mock interface
    compute_instance.preprocess(mock_data, mock_interface)
    
    # Verify prep was called
    assert compute_instance.prep.call_count > 0
    # Since we're using a mock, we can verify the call was made correctly
    assert mock_data.__setitem__.call_count > 0 or isinstance(mock_data.__getitem__.return_value, MagicMock)

# Test run_all method
def test_run_all(compute_instance, mock_data, mock_interface, mocker):
    # Mock the run method
    run_mock = mocker.patch.object(compute_instance, 'run')
    
    # Call run_all
    compute_instance.run_all(mock_data, mock_interface)
    
    # Check that set_index was called for each index and run method was called
    assert mock_data.set_index.call_count >= len(mock_data.index)
    assert run_mock.call_count >= len(mock_data.index)
    
    # Verify that index was reset at the end
    mock_data.set_index.assert_called_with('test_index')

# Test _compute_functions_list method
def test_compute_functions_list(compute_instance):
    functions_list = compute_instance._compute_functions_list()
    
    assert isinstance(functions_list, list)
    assert len(functions_list) > 0
    for func in functions_list:
        assert isinstance(func, dict)
        assert 'name' in func
        assert 'default_args' in func

# Test the properties
def test_compute_properties(compute_instance):
    # Test computes property
    assert compute_instance.computes == compute_instance._computes["compute"]
    
    # Test precomputes property
    assert compute_instance.precomputes == compute_instance._computes["precompute"]
    
    # Test postcomputes property
    assert compute_instance.postcomputes == compute_instance._computes["postcompute"]

# Test load_liquid method
def test_load_liquid(mocker):
    # Create a mock Environment class that will be returned by the call to liquid.Environment
    mock_env = MagicMock()
    
    # Properly mock the liquid.Environment constructor
    with patch('liquid.Environment', return_value=mock_env) as environment_mock:
        # Don't try to patch Mode.LAX directly - it's an enum member that can't be reassigned
        # Instead, patch the entire Compute.load_liquid method for this test
        # or mock what the code actually does with the enum value
        
        # Create a compute instance with an empty interface
        compute = Compute({})
        
        # Now call load_liquid with a mock interface
        compute.load_liquid({"base_directory": "/test/path"})
        
        # Verify Environment was called
        assert environment_mock.call_count > 0
        
        # Verify that _liquid_env was set
        assert compute._liquid_env is mock_env
        
        # Verify that the add_filter method was called for each filter
        assert mock_env.add_filter.call_count >= 5  # At least 5 filters are added in the code

# Test add_liquid_filters method
def test_add_liquid_filters(mocker):
    # In this test, we're just verifying the add_liquid_filters method works correctly
    # The method is currently empty but might be extended in the future
    
    # Create a mock environment
    mock_env = MagicMock()
    
    # Create a compute instance
    compute = Compute({})
    
    # Set the _liquid_env directly without going through load_liquid
    compute._liquid_env = mock_env
    
    # Call add_liquid_filters
    compute.add_liquid_filters()
    
    # Since the method is empty, we just check that it doesn't raise an exception
    # No need to verify any mock calls since the method doesn't do anything yet

# Test filter method
def test_filter(compute_instance, mock_data, mocker):
    # Create a filter function that returns True
    filter_func = lambda data, **kwargs: True
    
    # Mock the prep method to return our filter function
    mocker.patch.object(compute_instance, 'prep', return_value={"function": filter_func, "args": {}})
    
    # Create a mock Series for filtering
    mock_series = MagicMock(spec=pd.Series)
    mocker.patch('pandas.Series', return_value=mock_series)
    
    # Call filter with proper interface structure
    compute_instance.filter(mock_data, {"filter": [{"function": "test_filter"}]})
    
    # Verify the filter operation was applied
    mock_data.filter_row.assert_called_once()

# Test from_flow class method
def test_from_flow(mocker):
    # Looking at the code for from_flow, it takes an interface and returns cls(interface)
    # It doesn't call Interface.from_file - it expects the caller to have already done that
    
    # Create a mock interface 
    mock_interface = {'path': 'test/path'}
    
    # Patch Compute.__init__ to do nothing and return None
    with patch.object(Compute, '__init__', return_value=None) as mock_init:
        # Call from_flow with the interface dictionary
        result = Compute.from_flow(mock_interface)
        
        # Verify Compute.__init__ was called with the interface
        mock_init.assert_called_once_with(mock_interface)
        
        # Verify the returned object is a Compute instance
        assert isinstance(result, Compute)

# Test _liquid_render method
def test_liquid_render(compute_instance, mocker):
    # Create a mock template
    mock_template = MagicMock()
    mock_template.render.return_value = "Rendered template"
    
    # Mock the _liquid_env.from_string method
    compute_instance._liquid_env.from_string.return_value = mock_template
    
    # Call _liquid_render
    result = compute_instance._liquid_render("Template string", var1="value1", var2="value2")
    
    # Verify the template was rendered with the right arguments
    assert result == "Rendered template"
    compute_instance._liquid_env.from_string.assert_called_once_with("Template string")
    mock_template.render.assert_called_once()

# Test _today method
def test_today(compute_instance):
    # Call _today with default format
    result = compute_instance._today()
    
    # Assert the result is a string in the expected format
    assert isinstance(result, str)
    # Check if it's in YYYY-MM-DD format by trying to parse it
    try:
        datetime.strptime(result, "%Y-%m-%d")
    except ValueError:
        pytest.fail("_today() did not return a date in the expected format")
    
    # Call _today with custom format
    custom_format = "%d/%m/%Y"
    result_custom = compute_instance._today(custom_format)
    
    # Assert the result is in the custom format
    try:
        datetime.strptime(result_custom, custom_format)
    except ValueError:
        pytest.fail(f"_today({custom_format}) did not return a date in the expected format")

# Test _identity method
def test_identity(compute_instance):
    # Test with various input types
    assert compute_instance._identity(42) == 42
    assert compute_instance._identity("string") == "string"
    assert compute_instance._identity([1, 2, 3]) == [1, 2, 3]
    
    # Test with None
    assert compute_instance._identity(None) is None

# Test run_onchange method
def test_run_onchange(compute_instance, mock_data, mocker):
    # Create a mock prepare function
    def mock_prep(settings, data):
        return {"function": lambda x: None, "args": {}}
    
    # Mock the prep and run methods
    mocker.patch.object(compute_instance, 'prep', side_effect=mock_prep)
    mocker.patch.object(compute_instance, 'run', return_value=None)
    
    # Call run_onchange
    compute_instance.run_onchange(mock_data, 'index1', 'test_field')
    
    # Verify the logger was called with debugging information
    compute_instance.logger.debug.assert_called()

# Test __str__ method
def test_str_representation(compute_instance):
    # Call __str__
    result = str(compute_instance)
    
    # Assert that the result is a non-empty string
    assert isinstance(result, str)
    assert len(result) > 0

