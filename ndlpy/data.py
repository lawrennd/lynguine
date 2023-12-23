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
        
    def get_value(self):
        return self.at[self._index, self._column]

    def set_value(self, val):
        self.at[self._index, self._column] = val

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
        raise NotImplementedError("This is a base class")

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

    @classmethod
    def from_csv(cls, *args, **kwargs):        
        return cls.from_pandas(df=pd.read_csv(*args, **kwargs))

    @classmethod
    def from_dict(cls, data, *args, **kwargs):
        return cls.from_pandas(df=pd.DataFrame.from_dict(data, *args, **kwargs))

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
            return self.__class__(other)
        elif isinstance(other, np.ndarray):
            if other.shape == self.shape:
                return self.__class__(
                    data=pd.DataFrame(other,
                                      index=self.index,
                                      columns=self.columns,
                                      ),
                    colspecs=self._colspecs,
                    index=self._index,
                    column=self._column
                )
            elif len(other.shape) == 1 and other.shape[0] == self.shape[0]:
                return self.__class__(data=pd.DataFrame(other, index=self.index, columns=[self._column]), index=self._index, column=self._column)
            elif other.shape[1] == 1 and other.shape[0] == self.shape[0]:
                return self.__class__(data=pd.DataFrame(other, index=self.index, columns=[self._column]), index=self._index, column=self._column)
            elif other.shape[0] == 1 and other.shape[1] == self.shape[1]:
                return self.__class__(data=pd.DataFrame(other, columns=self.columns, index=[self._index]), index=self._index, column=self._column)
            # Broadcast cases
            elif other.shape[0] == 1 and other.shape[1] == self.shape[0]:
                return self.__class__(data=pd.DataFrame(other, columns=self.index, index=[self._column]), index=self._index, column=self._column)
            elif other.shape[1] == 1 and other.shape[0] == self.shape[1]:
                return self.__class__(data=pd.DataFrame(other, index=self.columns, columns=[self._index]), index=self._index, column=self._column)
                
        elif isinstance(other, list):
            return self.convert(np.array(other))
        elif isinstance(other, dict):
            return self.convert(pd.DataFrame(other))
        else:
            return other
        
        
        
    # Mathematical operations
    def sum(self, axis=0):
        if axis == 0:
            column = self._column
            colspecs = {"parameter_cache": list(self.columns)}
        else:
            column = self._index
            colspecs = {"parameter_cache": list(self.index)}

        return self.__class__(
            data=self.to_pandas().sum(axis),
            colspecs=colspecs,
            types=self.types,
            column=column,
        )

    def mean(self, axis=0):
        if axis == 0:
            column = self._column
            colspecs = {"parameter_cache": list(self.columns)}
        else:
            column = self._index
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
            index=self._index,
            column=self._column,
            selector=self._selector,
        )

    def subtract(self, other):
        other = self.convert(other)
        return self.__class__(
            data=self.to_pandas().subtract(other.to_pandas()),
            colspecs=self._colspecs,
            index=self._index,
            column=self._column,
            selector=self._selector,
        )

    def multiply(self, other):
        other = self.convert(other)
        return self.__class__(
            data=self.to_pandas().multiply(pd.DataFrame(other.to_pandas())),
            colspecs=self._colspecs,
            index=self._index,
            column=self._column,
            selector=self._selector,
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
            data=self.to_pandas().fillna(*args, **kwargs),
            colspecs=self._colspecs,
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
            data=vals,
            colspecs=self._colspecs,
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
            data=vals,
            colspecs=self._colspecs,
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
            data=vals,
            colspecs=self._colspecs,
            index=index,
            column=self._column,
            selector=self._selector,
        )
    
    def pivot_table(self, *args, **kwargs):
        return self.__class__(
            data=self.to_pandas().pivot_table(*args, **kwargs),
            )

    def _colspecs(self):
        return None
    
    def _apply_operator(self, other, operator):
        """Helper functions for pandas comparison operators."""
        other = self.convert(other)
        method = getattr(self.to_pandas(), operator)
        return self.__class__(
            data=method(other.to_pandas()),
            colspecs=self._colspecs,
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

    @property
    def colspecs(self):
        return self._colspecs

    @property
    def types(self):
        return self._types
    
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
        return self.__class__(
            data=~self.to_pandas(),
            colspecs=self._colspecs,
            index=self._index,
            column=self._column,
            selector=self._selector
        )

    def __neg__(self):
        # Overloading the unary '-' operator
        return self.__class__(
            data=-self.to_pandas(),
            colspecs=self._colspecs,
            index=self._index,
            column=self._column,
            selector=self._selector
        )
    
    def __truediv__(self, other):
        # Overloading the '/' operator
        other = self.convert(other)
        return self.__class__(
            data=self.to_pandas()/other.to_pandas(),
            colspecs=self._colspecs,
            index=self._index,
            column = self._column,
            selector= self._selector,
        )

    def __floordiv__(self, other):
        # Overloading the '//' operator
        other = self.convert(other)
        return self.__class__(
            data=self.to_pandas()//other.to_pandas(),
            colspecs=self._colspecs,
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
            data=self.to_pandas()**exponent,
            colspecs=self._colspecs,
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
        df = self.to_pandas()[key]
        if isinstance(df, pd.Series):
            df = df.to_frame()
        if self._index in df.index:
            index=self._index
        else:
            index=None
        if self._column in df.columns:
            column=self._column
        else:
            column=None
        if self._selector in df.columns:
            selector=self._selector
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

        self._index = index
        self._column = column
        self._selector = selector
        self._types = types
        self._colspecs = colspecs
        self._d = {}
            
        self._distribute_data(data)
                                
        if index is None:
            index = data.index[0]

        if column is None:
            column = data.columns[0]

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
                self._selector,
                self._index,
                self._column
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
