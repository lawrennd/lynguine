# Compute Framework Documentation

## Overview

The compute framework in lynguine provides a powerful and flexible system for defining and executing data transformations and computations. It follows a declarative approach where computations are specified in YAML configuration files and executed through a function registry system.

## Architecture

### Core Components

The compute framework consists of the following key components:

1. **Compute Class** (`lynguine.assess.compute.Compute`): The main engine that processes compute specifications
2. **Function Registry**: A list of available compute functions with their signatures and default arguments
3. **Argument Resolution System**: Handles different types of arguments (direct, row, column, subseries, view, function)
4. **Three-Phase Processing**: Supports precompute, compute, and postcompute operations

### Inheritance in referia

The `referia.assess.compute.Compute` class extends the lynguine base class with additional functions specific to review and assessment workflows:

```
lynguine.assess.compute.Compute
    ↑
    └── referia.assess.compute.Compute
```

## Compute Specification Format

### Basic Structure

Compute operations are defined in YAML configuration files using the following structure:

```yaml
compute:
  - function: function_name
    field: output_field_name
    args:
      arg1: value1
      arg2: value2
    refresh: boolean
```

### Key Fields

- **function**: The name of the function to execute (must be in the function registry)
- **field**: The column name(s) where results will be stored
  - Can be a single string for single-output functions
  - Can be a list for multi-output functions
  - Can be omitted for functions with no output (side effects only)
- **args**: Direct arguments passed as-is to the function
- **row_args**: Arguments extracted from the current row
- **column_args**: Arguments extracted from entire columns
- **subseries_args**: Arguments extracted from data subsets
- **view_args**: Arguments processed through liquid templates or formatters
- **function_args**: Arguments that are themselves functions
- **refresh**: Boolean indicating whether to recompute if value already exists (default: false)

## Argument Types

### 1. Direct Arguments (`args`)

Simple values passed directly to the function:

```yaml
compute:
  - function: add
    field: total
    args:
      increment: 10
```

### 2. Row Arguments (`row_args`)

Values extracted from the current row being processed:

```yaml
compute:
  - function: concat_strings
    field: full_name
    row_args:
      first: first_name
      last: last_name
```

### 3. Column Arguments (`column_args`)

Entire columns passed as arrays/series:

```yaml
compute:
  - function: calculate_mean
    field: avg_score
    column_args:
      values: scores
```

### 4. Subseries Arguments (`subseries_args`)

Subsets of data based on filtering criteria:

```yaml
compute:
  - function: sum_filtered
    field: dept_total
    subseries_args:
      values: amount
      filter_column: department
```

### 5. View Arguments (`view_args`)

Values processed through liquid templates or formatting:

```yaml
compute:
  - function: format_output
    field: formatted_text
    view_args:
      template: "{{ first_name }} {{ last_name }} - {{ department }}"
```

### 6. Function Arguments (`function_args`)

Arguments that are themselves compute functions:

```yaml
compute:
  - function: process_data
    field: result
    function_args:
      preprocessor: normalize_data
```

## Function Registry

### Structure

Each function in the registry is defined with:

```python
{
    "name": "function_name",
    "function": actual_function_object,
    "default_args": {"arg1": default_value},
    "docstr": "Function description",
    "context": False  # True if compute context is required
}
```

### Built-in Functions (lynguine)

The base lynguine Compute class provides:

- **render_liquid**: Render liquid templates with data context
- **today**: Return today's date as formatted string

### Extended Functions (referia)

The referia Compute class adds:

#### Text Processing
- **word_count**: Count words in text
- **text_summarizer**: Generate text summaries
- **paragraph_split**: Split text into paragraphs
- **sentence_split**: Split text into sentences
- **named_entities**: Extract named entities from text

#### File Operations
- **file_from_re**: Find first file matching regex pattern
- **files_from_re**: Find all files matching regex pattern
- **pdf_extract_comments**: Extract comments from PDF files

#### Data Processing
- **liquid**: Render liquid templates
- **max**: Maximum value from list
- **len**: Length of list
- **sum**: Sum of values
- **map**: Apply function to list elements
- **return_longest**: Return longest item in list
- **return_shortest**: Return shortest item in list

