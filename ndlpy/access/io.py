import os
import glob


import sys
import re
import tempfile

import yaml
import json

import numpy as np
import pandas as pd

import frontmatter
import pypandoc

import bibtexparser as bp

from ..util.misc import (
    extract_full_filename,
    extract_root_directory,
    extract_file_type,
    get_path_env,
    remove_nan,
    reorder_dictionary,
    prompt_stdin,
)
from ..util.fake import Generate

from ..config.context import Context
from ..util.dataframe import reorder_dataframe
from ..log import Logger

GSPREAD_AVAILABLE = True
try:
    import gspread_pandas as gspd
except ImportError:
    GSPREAD_AVAILABLE = False
# This file accesses the data

"""Place commands in this file to access the data electronically. Don't remove any missing values, or deal with outliers. Make sure you have legalities correct, both intellectual property and personal data privacy rights. Beyond the legal side also think about the ethical issues around this data. """

ctxt = Context()
log = Logger(
    name=__name__,
    level=ctxt._data["logging"]["level"],
    filename=ctxt._data["logging"]["filename"],
)


def multiline_str_representer(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, multiline_str_representer, Dumper=yaml.SafeDumper)

# class EnvTag(yaml.YAMLObject):
#     yaml_tag = u'!ENV'

#     def __init__(self, env_var):
#         self.env_var = env_var

#     def __repr__(self):
#         v = os.environ.get(self.env_var) or ''
#         return 'EnvTag({}, contains={})'.format(self.env_var, v)

#     @classmethod
#     def from_yaml(cls, loader, node):
#         return EnvTag(node.value)

#     @classmethod
#     def to_yaml(cls, dumper, data):
#         value = dumper.represent_scalar(cls.yaml_tag, data.env_var)
#         if '\n' in value:
#             # Use the '|' style for multi-line strings
#             return dumper.represent_scalar(cls.yaml_tag, value, style="|")
#         else:
#             return dumper.represent_scalar(cls.yaml_tag, value)
#         return value


# Required for safe_load
# yaml.SafeLoader.add_constructor('!ENV', EnvTag.from_yaml)
# Required for safe_dump
# yaml.SafeDumper.add_multi_representer(EnvTag, EnvTag.to_yaml)

bibtex_sort_by = ["author", "year", "title"]
bibtex_column_order = [
    "ENTRYTYPE",
    "ID",
    "title",
    "author",
    "editor",
    "abstract",
    "year",
    "journal",
    "booktitle",
    "volume",
    "issue",
    "pages",
    "publisher",
    "address",
    "doi",
    "url",
    "note",
]


def str_type():
    return str


def bool_type():
    return pd.BooleanDtype()


def int_type():
    return pd.Int32Dtype()


def float_type():
    return pd.Float64Dtype()


def extract_dtypes(details):
    """
    Extract dtypes from directory.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The dtypes.
    :rtype: dict
    """
    dtypes = {}
    if "dtypes" in details:
        if details["dtypes"] is not None:
            for dtype in details["dtypes"]:
                dtypes[dtype["field"]] = globals()[dtype["type"]]()
    return dtypes


def extract_sheet(details, gsheet=True):
    """
    Extract the sheet name from details

    :param details: The details of the file to be read.
    :type details: dict
    :param gsheet: Whether to use gspread_pandas.
    :type gsheet: bool
    """
    if "sheet" in details:
        return details["sheet"]
    else:
        if gsheet:
            return 0
        else:
            return None


def read_json(details):
    """
    Read data from a json file.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    filename = extract_full_filename(details)
    data = read_json_file(filename)
    return pd.DataFrame(data)


def write_json(df, details):
    """
    Write data to a json file.

    :param df: The data to be written.

    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    write_json_file(df.to_dict("records"), filename)


def read_yaml(details):
    """
    Read data from a yaml file.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    filename = extract_full_filename(details)
    data = read_yaml_file(filename)
    return pd.DataFrame(data)

def read_markdown(details):
    """
    Read data from a markdown file.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    filename = extract_full_filename(details)
    data = read_markdown_file(filename)
    return pd.DataFrame([data])

def write_markdown(df, details):
    """
    Write data to a markdown file.

    :param df: The data to be written.
    :type df: pandas.DataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    data_dict = df.to_dict("records")

    # Remove all the nan and missing values from the dictionary.
    for num, entry in enumerate(data_dict):
        data_dict[num] = remove_nan(entry)

    write_markdown_file(data_dict, filename)

def write_yaml(df, details):
    """
    Write data to a yaml file.

    :param df: The data to be written.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    data_dict = df.to_dict("records")

    # Remove all the nan and missing values from the dictionary.
    for num, entry in enumerate(data_dict):
        data_dict[num] = remove_nan(entry)
    write_yaml_file(data_dict, filename)


def read_bibtex(details):
    """
    Read data from a bibtex file.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    filename = extract_full_filename(details)
    data = read_bibtex_file(filename)

    return (
        reorder_dataframe(pd.DataFrame(data), bibtex_column_order)
        .sort_values(by=bibtex_sort_by)
        .reset_index(drop=True), details
    )


def write_bibtex(df, details):
    """
    Write data to a bibtex file.

    :param df: The data to be written.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    data_dict = df.to_dict("records")

    # Remove all the nan and missing values from the dictionary.
    for num, entry in enumerate(data_dict):
        data_dict[num] = remove_nan(entry)

    write_bibtex_file(data_dict, filename)


