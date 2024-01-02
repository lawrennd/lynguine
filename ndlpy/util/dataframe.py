import datetime
import math
import numpy as np
import pandas as pd

import ndlpy.config.context as context
from ndlpy.log import Logger



cntxt = context.Context(name="ndlpy")
log = Logger(
    name=__name__,
    level=cntxt["logging"]["level"],
    filename=cntxt["logging"]["filename"],
)

def convert_datetime_to_str(df):
    """
    Convert datetime columns to strings in isoformat for ease of writing.

    :param df: The DataFrame to convert.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :return: The converted DataFrame.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFram
    """
    write_df = df.copy(deep=True)
    for col in df.select_dtypes(include=["datetime64"]).columns.tolist():
        date_series = pd.Series(index=df.index, name=col, dtype="object")
        for ind, val in df[col].items():
            if pd.isnull(val):
                date_series.at[ind] = None
            else:
                date_series.at[ind] = val.strftime("%Y-%m-%d %H:%M:%S.%f")

        write_df[col] = date_series
    return write_df

def reorder_dataframe(df, order):
    """
    This function reorders the given data frame columns with the order given by the columns listed in order and any remaining columns placed alphabetically after order.

    :param df: The DataFrame to reorder.
    :type df: pd.DataFrame or ndlpy.data.CustomDataFrame
    :
    """
    # Remove any columns from order that are not in the dataframe
    order = [column for column in order if column in df.columns]
    remaining = [column for column in df.columns if column not in order]
    return df[order + sorted(remaining)]


## Preprocessors
def convert_datetime(df, columns):
    """Preprocessor to set datetime type on columns."""
    if type(columns) is not list:
        columns = [columns]
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column])
    return df


def convert_int(df, columns):
    """
    Preprocessor to set integer type on columns.

    :param df: The dataframe to be converted.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param columns: The columns to be converted.
    :type columns: list
    :return: The converted dataframe.
    :rtype: pandas.DataFrame
    """
    if type(columns) is not list:
        columns = [columns]
    for column in columns:
        if column in df.columns:
            df[column] = (
                pd.to_numeric(df[column])
                .apply(lambda x: int(x) if not pd.isna(x) else pd.NA)
                .astype("Int64")
            )
    return df


def convert_string(df, columns):
    """
    Preprocessor to set string type on columns.

    :param df: The dataframe to be converted.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param columns: The columns to be converted.
    :type columns: list
    :return: The converted dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    if type(columns) is not list:
        columns = [columns]
    for column in columns:
        if column in df.columns:
            df[column] = df[column].apply(lambda x: str(x) if not pd.isna(x) else pd.NA)
    return df


def convert_year_iso(df, column="year", month=1, day=1):
    """
    Preprocessor to set string type on columns.

    :param df: The dataframe to be converted.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param columns: The columns to be converted.
    :type columns: list
    :return: The converted dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """

    def year_to_iso(field):
        """
        Convert a year field to an iso date using the provided month and day.

        :param field: The field to be converted.
        :type field: int or str or datetime.date
        :return: The converted date.
        :rtype: datetime.date
        :raises TypeError: If the field is not of type int or str or datetime.date
        :raises ValueError: If the field is not a valid date
        """
        type_field = type(field)
        if isinstance(field, int):  # Assume it is integer year
            log.debug(f'Returning "{type_field}" from form "{field}"')
            dt = datetime.datetime(year=field, month=month, day=day)
        elif isinstance(field, str):
            try:
                year = int(field)  # Try it as string year
                log.debug(f'Returning "{type_field}" from form "{field}"')
                dt = datetime.datetime(year=year, month=month, day=day)
            except TypeError as e:
                log.debug(f'Returning "{type_field}" from form "{field}"')
                dt = datetime.datetime.strptime(
                    field, "%Y-%m-%d"
                )  # Try it as string YYYY-MM-DD
        elif isinstance(field, datetime.date):
            log.debug(f'Returning "{type_field}" from form "{field}"')
            return field
        else:
            raise TypeError(
                f'Expecting type of int or str or datetime but found "{type_field}"'
            )
        return dt

    df[column] = df[column].apply(year_to_iso)
    return df


## Augmentors
def addmonth(df, source="date"):
    """
    Add month column based on source date field.

    :param df: The dataframe to be augmented.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param source: The source column to be used.
    :type source: str
    :return: The augmented dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :raises KeyError: If the source column is not in the dataframe
    :raises TypeError: If the source column is not of type datetime.date
    :raises ValueError: If the source column is not a valid date
    """
    return df[source].apply(lambda x: x.month_name() if x is not None else pd.NA)


def addyear(df, source="date"):
    """
    Add year column and based on source date field.

    :param df: The dataframe to be augmented.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param source: The source column to be used.
    :type source: str
    :return: The augmented dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    return df[source].apply(lambda x: x.year if x is not None else pd.NA)