#### DataFrame Operations
- **addmonth**: Add month column from date field
- **addyear**: Add year column from date field
- **augmentmonth**: Augment with month based on date
- **augmentyear**: Augment with year based on date
- **ascending**: Sort in ascending order
- **descending**: Sort in descending order
- **columncontains**: Filter on column containing value
- **columnis**: Filter on column equality
- **convert_datetime**: Convert to datetime type
- **convert_int**: Convert to integer type
- **convert_string**: Convert to string type
- **current**: Filter for current items
- **former**: Filter for former items
- **recent**: Filter by year

#### Utility Functions
- **identity**: Return input unchanged (testing)
- **next_integer**: Add one to maximum value
- **most_recent_screen_shot**: Get most recent screenshot filename
- **histogram**: Create histogram visualization
- **get_url_file**: Download file from URL
- **remove_nan**: Remove NaN values from dictionary

## Three-Phase Processing

### 1. Precompute Phase

Operations executed before main compute phase. Typically used for:
- Data loading
- Initial transformations
- Setting up computed columns

```yaml
precompute:
  - function: load_data
    field: raw_data
    args:
      source: data.csv
```

### 2. Compute Phase

Main computational operations. These are executed for each row:

```yaml
compute:
  - function: word_count
    field: word_count
    row_args:
      text: review_text
```

### 3. Postcompute Phase

Operations executed after main compute phase. Typically used for:
- Aggregations
- Final transformations
- Cleanup

```yaml
postcompute:
  - function: calculate_statistics
    field: summary_stats
    column_args:
      values: scores
```

## Execution Model

### run_all() Method

Processes all rows in the dataframe:

```python
compute = Compute(interface)
compute.run_all(data, interface)
```

### run() Method

Processes the current row:

```python
compute = Compute(interface)
data.set_index(0)
compute.run(data, interface)
```

### run_onchange() Method

Runs computations triggered by cell changes (for reactive interfaces):

```python
compute.run_onchange(data, index=0, column='score')
```

## Refresh Behavior

By default, compute operations only execute when:
1. The output field doesn't exist, OR
2. The output field value is NaN/None

To force recomputation:

```yaml
compute:
  - function: expensive_operation
    field: result
    refresh: true  # Always recompute
```

## Complete Example

```yaml
# Configuration file example
compute:
  # Precomputation: prepare data
  precompute:
    - function: convert_datetime
      field: submission_date
      row_args:
        value: date_string
        format: "%Y-%m-%d"
  
  # Main computation: analyze each row
  compute:
    - function: word_count
      field: review_word_count
      row_args:
        text: review_text
    
    - function: named_entities
      field: entities
      row_args:
        text: review_text
    
    - function: text_summarizer
      field: summary
      row_args:
        text: review_text
      args:
        max_length: 150
    
    - function: liquid
      field: formatted_output
      view_args:
        template: "Review by {{ author }} on {{ submission_date }}: {{ summary }}"
  
  # Postcomputation: aggregate results
  postcompute:
    - function: sum
      field: total_word_count
      column_args:
        values: review_word_count
```

## Adding Custom Functions

### In lynguine

To add custom functions to the lynguine Compute class:

```python
class CustomCompute(lynguine.assess.compute.Compute):
    def _compute_functions_list(self):
        return super()._compute_functions_list() + [
            {
                "name": "my_custom_function",
                "function": my_function_impl,
                "default_args": {"param": "default_value"},
                "docstr": "Description of my function",
            }
        ]
```

### In referia

The referia Compute class already extends lynguine with many additional functions. To add more:

```python
# In referia/assess/compute.py
def _compute_functions_list(self):
    return super()._compute_functions_list() + [
        {
            "name": "new_function",
            "function": new_function_impl,
            "default_args": {},
            "docstr": "My new function",
        }
    ]
```

## Best Practices

1. **Use Appropriate Argument Types**: Choose the right argument type for your use case
   - Use `row_args` for row-by-row operations
   - Use `column_args` for operations on entire columns
   - Use `args` for static configuration values

2. **Leverage Default Arguments**: Define sensible defaults in the function registry

3. **Document Functions**: Always include a `docstr` in function registry entries

4. **Handle Missing Values**: Compute functions should gracefully handle NaN/None values

5. **Use Refresh Sparingly**: Only set `refresh: true` when necessary to avoid unnecessary computation

6. **Leverage Three-Phase Processing**: Use precompute/compute/postcompute appropriately for your workflow

7. **Consider Multi-Output Functions**: Use lists for `field` when functions return tuples

