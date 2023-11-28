from datetime import datetime
import math
import re
import os
import wget

"""Utility functions for helping, e.g. to create the relevant yaml files quickly."""
def filename_to_binary(filename):
    """Convert a filename to a binary by loading it"""
    return open(filename, 'rb').read()


def datetimeToYyyymmdd(date):
    """Convert from YYYY-MM-DD string to a datetime.datetime object."""
    return datetime.strftime(date, "%Y-%m-%d")

def extract_full_filename(details):
    """Return the filename from the details of directory and filename"""
    if "directory" not in details or details["directory"] is None:
        return details["filename"]
    return os.path.join(
        os.path.expandvars(details["directory"]),
        details["filename"],
    )


def extract_abs_filename(details):
    """Return the absolute filename by adding current directory if it's not present"""
    return os.path.abspath(extract_full_filename(details))

def camel_capitalize(text):
    if text == text.upper():
        return text
    else:
        return text.capitalize()

def remove_nan(dictionary):
    """Delete missing entries from dictionary"""
    dictionary2 = dictionary.copy()
    for key, entry in dictionary.items():
        if type(entry) is dict:
            dictionary2[key] = remove_nan(entry)
        else:
            isna = entry is None or math.isna(entry) # Switched from pd.isna
            if type(isna) is bool and isna:
                del(dictionary2[key])
    return dictionary2


def to_valid_var(varStr):
    """Replace invalid characters with underscore"""
    return re.sub('\W|^(?=\d)','_', varStr.lower())

def to_camel_case(text):
    """Remove non alpha-numeric characters and camelize capitalisation"""
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

def sub_path_environment(path):
    """Replace a path with values from environment variables."""
    vars = ["HOME", "USERPROFILE"]
    for var in vars:
        if var in os.environ:
            path = path.replace(os.environ[var], "$" + var)
    return path

def get_path_env():
    """Return the current parth with environment variables."""
    return sub_path_environment(os.path.abspath(os.getcwd()))
                                
        
def get_url_file(url, directory=None, filename=None, ext=None):
    """Download a file from a url and save it to disk."""
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
    
def return_longest(lst):
    return max(lst, key=len)

def return_shortest(lst):
    return min(lst, key=len)
