import os
from datetime import date
import warnings

import ndlpy.tex as latex
import ndlpy.util.yaml as ny


today = date.today()    

def talk_field(field, filename):
    """Return one field from a talk."""
    fields = ny.header_fields(filename)
    return ny.header_field(field, fields)    
        
def extract_bibinputs(filename):
    """Extract bibinput files from a talk"""
    # Hard coded for the moment
    raise NotImplementedError

def extract_all(filename, user_file=["_config.yml"]):
    """List the different files the talk file creates."""
    basename = os.path.basename(filename)
    base = os.path.splitext(basename)[0]
    fields = ny.header_fields(filename)
    list_files = []
    if ny.header_field('posts', fields, user_file):
        list_files += [base + '.posts.html']
    if ny.header_field('ipynb', fields, user_file):
        list_files += [base + '.ipynb']
    if ny.header_field('docx', fields, user_file):
        list_files += [base + '.docx']
    if ny.header_field('notespdf', fields, user_file):
        list_files += [base + '.notes.pdf']
    if ny.header_field('reveal', fields, user_file):
        list_files += [base + '.slides.html']
    if ny.header_field('slidesipynb', fields, user_file):
        list_files += [base + '.slides.ipynb']
    if ny.header_field('pptx', fields, user_file):
        list_files += [base + '.pptx']
        
    return list_files

def extract_inputs(filename, snippets_path=".."):
    """Extract input and include files from a talk"""
    list_files=[]
    snippets_path = os.path.expandvars(snippets_path)
    if filename=='\\filename.svg':
        return []
    if not os.path.exists(filename):
        snipname = os.path.join(snippets_path, filename)
        if os.path.exists(snipname):
            filename = snipname
        else:
            return [filename]
    with open(filename, 'r') as f:
        lines = f.readlines()

    filenames = latex.extract_inputs(lines)
    not_present=[]
    for i, filename in enumerate(filenames):
        includepos = os.path.join(snippets_path, filename)
        if os.path.isfile(filename):
            list_files.append(filename)
        elif os.path.isfile(includepos):
            list_files.append(includepos)
        elif filename == '\\filename.svg':
            pass
        else:
            not_present.append(filename)

    filenames = list_files

    for i, filename in enumerate(filenames):
        if os.path.exists(filename):
            list_files[i+1:i+1] = extract_inputs(filename, snippets_path=snippets_path) 

    return list_files + not_present

def extract_diagrams(filename, 
                     absolute_path=True,
                     diagram_exts=['svg', 'png', 'emf', 'pdf'],
                     diagrams_dir=None,
                     snippets_path=None):
    """Extract diagrams from a talk"""
    if snippets_path is not None:
        snippets_path = os.path.expandvars(snippets_path)
        
    if os.path.exists(filename):
        filenames = [filename] + extract_inputs(filename, snippets_path)
    else:
        warnings.warn(f"Warning, input file {filename} does not exist.")
        return

    listdiagrams = []
    for filen in filenames:
        # exclude talk-macros file.
        if filen[:14] =='../talk-macros':
            continue

        if filen == '\\filename.svg':
            continue
        else:
            if not os.path.exists(filen):
                exname = os.path.join(snippets_path, filen)
                if os.path.exists(exname):
                    filen = exname
                else:
                    warnings.warn(f"Input file {filen} does not exist with snippets path {snippets_path}..")
                    continue
            f = open(filen, 'r')
            lines = f.readlines()
            f.close()

        for ext in ['png', 'jpg', 'gif']:
            diagrams = latex.extract_diagrams(lines, ext)
            diag_list = []
            for i, diag_str in enumerate(diagrams):
                if diagrams_dir is not None: # Substitute if diagrams_dir exists
                    diag_str = diag_str.replace('\\diagramsDir', diagrams_dir)
                if "\\" not in diag_str: # Ignore remaining tex macros
                    diag_list.append(diag_str + '.' + ext)
            listdiagrams.extend(diag_list)
        diagrams = latex.extract_diagrams(lines, 'diagram')
        diag_dict = {}
        for ext in diagram_exts:
            diag_dict[ext] = []
        for i, diag_str in enumerate(diagrams):
            if diagrams_dir is not None: # Substitute if diagrams_dir exists
                diag_str = diag_str.replace('\\diagramsDir', diagrams_dir)
            if "\\" not in diag_str: # Ignore remaining tex macros
                for ext in diagram_exts:
                     diag_dict[ext].append(diag_str + '.' + ext)

        for ext in diagram_exts:
            listdiagrams.extend(diag_dict[ext])

    full_list = []
    if absolute_path:
        for diag in listdiagrams:
            full_list.append(os.path.abspath(diag))
    else:
        for diag in listdiagrams:
            full_list.append(diag)
    return full_list