8. **Test Function Registration**: Ensure custom functions are properly registered before use

## Error Handling

The compute framework provides detailed error messages:

- **Function Not Found**: If a function name isn't in the registry
- **Invalid Column**: If a row_arg or column_arg references a non-existent column
- **Type Mismatch**: If multi-output functions don't return tuples as expected

## Performance Considerations

1. **Minimize Refresh**: Only use `refresh: true` when absolutely necessary
2. **Batch Operations**: Use column_args for operations that can work on entire columns
3. **Cache Results**: The framework caches computed values by default
4. **Order Matters**: Place expensive operations later in the compute sequence when possible

## Integration with CustomDataFrame

The compute framework is designed to work seamlessly with `lynguine.assess.data.CustomDataFrame`:

```python
from lynguine.assess.data import CustomDataFrame
from lynguine.assess.compute import Compute
from lynguine.config.interface import Interface

# Load data
data = CustomDataFrame.from_csv("data.csv")

# Create compute instance
interface = Interface.from_file("config.yml")
compute = Compute(interface)

# Run computations
compute.run_all(data, interface)

# Access results
print(data["computed_field"])
```

## Liquid Template Support

The compute framework includes built-in support for Liquid templates:

```yaml
compute:
  - function: liquid
    field: formatted_text
    view_args:
      template: |
        Name: {{ first_name }} {{ last_name }}
        Score: {{ score }}
        Grade: {% if score >= 90 %}A{% elsif score >= 80 %}B{% else %}C{% endif %}
```

Available Liquid filters:
- `url_escape`: URL encode strings
- `markdownify`: Convert to markdown
- `relative_url`: Generate relative URLs
- `absolute_url`: Generate absolute URLs
- `to_i`: Convert to integer

## Function Registry Reference

### Complete Function List

#### Base Functions (lynguine.assess.compute.Compute)

##### render_liquid
Render a liquid template with data context.

**Arguments:**
- `template` (str): The liquid template string
- Context variables available from data

**Returns:** Rendered string

**Example:**
```yaml
compute:
  - function: render_liquid
    field: formatted_output
    view_args:
      template: "{{ first_name }} {{ last_name }}"
```

##### today
Return today's date as a formatted string.

**Arguments:**
- `format` (str, default: "%Y-%m-%d"): Date format string

**Returns:** String representation of today's date

**Example:**
```yaml
compute:
  - function: today
    field: current_date
    args:
      format: "%B %d, %Y"
```

#### Text Processing Functions (referia.assess.compute.Compute)

##### word_count
Count the number of words in text.

**Arguments:**
- `text` (str): Text to count words in

**Returns:** Integer word count

**Example:**
```yaml
compute:
  - function: word_count
    field: review_length
    row_args:
      text: review_text
```

##### text_summarizer
Generate a summary of the provided text using spaCy.

**Arguments:**
- `text` (str): Text to summarize
- `ratio` (float, optional): Compression ratio (0.0-1.0)

**Returns:** Summary string

**Example:**
```yaml
compute:
  - function: text_summarizer
    field: summary
    row_args:
      text: long_text
    args:
      ratio: 0.3
```

##### named_entities
Extract named entities from text using spaCy.

**Arguments:**
- `text` (str): Text to extract entities from

**Returns:** List of named entities with labels

**Example:**
```yaml
compute:
  - function: named_entities
    field: entities
    row_args:
      text: review_text
```

##### paragraph_split
Split text into paragraphs.

**Arguments:**
- `text` (str): Text to split
- `sep` (str, default: "\n\n"): Paragraph separator

**Returns:** List of paragraphs

**Example:**
```yaml
compute:
  - function: paragraph_split
    field: paragraphs
    row_args:
      text: document
    args:
      sep: "\n\n"
```

##### sentence_split
Split text into sentences using spaCy.

**Arguments:**
- `text` (str): Text to split

**Returns:** List of sentences

**Example:**
```yaml
compute:
  - function: sentence_split
    field: sentences
    row_args:
      text: review_text
```

##### comment_list
Extract comments from a list of paragraphs.

**Arguments:**
- `paragraphs` (list): List of text paragraphs

**Returns:** List of comment strings

**Example:**
```yaml
compute:
  - function: comment_list
    field: comments
    row_args:
      paragraphs: text_paragraphs
```