def read_directory(
    details, filereader=None, filereader_args={}, default_glob="*", source=None
):
    """
    Read data from a directory of files.

    :param details: The details of the directory to be read.
    :type details: dict
    :param filereader: The function to be used to read the file.
    :type filereader: function
    :param filereader_args: The arguments to be passed to the filereader.
    :type filereader_args: dict
    :param default_glob: The default glob to be used if none is specified.
    :type default_glob: str
    :param source: The source information for the data.
    :type source: dict
    :raises ValueError: if the same filename is specified multiple times.
    """
    filenames = []
    dirnames = []
    if "source" in details:
        sources = details["source"]
        if type(sources) is not list:
            sources = [sources]

        for source in sources:
            if "glob" in source:
                glob_text = source["glob"]
            else:
                glob_text = default_glob

            if "directory" in source:
                directory = os.path.expandvars(source["directory"])
            else:
                directory = "."
            globname = os.path.join(
                directory,
                glob_text,
            )
            log.debug(f'Reading directory "{globname}"')
            newfiles = glob.glob(globname)
            newdirs = [directory] * len(newfiles)
            if len(newfiles) == 0:
                log.warning(f'No files match "{globname}"')
            if "regexp" in source:
                regexp = source["regexp"]
                addfiles = []
                adddirs = []
                for filename, dirname in zip(newfiles, newdirs):
                    if re.match(regexp, os.path.basename(filename)):
                        addfiles.append(filename)
                        adddirs.append(dirname)
                if len(addfiles) == 0:
                    log.warning(f'No files match "regexp"')
            else:
                addfiles = newfiles
                adddirs = newdirs
            filenames += addfiles
            dirnames += adddirs
        if len(filenames) == 0:
            log.warning(f'No files in "{sources}".')
    else:
        log.warning(f'No source in "{details}".')

    filelist = [
        os.path.join(dirname, filename)
        for filename, dirname in zip(filenames, dirnames)
    ]

    return read_files(filelist, details["store_fields"], filereader, filereader_args)


def read_list(filelist):
    """
    Read from a list of files.

    :param filelist: The list of files to be read.
    :type filelist: list
    :return: The data read from the files.
    :rtype: pandas.DataFrame
    """
    return read_files(filelist)


def read_files(filelist, store_fields=None, filereader=None, filereader_args=None):
    """
    Read files from a given list.

    :param filelist: The list of files to be read.
    :type filelist: list
    :param store_fields: The fields to be stored in the data.
    :type store_fields: dict
    :param filereader: The function to be used to read the file.
    :type filereader: function
    :param filereader_args: The arguments to be passed to the filereader.
    :type filereader_args: dict
    :return: The data read from the files.
    :rtype: pandas.DataFrame
    """
    if store_fields is not None:
        directory_field = store_fields["directory"]
        filename_field = store_fields["filename"]
        root_field = store_fields["root"]
    else:
        directory_field = "sourceDirectory"
        filename_field = "sourceFile"
        root_field = "sourceRoot"

    if len(filelist) != len(set(filelist)):
        raise ValueError(f"There are repeated files listed in the file list.")
    filelist.sort()
    data = []
    for filename in filelist:
        if not os.path.exists(filename):
            log.warning(f'File "{filename}" is not a file or a directory.')
        if filereader is None:
            filereader = default_file_reader(filename)
        if filereader_args is None:
            data.append(filereader(filename))
        else:
            data.append(filereader(filename, **filereader_args))

        # Add the root location, directory and filename to the data.
        split_path = os.path.split(filename)
        root, direc = extract_root_directory(split_path[0])
        if root_field in data[-1]:
            raise ValueError(
                f'The field "{root_field}" is already in the data and is registered for setting as the root field.'
            )
        data[-1][root_field] = root
        if directory_field in data[-1]:
            raise ValueError(
                f'The field "{directory_field}" is already in the data and is registered for setting as the directory field.'
            )
        data[-1][directory_field] = direc
        if filename_field in data[-1]:
            raise ValueError(
                f'The field "{filename_field}" is already in the data and is registered for setting as the filename field.'
            )
        data[-1][filename_field] = split_path[1]
    return pd.json_normalize(data)


def write_directory(df, details, filewriter=None, filewriter_args={}):
    """
    Write scoring data to a directory of files.

    :param df: The data to be written.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    :param filewriter: The function to be used to write the file.
    :type filewriter: function
    :param filewriter_args: The arguments to be passed to the filewriter.
    :type filewriter_args: dict
    :raises ValueError: if the same filename is specified multiple times.
    """
    filename_field = details["store_fields"]["filename"]
    directory_field = details["store_fields"]["directory"]
    root_field = details["store_fields"]["root"]

    filenames = []
    # Check that none of the filenames are the same.
    for index, row in df.iterrows():
        # Don't write a file that contains only nulls
        if not row.isnull().values.all():
            directoryname = os.path.expandvars(
                os.path.join(
                    row[root_field],
                    row[directory_field],
                )
            )
            if not os.path.exists(directoryname):
                os.makedirs(directoryname)

            fullfilename = os.path.join(directoryname, row[filename_field])
            if fullfilename in filenames:
                raise ValueError(
                    'The specified filed name "{fullfilename}" has already been used for a different row of the data.'
                )
            filenames.append(fullfilename)
            if filewriter is None:
                typ = extract_file_type(fullfilename)
                filewriter = default_file_writer(typ)

            row_dict = row.to_dict()
            row_dict = remove_nan(row_dict)
            # Don't save the file information because that's situational.
            del row_dict[filename_field]
            del row_dict[root_field]
            del row_dict[directory_field]
            if filewriter_args is None:
                filewriter(row_dict, fullfilename)
            else:
                filewriter(row_dict, fullfilename, **filewriter_args)


