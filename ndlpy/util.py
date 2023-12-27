from datetime import datetime
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
    """Return the filename from the details of directory and filename"""
    if "directory" not in details or details["directory"] is None:
        return details["filename"]
    return os.path.join(
        os.path.expandvars(details["directory"]),
        details["filename"],
    )

def extract_file_type(filename):
    """Return a standardised file type."""
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
    raise ValueError(f"Unrecognised type of file in \"\{filename}\"")


def extract_abs_filename(details):
    """Return the absolute filename by adding current directory if it's not present"""
    return os.path.abspath(extract_full_filename(details))

def camel_capitalize(text):
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
    return re.sub('\W|^(?=\d)','_', variable.lower())

def to_camel_case(text):
    """
    Remove non alpha-numeric characters and convert to camel case.

    :param text: The text to be converted.
    :type text: str
    :return: The text converted to camel case.
    :rtype: str
    """

    # Remove non alpha-numeric characters
    text = text.replace("/", " or ")
    text = text.replace("@", " at ")
    non_alpha_chars = set([ch for ch in set(list(text)) if not ch.isalnum()])
    if len(non_alpha_chars) > 0:
        for ch in non_alpha_chars:
            text = text.replace(ch, " ")
        s = text.split()
        if len(text) == 0:
            return A
        if s[0] == s[0].upper():
            start = s[0]
        else:
            start = s[0].lower()

        return start + ''.join(camel_capitalize(i) for i in s[1:])
    else:
        return text

def sub_path_environment(path, environs=["HOME", "USERPROFILE"]):
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

def get_path_env(environs=["HOME", "USERPROFILE"]):
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
    """Preprocessor to set integer type on columns."""
    if type(columns) is not list:
        columns = [columns]
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column]).apply(lambda x: int(x) if not pd.isna(x) else pd.NA).astype('Int64')
    return df


def convert_string(df, columns):
    """Preprocessor to set string type on columns."""
    if type(columns) is not list:
        columns = [columns]
    for column in columns:
        if column in df.columns:
            df[column] = df[column].apply(lambda x: str(x) if not pd.isna(x) else pd.NA)
    return df

def convert_year_iso(df, column="year", month=1, day=1):
    """Preprocessor to set string type on columns."""
    def year_to_iso(field):
        """Convert a year field to an iso date using the provided month and day."""
        type_field = type(field)
        if type_field is int: # Assume it is integer year
            log.debug(f"Returning \"{type_field}\" from form \"{field}\"")
            dt = datetime.datetime(year=field, month=month, day=day)
        elif type_field is str: 
            try:
                year = int(field) # Try it as string year
                log.debug(f"Returning \"{type_field}\" from form \"{field}\"")
                dt = datetime.datetime(year=year, month=month, day=day)
            except TypeError as e:
                log.debug(f"Returning \"{type_field}\" from form \"{field}\"")
                dt = datetime.datetime.strptime(field, "%Y-%m-%d") # Try it as string YYYY-MM-DD
        elif type_field is datetime.date:
            log.debug(f"Returning \"{type_field}\" from form \"{field}\"")
            return field
        else:
            raise TypeError(f"Expecting type of int or str or datetime but found \"{type_field}\"")
        return dt
        
    df[column] = df[column].apply(year_to_iso)
    return df
        
        

## Augmentors
def addmonth(df, source="date"):
    """Add month column based on source date field."""
    return df[source].apply(lambda x: x.month_name() if x is not None else pd.NA)

def addyear(df, source="date"):
    """Add year column and based on source date field."""
    return df[source].apply(lambda x: x.year if x is not None else pd.NA)

def augmentmonth(df, destination='month', source="date"):
    """Augment the  month column based on source date field."""
    val = pd.Series(index=df.index)
    for index, entry in df.iterrows():
        if pd.isna(df.at[index, destination]) and not pd.isna(df.at[index, source]):
            val[index] = df.at[index, source].month_name()
        else:
            val[index] = df.at[index, destination]
    return val

def augmentyear(df, destination="year", source="date"):
    """Augment the year column based on source date field."""
    val = pd.Series(index=df.index)
    for index, entry in df.iterrows():
        if pd.isna(df.at[index, destination]) and not pd.isna(df.at[index, source]):
            val[index] = df.loc[index, source].year
        else:
            val[index] = df.at[index, destination]
    return val

def augmentcurrency(df, source="amount", sf=0):
    """Preprocessor to set integer type on columns."""
    fstr=f"{{0:,.{sf}f}}"
    return df[source].apply(lambda x: fstr.format(x))


def addsupervisor(df, column, supervisor):
    return df[column].fillna(supervisor)    

## Sorters
def ascending(df, by):
    """Sort in ascending order"""
    return df.sort_values(by=by, ascending=True)

def descending(df, by):
    """Sort in descending order"""
    return df.sort_values(by=by, ascending=False)

## Filters
def recent(df, column="year"):
    """Filter on year of item"""
    return df[column]>=get_since_year()

def current(df, start="start", end="end", current=None):
    """Filter on whether item is current"""
    now = pd.to_datetime(datetime.datetime.now().date())
    within = ((df[start] <= now) & (pd.isna(df[end]) | (df[end] >= now)))
    if current is not None:
        return (within | (~df[current].isna() & df[current]))
    else:
        return within

def former(df, end="end"):
    """Filter on whether item is current"""
    now = pd.to_datetime(datetime.datetime.now().date())
    return (df[end] < now)

def onbool(df, column="current", invert=False):
    """Filter on whether column is positive (or negative if inverted)"""
    if invert:
        return ~df[column]
    else:
        return df[column]

def columnis(df, column, value):
    """Filter on whether item is equal to a given value"""
    return (df[column]==value)

def columncontains(df, column, value):
    """Filter on whether column contains a given value"""
    colis = columnis(df, column, value)
    return (colis | df[column].apply(lambda x: (x==value).any() if type(x==value) is not bool else (x==value)))