#### File Operations Functions

##### file_from_re
Find the first file matching a regular expression pattern.

**Arguments:**
- `pattern` (str): Regular expression pattern
- `directory` (str, default: "."): Directory to search in

**Returns:** String filename or None

**Example:**
```yaml
compute:
  - function: file_from_re
    field: matching_file
    args:
      pattern: "review_.*\\.pdf"
      directory: "./reviews"
```

##### files_from_re
Find all files matching a regular expression pattern.

**Arguments:**
- `pattern` (str): Regular expression pattern
- `directory` (str, default: "."): Directory to search in

**Returns:** List of filenames

**Example:**
```yaml
compute:
  - function: files_from_re
    field: all_reviews
    args:
      pattern: "review_.*\\.pdf"
      directory: "./reviews"
```

##### pdf_extract_comments
Extract comments and annotations from a PDF file.

**Arguments:**
- `filename` (str): Path to PDF file

**Returns:** List of comments

**Example:**
```yaml
compute:
  - function: pdf_extract_comments
    field: pdf_comments
    row_args:
      filename: pdf_path
```

##### get_url_file
Download a file from a URL.

**Arguments:**
- `url` (str): URL to download from
- `filename` (str, optional): Local filename to save as

**Returns:** Path to downloaded file

**Example:**
```yaml
compute:
  - function: get_url_file
    field: local_file
    row_args:
      url: file_url
```

#### Data Processing Functions

##### liquid
Render a liquid template (alias for render_liquid with referia context).

**Arguments:**
- `template` (str): Liquid template string
- Additional context from data

**Returns:** Rendered string

**Example:**
```yaml
compute:
  - function: liquid
    field: formatted_text
    view_args:
      template: "Review #{{ id }}: {{ title }}"
```

##### max
Return the maximum value from a list.

**Arguments:**
- `values` (list): List of numeric values

**Returns:** Maximum value

**Example:**
```yaml
compute:
  - function: max
    field: max_score
    column_args:
      values: scores
```

##### len
Return the length of a list or string.

**Arguments:**
- `values` (list or str): Object to measure

**Returns:** Integer length

**Example:**
```yaml
compute:
  - function: len
    field: num_reviews
    column_args:
      values: reviews
```

##### sum
Calculate the sum of values.

**Arguments:**
- `x` (Series or list): Values to sum

**Returns:** Numeric sum

**Example:**
```yaml
compute:
  - function: sum
    field: total_score
    column_args:
      x: individual_scores
```

##### map
Apply a function to each element in a list.

**Arguments:**
- `entries` (list): List to map over
- `function` (callable): Function to apply

**Returns:** List of results

**Example:**
```yaml
compute:
  - function: map
    field: processed_items
    row_args:
      entries: raw_items
    function_args:
      function: process_item
```

##### return_longest
Return the longest item from a list.

**Arguments:**
- `items` (list): List of items (strings or lists)

**Returns:** Longest item

**Example:**
```yaml
compute:
  - function: return_longest
    field: longest_review
    column_args:
      items: reviews
```

##### return_shortest
Return the shortest item from a list.

**Arguments:**
- `items` (list): List of items (strings or lists)

**Returns:** Shortest item

**Example:**
```yaml
compute:
  - function: return_shortest
    field: shortest_review
    column_args:
      items: reviews
```

##### list_lengths
Return a list of lengths for each item in a list.

**Arguments:**
- `items` (list): List of items to measure

**Returns:** List of integer lengths

**Example:**
```yaml
compute:
  - function: list_lengths
    field: review_lengths
    row_args:
      items: reviews_list
```

##### next_integer
Add one to the maximum value in a series (useful for generating IDs).

**Arguments:**
- `values` (Series): Numeric values

**Returns:** Maximum value + 1

**Example:**
```yaml
compute:
  - function: next_integer
    field: new_id
    column_args:
      values: existing_ids
```

##### identity
Return the input value unchanged (useful for testing).

**Arguments:**
- `value` (any): Value to return

**Returns:** Same value

**Example:**
```yaml
compute:
  - function: identity
    field: copy_field
    row_args:
      value: original_field
```

##### remove_nan
Remove NaN/None values from a dictionary.

**Arguments:**
- `data` (dict): Dictionary to clean

**Returns:** Dictionary without NaN values