def read_json_file(filename):
    """
    Read a json file and return a python dictionary.

    :param filename: The filename of the json file.
    :type filename: str
    :return: The data read from the file.
    :rtype: dict
    """
    with open(filename, "r") as stream:
        try:
            log.debug(f'Reading json file "{filename}"')
            data = json.load(stream)
        except json.JSONDecodeError as exc:
            log.warning(exc)
            data = {}
    return data


def write_json_file(data, filename):
    """Write a json file from a python dicitonary."""
    with open(filename, "w") as stream:
        try:
            log.debug(f'Writing json file "{filename}".')
            json.dump(data, stream)
        except json.JSONDecodeError as exc:
            log.warning(exc)


def default_file_reader(typ):
    """
    Return the default file reader for a given type.

    :param typ: The type of file to be read.
    :type typ: str
    :return: The default file reader.
    :rtype: function
    :raises ValueError: if the type is not recognised.
    """
    if typ == "markdown":
        return read_markdown_file
    if typ == "yaml":
        return read_yaml_file
    if typ == "json":
        return read_json_file
    if typ == "bibtex":
        return read_bibtex_file
    if typ == "docx":
        return read_docx_file
    raise ValueError(f'Unrecognised type of file "{typ}".')

def default_file_writer(typ):
    """
    Return the default file writer for a given type.

    :param typ: The type of file to be written.
    :type typ: str
    :return: The default file writer.
    :rtype: function
    :raises ValueError: if the type is not recognised.
    """
    if typ == "markdown":
        return write_markdown_file
    if typ == "yaml":
        return write_yaml_file
    if typ == "json":
        return write_json_file
    if typ == "bibtex":
        return write_bibtex_file
    if typ == "docx":
        return write_docx_file
    raise ValueError(f'Unrecognised type of file "{typ}".')


def read_file(filename):
    """ "Attempt to read the file given the extention."""
    typ = extract_file_type(filename)
    return default_file_reader(typ)(filename)


def read_yaml_file(filename):
    """Read a yaml file and return a python dictionary."""
    with open(filename, "r") as stream:
        try:
            log.debug(f'Reading yaml file "{filename}"')
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            log.warning(exc)
            data = {}
    return data


def read_bibtex_file(filename):
    """
    Red a bibtex file and return a python dictionary.

    :param filename: The filename of the bibtex file.
    :type filename: str
    :return: The data read from the file.
    :rtype: dict
    """
    parser = bp.bparser.BibTexParser()
    parser.ignore_nonstandard_types = False
    parser.homogenize_fields = False
    parser.common_strings = False
    with open(filename, "r") as stream:
        log.debug(f'Reading bibtex file "{filename}"')
        data = bp.load(stream, parser)
    return reorder_dictionary(data.entries, bibtex_column_order)


def yaml_prep(data):
    """
    Prepare any fields for writing in yaml

    :param data: The data to be prepared.
    :type data: dict
    :return: The prepared data.
    :rtype: dict
    """
    writedata = data.copy()
    if type(writedata) is list:
        for num, el in enumerate(writedata):
            writedata[num] = yaml_prep(el)
        return writedata

    for key, item in writedata.items():
        if pd.api.types.is_datetime64_dtype(item) or type(item) is pd.Timestamp:
            writedata[key] = item.strftime("%Y-%m-%d %H:%M:%S.%f")
    return writedata


def write_bibtex_file(data, filename):
    """
    Write a bibtex file from a python dictionary.

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the bibtex file.
    :type filename: str
    """

    # Ensure that the data ID entries are unique
    ids = []
    for entry in data:
        if "ID" in entry:
            ids.append(entry["ID"])
        else:
            raise ValueError(f"Entry {entry} does not have an ID field.")
    if len(ids) != len(set(ids)):
        raise ValueError(f"There are repeated IDs in the data.")

    # Ensure that the ids are valid keys for bibtex.
    for entry in data:
        # invalid bibtex identifier characters are: @',#}{~% and whitespace characters such as space, tab, newline, and carriage return.
        # Check they aren't in the ID.
        if re.search(r"[@',#}{~% \t\n\r]", entry["ID"]):
            raise ValueError(f"The ID {entry['ID']} contains invalid characters.")

    bibdata = bp.bibdatabase.BibDatabase()
    bibdata.entries = data
    writer = bp.bwriter.BibTexWriter()
    writer.indent = "  "
    writer.order_entries_by = bibtex_sort_by
    writer.display_order = bibtex_column_order
    with open(filename, "w") as stream:
        log.debug(f'Writing bibtex file "{filename}".')
        bp.dump(bibdata, stream, writer)


def write_yaml_file(data, filename):
    """
    Write a yaml file from a python dictionary.

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the yaml file.
    :type filename: str
    """
    writedata = yaml_prep(data)
    with open(filename, "w") as stream:
        try:
            log.debug(f'Writing yaml file "{filename}".')
            yaml.dump(writedata, stream, sort_keys=False, allow_unicode=True, width=70)
        except yaml.YAMLError as exc:
            log.warning(exc)


def read_yaml_meta_file(filename):
    """
    Read meta information associated with a file as a yaml and return
    a python dictionary if it exists.

    :param filename: The filename of the file.
    :type filename: str
    :return: The meta information.
    :rtype: dict
    """
    metafile = filename + ".yml"
    if os.path.exists(metafile):
        data = read_yaml_file(metafile)
    else:
        data = {}
    return data


def write_yaml_meta_file(data, filename):
    """
    Write meta information associated with a file to a yaml.

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the file.
    :type filename: str
    """
    metafile = filename + ".yml"
    write_yaml_file(data, metafile)


