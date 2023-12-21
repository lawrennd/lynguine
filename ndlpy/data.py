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
    def __init__(self, data=None, selector=None, index=None, column=None):
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
        
    def get_value(self):
        return self._data.at[self._index, self._column]

    def set_value(self, val):
        self._data.at[self._index, self._column] = val

    def get_column(self):
        return self._column
    
    def set_column(self, column):
        self._column = column

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

    def head(self, n=5):
        self.to_pandas().head(n)

    def tail(self, n=5):
        self.to_pandas().tail(n)

    def add_column(self, column_name, data):
        raise NotImplementedError("This is a base class")

    def drop_column(self, column_name):
        raise NotImplementedError("This is a base class")

    def filter_rows(self, condition):
        raise NotImplementedError("This is a base class")

    def get_shape(self):
        return self.to_pandas().shape

    def describe(self):
        return self.to_pandas().describe()

    def to_pandas(self):
        return self._data

    def to_clipboard(self, *args, **kwargs):
        return self.to_pandas().to_clipboard(*args, **kwargs)

    def to_feather(self, *args, **kwargs):
        return self.to_pandas().to_feather(*args, **kwargs)

    def to_json(self, *args, **kwargs):
        return self.to_pandas().to_json(*args, **kwargs)

    def to_orc(self, *args, **kwargs):
        return self.to_pandas().to_orc(*args, **kwargs)

    def to_records(self, *args, **kwargs):
        return self.to_pandas().to_records(*args, **kwargs)

    def to_timestamp(self, *args, **kwargs):
        return self.to_pandas().to_timestamp(*args, **kwargs)

    def to_csv(self, *args, **kwargs):
        return self.to_pandas().to_csv(*args, **kwargs)

    def to_gbq(self, *args, **kwargs):
        return self.to_pandas().to_gbq(*args, **kwargs)

    def to_latex(self, *args, **kwargs):
        return self.to_pandas().to_latex(*args, **kwargs)

    def to_parquet(self, *args, **kwargs):
        return self.to_pandas().to_parquet(*args, **kwargs)

    def to_sql(self, *args, **kwargs):
        return self.to_pandas().to_sql(*args, **kwargs)

    def to_xarray(self, *args, **kwargs):
        return self.to_pandas().to_xarray(*args, **kwargs)

    def to_dict(self, *args, **kwargs):
        return self.to_pandas().to_dict(*args, **kwargs)

    def to_hdf(self, *args, **kwargs):
        return self.to_pandas().to_hdf(*args, **kwargs)

    def to_markdown(self, *args, **kwargs):
        return self.to_pandas().to_markdown(*args, **kwargs)

    def to_period(self, *args, **kwargs):
        return self.to_period().to_period(*args, **kwargs)
    
    def to_stata(self, *args, **kwargs):
        return self.to_pandas().tostata(*args, **kwargs)

    def to_xml(self, *args, **kwargs):
        return self.to_pandas().toxml(*args, **kwargs)

    def to_excel(self, *args, **kwargs):
        return self.to_pandas().to_excel(*args, **kwargs)

    def to_html(self, *args, **kwargs):
        return self.to_pandas().to_html(*args, **kwargs)

    def to_numpy(self, *args, **kwargs):
        return self.to_pandas().to_numpy(*args, **kwargs)

    def to_string(self, *args, **kwargs):
        return self.to_pandas().to_string(*args, **kwargs)

    def from_pandas(self, df):
        self._data = df
        self._column = df.columns[0]
        self._index = df.index[0]

    @classmethod
    def from_csv(cls, *args, **kwargs):        
        return cls(pd.read_csv(*args, **kwargs))
        
    def from_dict(self, data, *args, **kwargs):
        self.from_df(data=self._data.from_dict(data, *args, **kwargs))

    def sort_values(self, by, axis=0, ascending=True, inplace=False, **kwargs):
        raise NotImplementedError("This is a base class")

    def sort_index(self, axis=0, level=None, ascending=True, inplace=False, **kwargs):
        raise NotImplementedError("This is a base class")


    def convert(self, other):
        if isinstance(other, self.__class__):
            return other
        elif isinstance(other, pd.DataFrame):
            return self.__class__(other)
        elif isinstance(other, pd.Series):
            return self.__class__(other.to_frame())
        elif isinstance(other, np.ndarray):
            if other.shape == self.shape:
                return self.__class__(pd.DataFrame(other, index=self.index, columns=self.columns), index=self._index, column=self._column)
            elif len(other.shape) == 1 and other.shape[0] == self.shape[0]:
                return self.__class__(pd.DataFrame(other, index=self.index, columns=[self._column]), index=self._index, column=self._column)
            elif other.shape[1] == 1 and other.shape[0] == self.shape[0]:
                return self.__class__(pd.DataFrame(other, index=self.index, columns=[self._column]), index=self._index, column=self._column)
            elif other.shape[0] == 1 and other.shape[1] == self.shape[1]:
                return self.__class__(pd.DataFrame(other, columns=self.columns, index=[self._index]), index=self._index, column=self._column)
            # Broadcast cases
            elif other.shape[0] == 1 and other.shape[1] == self.shape[0]:
                return self.__class__(pd.DataFrame(other, columns=self.index, index=[self._column]), index=self._index, column=self._column)
            elif other.shape[1] == 1 and other.shape[0] == self.shape[1]:
                return self.__class__(pd.DataFrame(other, index=self.columns, columns=[self._index]), index=self._index, column=self._column)
                
        elif isinstance(other, list):
            return convert(self, np.array(other))
        elif isinstance(other, dict):
            return convert(self, pd.DataFrame(other))
        else:
            return other
        
        
        
    # Mathematical operations

    def sum(self, axis=0):
        if axis == 0:
            index = self._column
        else:
            index = self._index
        return self.__class__(
            self.to_pandas().sum(axis),
            index=index,
        )

    def mean(self, axis=0):
        if axis == 0:
            index = self._column
        else:
            index = self._index
        return self.__class__(
            self.to_pandas().mean(axis),
            index=index,
        )

    def add(self, other):
        other = self.convert(other)
        return self.__class__(
            self.to_pandas().add(other.to_pandas()),
            index=self._index,
            column=self._column,
            selector=self._selector,
        )

    def subtract(self, other):
        other = self.convert(other)
        return self.__class__(
            self.to_pandas().subtract(other.to_pandas()),
            index=self._index,
            column=self._column,
            selector=self._selector,
        )

    def multiply(self, other):
        other = self.convert(other)
        return self.__class__(
            self.to_pandas().multiply(pd.DataFrame(other.to_pandas())),
            index=self._index,
            column=self._column,
            selector=self._selector,
        )

    def equals(self, other):
        other = self.convert(other)
        return self.to_pandas().equals(other.to_pandas())

    def transpose(self):
        return self.__class__(self._data.transpose(), index=self._column, column=self._index)

    def dot(self, other):
        other = self.convert(other)
        return self.__class__(
            self.dot(self.to_pandas(), other.to_pandas()),
            index=self._index,
            column = other._column,
            selector= other._selector,
        )

    def isna(self):
        return self.__class__(
            self.to_pandas().isna(),
            index=self._index,
            column = self._column,
            selector = self._selector,
        )

    def isnull(self):
        return self.isna()

    def notna(self):
        return ~self.isna()

    def fillna(self, *args, **kwargs):
        return self.__class__(
            self.to_pandas().fillna(*args, **kwargs),
            index=self._index,
            column=self._column,
            selector=self._selector,
            )
        
    def dropna(self):
        vals = self.to_pandas().isna()
        if self._index not in vals.index:
            ind = None
        else:
            ind = self._index

        if self._column not in vals.columns:
            col = None
        else:
            col = self._column

        if self._selector is None or self._selector not in vals.columns:
            sel = None
        else:
            sel = self._selector
            
        return self.__class__(
            vals,
            index = ind,
            column = col,
            selector = sel,
        )

    def drop_duplicates(self, *args, **kwargs):
        vals = self.to_pandas().drop_duplicates(*args, **kwargs)
        if self._index not in vals.index:
            index = None
        else:
            index = self._index
        return self.__class__(
            vals,
            index=index,
            column=self._column,
            selector=self._selector,
        )

    def groupby(self, *args, **kwargs):
        vals = self.to_pandas().groupby(*args, **kwargs)
        if self._index not in vals.index:
            index = None
        else:
            index = self._index
            
        return self.__class__(
            vals,
            index=index,
            column=self._column,
            selector=self._selector,
        )
    
    def pivot_table(self, *args, **kwargs):
        return self.__class__(
            self.to_pandas().pivot_table(*args, **kwargs),
            )
    
    def _apply_operator(self, other, operator):
        """Helper functions for pandas comparison operators."""
        other = self.convert(other)
        method = getattr(self.to_pandas(), operator)
        return self.__class__(
            method(other.to_pandas()),
            index=self._index,
            column=self._column,
            selector=self._selector
        )
    
    @property
    def T(self):
        return self.transpose()
    
    @property
    def shape(self):
        return self.to_pandas().shape
    
    @property
    def columns(self):
        return self.to_pandas().columns

    @property
    def index(self):
        return self.to_pandas().index

    @property
    def values(self):
        return self.to_pandas().values

    # Operators
    def __add__(self, other):
        # Overloading the '+' operator
        return self.add(other)

    def __sub__(self, other):
        # Overloading the '-' operator
        return self.subtract(other)

    def __mul__(self, other):
        # Overloading the '*' operator
        return self.multiply(other)

    def __invert__(self):
        # Overloading the '~' operator
        return self.__class__(~self.to_pandas(),
                              index=self._index,
                              column=self._column,
                              selector=self._selector)

    def __neg__(self):
        # Overloading the unary '-' operator
        return self.__class__(-self.to_pandas(),
                              index=self._index,
                              column=self._column,
                              selector=self._selector)
    
    def __truediv__(self, other):
        # Overloading the '/' operator
        other = self.convert(other)
        return self.__class__(
            self.to_pandas()/other.to_pandas(),
            index=self._index,
            column = self._column,
            selector= self._selector,
        )

    def __floordiv__(self, other):
        # Overloading the '//' operator
        other = self.convert(other)
        return self.__class__(
            self.to_pandas()//other.to_pandas(),
            index=self._index,
            column = self._column,
            selector= self._selector,
        )
        
        
    def __matmul__(self, other):
        # Overloading the '@' operator
        return self.dot(other)

    def __pow__(self, exponent):
        # Overloading the '**' operator
        return self.__class__(
            self.to_pandas()**exponent,
            index = self._index,
            column = self._column,
            selector = self._selector,
        )
    
    def __eq__(self, other):
        # Overloading the '==' operator
        return self._apply_operator(other, "__eq__")

    def __gt__(self, other):
        return self._apply_operator(other, "__gt__")

    def __lt__(self, other):
        return self._apply_operator(other, "__lt__")

    def __ge__(self, other):
        return self._apply_operator(other, "__ge__")

    def __le__(self, other):
        return self._apply_operator(other, "__le__")

    def __eq__(self, other):
        return self._apply_operator(other, "__eq__")

    def __ne__(self, other):
        return self._apply_operator(other, "__ne__")
    
    def __array__(self, dtype=None):
        return np.array(self.to_pandas(), dtype=dtype)
    
    def __getitem__(self, key):
        vals = self.to_pandas()[key]
        if isinstance(vals, pd.Series):
            vals = vals.to_frame()
        if self._index in vals.index:
            index=self._index
        else:
            index=None
        if self._column in vals.columns:
            column=self._column
        else:
            column=None
        if self._selector in vals.columns:
            selector=self._selector
        else:
            selector=None
            
        return self.__class__(
            vals,
            index=index,
            column=column,
            selector=selector,
        )            

    def __setitem__(self, key, value):
        raise NotImplementedError("This is a base class")

    def __str__(self):
        raise NotImplementedError("This is a base class")

    def __repr__(self):
        raise NotImplementedError("This is a base class")

    
