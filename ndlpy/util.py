import datetime
import math
import re
import os
import wget



import sys

import argparse
import numpy as np

import pandas as pd
import ndlpy.data as nd

import ndlpy.access as access

import ndlpy.context as context
from ndlpy.log import Logger

cntxt = context.Context(name="ndlpy")
log = Logger(
    name=__name__,
    level=cntxt["logging"]["level"],
    filename=cntxt["logging"]["filename"]
)



"""Utility functions for helping, e.g. to create the relevant yaml files quickly."""
def extract_full_filename(details):
    """
    Return the filename from the details of directory and filename

    :param details: The details of the file to be extracted.
    :type details: dict
    :return: The filename.
    :rtype: str
    """
    if "directory" not in details or details["directory"] is None:
        return details["filename"]
    return os.path.join(
        os.path.expandvars(details["directory"]),
        details["filename"],
    )

def extract_root_directory(directory, environs=["HOME", "USERPROFILE", "TEMP", "TMPDIR", "TMP"]):
    """
    Extract a root directory and a subdirectory from a given directory string.

    :param directory: The directory to extract from.
    :type directory: str
    :return: The root directory and subdirectory.
    :rtype: tuple
    """

    if directory is None:
        return None, None

    # Extract a list of environment variables from the directory string
    environs = re.findall(r"\$([A-Za-z0-9_]+)", directory) + environs

    # Replace the environment variables with their values
    directory = os.path.expandvars(directory)

    # Find absolute path of the current working directory.
    cwd = os.path.abspath(os.getcwd())
    
    # Extract the root directory and subdirectory
    # If path contains cwd, return that as root and the rest as subdirectory
    if cwd in directory:
        return sub_path_environment(cwd, environs), directory.replace(cwd, ".").replace("./", "")
    else:
        # IF directory is not current, assume it is a root and a subdirectory, extracting each one.
        root, directory = os.path.split(directory)
        return sub_path_environment(root), directory
        
def extract_file_type(filename):
    """
    Return a standardised file type.

    :param filename: The filename to be extracted.
    :type filename: str
    :return: The standardised file type.
    :rtype: str
    """
    ext = os.path.splitext(filename)[1][1:]
    if ext in ["md", "mmd", "markdown", "html"]:
        return "markdown" 
    if ext in ["csv"]:
        return "csv" 
    if ext in ["xls", "xlsx", "markdown", "html"]:
        return "excel"
    if ext in ["yml", "yaml"]:
        return "yaml"
    if ext in ["bib", "bibtex"]:
        return "bibtex"
    if ext in ["docx"]:
        return "docx"
    raise ValueError(f"Unrecognised type of file in \"{filename}\"")


def extract_abs_filename(details):
    """
    Return the absolute filename by adding current directory if it's not present

    :param details: The details of the file to be extracted.
    :type details: dict
    :return: The absolute filename.
    :rtype: str
    
    """
    return os.path.abspath(extract_full_filename(details))

def camel_capitalize(text):
    """
    Capitalize the text in camel case.

    :param text: The text to be capitalized.
    :type text: str
    :return: The capitalized text.
    """
    if text == text.upper():
        return text
    else:
        return text.capitalize()

def remove_nan(dictionary):
    """
    Delete missing entries from dictionary

    :param dictionary: The dictionary to be cleaned.
    :type dictionary: dict
    :return: The dictionary with missing entries removed.
    :rtype: dict
    """
    dictionary2 = dictionary.copy()
    for key, entry in dictionary.items():
        if type(entry) is dict:
            dictionary2[key] = remove_nan(entry)
        else:
            isna = entry is None or (type(entry) is float and math.isnan(entry)) # Switched from pd.isna
            if type(isna) is bool and isna:
                del(dictionary2[key])
    return dictionary2


def to_valid_var(variable):
    """
    Replace invalid variable name characters with underscore

    :param variable: The variable name to be converted.
    :type variable: str
    :return: The variable name converted to a valid variable name.
    """
    return re.sub(r'\W|^(?=\d)','_', variable.lower())

