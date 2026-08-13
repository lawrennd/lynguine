import os
import re

from ..config.interface import Interface

interface = Interface.from_file(raise_error_if_not_found=False)

# Using list comprehensions and set for avoiding duplicate directories.
TEX_DIRECTORIES = list(set(["."] + interface.get("bibinputs", "").split(":") + interface.get("texinputs", "").split(":")))
if "TEXINPUTS" in os.environ:
    TEX_DIRECTORIES += os.environ["TEXINPUTS"].split(":")
if "BIBINPUTS" in os.environ:
    TEX_DIRECTORIES += os.environ["BIBINPUTS"].split(":")
TEX_DIRECTORIES = [os.path.expandvars(directory) for directory in TEX_DIRECTORIES]

def extract_bib_files(text):
    """
    Extract all the bib files listed in the file lines.

    :param text: The text of the file to be parsed.
    :type text: str
    :return: The list of bib files.
    :rtype: list

    """
    if isinstance(text, list):
        text = "\n".join(text)

    # Regular expressions for matching bibliography definitions
    patterns = [r'\\bibliography{([^}]*)}', r'\\begin{btSect}.*{([^}]*)}']

    # Extract the bib files
    bib_files = set()
    for pattern in patterns:
        for match in re.findall(pattern, text):
            bib_files.update(match.split(','))

    return list(bib_files)


def substitute_inputs(filename, directories=None):
    """
    Take the base file and substitute in any input and include files.

    :param filename: The filename to be substituted.
    :type filename: str
    :param directories: The directories to search for the input files.
    :type directories: list
    :return: The substituted file.
    :rtype: str
    """

    file_dir = os.path.dirname(filename)
    if directories == None:
        directories = [file_dir]
        filename = os.path.basename(filename)
    elif len(file_dir) > 0:
        if file_dir not in directories:
            directories.append(file_dir)

    for directory in TEX_DIRECTORIES:
        if directory not in directories:
            directories.append(directory)
    if filename[0] == "#":  # it's a macro
        return None
    tex_file_handle = None
    for directory in directories:
        full_filename = os.path.join(directory, filename)
        if os.path.exists(full_filename):
            tex_file_handle = open(full_filename, "r")
            dirname = directory
            break
    if not tex_file_handle:
        return None
    lines = tex_file_handle.readlines()
    new_lines = ""
    # Avoid parsing defined commands in notation def.
    for line in lines:
        if not line[0] == "%":
            match_inp = re.compile(r"""\\newsection *{([^}]*)} *{([^}]*)}""")
            for match in match_inp.finditer(line):
                subs = substitute_inputs(input_file_name(match.group(2)), directories)
                if subs:
                    replace_string = (
                        "\\section{" + match.group(1) + "}" + "\n" * 2 + subs
                    )
                    line = line.replace(match.group(0), replace_string)

            match_inp = re.compile(r"""\\newsubsection *{([^}]*)} *{([^}]*)}""")
            for match in match_inp.finditer(line):
                subs = substitute_inputs(input_file_name(match.group(2)), directories)
                if subs:
                    replace_string = (
                        "\\subsection{" + match.group(1) + "}" + "\n" * 2 + subs
                    )
                    line = line.replace(match.group(0), replace_string)

            match_inp = re.compile(r"""\\inputdiagram{([^}]*)}""")
            for match in match_inp.finditer(line):
                subs = substitute_inputs(input_file_name(match.group(1)), directories)
                if subs:
                    replace_string = "\\small" + subs + "\\vspace{0.5cm}"
                    line = line.replace(match.group(0), replace_string)

            match_inp = re.compile(r"""\\input{([^}]*)}""")
            for match in match_inp.finditer(line):
                subs = substitute_inputs(input_file_name(match.group(1)), directories)
                if subs:
                    line = line.replace(match.group(0), subs)

            match_inp = re.compile(r"""\\include{([^}]*)}""")
            for match in match_inp.finditer(line):
                subs = substitute_inputs(input_file_name(match.group(1)), directories)
                if subs:
                    line = line.replace(match.group(0), subs)

            match_inp = re.compile(r"""\\includetalkfile{([^}]*)}""")
            for match in match_inp.finditer(line):
                subs = substitute_inputs(input_file_name(match.group(1)), directories)
                if subs:
                    line = line.replace(match.group(0), subs)

        new_lines += line

    return new_lines


