import pytest
from io import StringIO
from unittest.mock import MagicMock
import os
import re
from ndlpy.util import tex  

# Sample YAML content for the settings file
settings_content = """
bibinputs: /path/to/bib
texinputs: /path/to/tex
"""
subbibfile_content = """@article{Author2021,
    title={Title},
    year={2021}
}
@article{Author2022,
    title={Title},
    year={2022}
}
"""
bibfile_content = subbibfile_content + """@article{Author2023,
    title={Title},
    year={2023}
}
"""

# Mock open for settings file
@pytest.fixture
def mock_settings_file(monkeypatch):
    
    def mock_open(*args, **kwargs):
        if args[0].endswith('.yml'):
            return StringIO(settings_content)
        elif args[0].endswith('.bib'):
            return StringIO(bibfile_content)
        return MagicMock()  # Return a mock object for other file types

    monkeypatch.setattr("builtins.open", mock_open)

# Test for extract_bib_files
def test_extract_bib_files():
    lines = ["\\bibliography{references}"]
    result = tex.extract_bib_files(lines)
    assert result == ["references"]


# Test for substitute_inputs using mocked settings file
@pytest.mark.parametrize("filename, file_exists, expected", [
    ("main.tex", True, "substituted content"),
    ("nonexistent.tex", False, None)
])
def test_substitute_inputs(filename, file_exists, expected, mocker):
    # Mock file existence check
    mocker.patch('os.path.exists', return_value=file_exists)

    # Mock 'open' only if the file exists
    if file_exists:
        mocker.patch('builtins.open', mocker.mock_open(read_data=expected), create=True)

    result = tex.substitute_inputs(filename)
    assert result == expected
    
# Test for extract_inputs
def test_extract_inputs():
    lines = ["\\input{chapter1}", "\\newsection{Section}{section1}\\input{chapter2}", "\\include{chapter3}", "\\newsubsection{Subsection}{subsection1}"]
    result = tex.extract_inputs(lines)
    assert result == ["chapter1", "section1", "chapter2", "chapter3", "subsection1"]

# Test for extract_citations
def test_extract_citations():
    lines = ["Some text \\cite{Author2021} more text."]
    result = tex.extract_citations(lines)
    assert result == ["Author2021"]


# Test for extract_diagrams
@pytest.mark.parametrize("lines, type, expected", [
    (["\\includediagram{diagram1}"], "diagram", ["diagram1"]),
    (["\\includeimg{image1}"], "img", ["image1"]),
    (["\\includepng{image2}"], "png", ["image2"]),
    # Add more combinations as needed
])
def test_extract_diagrams(lines, type, expected):
    result = tex.extract_diagrams(lines, type=type)
    assert result == expected

# Test for create_bib_file_given_tex
def test_create_bib_file_given_tex(mock_settings_file, mocker):
    lines = ["Some LaTeX content with \\cite{Ref1}", "\\bibliography{bibfile}"]
    mocker.patch('ndlpy.util.tex.extract_bib_files', return_value=["bibfile"])
    mocker.patch('ndlpy.util.tex.extract_citations', return_value=["Ref1"])
    mocker.patch('ndlpy.util.tex.make_bib_file', return_value="Bibliography Content")

    bib_content = tex.create_bib_file_given_tex(lines)

    # Assertions based on expected bibliography content
    assert "Bibliography Content" in bib_content

# Test for make_bib_file
def test_make_bib_file(mock_settings_file, mocker):
    citations_list = ["Author2021", "Author2022"]
    bib_files = ["bibfile"]
    mocker.patch('os.environ.get', return_value="/path/to/bib")
    mocker.patch('os.path.join', side_effect=lambda *args: '/'.join(args))
    mocker.patch('os.access', return_value=True)
    mocker.patch('builtins.open', mocker.mock_open(read_data=bibfile_content), create=True)

    result = tex.make_bib_file(citations_list, bib_files)

    # Assertions based on expected result
    assert subbibfile_content in result
    