def read_markdown_file(filename, include_content=True):
    """
    Read a markdown file and return a python dictionary.

    :param filename: The filename of the markdown file.
    :type filename: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    :return: The data read from the file.
    :rtype: dict
    """
    with open(filename, "r") as stream:
        try:
            log.debug(f"Reading markdown file {filename}")
            post = frontmatter.load(stream)
            data = post.metadata
            if include_content:
                data["content"] = post.content
        except yaml.YAMLError as exc:
            log.warning(exc)
            data = {}

    return data


def read_docx_file(filename, include_content=True):
    """
    Read information from a docx file.

    :param filename: The filename of the docx file.
    :type filename: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    :return: The data read from the file.
    :rtype: dict
    """
    directory = tempfile.gettempdir()
    tmpfile = os.path.join(directory, "tmp.md")
    extra_args = []
    extra_args.append("--standalone")
    extra_args.append("--track-change=all")
    pypandoc.convert_file(
        filename, "markdown", outputfile=tmpfile, extra_args=extra_args
    )
    data = read_markdown_file(tmpfile, include_content)
    return remove_nan(data)


def read_talk_file(filename, include_content=True):
    """
    Read a markdown talk file.

    :param filename: The filename of the talk file.
    :type filename: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    :return: The data read from the file.
    """
    data = read_markdown_file(filename, include_content)
    return remove_nan(data)


def read_talk_include_file(filename, include_content=True):
    """
    Read a markdown talk include file.

    :param filename: The filename of the talk include file.
    :type filename: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    :return: The data read from the file.
    """
    
    data = read_markdown_file(filename, include_content)
    return remove_nan(data)


def write_url_file(data, filename, content, include_content=True):
    """
    Write a url to a file

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the url file.
    :type filename: str
    :param content: The content of the url file.
    :type content: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    """
    # This is with writing links to prefilled google forms in mind.
    raise NotImplementedError("The write url file function has not been implemented.")


def write_markdown_file(data, filename, content=None, include_content=True):
    """
    Write a markdown file from a python dictionary

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the markdown file.
    :type filename: str
    :param content: The content of the markdown file.
    :type content: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    """
    if content is None:
        if include_content and "content" in data:
            write_data = {key: item for (key, item) in data.items() if key != "content"}
            content = data["content"]
        else:
            if not include_content:
                content = ""
            write_data = data
    else:
        write_data = data.copy()
        if "content" in data:
            del write_data["content"]
    log.debug(f'Writing markdown file "{filename}"')
    if pd.isna(content):
        content = ""
    post = frontmatter.Post(content, **write_data)
    with open(filename, "wb") as stream:
        frontmatter.dump(post, stream, sort_keys=False)

def create_document_content(**kwargs):
    """
    Create a document content from the arguments.
    :param content: The content of the document.
    :type content: str
    :param filename: The filename of the document.
    :type filename: str
    :param directory: The directory of the document.
    :type directory: str
    :return: The data, filename and content of the document.
    :rtype: tuple
    """
    filename = extract_full_filename(kwargs)
    if "content" in kwargs:
        content = kwargs["content"]
    else:
        content = ""
    data = {}
    for key, item in kwargs.items():
        if key not in ["filename", "directory", "content"]:
            data[key] = item
    return data, filename, content
        

def create_letter(**kwargs):
    """
    Create a markdown letter.
    :param content: The content of the letter.
    :type content: str
    :param filename: The filename of the letter.
    :type filename: str
    :param directory: The directory of the letter.
    :type directory: str
    :return: The data, filename and content of the letter.
    :rtype: tuple
    """
    data, filename, content = create_document_content(**kwargs)
    write_letter_file(data=data, filename=filename, content=content)

    
def write_letter_file(data, filename, content, include_content=True):
    """
    Write a letter file from a python dictionary

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the letter.
    :type filename: str
    :param content: The content of the letter.
    :type content: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    """
    if include_content and content in data:
        write_data = {key: item for (key, item) in data.items() if key != "content"}
        content = data[content]
    else:
        if not include_content:
            content = ""
        write_data = data

    log.debug(f'Writing markdown letter file "{filename}"')
    post = frontmatter.Post(content, **write_data)
    with open(filename, "wb") as stream:
        frontmatter.dump(post, stream, sort_keys=False)


def write_formlink(data, filename, content, include_content=True):
    """
    Write a url to prepopulate a Google form
    """
    write_url_file(data, filename, content, include_content)


def write_docx_file(data, filename, content, include_content=True):
    """
    Write a docx file from a python dictionary.

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the docx file.
    :type filename: str
    :param content: The content of the docx file.
    :type content: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    """
    directory = tempfile.gettempdir()
    tmpfile = os.path.join(directory, "tmp.md")
    write_markdown_file(data, tmpfile, content, include_content)
    log.debug(f'Converting markdown file "{tmpfile}" to docx file "{filename}"')
    extra_args = []
    if "reference-doc" in data:
        extra_args.append("--reference-doc=" + data["reference-doc"])
    pypandoc.convert_file(tmpfile, "docx", outputfile=filename, extra_args=extra_args)


def write_tex_file(data, filename, content, include_content=True):
    """
    Write a docx file from a python dictionary.

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the docx file.
    :type filename: str
    :param content: The content of the docx file.
    :type content: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    """
    directory = tempfile.gettempdir()
    tmpfile = os.path.join(directory, "tmp.md")
    write_markdown_file(data, tmpfile, content, include_content)
    log.debug(f'Converting markdown file "{tmpfile}" to tex file "{filename}"')
    extra_args = []
    pypandoc.convert_file(tmpfile, "tex", outputfile=filename, extra_args=extra_args)