def input_file_name(filename, extension=".tex"):
    """
    Return the filename with the extension if it exists.

    :param filename: The filename to be checked.
    :type filename: str
    :param extension: The extension to be checked.
    :type extension: str
    :return: The filename with the extension if it exists.
    :rtype: str
    """

    ext_list = ["md", "tex"]
    if os.path.exists(filename):
        return filename
    else:
        for ext in ext_list:
            if os.path.exists(filename + "." + ext):
                return filename + "." + ext


def process_file(filename, extension=".tex"):
    """
    Process a file and return the lines.

    :param filename: The filename to be processed.
    :type filename: str
    :param extension: The extension to be processed.
    :type extension: str
    :return: The lines of the processed file.
    :rtype: list
    """

    tex_file_handle = open(filename, "r")
    lines = tex_file_handle.readlines()
    inp_list = extract_inputs(lines)
    for inp in inp_list:
        if not inp[0] == "#":
            if inp[-len(extension) :] == extension:
                lines += process_file(inp, extension)
            else:
                lines += process_file(inp + extension, extension)
    return lines


def extract_inputs(text):
    """
    Extract latex file dependencies.

    :param text: The text of the file to be processed.
    :type text: str or list of str (for backwards compatability)
    :return: The list of files.
    :rtype: list
    """

    if isinstance(text, str):
        lines = text.split("\n")
    else:
        lines = text
        
    def extract_input(line, matchstr):
        line_inp = re.compile(matchstr).findall(line)
        inp_list = []
        if line_inp:
            for inp in line_inp:
                inp_list = inp_list + inp.split(",")
        return inp_list

    inp_list = []
    for line in lines:
        inp_list += extract_input(line, r"""\\newsection *{[^}]*} *{([^}]*)}""")
        inp_list += extract_input(line, r"""\\newsubsection *{[^}]*} *{([^}]*)}""")
        inp_list += extract_input(line, r"""\\includetalkfile{([^}]*)}""")
        inp_list += extract_input(line, r"""\\input *{([^}]*)}""")
        inp_list += extract_input(line, r"""\\include *{([^}]*)}""")
    return inp_list


_DEFINE_MACRO_RE = re.compile(r"""\\define\{([^}]*)\}\{([^}]*)}""")
_CONCAT_MACRO_RE = re.compile(r"""\\concat\{([^}]*)\}\{([^}]*)}""")


def _extract_balanced_brace_content(text, open_brace_index):
    """
    Return the content inside balanced braces starting at ``open_brace_index``.

    :param text: Source text.
    :type text: str
    :param open_brace_index: Index of the opening ``{``.
    :type open_brace_index: int
    :return: Inner content without the surrounding braces, or None.
    :rtype: str or None
    """
    if open_brace_index >= len(text) or text[open_brace_index] != "{":
        return None

    depth = 0
    for index in range(open_brace_index, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1 : index]
    return None


def _extract_braced_command_arguments(line, command):
    """
    Extract first braced arguments for each ``command`` occurrence on a line.

    Optional ``[...]`` and ``<...>`` modifiers between the command and the
    opening brace are skipped.
    """
    arguments = []
    start = 0
    while True:
        index = line.find(command, start)
        if index == -1:
            break

        pos = index + len(command)
        while pos < len(line) and line[pos] in " \t":
            pos += 1
        if pos < len(line) and line[pos] == "[":
            closing = line.find("]", pos)
            if closing == -1:
                start = index + 1
                continue
            pos = closing + 1
            while pos < len(line) and line[pos] in " \t":
                pos += 1
        if pos < len(line) and line[pos] == "<":
            closing = line.find(">", pos)
            if closing == -1:
                start = index + 1
                continue
            pos = closing + 1
            while pos < len(line) and line[pos] in " \t":
                pos += 1
            if pos < len(line) and line[pos] == "[":
                closing = line.find("]", pos)
                if closing == -1:
                    start = index + 1
                    continue
                pos = closing + 1
                while pos < len(line) and line[pos] in " \t":
                    pos += 1

        if pos < len(line) and line[pos] == "{":
            content = _extract_balanced_brace_content(line, pos)
            if content is not None:
                arguments.append(content)

        start = index + 1

    return arguments


