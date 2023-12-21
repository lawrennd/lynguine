import os
import json
import yaml
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

def writedata(data, filename):
    with open(filename, 'w') as file:
        _writedatastream(data, file)
        
def _loaddatastream(file):
    """Loads in the data from the stream to a dictionary or list of dictionaries and adds the name of the source file to the dictionary entries."""
    name, ext = os.path.splitext(file.name)
    ext = ext[1:]
    if (ext == 'md'
        or ext == 'markdown'
        or ext == 'html'):
        print(name, ext)
        new_data, content = fm.loads(file)
        new_data["content"] = content
    elif (ext == "yaml"
          or ext == "yml"):
        new_data = yaml.safe_load(file)
    elif ext == 'json':
        new_data = json.load(file)
    elif ext == 'csv':
        new_data = list(csv.DictReader(file, quotechar='"'))
    elif ext == 'bib':
        bd = bp(file)
        new_data = bd.entries
    else:
        new_data = {}
    if isinstance(new_data, list):
        for entry in new_data:
            entry['sourcefile'] = file.name
            for key in entry:
                if key is None:
                    raise TypeError("File {name} has generated a non-string key.".format(name=file.name))

    else:
        new_data['sourcefile'] = file.name
        for key in new_data:
            if key is None:
                raise TypeError("File {name} has generated a non-string key.".format(name=file.name))
    return new_data


def _writedatastream(data, file):
    """Write data to a given file stream."""
    name, ext = os.path.splitext(file.name)
    ext = ext[1:]
                
    if (ext == 'md'
        or ext == 'markdown'
        or ext == 'html'):
        post = frontmatter.Post(content, **write_data)
        with open(filename, "wb") as stream:
            frontmatter.dump(post, stream, sort_keys=False)
        new_data, _ = fm.parse(file.read())
    elif (ext == "yaml"
          or ext == "yml"):
        new_data = yaml.dump(data, file)
    elif ext == 'json':
        new_data = json.dump(data, file)
    elif ext == 'bib':
        bd = bp.bibdatabase.BibDatabase(entries=data)
        bd = bp.dump(file)
    else:
        raise Error("Unrecognised output file type")
    