def to_camel_case(text):
    """
    Remove non alpha-numeric characters and convert to camel case.

    :param text: The text to be converted.
    :type text: str
    :return: The text converted to camel case.
    :rtype: str
    """

    if len(text) == 0:
        raise ValueError(f"Provided a zero length string to convert to camel case.")
    
    # Remove non alpha-numeric characters
    text = text.replace("/", " or ")
    text = text.replace("@", " at ")
    non_alpha_chars = set([ch for ch in set(list(text)) if not ch.isalnum()])
    if len(non_alpha_chars) > 0:
        for ch in non_alpha_chars:
            text = text.replace(ch, " ")

    s = text.split()
    if s[0] == s[0].capitalize() or s[0] == s[0].upper():
        start = s[0]
    else:
        start = s[0].lower()

    if len(s)>1:
        return start + ''.join(camel_capitalize(i) for i in s[1:])
    else:
        return start

def sub_path_environment(path, environs=["HOME", "USERPROFILE", "TEMP", "TMPDIR", "TMP"]):
    """
    Replace a path with values from environment variables.

    :param path: The path to be replaced.
    :type path: str
    :param environs: The environment variables to be replaced.
    :type environs: list
    :return: The path with environment variables replaced.
    :rtype: str
    """
    for var in environs:
        if var in os.environ:
            path = path.replace(os.environ[var], "$" + var)
    return path

def get_path_env(environs=["HOME", "USERPROFILE", "TEMP", "TMPDIR", "TMP"]):
    """
    Return the current path with environment variables.

    :return: The current path with environment variables replacing.
    :rtype: str
    """
    return sub_path_environment(os.path.abspath(os.getcwd()), environs)
                                        
def get_url_file(url, directory=None, filename=None, ext=None):
    """
    Download a file from a url and save it to disk.

    :param url: The url of the file to be downloaded.
    :type url: str
    :param directory: The directory to save the file to
    :type directory: str
    :param filename: The filename to save the file to
    :type filename: str
    :param ext: The extension to save the file to
    :type ext: str
    :return: The filename of the downloaded file
    :rtype: str
    """
    try:
        dfilename = wget.download(url)
    except:
        return ""
    if filename is None:
        return dfilename
    else:
        if ext is None:
            ext = os.path.splitext(dfilename)[1][1:]
        filename+="." + ext
        if directory is not None:
            filename = os.path.join(directory,filename)
        os.rename(dfilename, filename)
        return filename                  
    


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
            df[column] = pd.to_numeric(df[column]).apply(lambda x: int(x) if not pd.isna(x) else pd.NA).astype('Int64')
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
        if isinstance(field, int): # Assume it is integer year
            log.debug(f"Returning \"{type_field}\" from form \"{field}\"")
            dt = datetime.datetime(year=field, month=month, day=day)
        elif isinstance(field, str):
            try:
                year = int(field) # Try it as string year
                log.debug(f"Returning \"{type_field}\" from form \"{field}\"")
                dt = datetime.datetime(year=year, month=month, day=day)
            except TypeError as e:
                log.debug(f"Returning \"{type_field}\" from form \"{field}\"")
                dt = datetime.datetime.strptime(field, "%Y-%m-%d") # Try it as string YYYY-MM-DD
        elif isinstance(field, datetime.date):
            log.debug(f"Returning \"{type_field}\" from form \"{field}\"")
            return field
        else:
            raise TypeError(f"Expecting type of int or str or datetime but found \"{type_field}\"")
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

def augmentmonth(df, destination='month', source="date"):
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
    fstr=f"{{0:,.{sf}f}}"
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
    return df[column]>=since_year

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
    within = ((df[start] <= now) & (pd.isna(df[end]) | (df[end] >= now)))
    if current is not None:
        return (within | (~df[current].isna() & df[current]))
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
    return (df[end] < now)

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
    
    return (df[column]==value)

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
    return (colis | df[column].apply(lambda x: x == value or (hasattr(x, '__contains__') and value in x)))