**Example:**
```yaml
compute:
  - function: remove_nan
    field: clean_data
    row_args:
      data: raw_data_dict
```

#### DataFrame Manipulation Functions

##### addmonth
Add a month column based on a source date field.

**Arguments:**
- `data` (DataFrame): DataFrame to modify
- `source` (str): Name of source date column
- `target` (str, optional): Name of target month column

**Returns:** Modified DataFrame

**Example:**
```yaml
precompute:
  - function: addmonth
    args:
      source: submission_date
      target: month
```

##### addyear
Add a year column based on a source date field.

**Arguments:**
- `data` (DataFrame): DataFrame to modify
- `source` (str): Name of source date column
- `target` (str, optional): Name of target year column

**Returns:** Modified DataFrame

**Example:**
```yaml
precompute:
  - function: addyear
    args:
      source: submission_date
      target: year
```

##### augmentmonth
Augment DataFrame with month column (preprocessor).

**Arguments:**
- `data` (DataFrame): DataFrame to augment
- `column` (str): Date column name

**Returns:** Modified DataFrame

**Example:**
```yaml
precompute:
  - function: augmentmonth
    args:
      column: created_date
```

##### augmentyear
Augment DataFrame with year column (preprocessor).

**Arguments:**
- `data` (DataFrame): DataFrame to augment
- `column` (str): Date column name

**Returns:** Modified DataFrame

**Example:**
```yaml
precompute:
  - function: augmentyear
    args:
      column: created_date
```

##### ascending
Sort DataFrame in ascending order.

**Arguments:**
- `data` (DataFrame): DataFrame to sort
- `column` (str): Column to sort by

**Returns:** Sorted DataFrame

**Example:**
```yaml
precompute:
  - function: ascending
    args:
      column: submission_date
```

##### descending
Sort DataFrame in descending order.

**Arguments:**
- `data` (DataFrame): DataFrame to sort
- `column` (str): Column to sort by

**Returns:** Sorted DataFrame

**Example:**
```yaml
precompute:
  - function: descending
    args:
      column: priority_score
```

##### columncontains
Filter DataFrame where column contains a specific value.

**Arguments:**
- `data` (DataFrame): DataFrame to filter
- `column` (str): Column to check
- `value` (str): Value to search for

**Returns:** Boolean Series for filtering

**Example:**
```yaml
compute:
  - function: columncontains
    field: filter_mask
    args:
      column: review_text
      value: "methodology"
```

##### columnis
Filter DataFrame where column equals a specific value.

**Arguments:**
- `data` (DataFrame): DataFrame to filter
- `column` (str): Column to check
- `value` (any): Value to match

**Returns:** Boolean Series for filtering

**Example:**
```yaml
compute:
  - function: columnis
    field: filter_mask
    args:
      column: status
      value: "approved"
```

##### current
Filter for current items (date-based).

**Arguments:**
- `data` (DataFrame): DataFrame to filter
- `date_column` (str): Date column to check

**Returns:** Boolean Series for filtering

**Example:**
```yaml
compute:
  - function: current
    args:
      date_column: end_date
```

##### former
Filter for former/past items (date-based).

**Arguments:**
- `data` (DataFrame): DataFrame to filter
- `date_column` (str): Date column to check

**Returns:** Boolean Series for filtering

**Example:**
```yaml
compute:
  - function: former
    args:
      date_column: end_date
```

##### recent
Filter for recent items by year.

**Arguments:**
- `data` (DataFrame): DataFrame to filter
- `date_column` (str): Date column to check
- `years` (int): Number of recent years

**Returns:** Boolean Series for filtering

**Example:**
```yaml
compute:
  - function: recent
    args:
      date_column: submission_date
      years: 2
```

##### onbool
Filter on boolean column value.

**Arguments:**
- `data` (DataFrame): DataFrame to filter
- `column` (str): Boolean column name
- `invert` (bool, default: False): Invert the filter

**Returns:** Boolean Series for filtering

**Example:**
```yaml
compute:
  - function: onbool
    args:
      column: is_published
      invert: false
```

#### Type Conversion Functions

##### convert_datetime
Convert column to datetime type (preprocessor).

**Arguments:**
- `data` (DataFrame): DataFrame to modify
- `columns` (list): Column names to convert
- `format` (str, optional): Date format string

**Returns:** Modified DataFrame