def collect_define_macros(lines):
    """
    Collect gpp-style ``\\define{name}{value}`` macros from file lines.

    Supports ``\\define{\\name}{value}`` and ``\\define{name}{value}``.
    Later definitions in the same file override earlier ones.

    :param lines: File lines or a single string.
    :type lines: list or str
    :return: Mapping from macro name (without leading backslash) to value.
    :rtype: dict
    """
    if isinstance(lines, str):
        text = lines
    else:
        text = "".join(lines)

    macros = {}
    for match in _DEFINE_MACRO_RE.finditer(text):
        name = match.group(1).strip()
        if name.startswith("\\"):
            name = name[1:]
        macros[name] = match.group(2).strip()
    return macros


def expand_diagram_path(path, macros, max_depth=20):
    """
    Expand a bounded subset of gpp macros used in diagram paths.

    Supported forms:

    - ``\\name`` substitution using macros from :func:`collect_define_macros`
    - ``\\concat{left}{right}`` (including nested ``\\concat``)

    This is not a general gpp preprocessor. Paths that still contain
    unsupported ``\\`` tokens after expansion are left unchanged so callers
    can skip them. Nested ``\\concat`` inside a ``\\concat`` argument is
    not supported; use a single ``\\concat`` with ``\\define`` macros instead.

    :param path: Diagram path string, typically from :func:`extract_diagrams`.
    :type path: str
    :param macros: Macro name to replacement value mapping.
    :type macros: dict
    :param max_depth: Maximum ``\\concat`` expansion iterations.
    :type max_depth: int
    :return: Path with supported macros expanded.
    :rtype: str
    """
    if not macros and "\\concat" not in path:
        return path

    if max_depth <= 0:
        return path

    def substitute_names(fragment):
        result = fragment
        for name, value in sorted(macros.items(), key=lambda item: len(item[0]), reverse=True):
            result = result.replace("\\" + name, value)
        return result

    path = substitute_names(path)
    match = _CONCAT_MACRO_RE.search(path)
    if match:
        left = expand_diagram_path(match.group(1), macros, max_depth - 1)
        right = expand_diagram_path(match.group(2), macros, max_depth - 1)
        path = path[: match.start()] + left + right + path[match.end() :]
        return expand_diagram_path(path, macros, max_depth - 1)
    return path


def extract_diagrams(lines, type="all"):
    """
    Extract all the diagrams listed in the file.

    :param lines: The lines of the file to be processed.
    :type lines: list
    :param type: The type of diagrams to be extracted.
    :type type: str
    :return: The list of diagrams.
    :rtype: list
    """
    diagram_list = []

    rebases = {}
    rebases["diagram"] = [
        r"\includediagram",
        r"\includediagramclass",
        r"\inlinediagram",
        r"\inputdiagram",
    ]
    rebases["img"] = [r"\includeimg"]
    rebases["png"] = [r"\includepng"]
    rebases["gif"] = [r"\includegif"]
    rebases["jpg"] = [r"\includejpg"]
    all_val = []
    for key in rebases:
        all_val += rebases[key]
    rebases["all"] = all_val

    for rebase in rebases[type]:
        for line in lines:
            for argument in _extract_braced_command_arguments(line, rebase):
                diagram_list += argument.split(",")

    return diagram_list


