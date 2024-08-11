# lynguine


![Tests](https://github.com/lawrennd/lynguine/actions/workflows/python-tests.yml/badge.svg)


[![codecov](https://codecov.io/gh/lawrennd/lynguine/branch/main/graph/badge.svg?token=YOUR_CODECOV_TOKEN)](https://codecov.io/gh/lawrennd/lynguine)

The `lynguine` library is a library based on DOA principles for managing data. It provides these capabilities to support other libraries like `lamd` and `referia`.

To install use

```bash
%pip install lynguine
```

The softare consists of TK principle parts.

### Config 

First `config` which consists of `interface` and `context`. 

`context` defines the `Context` object which is used to store information about the context, such as machine type etc. On the other hand`interface` defines the `Interface` object that's used for defining inputs and outputs which defines connections to other 'black box processes'. 

#### A short example

The local context can be loaded in using the following command.
```
import lynguine as ln

ctxt = ln.config.context.Context()
```

### Interface

The `interface` module contains the key structure of `lynguine`. It specifies incoming and outgoing flows, as well as computational operations. Each flow is specified in the following form.

```yaml
input:
  source:
```

There are different forms of flow that can be considered. The `input` flow will not be modified and has a different entry for each unique `index` value. The `constants` flow also cannot be modified, but has a single value that is returned regardless of index. 

Modifiable flows include `output` which has a uniquely indexed value for each column of the output. `parameters` which has a single value returned regardless of index and `series` which has a series of values (in the sense of `pd.Series`) for each unique index. The series has an additional `selector` that must be specified to return a unique entry from the series. 

#### `series`

What's the point in having a series? It can be useful if there's e.g. a time series or another set of values associated with the index.

#### Preprocessing

Preprocessing can be done with a compute field.

```yaml
input:
  compute:
    field: ColumnName0
    function: computeFunction
    args:
      arg1: argument1
      arg2: argument2
    row_args:
      arg3: ColumnName1
```

Often the data will be stored in another file (csv, excel, yaml etc) but sometimes it's convenient to store it as a `local` in a field calld 'data'. In the next example we do this to illustrate how the `compute` capability can be used to augment the file. Here two fields are added, the full name (used as an index) and today's date as an access date.

```python
import yaml
from lynguine.config.interface import Interface
from lynguine.assess.data import CustomDataFrame

# Let's assume this is the text stored in the interface file
yaml_text = """input:
  type: local
  index: name
  add_columns:  # These columns are added if they aren't present.
  - prefix
  - suffix
  ignore_columns: # These columns are ignored even if they're present
  - email
  rename_columns:
    family: familyName
    given: givenName
  data:
  - family: Xing
    given: Pei
    email: pei@uni-got.ac.de
  - family: Venkatasubramanian
    given: Siva
    email: siva@microserve.com
  - family: Paz Luiz
    given: Miguel
    email: miguel@birkingham.ac.uk
  compute:  # compute is used for preprocessing as data is loaded
  - field: name # the field name is created from this compute command
    function: render_liquid
    args: # keyword arguments to pass to the function
      template: "{% capture index %}{% if prefix %}{{ prefix }} {%endif%}{%if familyName %}{{ familyName }} {%endif%}{% if suffix %}{{ suffix }} {%endif%}{%if givenName %}{{ givenName }}{%endif%}{% endcapture %}{{ index | replace: ' ', '_' | replace: '.', '' }}" # This is a liquid template to create an index from the name
    row_args: # arguments are taken from the same row
      givenName: givenName 
      familyName: familyName
  - field: accessDate
    function: today"""

interface = Interface.from_yaml(yaml_text)

data = CustomDataFrame.from_flow(interface)
print(data)
```

would create a new field `name` which is then used as the index.



### Access

Secondly the software uses the access, assess, address decomposition. Where `access` is used for accessing data and consists of `io` and `download`. `io` allows for reading from and writing to various different file formats such as `json`, `yaml`, `markdown`, `csv`, `xls`, `bibtex`. 

`download` is for accessing resources from the web, such as downloading a specific url.

#### A short example

Perhaps you would like to create a bibtex file from the PMLR proceedings volume 1, Gaussian processes in practice. In the short example below, we use `lynguine` to first download the relevant URL, then we load it in and save as bibtex.

```python
import lynguine
```


### Assess

Assess is about taking the raw data and processing it. Under `assess` `lynguine` provides `data` and `compute`. The `data` module provides a `CustomDataFrame` object that provides access to the data and manipulation capabilities. the `compute` module wraps various compute capabilities for preprocessing and processing the data. 

#### A short example

```python
import lynguine
```

### `compute`

The compute capability allows the user to specify computations that should take place on the data. The format is as follows.

```yaml
compute:
- field: OutputColumnName
  function: 
```


### Util

The `util` module provides various utilities for working with data. They include 

* `dataframe` for operating on data frames. 
* `fake` for generating fake data.
* `files` for interacting with files.
* `html` for working with html.
* `liquid` for working with the liquid template language.
* `talk` for working with Neil's talk format.
* `tex` for working with latex.
* `text` for working with text.
* `yaml` for working with yaml.
* `misc` for other miscellaneous utilities.

### A short example

```python
import lynguine
```

### Tests

The tests are stored in the `tests` subdirectory. They use `pytest`.


#### A short example

If you have poetry installed you can run the tests using

```bash
poetry run pytest 
```

### Why lynguine?

The name comes from the idea that data oriented architecture is like a set of streams of data, like linguine pasta. In Italian the word also means "little toungues" so there's also a connotation of translation between services.
