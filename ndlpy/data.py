import pandas as pd
import numpy as np
"""Wrapper classes for data objects"""

class Accessor():
    def __init__(self, data):
        self._data_object = data

    def __getitem__(self, key):
        raise NotImplementedError("This is a base accessor class")

    def __setitem__(self, key, value):
        raise NotImplementedError("This is a base accessor class")
        
    
class DataObject():
    def __init__(self, data=None, colspecs=None, index=None, column=None, selector=None):
        self.at = self._AtAccessor(self)
        self.iloc = self._IlocAccessor(self)
        self.loc = self._locAccessor(self)

    class _AtAccessor(Accessor):
        def __init__(self, data):
            super().__init__(data=data)

    class _LocAccessor(Accessor):
        def __init__(self, data):
            super().__init__(data=data)

    class _IlocAccessor(Accessor):
        def __init__(self, data):
            super().__init__(data=data)
        
    def get_subindex(self):
        raise NotImplementedError("This is a base class")

    def set_subindex(self, val):
        raise NotImplementedError("This is a base class")

    def get_subindices(self):
        raise NotImplementedError("This is a base class")

    def get_index(self):
        return self._index

    def set_index(self, index):
        if index in self.index:
            self._index = index
        else:
            raise KeyError("Invalid index set.")

    def get_column(self):
        return self._column
    
    def set_column(self, column):
        if column in self.columns:
            self._column = column
        else:
            raise KeyError("Invalid column set.")        

    def get_selector(self):
        return self._selector
    
    def set_selector(self, selector):
        if selector in self.columns:
            self._selector = selector
        else:
            raise KeyError("Invalid selector set.")        
        
    def get_value(self):
        return self.at[self.get_index(), self.get_column()]

    def set_value(self, val):
        self.at[self.get_index(), self.get_column()] = val
        
    def head(self, n=5):
        """
        Return the first `n` rows of the DataFrame.

        :param n: Number of rows to select.
        :return: The first `n` rows of the DataFrame.
        """
        return self.to_pandas().head(n)

    def tail(self, n=5):
        """
        Return the last `n` rows of the DataFrame.

        :param n: Number of rows to select.
        :return: The last `n` rows of the DataFrame.
        """
        return self.to_pandas().tail(n)

    def add_column(self, column_name, data):
        """
        Add a new column to the DataFrame.

        :param column_name: The name of the new column.
        :param data: The data for the new column.
        :raise NotImplementedError: Indicates the method needs to be implemented in a subclass.
        """
        raise NotImplementedError("This is a base class")

    def drop_column(self, column_name):
        """
        Drop a column from the DataFrame.

        :param column_name: The name of the column to drop.
        :raise NotImplementedError: Indicates the method needs to be implemented in a subclass.
        """
        raise NotImplementedError("This is a base class")

    def filter_rows(self, condition):
        """
        Filter rows based on a specified condition.

        :param condition: The condition to filter rows.
        :raise NotImplementedError: Indicates the method needs to be implemented in a subclass.
        """
        raise NotImplementedError("This is a base class")

    def get_shape(self):
        """
        Get the shape of the DataFrame.

        :return: A tuple representing the shape of the DataFrame.
        """
        return self.to_pandas().shape

    def describe(self):
        """
        Generate descriptive statistics.

        :return: Descriptive statistics for the DataFrame.
        """
        return self.to_pandas().describe()

    def to_pandas(self):
        """
        Convert the custom DataFrame to a Pandas DataFrame.

        :raise NotImplementedError: Indicates the method needs to be implemented in a subclass.
        """
        raise NotImplementedError("This is a base class")

    def to_clipboard(self, *args, **kwargs):
        """
        Copy the DataFrame to the system clipboard.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_clipboard.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_clipboard.
        :return: Output of Pandas DataFrame to_clipboard method.
        """
        return self.to_pandas().to_clipboard(*args, **kwargs)

    def to_feather(self, *args, **kwargs):
        """
        Write the DataFrame to a Feather file.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_feather.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_feather.
        :return: Output of Pandas DataFrame to_feather method.
        """
        return self.to_pandas().to_feather(*args, **kwargs)

    def to_json(self, *args, **kwargs):
        """
        Convert the DataFrame to a JSON string.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_json.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_json.
        :return: Output of Pandas DataFrame to_json method.
        """
        return self.to_pandas().to_json(*args, **kwargs)

    def to_orc(self, *args, **kwargs):
        """
        Write the DataFrame to an ORC file.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_orc.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_orc.
        :return: Output of Pandas DataFrame to_orc method.
        """
        return self.to_pandas().to_orc(*args, **kwargs)

    def to_records(self, *args, **kwargs):
        """
        Convert the DataFrame to a NumPy record array.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_records.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_records.
        :return: Output of Pandas DataFrame to_records method.
        """
        return self.to_pandas().to_records(*args, **kwargs)

    def to_timestamp(self, *args, **kwargs):
        """
        Cast to DatetimeIndex of timestamps.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_timestamp.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_timestamp.
        :return: Output of Pandas DataFrame to_timestamp method.
        """
        return self.to_pandas().to_timestamp(*args, **kwargs)

    def to_csv(self, *args, **kwargs):
        """
        Write the DataFrame to a comma-separated values (csv) file.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_csv.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_csv.
        :return: Output of Pandas DataFrame to_csv method.
        """
        return self.to_pandas().to_csv(*args, **kwargs)

    def to_gbq(self, *args, **kwargs):
        """
        Write the DataFrame to a Google BigQuery table.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_gbq.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_gbq.
        :return: Output of Pandas DataFrame to_gbq method.
        """
        return self.to_pandas().to_gbq(*args, **kwargs)

    def to_latex(self, *args, **kwargs):
        """
        Render the DataFrame as a LaTeX tabular environment table.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_latex.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_latex.
        :return: Output of Pandas DataFrame to_latex method.
        """
        return self.to_pandas().to_latex(*args, **kwargs)

    def to_parquet(self, *args, **kwargs):
        """
        Write the DataFrame to a Parquet file.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_parquet.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_parquet.
        :return: Output of Pandas DataFrame to_parquet method.
        """
        return self.to_pandas().to_parquet(*args, **kwargs)

    def to_sql(self, *args, **kwargs):
        """
        Write records stored in the DataFrame to a SQL database.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_sql.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_sql.
        :return: Output of Pandas DataFrame to_sql method.
        """
        return self.to_pandas().to_sql(*args, **kwargs)

    def to_xarray(self, *args, **kwargs):
        """
        Convert the DataFrame to an xarray Dataset.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_xarray.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_xarray.
        :return: Output of Pandas DataFrame to_xarray method.
        """
        return self.to_pandas().to_xarray(*args, **kwargs)

    def to_dict(self, *args, **kwargs):
        """
        Convert the DataFrame to a dictionary.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_dict.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_dict.
        :return: Output of Pandas DataFrame to_dict method.
        """
        return self.to_pandas().to_dict(*args, **kwargs)

    def to_hdf(self, *args, **kwargs):
        """
        Write the DataFrame to a Hierarchical Data Format (HDF) file.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_hdf.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_hdf.
        :return: Output of Pandas DataFrame to_hdf method.
        """
        return self.to_pandas().to_hdf(*args, **kwargs)

    def to_markdown(self, *args, **kwargs):
        """
        Convert the DataFrame to a Markdown string.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_markdown.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_markdown.
        :return: Output of Pandas DataFrame to_markdown method.
        """
        return self.to_pandas().to_markdown(*args, **kwargs)

    def to_period(self, *args, **kwargs):
        """
        Convert DataFrame from DatetimeIndex to PeriodIndex.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_period.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_period.
        :return: Output of Pandas DataFrame to_period method.
        """
        return self.to_pandas().to_period(*args, **kwargs)

    def to_stata(self, *args, **kwargs):
        """
        Export the DataFrame to Stata dta format.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_stata.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_stata.
        :return: Output of Pandas DataFrame to_stata method.
        """
        return self.to_pandas().to_stata(*args, **kwargs)

    def to_xml(self, *args, **kwargs):
        """
        Convert the DataFrame to an XML string.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_xml.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_xml.
        :return: Output of Pandas DataFrame to_xml method.
        """
        return self.to_pandas().to_xml(*args, **kwargs)

    def to_excel(self, *args, **kwargs):
        """
        Write the DataFrame to an Excel file.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_excel.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_excel.
        :return: Output of Pandas DataFrame to_excel method.
        """
        return self.to_pandas().to_excel(*args, **kwargs)

    def to_html(self, *args, **kwargs):
        """
        Render the DataFrame as an HTML table.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_html.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_html.
        :return: Output of Pandas DataFrame to_html method.
        """
        return self.to_pandas().to_html(*args, **kwargs)

    def to_numpy(self, *args, **kwargs):
        """
        Convert the DataFrame to a NumPy array.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_numpy.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_numpy.
        :return: Output of Pandas DataFrame to_numpy method.
        """
        return self.to_pandas().to_numpy(*args, **kwargs)

    def to_string(self, *args, **kwargs):
        """
        Render the DataFrame to a console-friendly tabular output.

        :param args: Positional arguments to be passed to pandas.DataFrame.to_string.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.to_string.
        :return: Output of Pandas DataFrame to_string method.
        """
        return self.to_pandas().to_string(*args, **kwargs)

    @classmethod
    def from_csv(cls, *args, **kwargs):
        """
        Read a comma-separated values (csv) file into a CustomDataFrame.

        :param args: Positional arguments to be passed to pandas.read_csv.
        :param kwargs: Keyword arguments to be passed to pandas.read_csv.
        :return: A CustomDataFrame object.
        """
        return cls.from_pandas(df=pd.read_csv(*args, **kwargs))

    @classmethod
    def from_dict(cls, data, *args, **kwargs):
        """
        Construct a CustomDataFrame from a dict of array-like or dicts.

        :param data: Dictionary of data.
        :param args: Positional arguments to be passed to pandas.DataFrame.from_dict.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.from_dict.
        :return: A CustomDataFrame object.
        """
        return cls.from_pandas(df=pd.DataFrame.from_dict(data, *args, **kwargs))

    def sort_values(self, by, axis=0, ascending=True, inplace=False, **kwargs):
        raise NotImplementedError("This is a base class")

    def sort_index(self, axis=0, level=None, ascending=True, inplace=False, **kwargs):
        raise NotImplementedError("This is a base class")


    def convert(self, other):
        """
        Convert various data types to a CustomDataFrame.

        This method handles conversion from different data types like Pandas DataFrame,
        Pandas Series, NumPy array, list, and dictionary to the CustomDataFrame format.

        :param other: The data to be converted.
        :return: A CustomDataFrame object.
        :raises ValueError: If the data type of `other` cannot be converted.
        """

        if isinstance(other, self.__class__):
            # No conversion needed if it's already a CustomDataFrame
            return other

        elif isinstance(other, (pd.DataFrame, pd.Series)):
            # Directly convert from Pandas DataFrame or Series
            return self.__class__(other)

        elif isinstance(other, np.ndarray):
            # Handle NumPy array conversion
            return self._convert_numpy_array(other)

        elif isinstance(other, list):
            # Convert list to CustomDataFrame
            return self.__class__(pd.DataFrame(other))

        elif isinstance(other, dict):
            # Convert dictionary to CustomDataFrame
            return self.__class__(pd.DataFrame.from_dict(other))

        else:
            # Raise error for unsupported types
            raise ValueError(f"Unsupported type for conversion: {type(other)}")

    def _convert_numpy_array(self, array):
        """
        Helper method to convert a NumPy array to a CustomDataFrame.

        This method is called internally to handle specific scenarios based on the shape
        of the NumPy array.

        :param array: The NumPy array to be converted.
        :return: A CustomDataFrame object.
        :raises ValueError: If the array shape is not compatible.
        """

        if array.shape == self.shape:
            # Array shape matches the CustomDataFrame shape
            return self.__class__(
                data=pd.DataFrame(array, index=self.index, columns=self.columns),
            )
        elif len(array.shape) == 1:
            # Single dimensional array
            return self.__class__(
                data=pd.DataFrame(array, index=self.index, columns=[self.get_column()]),
            )
        elif array.ndim == 2 and (array.shape[0] == 1 or array.shape[1] == 1):
            # Two-dimensional array but with a single row or column
            if array.shape[0] == 1:
                if array.shape[1] != len(self.columns):
                    raise ValueError("NumPy array width doesn't match CustomDataFrame array width.")
                return self.__class__(
                    data=pd.DataFrame(
                        array,
                        index=[self.get_index()],
                        columns=self.columns,
                    ),
                )
            else:
                if array.shape[0] != len(self.index):
                    raise ValueError("NumPy array depth doesn't match CustomDataFrame array depth.")
                return self.__class__(
                    data=pd.DataFrame(
                        array,
                        index=self.index,
                        columns=self.get_column(),
                    ),
                )
        else:
            # Incompatible array shape
            raise ValueError("NumPy array shape is not compatible with CustomDataFrame.")        
        
        
    # Mathematical operations
    def sum(self, axis=0):
        if axis == 0:
            column = self.get_column()
            colspecs = {"parameter_cache": list(self.columns)}
        else:
            column = self.get_index()
            colspecs = {"parameter_cache": list(self.index)}

        return self.__class__(
            data=self.to_pandas().sum(axis),
            colspecs=colspecs,
            types=self.types,
            column=column,
        )

    def mean(self, axis=0):
        if axis == 0:
            column = self.get_column()
            colspecs = {"parameter_cache": list(self.columns)}
        else:
            column = self.get_index()
            colspecs = {"parameter_cache": list(self.index)}
        return self.__class__(
            data=self.to_pandas().mean(axis),
            colspecs=colspecs,
            types=self.types,
            column=column,
        )

    def add(self, other):
        other = self.convert(other)
        return self.__class__(
            data=self.to_pandas().add(other.to_pandas()),
            colspecs=self._colspecs,
            index=self.get_index(),
            column=self.get_column(),
            selector=self.get_selector(),
        )

    def subtract(self, other):
        other = self.convert(other)
        return self.__class__(
            data=self.to_pandas().subtract(other.to_pandas()),
            colspecs=self._colspecs,
            index=self.get_index(),
            column=self.get_column(),
            selector=self.get_selector(),
        )

    def multiply(self, other):
        other = self.convert(other)
        return self.__class__(
            data=self.to_pandas().multiply(pd.DataFrame(other.to_pandas())),
            colspecs=self._colspecs,
            index=self.get_index(),
            column=self.get_column(),
            selector=self.get_selector(),
        )

    def equals(self, other):
        other = self.convert(other)
        return self.to_pandas().equals(other.to_pandas())

    def transpose(self):
        return self.from_pandas(
            self.to_pandas().transpose()
            )

    def dot(self, other):
        other = self.convert(other)
        return self.from_pandas(
            self.dot(self.to_pandas(), other.to_pandas()),
        )

    def isna(self):
        return self.__class__(
            data=self.to_pandas().isna(),
            colspecs=self._colspecs,
            index=self.get_index(),
            column = self.get_column(),
            selector = self.get_selector(),
        )

    def isnull(self):
        return self.isna()

    def notna(self):
        return ~self.isna()

    def fillna(self, *args, **kwargs):
        return self.__class__(
            data=self.to_pandas().fillna(*args, **kwargs),
            colspecs=self._colspecs,
            index=self.get_index(),
            column=self.get_column(),
            selector=self.get_selector(),
            )
        
    def dropna(self):
        vals = self.to_pandas().isna()
        if self.get_index() not in vals.index:
            ind = None
        else:
            ind = self.get_index()

        if self.get_column() not in vals.columns:
            col = None
        else:
            col = self.get_column()

        if self.get_selector() is None or self.get_selector() not in vals.columns:
            sel = None
        else:
            sel = self.get_selector()
            
        return self.__class__(
            data=vals,
            colspecs=self._colspecs,
            index = ind,
            column = col,
            selector = sel,
        )

    def drop_duplicates(self, *args, **kwargs):
        vals = self.to_pandas().drop_duplicates(*args, **kwargs)
        if self.get_index() not in vals.index:
            index = None
        else:
            index = self.get_index()
        return self.__class__(
            data=vals,
            colspecs=self._colspecs,
            index=index,
            column=self.get_column(),
            selector=self.get_selector(),
        )

    def groupby(self, *args, **kwargs):
        """
        Group DataFrame using a mapper or by a Series of columns.

        :param args: Positional arguments to be passed to pandas.DataFrame.groupby.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.groupby.
        :return: A grouped CustomDataFrame object.
        """
        vals = self.to_pandas().groupby(*args, **kwargs)
        if self.get_index() not in vals.index:
            index = None
        else:
            index = self.get_index()
            
        return self.__class__(
            data=vals,
            colspecs=self._colspecs,
            index=index,
            column=self.get_column(),
            selector=self.get_selector(),
        )
    
    def pivot_table(self, *args, **kwargs):
        """
        Create a pivot table as a CustomDataFrame.

        :param args: Positional arguments to be passed to pandas.DataFrame.pivot_table.
        :param kwargs: Keyword arguments to be passed to pandas.DataFrame.pivot_table.
        :return: A pivoted CustomDataFrame object.
        """
        return self.__class__(
            data=self.to_pandas().pivot_table(*args, **kwargs),
            )

    def _colspecs(self):
        """
        Define the column specifications.

        :return: Column specifications.
        """
        return None
    
    def _apply_operator(self, other, operator):
        """
        Apply a specified operator to the DataFrame.

        :param other: The right-hand operand.
        :param operator: The operator function to apply.
        :return: A new instance of CustomDataFrame after applying the operator.
        """
        other = self.convert(other)
        method = getattr(self.to_pandas(), operator)
        return self.__class__(
            data=method(other.to_pandas()),
            colspecs=self._colspecs,
            index=self.get_index(),
            column=self.get_column(),
            selector=self.get_selector()
        )
    
    @property
    def T(self):
        """
        Transpose the DataFrame.

        :return: Transposed CustomDataFrame.
        """
        return self.transpose()

    @property
    def shape(self):
        """
        Return the shape of the DataFrame.

        :return: A tuple representing the DataFrame's dimensions.
        """
        return self.to_pandas().shape

    @property
    def columns(self):
        """
        Return the column labels of the DataFrame.

        :return: Index object containing the column labels.
        """
        return self.to_pandas().columns

    @property
    def index(self):
        """
        Return the index (row labels) of the DataFrame.

        :return: Index object containing the row labels.
        """
        return self.to_pandas().index

    @property
    def values(self):
        """
        Return the values of the DataFrame as a NumPy array.

        :return: A NumPy array of the DataFrame's values.
        """
        return self.to_pandas().values

    @property
    def colspecs(self):
        """
        Return the column specifications.

        :return: Column specifications.
        """
        return self._colspecs

    @property
    def types(self):
        """
        Return the data types of the DataFrame.

        :return: A Series with the data type of each column.
        """
        return self._types

    # Operators
    def __add__(self, other):
        """
        Overload the addition ('+') operator.

        :param other: The right-hand operand for addition.
        :return: The result of adding the CustomDataFrame and other.
        """
        return self.add(other)

    def __sub__(self, other):
        """
        Overload the subtraction ('-') operator.

        :param other: The right-hand operand for subtraction.
        :return: The result of subtracting other from the CustomDataFrame.
        """
        return self.subtract(other)

    def __mul__(self, other):
        """
        Overload the multiplication ('*') operator.

        :param other: The right-hand operand for multiplication.
        :return: The result of multiplying the CustomDataFrame and other.
        """
        return self.multiply(other)

    def __invert__(self):
        """
        Overload the bitwise NOT ('~') operator.

        :return: The result of bitwise NOT of the CustomDataFrame.
        """
        return self.__class__(
            data=~self.to_pandas(),
            colspecs=self._colspecs,
            index=self.get_index(),
            column=self.get_column(),
            selector=self.get_selector()
        )

    def __neg__(self):
        """
        Overload the unary negation ('-') operator.

        :return: The result of negating the CustomDataFrame.
        """
        return self.__class__(
            data=-self.to_pandas(),
            colspecs=self._colspecs,
            index=self.get_index(),
            column=self.get_column(),
            selector=self.get_selector()
        )

    def __truediv__(self, other):
        """
        Overload the true division ('/') operator.

        :param other: The right-hand operand for division.
        :return: The result of true division of the CustomDataFrame by other.
        """
        other = self.convert(other)
        return self.__class__(
            data=self.to_pandas()/other.to_pandas(),
            colspecs=self._colspecs,
            index=self.get_index(),
            column = self.get_column(),
            selector= self.get_selector(),
        )

    def __floordiv__(self, other):
        """
        Overload the floor division ('//') operator.

        :param other: The right-hand operand for floor division.
        :return: A new instance of CustomDataFrame after floor division.
        """
        other = self.convert(other)
        return self.__class__(
            data=self.to_pandas() // other.to_pandas(),
            colspecs=self._colspecs,
            index=self.get_index(),
            column=self.get_column(),
            selector=self.get_selector(),
        )

    def __matmul__(self, other):
        """
        Overload the matrix multiplication ('@') operator.

        :param other: The right-hand operand for matrix multiplication.
        :return: The result of the matrix multiplication.
        """
        return self.dot(other)

    def __pow__(self, exponent):
        """
        Overload the power ('**') operator.

        :param exponent: The exponent to raise the dataframe to.
        :return: A new instance of CustomDataFrame after raising to the power.
        """
        return self.__class__(
            data=self.to_pandas() ** exponent,
            colspecs=self._colspecs,
            index=self.get_index(),
            column=self.get_column(),
            selector=self.get_selector(),
        )

    def __eq__(self, other):
        """
        Overload the equality ('==') operator.

        :param other: The right-hand operand for comparison.
        :return: The result of the equality comparison.
        """
        return self._apply_operator(other, "__eq__")

    def __gt__(self, other):
        """
        Overload the greater than ('>') operator.

        :param other: The right-hand operand for comparison.
        :return: The result of the greater than comparison.
        """
        return self._apply_operator(other, "__gt__")

    def __lt__(self, other):
        """
        Overload the less than ('<') operator.

        :param other: The right-hand operand for comparison.
        :return: The result of the less than comparison.
        """
        return self._apply_operator(other, "__lt__")

    def __ge__(self, other):
        """
        Overload the greater than or equal to ('>=') operator.

        :param other: The right-hand operand for comparison.
        :return: The result of the greater than or equal to comparison.
        """
        return self._apply_operator(other, "__ge__")

    def __le__(self, other):
        """
        Overload the less than or equal to ('<=') operator.

        :param other: The right-hand operand for comparison.
        :return: The result of the less than or equal to comparison.
        """
        return self._apply_operator(other, "__le__")

    def __ne__(self, other):
        """
        Overload the not equal ('!=') operator.

        :param other: The right-hand operand for comparison.
        :return: The result of the not equal comparison.
        """
        return self._apply_operator(other, "__ne__")

    def __array__(self, dtype=None):
        """
        Convert the CustomDataFrame to a NumPy array.

        :param dtype: The desired data-type for the array.
        :return: A NumPy array representation of the CustomDataFrame.
        """
        return np.array(self.to_pandas(), dtype=dtype)

    def __getitem__(self, key):
        """
        Get item or slice from the DataFrame.

        :param key: The key or slice to access elements of the DataFrame.
        :return: A subset of the DataFrame corresponding to the given key.
        """
        df = self.to_pandas()[key]
        if isinstance(df, pd.Series):
            df = df.to_frame()
        if self.get_index() in df.index:
            index=self.get_index()
        else:
            index=None
        if self.get_column() in df.columns:
            column=self.get_column()
        else:
            column=None
        if self.get_selector() in df.columns:
            selector=self.get_selector()
        else:
            selector=None

        colspecs = {"cache" : df.columns}
        return self.__class__(
            data=df,
            colspecs=colspecs,
            index=index,
            column=column,
            selector=selector,
        )            

    def __setitem__(self, key, value):
        raise NotImplementedError("This is a base class")
    
    def __iter__(self):
        for column in self.columns:
            yield column
            
    def __str__(self):
        return str(self.to_pandas())

    def __repr__(self):
        return repr(self.to_pandas())

    
