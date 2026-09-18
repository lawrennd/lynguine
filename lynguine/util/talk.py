import os
from datetime import date
import warnings

import lynguine.util.tex as latex
import lynguine.util.yaml as ny

today = date.today()    

def talk_field(field, filename, user_file=["_config.yml"]):
    """
    Return one field from a talk.

    :param field: The field to return.
    :type field: str
    :param filename: The filename of the talk.
    :type filename: str
    """
    fields = ny.header_fields(filename)
    return ny.header_field(field, fields, user_file)    
        
def extract_bibinputs(filename):
    """
    Extract bibinput files from a talk

    :param filename: The filename of the talk.
    :type filename: str
    :return: The bibinput files.
    :rtype: list
    """
    # Hard coded for the moment
    raise NotImplementedError

def extract_all(filename, user_file=["_config.yml"]):
    """
    List the different files the talk file creates.

    :param filename: The filename of the talk.
    :type filename: str
    :param user_file: The user file to use.
    :type user_file: list
    :return: The list of files.
    :rtype: list
    """
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
    """
    Extract input and include files from a talk

    :param filename: The filename of the talk.
    :type filename: str
    :param snippets_path: The snippets path.
    :type snippets_path: str
    :return: The list of files.
    :rtype: list
    """
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
        lines = f.read()

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

def _skip_scanned_file(filename):
    """Return True for include names that diagram scanning must not open."""
    return filename == '\\filename.svg' or filename[:14] == '../talk-macros'


def _resolve_included_file(filename, snippets_path):
    """
    Resolve an include name the same way :func:`extract_inputs` does.

    :return: Existing path, or None when the file cannot be found.
    """
    if os.path.isfile(filename):
        return filename
    if snippets_path is not None:
        includepos = os.path.join(snippets_path, filename)
        if os.path.isfile(includepos):
            return includepos
    return None


def _expanded_diagrams(lines, define_macros, diagrams_dir, diagram_exts):
    """Expand diagram paths in one file and return concrete dependency names."""
    listdiagrams = []
    for ext in ['png', 'jpg', 'gif']:
        diagrams = latex.extract_diagrams(lines, ext)
        for diag_str in diagrams:
            if diagrams_dir is not None:
                diag_str = diag_str.replace('\\diagramsDir', diagrams_dir)
            diag_str = latex.expand_diagram_path(diag_str, define_macros)
            if "\\" not in diag_str:
                listdiagrams.append(diag_str + '.' + ext)
    diagrams = latex.extract_diagrams(lines, 'diagram')
    diag_dict = {ext: [] for ext in diagram_exts}
    for diag_str in diagrams:
        if diagrams_dir is not None:
            diag_str = diag_str.replace('\\diagramsDir', diagrams_dir)
        diag_str = latex.expand_diagram_path(diag_str, define_macros)
        if "\\" not in diag_str:
            for ext in diagram_exts:
                diag_dict[ext].append(diag_str + '.' + ext)
    for ext in diagram_exts:
        listdiagrams.extend(diag_dict[ext])
    return listdiagrams


def _extract_diagrams_scoped(filename, inherited_macros, diagrams_dir, diagram_exts, snippets_path, stack):
    """
    Scan one file and the includes it reaches, carrying an inherited macro map.

    ``inherited_macros`` is the parent scope. Defines in this file override
    those names. The merged map is passed into files reached by the same
    include edges as :func:`extract_inputs` (``\\include``, ``\\includetalkfile``,
    ``\\input``, ``\\newsection``, ``\\newsubsection``). A child's defines are
    not written back, so they are invisible to later siblings.

    Defines are taken from the whole including file, not only lines above the
    include. Expansion is still only ``\\define`` and ``\\concat``, not full gpp.
    ``stack`` is the include chain currently open, so a cycle stops instead of
    recursing forever. The same file may be scanned again from another parent.
    """
    if filename in stack or _skip_scanned_file(filename):
        return []
    if not os.path.exists(filename):
        resolved = _resolve_included_file(filename, snippets_path)
        if resolved is None:
            warnings.warn(
                f'Input file "{filename}" does not exist with snippets path "{snippets_path}".'
            )
            return []
        if _skip_scanned_file(resolved):
            return []
        filename = resolved
        if filename in stack:
            return []

    stack.append(filename)
    try:
        with open(filename, 'r') as handle:
            lines = handle.readlines()
        macros = dict(inherited_macros)
        macros.update(latex.collect_define_macros(lines))
        found = _expanded_diagrams(lines, macros, diagrams_dir, diagram_exts)
        for include_name in latex.extract_inputs(lines):
            if _skip_scanned_file(include_name):
                continue
            child = _resolve_included_file(include_name, snippets_path)
            if child is None:
                warnings.warn(
                    f'Input file "{include_name}" does not exist with snippets path "{snippets_path}".'
                )
                continue
            if _skip_scanned_file(child):
                continue
            found.extend(
                _extract_diagrams_scoped(
                    child,
                    macros,
                    diagrams_dir,
                    diagram_exts,
                    snippets_path,
                    stack,
                )
            )
        return found
    finally:
        stack.pop()


def extract_diagrams(filename, 
                     absolute_path=True,
                     diagram_exts=['svg', 'png', 'emf', 'pdf'],
                     diagrams_dir=None,
                     snippets_path=None):
    """
    Extract diagrams from a talk.

    ``\\define`` macros are inherited across the include tree. A file sees
    defines from the files that included it, then its own defines, which
    win on a name clash. Included files do not publish their defines to
    siblings. The include edges are those :func:`extract_inputs` already
    discovers: ``\\include``, ``\\includetalkfile``, ``\\input``,
    ``\\newsection``, and ``\\newsubsection``.

    This is bounded expansion (``\\define`` name substitution and
    ``\\concat``), not full gpp. Every ``\\define`` in an including file is
    visible to its includes, including defines that appear textually after
    the include line.

    :param filename: The filename of the talk.
    :type filename: str
    :param absolute_path: Whether to use absolute paths.
    :type absolute_path: bool
    :param diagram_exts: The diagram extensions.
    :type diagram_exts: list
    :param diagrams_dir: The diagrams directory.
    :type diagrams_dir: str
    :param snippets_path: The snippets path.
    :type snippets_path: str
    :return: The list of diagrams.
    :rtype: list
    """
    if snippets_path is not None:
        snippets_path = os.path.expandvars(snippets_path)

    if not os.path.exists(filename):
        warnings.warn(f'Warning, input file "{filename}" does not exist.')
        return

    listdiagrams = _extract_diagrams_scoped(
        filename,
        {},
        diagrams_dir,
        diagram_exts,
        snippets_path,
        [],
    )

    full_list = []
    if absolute_path:
        for diag in listdiagrams:
            full_list.append(os.path.abspath(diag))
    else:
        for diag in listdiagrams:
            full_list.append(diag)
    return full_list
