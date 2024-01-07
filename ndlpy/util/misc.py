import datetime
import math
import re
import os
import sys
import wget

import ndlpy.config.context as context
from ndlpy.log import Logger

from keyword import iskeyword

cntxt = context.Context(name="ndlpy")
log = Logger(
    name=__name__,
    level=cntxt["logging"]["level"],
    filename=cntxt["logging"]["filename"],
)

"""Utility functions for helping, e.g. to create the relevant yaml files quickly."""


def reorder_dictionary(dictionary : dict | list[dict], order : list[str], sort_remaining : bool = True) -> dict | list[dict]:
    """
    Reorder a dictionary according to a given order.

    :param dictionary: The dictionary to be reordered.
    :type dictionary: dict
    :param order: The order to be used for reordering.
    :type order: list
    :return: The reordered dictionary.
    :rtype: dict
    """

    # Check if the dictionary is a list of dictionaries.
    if isinstance(dictionary, list):
        for i, entry in enumerate(dictionary):
            dictionary[i] = reorder_dictionary(entry, order, sort_remaining)
        return dictionary

    # Check any keys that are in the dictionary but not in the order.
    remaining = [key for key in dictionary if key not in order]

    # Sort the remaining keys if required.
    if sort_remaining:
        remaining.sort()

    # Add remaining keys to the end of the dictionary.
    order = order + remaining
    return {key: dictionary[key] for key in order if key in dictionary}


def extract_full_filename(details : dict) -> str:
    """
    Return the filename from the details of directory and filename

    :param details: The details of the file to be extracted.
    :type details: dict
    :return: The filename.
    :rtype: str
    """
    if "directory" not in details or details["directory"] is None:
        if "filename" not in details or details["filename"] is None:
            errmsg = f"No filename provided in details."
            log.error(errmsg)
            raise ValueError(errmsg)
        return details["filename"]
    return os.path.join(
        os.path.expandvars(details["directory"]),
        details["filename"],
    )


def extract_root_directory(
    directory, environs : list[str] = ["HOME", "USERPROFILE", "TEMP", "TMPDIR", "TMP"] 
) -> tuple[str, str]:
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
        return sub_path_environment(cwd, environs), directory.replace(cwd, ".").replace(
            "./", ""
        )
    else:
        # IF directory is not current, assume it is a root and a subdirectory, extracting each one.
        root, directory = os.path.split(directory)
        return sub_path_environment(root), directory


def extract_file_type(filename : str) -> str:
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
    if ext in ["xls", "xlsx"]:
        return "excel"
    if ext in ["yml", "yaml"]:
        return "yaml"
    if ext in ["json"]:
        return "json"
    if ext in ["bib", "bibtex"]:
        return "bibtex"
    if ext in ["docx"]:
        return "docx"
    raise ValueError(f'Unrecognised type of file in "{filename}"')


def extract_abs_filename(details : dict) -> str:
    """
    Return the absolute filename by adding current directory if it's not present

    :param details: The details of the file to be extracted.
    :type details: dict
    :return: The absolute filename.
    :rtype: str

    """
    return os.path.abspath(extract_full_filename(details))


def camel_capitalize(word : str) -> str:
    """
    Capitalize the word in camel case.

    :param word: The word to be capitalized.
    :type word: str
    :return: The capitalized word.
    """
    if word == word.upper():
        return word
    else:
        return word.capitalize()


def remove_nan(dictionary : dict) -> dict:
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
            isna = entry is None or (
                type(entry) is float and math.isnan(entry)
            )  # Switched from pd.isna
            if type(isna) is bool and isna:
                del dictionary2[key]
    return dictionary2

def is_valid_var(variable) -> bool:
    """
    Test if a variable name is valid.

    :param variable: The variable name to be tested.
    :type variable: str
    :return: True if the variable name is valid, False otherwise.
    :rtype: bool
    """
    if not isinstance(variable, str):
        return False
    return variable.isidentifier() and not iskeyword(variable)

def to_valid_var(variable: int | float | str) -> str:
    """
    Convert a given input (scalar or string) to a valid Python variable name.
    Replaces invalid characters with underscores and ensures the name is not a Python keyword.

    :param variable: The input to be converted to a valid variable name.
    :type variable: int, float, or str
    :return: The input converted to a valid variable name.
    """
    if not isinstance(variable, (int, float, str)):
        raise TypeError("Input must be an integer, float, or string")
    
    if isinstance(variable, (int, float)):
        var_name = str(variable).replace("-", "neg").replace(".", "p")
        if var_name[0].isdigit():
            var_name = "n" + var_name
    else:
        var_name = re.sub(r"\W|^(?=\d)", "_", variable.lower())

    # Append underscore if the result is a Python keyword
    if iskeyword(var_name) or len(var_name) == 0:
        log.warning(f"Variable name '{var_name}' is a Python keyword or empty. Appending underscore.")
        var_name += "_"

    return var_name


def to_camel_case(text : str) -> str:
    """
    Remove non alpha-numeric characters and convert to camel case.

    :param text: The text to be converted.
    :type text: str
    :return: The text converted to camel case.
    :rtype: str
    :raises ValueError: If the text is empty.
    """
    if isinstance(text, str) and len(text) == 0:
        raise ValueError("Provided a zero length string to convert to camel case.")
    if not isinstance(text, str):
        text = to_valid_var(text)  # Assuming to_valid_var is defined as previously discussed


    # Replace specific non alpha-numeric characters with words
    replacements = {"/": " or ", "@": " at "}
    for key, value in replacements.items():
        text = text.replace(key, value)

    # Remove remaining non alpha-numeric characters
    text = re.sub(r'[^a-zA-Z0-9]', ' ', text)

    # Split and capitalize
    words = text.split()
    if words:
        return words[0].lower() + ''.join(camel_capitalize(word) for word in words[1:])
    else:
        return ""


def sub_path_environment(
    path : str, environs : list[str] = ["HOME", "USERPROFILE", "TEMP", "TMPDIR", "TMP", "BASE"] 
) -> str:
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
            path = path.replace(os.environ[var], "${" + var + "}")
    return path


def get_path_env(environs : list[str] = ["HOME", "USERPROFILE", "TEMP", "TMPDIR", "TMP", "BASE"]) -> str:
    """
    Return the current path with environment variables.

    :return: The current path with environment variables replacing.
    :rtype: str
    """
    return sub_path_environment(os.path.abspath(os.getcwd()), environs)


def get_url_file(url : str, directory : str = None, filename : str = None, ext : str = None) -> str:
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
        filename += "." + ext
        if directory is not None:
            filename = os.path.join(directory, filename)
        os.rename(dfilename, filename)
        return filename


def prompt_stdin(prompt : str) -> bool:
    """
    Ask user for agreeing to data set licenses.

    :param prompt: The prompt message to display to the user.
    :type prompt: str
    :return: True if the user agrees, False otherwise.
    :rtype: bool
    """
    yes = {"yes", "y"}
    no = {"no", "n"}

    while True:
        try:
            print(prompt)
            choice = input().lower()

            if choice in yes:
                return True
            elif choice in no:
                return False
            else:
                print(
                    f"Your response ('{choice}') was not recognized. Please respond with 'yes', 'y' or 'no', 'n'."
                )
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return False
        except EOFError:
            print("\nUnexpected end of input. Please try again.")

            