def augmentmonth(df, destination="month", source="date"):
    """
    Augment the month column based on source date field.

    :param df: The dataframe to be augmented.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param destination: The destination column to be used.
    :type destination: str
    :param source: The source column to be used.
    :type source: str
    :return: The augmented dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    val = pd.Series(index=df.index, dtype=object)
    for index, entry in df.iterrows():
        if pd.isna(df.at[index, destination]) and not pd.isna(df.at[index, source]):
            val[index] = df.at[index, source].month_name()
        else:
            val[index] = df.at[index, destination]
    return val


def augmentyear(df, destination="year", source="date"):
    """
    Augment the year column based on source date field.

    :param df: The dataframe to be augmented.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param destination: The destination column to be used.
    :type destination: str
    :param source: The source column to be used.
    :type source: str
    :return: The augmented dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    val = pd.Series(index=df.index)
    for index, entry in df.iterrows():
        if pd.isna(df.at[index, destination]) and not pd.isna(df.at[index, source]):
            val[index] = df.loc[index, source].year
        else:
            val[index] = df.at[index, destination]
    return val


def augmentcurrency(df, source="amount", sf=0):
    """
    Preprocessor to set integer type on columns.

    :param df: The dataframe to be converted.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param columns: The columns to be converted.
    :type columns: list
    :return: The converted dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    fstr = f"{{0:,.{sf}f}}"
    return df[source].apply(lambda x: fstr.format(x))


def fillna(df, column, value):
    """
    Fill missing values in a column with a given value.

    :param df: The dataframe to be converted.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param column: The column to be converted.
    :type column: str
    :param value: The value to be used to fill missing values.
    :type value: str
    :return: The converted dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    return df[column].fillna(value)


## Sorters
def ascending(df, by):
    """
    Sort in ascending order

    :param df: The dataframe to be sorted.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param by: The column to be sorted by.
    :type by: str
    :return: The sorted dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    return df.sort_values(by=by, ascending=True)


def descending(df, by):
    """
    Sort in descending order

    :param df: The dataframe to be sorted.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param by: The column to be sorted by.
    :type by: str
    :return: The sorted dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    return df.sort_values(by=by, ascending=False)


## Filters
def recent(df, column="year", since_year=2000):
    """
    Filter on whether item is recent

    :param df: The dataframe to be filtered.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param column: The column to be filtered on.
    :type column: str
    :return: The filtered dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame

    """
    return df[column] >= since_year


def current(df, start="start", end="end", current=None, today=None):
    """
    Filter on whether the row is current as given by start and end dates. If current is given then it is used instead of the range check. If today is given then it is used instead of the current date.

    :param df: The dataframe to be filtered.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param start: The start date of the entry.
    :type start: str
    :param end: The end date of the entry.
    :type end: str
    :param current: Column of true/false current entries.
    :type current: str
    :param today: The date to be used as today.
    :type today: datetime.date
    :return: The filtered dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    if today is None:
        now = pd.to_datetime(datetime.datetime.now().date())
    else:
        now = today
    within = (df[start] <= now) & (pd.isna(df[end]) | (df[end] >= now))
    if current is not None:
        return within | (~df[current].isna() & df[current])
    else:
        return within


def former(df, end="end"):
    """
    Filter on whether item is former.

    :param df: The dataframe to be filtered.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param end: The end date of the entry.
    :type end: str
    :return: The filtered dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    now = pd.to_datetime(datetime.datetime.now().date())
    return df[end] < now


def onbool(df, column="current", invert=False):
    """
    Filter on whether column is positive (or negative if inverted)

    :param df: The dataframe to be filtered.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param column: The column to be filtered on.
    :type column: str
    :param invert: Whether to invert the filter.
    :type invert: bool
    :return: The filtered dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    if invert:
        return ~df[column]
    else:
        return df[column]


def columnis(df, column, value):
    """
    Filter on whether a given column is equal to a given value

    :param df: The dataframe to be filtered.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param column: The column to be filtered on.
    :type column: str
    :param value: The value to be used to filter.
    :return: The filtered dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """

    return df[column] == value


def columncontains(df, column, value):
    """
    Filter on whether column contains a given value

    :param df: The dataframe to be filtered.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param column: The column to be filtered on.
    :type column: str
    :param value: The value to be used to filter.
    :return: The filtered dataframe.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """
    colis = columnis(df, column, value)
    return colis | df[column].apply(
        lambda x: x == value or (hasattr(x, "__contains__") and value in x)
    )