def read_csv(details):
    """
    Read data from a csv file.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    dtypes = extract_dtypes(details)
    filename = extract_full_filename(details)
    if "header" in details:
        header = details["header"]
    else:
        header = 0

    if "delimiter" in details:
        delimiter = details["delimiter"]
    else:
        delimiter = ","

    if "quotechar" in details:
        quotechar = details["quotechar"]
    else:
        quotechar = '"'
    log.debug(
        f'Reading csv file "{filename}" from row "{header}" with quote character {quotechar} and delimiter "{delimiter}"'
    )

    data = pd.read_csv(
        filename,
        dtype=dtypes,
        header=header,
        delimiter=delimiter,
        quotechar=quotechar,
    )
    return data


def read_excel(details):
    """
    Read data from an excel spreadsheet.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    
    dtypes = extract_dtypes(details)
    filename = extract_full_filename(details)
    if "header" in details:
        header = details["header"]
    else:
        header = 0

    if "sheet" in details:
        sheet_name = details["sheet"]
    else:
        sheet_name = "Sheet1"
    log.debug(
        f'Reading excel file "{filename}" sheet "{sheet_name}" from row "{header}"'
    )

    data = pd.read_excel(
        filename,
        sheet_name=sheet_name,
        dtype=dtypes,
        header=header,
    )

    return data


def read_fake(details):
    """
    Read data from an artificially generated source.

    :param details: The details of the data to be read.
    :type details: dict
    :return: The data read from the source.
    :rtype: pandas.DataFrame
    """

    if not isinstance(details, dict):
        errmsg = "\"fake\" specified in config but not in form of a dictionary."
        log.error(errmsg)
        raise ValueError(errmsg)

    required_keys = ["nrows", "cols"]
    for key in required_keys:
        if key not in details:
            errmsg = f"\"fake\" specified in config but missing \"{key}\" key."
            log.error(errmsg)
            raise ValueError(errmsg)
        
    if isinstance(details["cols"], list):
        log.info("\"cols\" for fake data specified as a list, converting to dictionary with all columns set to the given name of column.")
        cols_are_attributes = [hasattr(Generate, col) for col in details["cols"]]
        if all(cols_are_attributes):
            details["cols"] = {col: col for col in details["cols"]}
        else:
            # Extract which columns aren't attributes and return in error message.
            wrong_cols = [col for col, is_attr in zip(details["cols"], cols_are_attributes) if not is_attr]
            errmsg = f"\"fake\" specified as the type and columns are provided as a list, but the following columns are not attributes of ndlpy.util.fake.Generate: \"{', '.join(wrong_cols)}\""
            log.error(errmsg)
            raise ValueError(errmsg)
        
    if not isinstance(details["cols"], dict):
        errmsg = ("\"fake\" specified in config which requires that cols are specified as a dictionary, "
                  "with dictionary entries representing the type of fake data to be generated.")
        log.error(errmsg)
        raise ValueError(errmsg)

    if not isinstance(details["nrows"], int) or details["nrows"] < 0:
        errmsg = "\"nrows\" must be a non-negative integer."
        log.error(errmsg)
        raise ValueError(errmsg)

    cols = details['cols']  # Correct reference to cols
    for col, gen in cols.items():
        if hasattr(Generate, gen):
            gen_func = getattr(Generate, gen)
            if callable(gen_func):
                cols[col] = gen_func
            else:
                errmsg = f"\"fake\" specified in config but \"{gen}\" is not a callable function attribute of ndlpy.util.fake.Generate."
                if list_convert:
                    errmsg += " This is likely because the \"cols\" were specified as a list and not a dictionary, meaning that in dictionary conversion I've created columns where the function attributes match the column title."
                log.error(errmsg)
                raise ValueError(errmsg)
        else:
            errmsg = f"\"{gen}\" specified as column's fake function, \"{gen}\" is not an attribute of ndlpy.util.fake.Generate."
            log.error(errmsg)
            raise ValueError(errmsg)

    data = []
    for _ in range(details["nrows"]):
        row = {col: gen() for col, gen in cols.items()}
        data.append(row)

    return pd.DataFrame(data)
    
    
def read_local(details):
    """
    Read data directly from details file.

    :param details: The details of the data to be read.
    :type details: dict
    :return: The data read from the settings file..
    :rtype: pandas.DataFrame
    :raises ValueError: If the 'details' is not a dictionary or is missing required keys.
    """

    if not isinstance(details, dict):
        errmsg = "\"local\" specified in config but not in form of a dictionary."
        log.error(errmsg)
        raise ValueError(errmsg)

    # Create data frame from details
    
    try:
        df = pd.DataFrame(data=details["data"])
    except KeyError as e:
        errmsg = f"Could not create data frame from details specified in \"local\" entry. Missing key {e}."
        log.error(errmsg)
        raise ValueError(errmsg)
    except Exception as e:
        errmsg = f"Could not create data frame from details specified in \"local\" entry. {e}"
        log.error(errmsg)
        raise ValueError(errmsg)

    # Optionally set index name if not already set
    if df.index.name is None:
        log.debug('Index name not set in data frame. Setting to "index".')
        df.index.name = "index"

    return df

