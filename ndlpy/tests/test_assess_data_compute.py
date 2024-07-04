# tests/test_assess_data_compute.py
# integrated tests of data and compute

import pytest
import ndlpy.assess.data
import ndlpy.config.interface
import pandas as pd
import numpy as np

from deepdiff import DeepDiff


    
@pytest.fixture
def valid_local_data():
    # Return a sample interface object that is valid
    return ndlpy.config.interface.Interface({
        "input":
        {
            "type" : "local",
            "index" : "index",
            "select" : "indexValue2",
            "data" : [
            {
                'index': 'indexValue',
                'key1': 'value1',
                'key2': 'value2',
                'key3': 'value3',
            },
            {
                'index': 'indexValue2',
                'key1': 'value1row2',
                'key2': 'value2row2',
                'key3': 'value3row2',
            }],
            "compute" : {
                "field" : "today",
                "function" : "today",
                "args" : {
                    "format" : "%d %B %Y",
                    }
                }
        }
            
    })

# test from_flow with a valid setting that specifies local data.
def test_from_flow_with_compute(valid_local_data):
    cdf = ndlpy.assess.data.CustomDataFrame.from_flow(valid_local_data)
    today = '04 July 2024'
    assert isinstance(cdf, ndlpy.assess.data.CustomDataFrame)
    assert cdf == ndlpy.assess.data.CustomDataFrame(pd.DataFrame([{'key1': 'value1', 'key2' : 'value2', 'key3': 'value3', 'today' : today}, {'key1': 'value1row2', 'key2' : 'value2row2', 'key3': 'value3row3', 'today' : today}], index=pd.Index(['indexValue', 'indexValue2'], name='index')))
    assert cdf.colspecs == {"input" : ["key1", "key2", "key3", "today"]}

