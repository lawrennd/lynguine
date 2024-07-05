from ..config.interface import Interface

import re
from ..access import io


class FileFormatError(Exception):
    """
    Exception raised for errors in the file format.
    """
    def __init__(self, ind, msg=None, field=None):
        if msg is None:
            msg = "File format error occured with index {ind}".format(ind=ind)
        if field is not None:
            msg += " field: {field}".format(field=field)
        super(FileFormatError, self).__init__(msg)
        

def update_from_file(dictionary, filename):
    """
    Update a given dictionary with the fields from a specified file.

    :param dictionary: The dictionary to be updated.
    :type dictionary: dict
    :param filename: The name of the file to be read in.
    :type filename: str
    :return: The updated dictionary.
    """
    dictionary.update(io.read_yaml_file(filename))
    return dictionary
    

def header_field(field, fields, user_file=["_config.yml"]):
    """
    Return one field from yaml header fields.

    :param field: The field to be returned.
    :type field: str
    :param fields: The fields to be searched.
    :type fields: dict
    :param user_file: The user file to be searched.
    :type user_file: str
    """
    if field not in fields:
        interface = Interface.from_file(user_file, directory=".")
        if field in interface:
            answer = interface[field]
        else:
            raise FileFormatError(1, "Field not found in file or defaults.", field)
    else:
        answer = fields[field]
    return answer

def header_fields(filename):
    """
    Extract headers from a talk file.

    :param filename: The name of the file to be read in.
    :type filename: str
    :return: The headers.
    :rtype: dict
    """
    head, _ = extract_header_body(filename)
    return head

def extract_header_body(filename):
    """
    Extract the text of the headers and body from a yaml headed file.

    :param filename: The name of the file to be read in.
    :type filename: str
    :return: The headers and body.
    :rtype: tuple
    """
    data = io.read_markdown_file(filename)
    if "content" in data:
        content = data["content"]
        del data["content"]
    else:
        content = None
    return data, content
