# tests/test_assess_data_compute.py
# integrated tests of data and compute

import pytest
import lynguine.assess.data
import lynguine.config.interface
import yaml
import pandas as pd
import numpy as np
import datetime

from deepdiff import DeepDiff


    
@pytest.fixture
def valid_local_data():
    # Return a sample interface object that is valid
    return lynguine.config.interface.Interface({
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

@pytest.fixture
def local_name_inputs():

    input_yaml_text="""input:
  type: local
  index: fullName
  data:
  - familyName: Xing
    givenName: Pei
  - familyName: Venkatasubramanian
    givenName: Siva
  - familyName: Paz Luiz
    givenName: Miguel
  compute:
    field: fullName
    function: render_liquid
    args:
      template: '{{familyName | replace: " ", "-"}}_{{givenName | replace: " ", "-"}}'
    row_args:
      givenName: givenName
      familyName: familyName"""
    # Read in dictionaary from yaml text
    input_dict = yaml.safe_load(input_yaml_text)
    return lynguine.config.interface.Interface(input_dict)

# test from_flow with a valid setting that specifies local data.
def test_from_flow_with_compute(valid_local_data):
    cdf = lynguine.assess.data.CustomDataFrame.from_flow(valid_local_data)
    today = datetime.datetime.now().strftime(format="%Y-%m-%d")
    assert isinstance(cdf, lynguine.assess.data.CustomDataFrame)
    assert cdf == lynguine.assess.data.CustomDataFrame(pd.DataFrame([{'key1': 'value1', 'key2' : 'value2', 'key3': 'value3', 'today' : today}, {'key1': 'value1row2', 'key2' : 'value2row2', 'key3': 'value3row3', 'today' : today}], index=pd.Index(['indexValue', 'indexValue2'], name='index')))
    assert cdf.colspecs == {"input" : ["key1", "key2", "key3", "today"]}


# test from_flow with a valid setting that specifies local data.
def test_from_flow_with_compute_liquid(local_name_inputs):
    cdf = lynguine.assess.data.CustomDataFrame.from_flow(local_name_inputs)
    assert isinstance(cdf, lynguine.assess.data.CustomDataFrame)
    assert cdf == lynguine.assess.data.CustomDataFrame(pd.DataFrame([{'familyName': 'Xing', 'givenName' : 'Pei'}, {'familyName': 'Venkatasubramanian', 'givenName' : 'Siva'}, {'familyName': 'Paz Luiz', 'givenName' : 'Miguel'}], index=pd.Index(['Xing_Pei', 'Venkatasubramanian_Siva', 'Paz-Luiz_Miguel'], name='fullName')))
    assert cdf.colspecs == {"input" : ["familyName", "givenName"]}