if GSPREAD_AVAILABLE:

    def read_gsheet(details):
        """
        Read data from a Google sheet.

        :param details: The details of the file to be read.
        :type details: dict
        :return: The data read from the file.
        :rtype: pandas.DataFrame
        """
        dtypes = extract_dtypes(details)
        filename = extract_full_filename(details)
        log.debug(f"Reading Google sheet named {filename}")
        sheet = extract_sheet(details)
        gconfig = {}
        for key, val in ctxt["google_oauth"].items():
            gconfig[key] = os.path.expandvars(val)
        gsheet = gspd.Spread(
            spread=filename,
            sheet=sheet,
            config=gconfig,
        )
        data = gsheet.sheet_to_df(
            index=None,
            header_rows=details["header"] + 1,
            start_row=details["header"] + 1,
        )
        return data


def write_excel(df, details):
    """
    Write data to an excel spreadsheet.

    :param df: The data to be written.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    if "header" in details:
        header = details["header"]
    else:
        header = 0

    if "sheet" in details:
        sheet_name = details["sheet"]
    else:
        sheet_name = "Sheet1"

    log.debug(
        f'Writing excel file "{filename}" sheet "{sheet_name}" header at row "{header}".'
    )

    writer = pd.ExcelWriter(
        filename, engine="xlsxwriter", datetime_format="YYYY-MM-DD HH:MM:SS.000"
    )
    sheet_name = details["sheet"]
    df.to_excel(writer, sheet_name=sheet_name, startrow=header, index=False)
    writer.close()


def write_csv(df, details):
    """
    Write data to an csv spreadsheet.

    :param df: The data to be written.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    if "delimiter" in details:
        delimiter = details["delimiter"]
    else:
        delimiter = ","

    if "quotechar" in details:
        quotechar = details["quotechar"]
    else:
        quotechar = '"'
    log.debug(
        f'Writing csv file "{filename}" with quote character {quotechar} and delimiter "{delimiter}"'
    )

    with open(filename, "w") as stream:
        df.to_csv(
            stream,
            sep=delimiter,
            quotechar=quotechar,
            header=True,
            index=False,
        )


if GSPREAD_AVAILABLE:

    def write_gsheet(df, details):
        """
        Read data from a Google sheet.

        :param details: The details of the file to be read.
        :type details: dict
        :return: The data read from the file.
        :rtype: pandas.DataFrame
        """
        filename = extract_full_filename(details)
        sheet = extract_sheet(details)
        log.debug(f"Writing Google sheet named {filename}")
        gsheet = gspd.Spread(
            spread=filename,
            sheet=sheet,
            create_spread=True,
            config=ctxt["gspread_pandas"],
        )
        gsheet.df_to_sheet(
            df=df,
            index=False,
            headers=True,
            replace=True,
            sheet=sheet,
            start=(details["header"] + 1, 1),
        )


directory_readers = [
    {
        "default_glob": "*.yml",
        "filereader": read_yaml_file,
        "name": "read_yaml_directory",
        "docstr": "Read a directory of yaml files.",
    },
    {
        "default_glob": "*.json",
        "filereader": read_json_file,
        "name": "read_json_directory",
        "docstr": "Read a directory of json files.",
    },
    {
        "default_glob": "*.bib",
        "filereader": read_bibtex_file,
        "name": "read_bibtex_directory",
        "docstr": "Read a directory of bibtex files.",
    },
    {
        "default_glob": "*.md",
        "filereader": read_markdown_file,
        "name": "read_markdown_directory",
        "docstr": "Read a directory of markdown files.",
    },
    {
        "default_glob": "*",
        "filereader": read_file,
        "name": "read_plain_directory",
        "docstr": "Read a directory of files.",
    },
    {
        "default_glob": "*",
        "filereader": read_yaml_meta_file,
        "name": "read_meta_directory",
        "docstr": "Read a directory of yaml meta files.",
    },
    {
        "default_glob": "*.docx",
        "filereader": read_docx_file,
        "name": "read_docx_directory",
        "docstr": "Read a directory of word files.",
    },
]


directory_writers = [
    {
        "filewriter": write_json_file,
        "name": "write_json_directory",
        "docstr": "Write a directory of json files.",
    },
    {
        "filewriter": write_yaml_file,
        "name": "write_yaml_directory",
        "docstr": "Write a directory of yaml files.",
    },
    {
        "filewriter": write_markdown_file,
        "name": "write_markdown_directory",
        "docstr": "Write a directory of markdown files.",
    },
    {
        "filewriter": write_yaml_meta_file,
        "name": "write_meta_directory",
        "docstr": "Write a directory of yaml meta files.",
    },
]


def gdrf_(default_glob, filereader, name="", docstr=""):
    """
    Function generator for different directory readers.

    :param default_glob: The default glob to be used for the directory reader.
    :type default_glob: str
    :param filereader: The function to be used to read the files.
    :type filereader: function
    :param name: The name of the function to be created.
    :type name: str
    :param docstr: The docstring for the function to be created.
    :type docstr: str
    :return: The function to be created.
    :rtype: function
    """

    def directory_reader(details):
        """
        Return a function for reading the directory.

        :param details: The details of the directory to be read.
        :type details: dict
        :return: The directory reader function
        :rtype: function
        """
        
        details = update_store_fields(details)
        globname = None
        if "glob" in details:
            globname = details["glob"]
        if globname is None or globname == "":
            globname = default_glob
        if "source" in details:
            source = details["source"]
        else:
            source = None
        return read_directory(
            details=details,
            filereader=filereader,
            default_glob=globname,
            source=source,
        )

    directory_reader.__name__ = name
    directory_reader.__doc__ = docstr
    return directory_reader