**Example:**
```yaml
precompute:
  - function: convert_datetime
    args:
      columns: ["submission_date", "review_date"]
      format: "%Y-%m-%d"
```

##### convert_int
Convert column to integer type (preprocessor).

**Arguments:**
- `data` (DataFrame): DataFrame to modify
- `columns` (list): Column names to convert

**Returns:** Modified DataFrame

**Example:**
```yaml
precompute:
  - function: convert_int
    args:
      columns: ["score", "ranking"]
```

##### convert_string
Convert column to string type (preprocessor).

**Arguments:**
- `data` (DataFrame): DataFrame to modify
- `columns` (list): Column names to convert

**Returns:** Modified DataFrame

**Example:**
```yaml
precompute:
  - function: convert_string
    args:
      columns: ["id", "category"]
```

##### convert_year_iso
Convert year column to ISO format (preprocessor).

**Arguments:**
- `data` (DataFrame): DataFrame to modify
- `column` (str): Column name to convert

**Returns:** Modified DataFrame

**Example:**
```yaml
precompute:
  - function: convert_year_iso
    args:
      column: year
```

##### augmentcurrency
Augment DataFrame with currency formatting (preprocessor).

**Arguments:**
- `data` (DataFrame): DataFrame to augment
- `column` (str): Column to format

**Returns:** Modified DataFrame

**Example:**
```yaml
precompute:
  - function: augmentcurrency
    args:
      column: amount
```

#### Date/Time Functions

##### fromisoformat
Parse ISO format date string to datetime object.

**Arguments:**
- `date_string` (str): ISO format date string

**Returns:** datetime object

**Example:**
```yaml
compute:
  - function: fromisoformat
    field: parsed_date
    row_args:
      date_string: iso_date
```

##### strptime
Parse date string using format specification.

**Arguments:**
- `date_string` (str): Date string to parse
- `format` (str): Format specification

**Returns:** datetime object

**Example:**
```yaml
compute:
  - function: strptime
    field: parsed_date
    row_args:
      date_string: date_text
    args:
      format: "%d/%m/%Y"
```

#### Visualization Functions

##### histogram
Create a histogram visualization of numeric data.

**Arguments:**
- `values` (Series or list): Numeric values to plot
- `bins` (int, optional): Number of bins

**Returns:** Histogram plot object

**Example:**
```yaml
compute:
  - function: histogram
    field: score_distribution
    column_args:
      values: scores
    args:
      bins: 20
```

##### bar_plot
Create a bar plot visualization.

**Arguments:**
- `data` (dict or DataFrame): Data to plot
- `x` (str, optional): X-axis column
- `y` (str, optional): Y-axis column

**Returns:** Bar plot object

**Example:**
```yaml
postcompute:
  - function: bar_plot
    field: category_chart
    args:
      x: category
      y: count
```

#### System Functions

##### most_recent_screen_shot
Get the filename of the most recent screenshot.

**Arguments:** None

**Returns:** String filename

**Example:**
```yaml
compute:
  - function: most_recent_screen_shot
    field: screenshot_path
```

### Registering Custom Functions

To register your own compute functions:

```python
from lynguine.assess.compute import Compute

class MyCompute(Compute):
    def _compute_functions_list(self):
        # Get base functions
        base = super()._compute_functions_list()
        
        # Add custom functions
        custom = [
            {
                "name": "my_function",
                "function": self._my_function_impl,
                "default_args": {
                    "param1": "default_value",
                },
                "docstr": "My custom function description.",
                "context": False,  # Set True if function needs compute context
            }
        ]
        
        return base + custom
    
    def _my_function_impl(self, text, param1="default"):
        """Implementation of my custom function."""
        # Your logic here
        return processed_text
```

### Function Registry Best Practices

1. **Naming Conventions**: Use descriptive, lowercase names with underscores
2. **Default Arguments**: Provide sensible defaults for optional parameters
3. **Documentation**: Always include a `docstr` describing the function
4. **Type Hints**: Use type hints in function implementations
5. **Error Handling**: Handle edge cases and invalid inputs gracefully
6. **Testing**: Write unit tests for each custom function
7. **Performance**: Consider caching for expensive operations
8. **Composability**: Design functions to work well with others in chains

## See Also

- [CustomDataFrame Documentation](./data_frame.md)
- [Interface Configuration](./configuration.md)
- [Liquid Templates](https://shopify.github.io/liquid/)

