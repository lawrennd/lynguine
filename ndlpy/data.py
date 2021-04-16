import os
import json
import csv
import frontmatter as fm
import bibtexparser as bp

def loaddata(files):
    """Load data from yaml, json, bib and csv files into a python dictionary"""

    entries = []
    for file in files:
        with open(file, 'r') as file:
            new_data = _loaddatastream(file)
        if isinstance(new_data, list):
            entries += new_data
        else:
            entries.append(new_data)
    return entries

def _loaddatastream(file):
    """Loads in the data from the stream to a dictionary or list of dictionaries and adds the name of the source file to the dictionary entries."""
    name, ext = os.path.splitext(file.name)
    ext = ext[1:]
    if (ext == 'yaml'
        or ext == 'md'
        or ext == 'markdown'
        or ext == 'html'):
        new_data, _ = fm.parse(file.read())
    elif ext == 'json':
        new_data = json.load(f)
    elif ext == 'csv':
        new_data = list(csv.DictReader(file, quotechar='"'))
    elif ext == 'bib':
        bd = bp(file)
        new_data = bd.entries
        
    if isinstance(new_data, list):
        for entry in new_data:
            entry['sourcefile'] = file.name
    else:
        new_data['sourcefile'] = file.name
    return new_data