def update_store_fields(details):
    """
    Add default store fields values

    :param details: The details to update with.
    :type details: dict
    :return: The updated details.
    :rtype: dict
    """
    # TK: Perhaps this should be set in config defaults somewhere.
    # Extracts info about where the directory read file data is to be written.
    if "store_fields" not in details:
        details["store_fields"] = {
            "directory": "sourceDirectory",
            "filename": "sourceFilename",
            "root": "sourceRoot",
        }
    else:
        if "directory" not in details["store_fields"]:
            details["store_fields"]["directory"] = "sourceDirectory"
        if "filename" not in details["store_fields"]:
            details["store_fields"]["filename"] = "sourceFilename"
        if "root" not in details["store_fields"]:
            details["store_fields"]["root"] = "sourceRoot"
    return details


def gdwf_(filewriter, name="", docstr=""):
    """
    Function generator for different directory writers.

    :param filewriter: The function to be used to write the files.
    :type filewriter: function
    :param name: The name of the function to be created.
    :type name: str
    :param docstr: The docstring for the function to be created.
    :type docstr: str
    :return: The function to be created.
    :rtype: function
    """

    def directory_writer(df, details):
        """
        Return a function for writing the directory.

        :param df: The data to be written.
        :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
        :param details: The details of the directory to be written.
        :type details: dict
        :return: The directory writer function
        :rtype: function
        """
        details = update_store_fields(details)
        return write_directory(
            df=df,
            details=details,
            filewriter=filewriter,
        )

    directory_writer.__name__ = name
    directory_writer.__doc__ = docstr
    return directory_writer


def populate_directory_readers(readers):
    """
    Populate the directory readers automatically creates functions for reading directories.

    :param readers: The readers to be created.
    :type readers: list
    """
    this_module = sys.modules[__name__]
    for reader in readers:
        setattr(
            this_module,
            reader["name"],
            gdrf_(**reader),
        )


def populate_directory_writers(writers):
    """
    This function automatically create functions for writing directories.

    :param writers: The writers to be created.
    :type writers: list
    """
    this_module = sys.modules[__name__]
    for writer in writers:
        setattr(
            this_module,
            writer["name"],
            gdwf_(**writer),
        )


populate_directory_readers(directory_readers)
populate_directory_writers(directory_writers)


def finalize_data(df, details):
    """
    Finalize the data frame by augmenting with any columns.

    :param df: The data frame to be finalized.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param details: The details of the data frame.
    :type details: dict
    :return: The finalized data frame.
    :rtype: pandas.DataFrame or ndlpy.data.CustomDataFrame
    """

    # Eventually this should do any augmentation that isn't required
    # by the series. The problem is at the moment the liquid rendering
    # (and other renderings) are too integrated with assess. They need
    # to be pulled out and not so dependent on the data structure.

    if df.index.name is None:
        if "index" in details:
            index = details["index"]
            if type(index) is dict:
                df.index.name = index["name"]
            elif type(index) is str:
                df.index.name = index
            else:
                self._log.warning(
                    f'Index "{index}" present in details but no valid name found.'
                )

    if "rename_columns" in details:
        for col in details["rename_columns"]:
            cols = df.columns
            if col not in cols:
                raise ValueError(
                    f'rename_columns contains key "{col}" which is not a column in the loaded DataFrame. Columns are "{cols}"'
                )
        df.rename(columns=details["rename_columns"], inplace=True)

    if "ignore_columns" in details:
        for col in details["ignore_columns"]:
            cols = df.columns
            if col not in cols:
                raise ValueError(
                    f'ignore_columns contains key "{col}" which is not a column in the loaded DataFrame. Columns are "{cols}"'
                )
        df.drop(columns=details["ignore_columns"], inplace=True)
    return df, details


def read_data(details):
    """
    Read in the data from the details given in configuration.

    :param details: The details of the data to be read.
    :type details: dict
    :return: The data read in.
    :rtype: pandas.DataFrame
    """
    if "type" in details:
        ftype = details["type"]
    else:
        raise ValueError(f'Field "type" missing in data source details for read_data, details are given as "{", ".join(details)}".')

    if ftype == "excel":
        df = read_excel(details)
    elif ftype == "gsheet":
        df = read_gsheet(details)
    elif ftype == "yaml":
        df = read_yaml(details)
    elif ftype == "csv":
        df = read_csv(details)
    elif ftype == "json":
        df = read_json(details)
    elif ftype == "bibtex":
        df = read_bibtex(details)
    elif ftype == "markdown":
        df = read_markdown(details)
    elif ftype == "list":
        df = read_list(details)
    elif ftype == "yaml_directory":
        df = read_yaml_directory(details)
    elif ftype == "json_directory":
        df = read_json_directory(details)
    elif ftype == "markdown_directory":
        df = read_markdown_directory(details)
    elif ftype == "directory":
        df = read_plain_directory(details)
    elif ftype == "meta_directory":
        df = read_meta_directory(details)
    elif ftype == "bibtex_directory":
        df = read_bibtex_directory(details)
    elif ftype == "docx_directory":
        df = read_docx_directory(details)
    elif ftype == "local":
        df = read_local(details)
    elif ftype == "fake":
        df = read_fake(details)
    else:
        errmsg = f'Unknown type "{ftype}" in read_data.'
        log.error(errmsg)        
        raise ValueError(errmsg)
    return finalize_data(df, details)


def convert_data(read_details, write_details):
    """
    Convert a data set from one form to another.

    :param read_details: The details of the data to be read.
    :type read_details: dict
    :param write_details: The details of the data to be written.
    :type write_details: dict
    """
    data, details = read_data(read_details)
    write_data(data, write_details)


