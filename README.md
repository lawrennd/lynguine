# lynguine


![Tests](https://github.com/lawrennd/lynguine/actions/workflows/python-tests.yml/badge.svg)
[![Documentation](https://github.com/lawrennd/lynguine/actions/workflows/docs.yml/badge.svg)](https://lawrennd.github.io/lynguine/)
[![ReadTheDocs](https://readthedocs.org/projects/lynguine/badge/?version=latest)](https://lynguine.readthedocs.io/en/latest/)


[![codecov](https://codecov.io/gh/lawrennd/lynguine/branch/main/graph/badge.svg?token=YOUR_CODECOV_TOKEN)](https://codecov.io/gh/lawrennd/lynguine)

The `lynguine` library is a library based on DOA principles for managing data. It provides these capabilities to support other libraries like `lamd` and `referia`.

It is an attempt to implement the emerging linguine specification, <https://github.com/lawrennd/linguine.git>.

## Quick Links

- [Documentation](https://lynguine.readthedocs.io/)
- [Code Improvement Plans](cip/)
- [Project Backlog](backlog/)
- [Security Documentation](https://lynguine.readthedocs.io/en/latest/security/)

## Security

Lynguine includes enterprise-grade secure credential management for API keys, OAuth tokens, and other sensitive data. Features include:

- 🔒 **Encrypted Storage** - AES-256 encryption for credentials at rest
- 🔑 **Multiple Backends** - Environment variables, encrypted files, or cloud vaults
- 👥 **Access Control** - Role-based permissions and rate limiting
- 📊 **Audit Logging** - Comprehensive security event tracking
- 🔄 **Easy Migration** - Tools to migrate from plain-text credentials

**Quick Start**: See the [Security User Guide](docs/security/USER_GUIDE.md) for setup instructions and examples.

**Technical Details**: See [CIP-0005](cip/cip0005.md) for the complete security architecture.

## Installation

To install use:

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

#### Working with Columns in CustomDataFrame

CustomDataFrame supports dynamic column creation and management:

```python
import pandas as pd
from lynguine.assess.data import CustomDataFrame

# Create a basic dataframe
df = CustomDataFrame(pd.DataFrame({'A': [1, 2, 3]}, index=['a', 'b', 'c']))

# Add columns using direct assignment (default: cache type)
df['B'] = [4, 5, 6]

# Add columns with explicit type using add_column()
df.add_column('output_col', [7, 8, 9], colspec='output')  # Saved to file
df.add_column('cache_col', [10, 11, 12])  # Temporary data

# Remove columns
df.drop_column('cache_col')

# Check column types
print(df.get_column_type('output_col'))  # 'output'
```

**Column Types (colspecs):**
- `input`: Read-only source data
- `output`: Mutable data written to files
- `cache`: Temporary intermediate calculations
- `parameters`: Global values without index
- `series`: Data with multiple rows per index

For detailed documentation, see the [Column Management Guide](https://lynguine.readthedocs.io/en/latest/getting_started/column_management.html).

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

The name comes from the idea that data oriented architecture is like a set of streams of data, like linguine pasta. In Italian the word also means "little tongues" so there's also a connotation of translation between services.

## Linguine Configuration File Format

A Linguine configuration file is a YAML file used to define the structure and behavior of data-oriented interfaces. These files specify the inputs, outputs, and various operations to be performed on the data. The configuration is hierarchical, allowing one interface to inherit from another.

### Characteristics

1. **Hierarchical Structure**: Interfaces can inherit from other interfaces, allowing for reusable and extendable configurations.
2. **Data Specification**: Inputs, outputs, and other data-related specifications are clearly defined.
3. **Operations**: The file can specify operations such as computing and reviewing data.
4. **Environment Variable Expansion**: Environment variables can be used within the configuration and will be expanded at runtime.

### Required Entries

A typical Linguine configuration file contains the following entries:

#### `input`
Specifies the input data for the interface. This can include mappings and columns.

- **Type**: `dict`
- **Keys**:
  - `type`: The type of input (e.g., `hstack` for horizontal stacking).
  - `index`: The index of the input data.
  - `mapping`: A dictionary mapping input fields to their corresponding values.
  - `specifications`: A list of specifications for the input data.

#### `output`

Specifies the output data for the interface. This can include mappings and columns.

- **Type**: `dict`
- **Keys**:
  - `type`: The type of output (e.g., `hstack` for horizontal stacking).
  - `index`: The index of the output data.
  - `mapping`: A dictionary mapping output fields to their corresponding values.
  - `specifications`: A list of specifications for the output data.

#### `compute`

Defines the computations to be performed on the data.

- **Type**: `list`
- **Items**: Each item is a dictionary specifying a computation.
  - `field`: The field to be computed.
  - `operation`: The operation to be performed.

#### `review`

Specifies the fields to be reviewed.

- **Type**: `list`
- **Items**: Each item is a dictionary specifying a review operation.
  - `field`: The field to be reviewed.
  - `operation`: The review operation.

#### `cache`

Specifies the cache columns.

- **Type**: `dict`
- **Keys**:
  - `columns`: A list of columns to be cached.

#### `constants`

Defines constant values to be used in the interface.

- **Type**: `dict`
- **Keys**:
  - `type`: The type of constants (e.g., `hstack` for horizontal stacking).
  - `specifications`: A list of specifications for the constants.

#### `parameters`

Specifies parameters for the interface.

- **Type**: `dict`
- **Keys**:
  - `type`: The type of parameters (e.g., `hstack` for horizontal stacking).
  - `specifications`: A list of specifications for the parameters.

#### `inherit`

Specifies inheritance from another interface.

- **Type**: `dict`
- **Keys**:
  - `directory`: The directory of the parent interface.
  - `filename`: The filename of the parent interface.
  - `ignore`: A list of keys to ignore from the parent interface.
  - `append`: A list of keys
  
---

## Accessing Data in Linguine

The "access" phase in the Linguine framework is about obtaining an electronic version of the data. The `io.py` file provides the capability to access data in various formats. These formats can be specified in the Linguine interface file. Below are the details on how to specify different data formats in the interface file.

### Data Formats

Linguine supports various data formats, each requiring specific information to be accessed. The following sections describe the required entries for each supported data format.

#### CSV

To access data from a CSV file, specify the following details:

```yaml
type: csv
filename: path/to/file.csv
header: 0  # Optional, default is 0
delimiter: ","  # Optional, default is ","
quotechar: '"'  # Optional, default is '"'
dtypes:  # Optional, specify data types for columns
  - field: column_name
    type: str_type
```

#### Excel

To access data from an Excel spreadsheet, specify the following details:

```yaml
type: excel
filename: path/to/file.xlsx
sheet: Sheet1  # Optional, default is "Sheet1"
header: 0  # Optional, default is 0
dtypes:  # Optional, specify data types for columns
  - field: column_name
    type: str_type
```

#### JSON

To access data from a JSON file, specify the following details:

```yaml
type: json
filename: path/to/file.json
```

#### YAML

To access data from a YAML file, specify the following details:

```yaml
type: yaml
filename: path/to/file.yaml
```

A top-level **mapping** loads as a **single-row** table (useful for `constants` / parameters). All-scalar maps keep an explicit index (default `value`). Maps that mix scalars with nested dicts or lists (for example a Jekyll `_config.yml`) become one row with nested values as cell objects. A **sequence of mappings** remains a multi-row table.

Optional `fields` projects the document before the row is formed — top-level keys, dotted paths, or renamed projections via `path` / `liquid`:

```yaml
type: yaml
filename: _config.yml
fields:
  - github_username
  - field: github_repository
    path: ghub.repository
  - field: edit_base
    liquid: "https://github.com/{{github_username}}/{{ghub.repository}}"
```

#### Markdown

To access data from a Markdown file, specify the following details:

```yaml
type: markdown
filename: path/to/file.md
```

#### BibTeX

To access data from a BibTeX file, specify the following details:

```yaml
type: bibtex
filename: path/to/file.bib
```

#### Google Sheets

To access data from a Google Sheet, specify the following details:

```yaml
type: gsheet
filename: Google_Sheet_Name
sheet: Sheet1  # Optional, default is "Sheet1"
header: 0  # Optional, default is 0
dtypes:  # Optional, specify data types for columns
  - field: column_name
    type: str_type
```

#### Directory of Files

Directory readers allocate **one row per matched file**. Choose a typed reader for the file format (each has a default glob):

| Type | Default glob | Reader |
|------|--------------|--------|
| `yaml_directory` | `*.yml` | YAML mappings |
| `json_directory` | `*.json` | JSON mappings |
| `markdown_directory` | `*.md` | Markdown (+ front matter) |
| `bibtex_directory` | `*.bib` | BibTeX |
| `docx_directory` | `*.docx` | Word documents |
| `directory` | `*` | Plain / auto by extension |
| `meta_directory` | `*` | Sidecar YAML meta files |

Shared options on each `source` entry (or, for `recursive` / `fields`, on the top-level details when omitted per source):

```yaml
type: yaml_directory
source:
  - directory: path/to/directory
    glob: "*.yml"           # Optional; defaults per type (see table)
    regexp: "^cfg_.*\\.yml$"  # Optional; filter on basename after expand
    recursive: false          # Optional; default false (flat discovery)
    fields:                   # Optional; project mapping keys before normalize
      - title
      - description
store_fields:                 # Optional; path metadata columns (defaults shown)
  directory: sourceDirectory
  filename: sourceFilename
  root: sourceRoot
```

**Defaults preserve existing behaviour:** omit `recursive` (or set `false`) for flat globs only; omit `fields` for full-document `json_normalize`. The pattern `**` is meaningful only when `recursive: true`. Field projection applies to **mapping-valued** readers (YAML/JSON/etc.); non-mapping payloads warn and yield nulls for the listed fields.

Nested catalog example (opt-in recursive discovery + lean rows):

```yaml
type: yaml_directory
source:
  - directory: catalogs
    glob: "**/config.yml"
    recursive: true
fields:
  - title
  - description
  - date
store_fields:
  directory: sourceDirectory
  filename: sourceFilename
  root: sourceRoot
```

**Release note (CIP-000F):** `recursive` and `fields` are opt-in. Existing directory configs without these keys behave as before (non-recursive, full-document rows). Relative source directories no longer double-join glob matches.

To present directory rows as **one wide data point** (index-augmented column names) instead of a multi-row table, wrap the directory source in [`wide_flatten`](#wide-flatten-wide_flatten) (CIP-0010).

#### Local Data

To access data directly from the details file, specify the following details:

```yaml
type: local
data:
  - column1: value1
    column2: value2
  - column1: value3
    column2: value4
```

#### Fake Data

To access artificially generated data, specify the following details:

```yaml
type: fake
nrows: 100  # Number of rows to generate
cols:  # Specify columns and their types
  column1: random_string
  column2: random_integer
```

### Example Configuration

Here is an example configuration for accessing multiple data formats:

```yaml
input:
  type: hstack
  specifications:
    - type: csv
      filename: data/file1.csv
      header: 0
      delimiter: ","
    - type: excel
      filename: data/file2.xlsx
      sheet: Sheet1
    - type: json
      filename: data/file3.json
    - type: yaml
      filename: data/file4.yaml
    - type: markdown
      filename: data/file5.md
    - type: bibtex
      filename: data/file6.bib
    - type: gsheet
      filename: Google_Sheet_Name
      sheet: Sheet1
    - type: yaml_directory
      source:
        - directory: data/directory
          glob: "*.yml"
      store_fields:
        directory: sourceDirectory
        filename: sourceFilename
        root: sourceRoot
    - type: local
      data:
        - column1: value1
          column2: value2
        - column1: value3
          column2: value4
    - type: fake
      nrows: 100
      cols:
        column1: random_string
        column2: random_integer
```

This configuration specifies how to access data from various sources, including CSV, Excel, JSON, YAML, Markdown, BibTeX, Google Sheets, directories, local data, and fake data. Each data format has its own set of required and optional entries to ensure the data is accessed correctly.


## Stacking Data in Linguine

Linguine provides mechanisms to stack `input` data either horizontally (`hstack`) or vertically (`vstack`). These operations allow you to combine multiple data sources into a single entity.

### Horizontal Stacking (`hstack`)

Horizontal stacking (`hstack`) combines data sources by aligning them side-by-side based on a common key or index. This is useful when you have different sets of columns for the same set of rows.

#### Required Entries

- **type**: Must be set to `hstack`.
- **specifications**: A list of data sources to be horizontally stacked.
  - **on**: The column or index to join on. Default is `index`.
  - **how**: The type of join to perform (`left`, `right`, `outer`, `inner`). Default is `left`.
  - **lsuffix**: Suffix to use for overlapping columns from the left data source. Default is an empty string.
  - **rsuffix**: Suffix to use for overlapping columns from the right data source. Default is `_right`.

#### Example

```yaml
type: hstack
specifications:
  - type: csv
    filename: data/file1.csv
    on: id
    how: left
  - type: excel
    filename: data/file2.xlsx
    sheet: Sheet1
    on: id
    how: left
    lsuffix: _left
    rsuffix: _right
```

In this example, data from `file1.csv` and `file2.xlsx` are horizontally stacked based on the `id` column.

### Vertical Stacking (`vstack`)

Vertical stacking (`vstack`) combines data sources by aligning them one below the other. This is useful when you have the same set of columns for different sets of rows.

#### Required Entries

- **type**: Must be set to `vstack`.
- **specifications**: A list of data sources to be vertically stacked.
- **reset_index**: Whether to reset the index after stacking. Default is `False`.

#### Example

```yaml
type: vstack
specifications:
  - type: csv
    filename: data/file1.csv
  - type: excel
    filename: data/file2.xlsx
    sheet: Sheet1
reset_index: True
```

In this example, data from `file1.csv` and `file2.xlsx` are vertically stacked, and the index is reset after stacking.

### Combining Stacks

You can combine `hstack` and `vstack` operations to create complex data structures. For example, you can first horizontally stack multiple data sources and then vertically stack the result with another data source.

#### Example

```yaml
type: vstack
specifications:
  - type: hstack
    specifications:
      - type: csv
        filename: data/file1.csv
        on: id
        how: left
      - type: excel
        filename: data/file2.xlsx
        sheet: Sheet1
        on: id
        how: left
  - type: csv
    filename: data/file3.csv
reset_index: True
```

In this example, data from `file1.csv` and `file2.xlsx` are first horizontally stacked based on the `id` column. The result is then vertically stacked with data from `file3.csv`, and the index is reset after stacking.

### Wide Flatten (`wide_flatten`) and wide views

Guided by the [Authoritative Store and Views](tenets/lynguine/authoritative-store-and-views.md) tenet:

| Pattern | What | When |
|---------|------|------|
| **A (preferred for editable data)** | Tall store + virtual wide names via `wide_view_get` / `wide_view_set` | Catalog scores such as `complete`; Save writes tall columns |
| **B (materialized snapshot)** | Access `type: wide_flatten` → one wide row | Liquid/templates or one-shot flows; use `wide_unflatten` only if you must rebuild tall from wide |

This is **not** `series` (list-valued columns under a parent index) and **not** `hstack`/`vstack` (source concat). Aggregating `pivot_table` is a different, often lossy, story — see CIP-0012.

#### Pattern B — access `type: wide_flatten`

- **type**: Must be `wide_flatten`.
- **specifications**: Nested data source (any `read_data` type). Declare tall identity with nested **`index`** (column promoted before flatten), or rely on the nested frame’s existing index.
- **separator**: Joiner between index and field (default `_`). Must not appear in index labels (v1).
- **order**: `index_then_field` (default) or `field_then_index`.
- **columns**: Optional value fields to widen; others dropped.
- **index** (outer / wrapping): Label of the **singleton wide row** (same role as wrapping `index` on `stack` / `local`). Omit for legacy label `0` (deprecated for new configs). Do **not** use outer `index` as the tall column name — put that on `specifications.index`.
- **keys_field**: Name of the ordered key-list column (default `flattenKeys`); set `false` to omit.

Nested `compute` on `specifications` runs on the multi-row frame; outer `compute` on the wide row uses thin `finalize_data` (see CIP-0011 for full phases).

```yaml
input:
  type: wide_flatten
  separator: "_"
  order: index_then_field
  index: root                 # singleton result label (REQ-000C)
  columns:
    - title
    - complete
  specifications:
    type: local
    index: id                 # tall identity before flatten
    data:
      - id: grant/a
        title: A
        complete: true
      - id: grant/b
        title: B
        complete: false
```

Result is one row indexed `root` with `flattenKeys: [grant/a, grant/b]` plus columns such as `grant/a_title`, `grant/b_complete`. Loop keys in Liquid with `flattenKeys`; do not parse column names in the application.

**Migration (CIP-0010 Phase 3):** configs that used outer `index: id` to mean “tall column” should move that key under `specifications` and set outer `index` to the overview/singleton label (or omit it for legacy `0`).

#### Pattern A — virtual wide view (Python)

Keep the tall frame as the store. Resolve wide names without changing shape:

```python
from lynguine.access.io import wide_view_get, wide_view_set

keys = list(df.index)
wide_view_set(df, "grant/a_complete", True, keys=keys, fields=["complete"])
value = wide_view_get(df, "grant/a_complete", keys=keys, fields=["complete"])
# df.shape unchanged; write_data sees tall columns
```

Helpers: `compose_wide_column_name`, `parse_wide_column_name`, `wide_unflatten_dataframe` (Pattern B inverse / tests).

**Release note (CIP-0010):** Additive and opt-in. Prefer Pattern A for writable scores; `type: wide_flatten` is a snapshot unless you explicitly unflatten.

---

## Compute Operations in Linguine

The `compute` field in a Linguine configuration file is used to define computations to be performed on the data. These computations can transform existing data, create new fields, or perform complex operations across multiple fields.

### Compute Field Structure

The `compute` field is typically a list of computation specifications. Each computation is defined by a dictionary with the following key components:

```yaml
compute:
  - function: function_name
    field: output_field_name
    args:
      arg1: value1
      arg2: value2
    refresh: boolean
```

#### Key Components:

- **function**: The name of the function to be executed.
- **field**: The name of the field where the result will be stored. This can be a single field or a list of fields for functions that return multiple values.
- **args**: A dictionary of arguments to be passed to the function.
- **refresh**: (Optional) A boolean indicating whether to recompute the value even if it already exists. Default is `False`.

### Types of Compute Arguments

The `args` field can contain different types of arguments:

1. **Direct Arguments**: Simple values passed directly to the function.
2. **Column Arguments**: References to entire columns of data.
3. **Row Arguments**: References to values from the current row.
4. **View Arguments**: References to values processed through a view (e.g., formatted strings).
5. **Subseries Arguments**: References to subsets of data series.
6. **Function Arguments**: References to other compute functions.

### Example Compute Specifications

Here are some examples of compute specifications:

```yaml
compute:
  - function: add
    field: sum
    args:
      a: 
        column: column1
      b: 
        column: column2

  - function: format_name
    field: full_name
    args:
      first_name: 
        row: first_name
      last_name: 
        row: last_name

  - function: calculate_average
    field: average
    args:
      values: 
        subseries: data_column

  - function: complex_calculation
    field: result
    args:
      input1: 
        column: input_column1
      input2: 
        column: input_column2
      operation:
        function: another_function
    refresh: true
```

### Execution Order

Compute operations are executed in the order they are defined in the configuration file. This allows for dependencies between computations, where one computation may rely on the results of a previous one.

### Function List

The available functions for compute operations are defined in the `_compute_functions_list` method of the `Compute` class. This list includes the function name, the actual function object, default arguments, and an optional docstring.

### Error Handling

If a specified function is not found in the function list, a `ValueError` will be raised with an appropriate error message.

---

## Review Entries in Linguine

The `review` section in a Linguine configuration file is used to specify how data should be displayed and interacted with for review purposes. This section is closely tied to the functionality provided by the `DisplaySystem` class in `display.py`.

### Review Entry Structure

The `review` section typically contains a list of review specifications. Each specification is a dictionary that defines how a particular field or set of fields should be presented for review. Here's the general structure:

```yaml
review:
  - field: field_name
    type: review_type
    options:
      option1: value1
      option2: value2
```

#### Key Components:

- **field**: The name of the field to be reviewed. This can be a single field or a list of fields.
- **type**: The type of review widget to be used (e.g., "text", "dropdown", "checkbox", etc.).
- **options**: A dictionary of additional options specific to the review type.

### Common Review Types

1. **Text Review**
   ```yaml
   - field: description
     type: text
     options:
       multiline: true
       max_length: 500
   ```

2. **Dropdown Review**
   ```yaml
   - field: category
     type: dropdown
     options:
       choices: ["A", "B", "C"]
       allow_multiple: false
   ```

3. **Checkbox Review**
   ```yaml
   - field: is_active
     type: checkbox
   ```

4. **Date Review**
   ```yaml
   - field: event_date
     type: date
     options:
       format: "%Y-%m-%d"
   ```

5. **Numeric Review**
   ```yaml
   - field: score
     type: numeric
     options:
       min: 0
       max: 100
       step: 0.1
   ```

### Advanced Review Features

1. **Multiple Fields**
   ```yaml
   - field: [first_name, last_name]
     type: text
     options:
       label: "Full Name"
   ```

2. **Conditional Display**
   ```yaml
   - field: additional_info
     type: text
     options:
       display_if:
         field: has_additional_info
         value: true
   ```

3. **Custom Validation**
   ```yaml
   - field: email
     type: text
     options:
       validation: email_format
   ```

### Interaction with DisplaySystem

The `review` entries are processed by the `DisplaySystem` class in `display.py`. This class creates appropriate widgets based on the review specifications and manages the interaction between the user interface and the underlying data.

Key methods in `DisplaySystem` that handle review entries include:

- `populate_display()`: Creates and updates widgets based on review specifications.
- `value_updated()`: Handles updates when a reviewed value changes.
- `set_value()` and `set_value_by_element()`: Update specific values in the data.

### Example Review Section

Here's an example of a complete `review` section in a Linguine configuration file:

```yaml
review:
  - field: title
    type: text
    options:
      max_length: 100
      label: "Article Title"

  - field: content
    type: text
    options:
      multiline: true
      max_length: 1000
      label: "Article Content"

  - field: category
    type: dropdown
    options:
      choices: ["News", "Opinion", "Feature"]
      allow_multiple: false
      label: "Article Category"

  - field: tags
    type: dropdown
    options:
      choices: ["Politics", "Technology", "Science", "Culture"]
      allow_multiple: true
      label: "Article Tags"

  - field: publish_date
    type: date
    options:
      format: "%Y-%m-%d"
      label: "Publication Date"

  - field: is_featured
    type: checkbox
    options:
      label: "Feature this article?"

  - field: [author_first_name, author_last_name]
    type: text
    options:
      label: "Author Name"
```

This example demonstrates various types of review entries that can be used to create a comprehensive review interface for an article management system.

---