class DataFrame(DataObject):
    def __init__(self, data, selector=None, index=None, column=None):
        if isinstance(data, dict):
            data = pd.DataFrame(data)
        if isinstance(data, pd.Series):
            data = data.to_frame()
        self._data = data
        if index is None:
            index = data.index[0]
        self._index = index
        if column is None:
            column = data.columns[0]
        self._column = column
        self._selector = selector
        self.at = self._AtAccessor(self)
        self.loc = self._LocAccessor(self)
        self.iloc = self._IlocAccessor(self)

    class _AtAccessor(Accessor):
        def __init__(self, data):
            super().__init__(data=data)

        def __getitem__(self, key):
            return self._data_object._data.at[key]

        def __setitem__(self, key, value):
            self._data_object._data.at[key] = value
        
    class _LocAccessor(Accessor):
        def __init__(self, data):
            super().__init__(data=data)

        def __getitem__(self, key):
            return self._data_object._data.loc[key]

        def __setitem__(self, key, value):
            self._data_object._data.loc[key] = value
            
    class _IlocAccessor(Accessor):
        def __init__(self, data):
            super().__init__(data=data)

        def __getitem__(self, key):
            return self._data_object._data.iloc[key]

        def __setitem__(self, key, value):
            self._data_object._data.iloc[key] = value

    def add_column(self, column_name, data):
        self._data[column_name] = data

    def drop_column(self, column_name):
        self._data.drop(column_name, axis=1, inplace=True)

    def filter_rows(self, condition):
        return self._data[condition]

    def sort_values(self, by, axis=0, ascending=True, inplace=False, **kwargs):
        value = self._data.sort_values(by=by,
                                       axis=axis,
                                       ascending=ascending,
                                       inplace=inplace,
                                       **kwargs)
        if inplace:
            return value
        else:
            return DataFrame(value, self._selector, self._index, self._column)

    def sort_index(self, axis=0, level=None, ascending=True, inplace=False, **kwargs):
        value = self._data.sort_index(axis=axis,
                                      level=level, 
                                      scending=ascending,
                                      inplace=inplace,
                                      **kwargs)
        if inplace:
            return value
        else:
            return DataFrame(value, self._selector, self._index, self._column)


    def __setitem__(self, key, value):
        self._data[key] = value

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)
    
