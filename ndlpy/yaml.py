from .settings import Settings

import re
from . import access


class FileFormatError(Exception):
    def __init__(self, ind, msg=None, field=None):
        if msg is None:
            msg = "File format error occured with index {ind}".format(ind=ind)
        if field is not None:
            msg += " field: {field}".format(field=field)
        super(FileFormatError, self).__init__(msg)
        

def update_from_file(dictionary, filename):
    """Update a given dictionary with the fields from a specified file."""
    dictionary.update(read_yaml_file(filename))
    return dictionary
    

def header_field(field, fields, user_file=["_config.yml"]):
    """Return one field from yaml header fields."""
    if field not in fields:
        settings = Settings(user_file, directory=".")
        if field in settings:
            answer = settings[field]
        else:
            raise FileFormatError(1, "Field not found in file or defaults.", field)
    else:
        answer = fields[field]
    return answer

def header_fields(filename):
    """Extract headers from a talk file."""
    head, _ = extract_header_body(filename)
    return head

def extract_header_body(filename):
    """Extract the text of the headers and body from a yaml headed file."""
    data = access.read_markdown_file(filename)
    if "content" in data:
        content = data["content"]
        del data["content"]
    else:
        content = None
    return data, content