def extract_citations(lines):
    """
    Extract all the citations listed in the file lines.

    :param lines: The lines of the file to be processed.
    :type lines: list
    :return: The list of citations.
    :rtype: list
    """
    citations_list = []
    match_cite = re.compile(r"""\\cite[^\{]*{([^}\\#]+)}""")
    full_text = ""
    for line in lines:
        full_text += line
    line_cite = match_cite.findall(full_text)
    if line_cite:
        for cite in line_cite:
            citations_list = citations_list + cite.split(",")
    for i in range(len(citations_list)):
        for j in range(i + 1, len(citations_list)):
            if citations_list[i] == citations_list[j]:
                citations_list[j] = []

    return citations_list


def make_bib_file(citations_list, bib_files):
    """
    Create a new bibliography file for a given list of citations.

    :param citations_list: The list of citations.
    :type citations_list: list
    :param bib_files: The list of bib files.
    :type bib_files: list
    :return: The new bibliography file.
    :rtype: str
    """

    if citations_list:
        citations_list.sort()
        cross_ref_list = []
        string_list = []
        out = ""
        # Get the location of the bibfiles
        bib_dir = TEX_DIRECTORIES

        # Regular expressions
        match_bib_field = re.compile(r"""(\@\w+{)""")
        match_cross_ref = re.compile(
            r"""\bcrossref\s*=\s*[\"|{](.*)[}|\"]""", re.IGNORECASE
        )
        match_string = re.compile(r"""\b\w*\s*=\s*(\w[^0-9]\w*),""")

        for dir in bib_dir:
            if not dir:
                dir = "."
            for filename in bib_files:
                if os.access(os.path.join(dir, filename) + ".bib", os.R_OK):
                    bib_file_handle = open(os.path.join(dir, filename) + ".bib", "r")
                    bib_file = bib_file_handle.read()
                    # Split the bib file at the entries.
                    bib_comp = match_bib_field.split(bib_file)
                    for i in range(len(citations_list)):
                        if citations_list[i]:
                            if i > 0 and citations_list[i] == citations_list[i - 1]:
                                citations_list[i] = []
                                continue
                            for j in range(2, len(bib_comp)):
                                entry = bib_comp[j].split(",")
                                entry = entry[0].split("=")
                                if not entry[0].find(citations_list[i]) == -1:
                                    # print entry[0]
                                    # Adds the entry to output
                                    out = out + bib_comp[j - 1] + bib_comp[j]
                                    # Removes the citation from the list
                                    citations_list[i] = []
                                    cross_refs = match_cross_ref.findall(bib_comp[j])
                                    if cross_refs:
                                        cross_ref_list = cross_ref_list + cross_refs
                                    else:
                                        strings = match_string.findall(bib_comp[j])
                                        if strings:
                                            for string in strings:
                                                if not string_list.count(string):
                                                    string_list.append(string)
                                    break
        return (
            get_bib_strings(string_list, bib_files)
            + out
            + get_bib_cross_refs(cross_ref_list, bib_files)
        )
    else:
        return ""


def get_bib_strings(string_list, bib_files):
    """
    Create a new bibliography file for a given list of bibtex strings.

    :param string_list: The list of bibtex strings.
    :type string_list: list
    :param bib_files: The list of bib files.
    :type bib_files: list
    :return: The new bibliography file.
    :rtype: str
    """
    if string_list:
        return make_bib_file(string_list, bib_files)
    else:
        return ""


def get_bib_cross_refs(string_list, bib_files):
    """
    Create a new bibliography file for a given list of cross references.

    :param string_list: The list of cross references.
    :type string_list: list
    :param bib_files: The list of bib files.
    :type bib_files: list
    :return: The new bibliography file.
    :rtype: str
    """
    if string_list:
        return make_bib_file(string_list, bib_files)
    else:
        return ""


def create_bib_file_given_tex(lines):
    """
    Create a new bibliography file for a given latex file.

    :param lines: The lines of the file to be processed.
    :type lines: list
    :return: The new bibliography file.
    :rtype: str
    """
    bib_files = extract_bib_files(lines)
    citations_list = extract_citations(lines)

    return make_bib_file(citations_list, bib_files)