class CustomDataFrame(DataObject):
    def __init__(self, data,
                 colspecs=None,
                 index=None,
                 column=None,
                 selector=None,
                 types=None):
        
        if isinstance(data, dict):
            entries = data.values()
            if all([isinstance(entry, (int, float, str, bool, complex)) for entry in entries]):
                data = pd.Series(data).to_frame().T
            data = pd.DataFrame(data)
        if isinstance(data, pd.Series):
            data = data.to_frame(name=data.name).T
        if data is None:
            data = {}
        if isinstance(data, dict):
            data = pd.DataFame(data)
        if isinstance(data, list):
            data = pd.DataFame(data)

        if types is None:
            types = {
                "parameters" : [
                    "constants",
                    "global_consts",
                    "parameters",
                    "globals",
                    "parameter_cache",
                    "global_cache",
                ],
                "input" : [
                    "input",
                    "data",
                    "constants",
                    "global_consts",
                ],
                "output" : [
                    "output",
                    "writedata",
                    "writeseries",
                    "parameters",
                    "globals",
                ],
                "cache" : [
                    "cache",
                    "parameter_cache",
                    "global_cache",
                ],
                "series" : [
                    "writeseries",
                ],
            }

            
            
        if colspecs is None:
            colspecs = {
                "cache" : list(data.columns)
            }
        columns = [col for cols in colspecs.values() for col in cols]
        cache = [col for col in data.columns if col not in columns]
        if len(cache)>0:
            if "cache" not in colspecs:
                colspecs["cache"] = []
            colspecs["cache"] += cache

        self._types = types
        self._colspecs = colspecs
        self._d = {}
            
        self._distribute_data(data)
                                
        if index is None:
            index = self.index[0]
        self.set_index(index)

        if column is None:
            column = self.columns[0]
        self.set_column(column)
        
        if selector is None:
            selector = self.columns[0]
        self.set_selector(selector)
            
        self.at = self._AtAccessor(self)
        self.loc = self._LocAccessor(self)
        self.iloc = self._IlocAccessor(self)

    class _AtAccessor(Accessor):
        def __init__(self, data):
            super().__init__(data=data)

        def __getitem__(self, key):
            return self._data_object._d["cache"].at[key]

        def __setitem__(self, key, value):
            self._data_object._d["cache"].at[key] = value
        
    class _LocAccessor(Accessor):
        def __init__(self, data):
            super().__init__(data=data)

        def __getitem__(self, key):
            return self._data_object._d["cache"].loc[key]

        def __setitem__(self, key, value):
            self._data_object._d["cache"].loc[key] = value
            
    class _IlocAccessor(Accessor):
        def __init__(self, data):
            super().__init__(data=data)

        def __getitem__(self, key):
            return self._data_object._d["cache"].iloc[key]

        def __setitem__(self, key, value):
            self._data_object._d["cache"].iloc[key] = value

    def _distribute_data(self, data):
        """Distribute input data according to the colspec."""
        # Distribute data across names columns
        for typ, cols in self._colspecs.items():
            if typ in self._types["parameters"]:
                self._d[typ] = pd.Series(index=cols, data=None)
                for col in cols:
                    if all(data[col]==data[col].iloc[0]):
                        self._d[typ][col] = data[col].iloc[0]
                    else:
                        raise ValueError(f"Column \"{col}\" is specified as a parameter column and yet the values of the column are not all the same..")
            else:
                d = data[cols]
                if typ in self._types["series"]:
                    self._d[typ] = d
                else:
                    # If it's not a series type make sure it's deduplicated.
                    self._d[typ] = d[~d.index.duplicated(keep='first')]
                    if len(d.index) > len(self._d[typ]):
                        self._log.debug("Removing duplicated elements from \"{typ}\" loaded data.")

    def to_pandas(self):
        """Concatenate the dataframes from _d."""
        df1 = pd.DataFrame()
        for typ, data in self._d.items():
            if typ in self._types["parameters"]:
                if len(df1.index)==0:
                    ind = data.name if data.name is not None else 0
                    for col in data.index:
                        df1.at[ind, col] = data[col]
                else:
                    df.assign(**data)
            else:
                df1 = df1.join(data, how="outer")
        return df1
                        
    def from_pandas(self, df, inplace=False):
        """Convert from a pandas data frame to a CustomDataFrame"""
        if inplace:
            self._distribute_data(df)
        else:
            return self.__class__(
                df,
                self._colspecs,
                self.get_selector(),
                self.get_index(),
                self.get_column()
            )
                        
    def filter(self, *args, **kwargs):
        return self.from_pandas(
            self.to_pandas().filter(*args, **kwargs)
        )
    
    def sort_values(self, *args, inplace=False, **kwargs):
        df = self.to_pandas().sort_values(
            *args,
            inplace=False,
            **kwargs,
        )
        return self.from_pandas(df, inplace=inplace)
    
    def sort_index(self, *args, inplace=False, **kwargs):
        df = self.to_pandas().sort_index(
            *args,
            inplace=False,
            **kwargs
        )
        return self.from_pandas(df, inplace=inplace)



    def __setitem__(self, key, value):
        self._d["output"][key] = value

    
def concat(objs, *args, **kwargs):
    df = pd.concat(
        [obj.to_pandas() for obj in objs],
        *args,
        **kwargs
    )
    colspecs = {}
    for obj in objs:
        colspecs.update(obj.colspecs)
    
    return obj.__class__(df, colspecs, types=obj[0].types)