def data_exists(details):
    """
    Check if a particular data structure exists or needs to be created.

    :param details: The details of the data to be checked.
    :type details: dict
    :return: Whether the data exists or not.
    :rtype: bool
    """
    if "filename" in details:
        filename = extract_full_filename(details)
        if os.path.exists(filename):
            return True
        else:
            return False
    if details["type"] == "gsheet":
        raise NotImplementedError(
            "Haven't yet implemented check for existence fo particular google sheets."
        )

    if "source" in details:
        sources = details["source"]
        available = True
        if type(sources) is not list:
            sources = [sources]
        for source in sources:
            directory = source["directory"]
            if not os.path.exists(os.path.expandvars(directory)):
                log.error(f'Missing directory "{directory}".')
                available = False
        return available

    else:
        log.error("Unhandled data source availability type.")
        return False


def load_or_create_df(details, index):
    """
    Load in a data frame or create it if it doesn't exist yet.

    :param details: The details of the data to be loaded or created.
    :type details: dict
    :param index: The index to be used if the data frame needs to be created.
    :type index: pandas.Index
    :return: The data frame.
    """
    if data_exists(details):
        return read_data(details)
    elif index is not None:
        log.debug(f'Creating new DataFrame from index as "{details}" is not found.')
        if "columns" in details:
            df = pd.DataFrame(index=index, columns=[index.name] + details["columns"])
            df[index.name] = index
        else:
            df = pd.DataFrame(index=index, data=index)
            df.index.name = index.name
        return finalize_data(df, details)
    else:
        raise FileNotFoundError(f'Could not find file "{extract_full_filename(details)}" and no index was provided to create it.')


def globals_data(details, index=None):
    """
    Load in the globals data to a data frame.

    :param details: The details of the data to be loaded.
    :type details: dict
    
    """
    # don't do it in the standard way as we don't want the index to be a column
    # if "index" in details:
    #     index_column_name = details["index"]
    # else:
    #     index_column_name = "index"
    # if data_exists(details):
    #     df, details = read_data(details)
    #     df.set_index(index_column_name, inplace=True)
    #     return df, details
    # elif index is not None:
    #     log.debug(f"Creating new globals DataFrame from index as \"{details}\" is not found.")
    #     if "columns" in details:
    #         df = pd.DataFrame(index=pd.Index(data=index, name=index_column_name), columns=details["columns"])
    #     else:
    #         raise ValueError(f"Field \"columns\" must be provided in globals.")
    #     return finalize_data(df, details)
    # else:
    #     raise FileNotFoundError(
    #         errno.ENOENT,
    #         os.strerror(errno.ENOENT), filename
    #         )

    return load_or_create_df(details, index)


def cache(details, index=None):
    """
    Load in the cache data to a data frame.

    :param details: The details of the data to be loaded.
    :type details: dict
    """
    return load_or_create_df(details, index)


def scores(details, index=None):
    """
    Load in the score data to data frames.

    :param details: The details of the data to be loaded.
    :type details: dict
    """
    return load_or_create_df(details, index)


def series(details, index=None):
    """
    Load in a series to data frame

    :param details: The details of the data to be loaded.
    :type details: dict
    """
    if data_exists(details):
        return read_data(details)
    elif index is not None:
        log.debug(
            f'Creating new DataFrame for write data from index as "{details}" is not found.'
        )
        return finalize_data(pd.DataFrame(index=index, data=index), details)
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), details)


def write_data(df, details):
    """
    Write the data using the details given in configuration.

    :param df: The data to be written.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param details: The details of the data to be written.
    :type details: dict
    """
    if "type" in details:
        ftype = details["type"]
    else:
        log.error('Field "type" missing in data source details for write_data.')
        return

    if ftype == "excel":
        write_excel(df, details)
    elif ftype == "gsheet":
        write_gsheet(df, details)
    elif ftype == "csv":
        write_csv(df, details)
    elif ftype == "json":
        write_json(df, details)
    elif ftype == "bibtex":
        write_bibtex(df, details)
    elif ftype == "yaml":
        write_yaml(df, details)
    elif ftype == "markdown":
        write_markdown(df, details)
    elif ftype == "yaml_directory":
        write_yaml_directory(df, details)
    elif ftype == "markdown_directory":
        write_markdown_directory(df, details)
    elif ftype == "meta_directory":
        write_meta_directory(df, details)
    else:
        errmsg = f'Unknown type "{ftype}" in write_data.'
        log.error(errmsg)
        raise ValueError(errmsg)


def write_globals(df, config):
    """
    Write the globals to a file.

    :param df: The data to be written.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param config: The configuration to be used.
    :type config: dict
    """
    write_df = pd.concat(
        [pd.Series(list(df.index), index=df.index, name=df.index.name), df], axis=1
    )
    write_data(write_df, config["globals"])


def write_cache(df, config):
    """
    Write the cache to a file.

    :param df: The data to be written.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param config: The configuration to be used.
    :type config: dict
    """
    write_df = pd.concat(
        [pd.Series(list(df.index), index=df.index, name=df.index.name), df], axis=1
    )
    write_data(write_df, config["cache"])


def write_scores(df, config):
    """
    Write the scoring data frame to a file.

    :param df: The data to be written.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param config: The configuration to be used.
    :type config: dict
    """
    write_df = pd.concat(
        [pd.Series(list(df.index), index=df.index, name=df.index.name), df], axis=1
    )
    write_data(write_df, config["scores"])


def write_series(df, config):
    """
    Load in the series data to a file.

    :param df: The data to be written.
    :type df: pandas.DataFrame or ndlpy.data.CustomDataFrame
    :param config: The configuration to be used.
    :type config: dict
    """
    write_df = pd.concat(
        [pd.Series(list(df.index), index=df.index, name=df.index.name), df], axis=1
    )
    write_data(write_df, config["series"])
