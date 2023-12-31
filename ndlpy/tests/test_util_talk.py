import pytest
from pytest_mock import mocker
import ndlpy.util.talk as talk
import ndlpy.util.yaml as ny

# Test for talk_field function
def test_talk_field(mocker):
    mock_header_fields = mocker.patch('ndlpy.util.yaml.header_fields', return_value={'title': 'Sample Talk'})
    mock_header_field = mocker.patch('ndlpy.util.yaml.header_field', return_value='Sample Talk')

    result = talk.talk_field('title', 'sample_talk.md')

    mock_header_fields.assert_called_once_with('sample_talk.md')
    mock_header_field.assert_called_once_with('title', {'title': 'Sample Talk'})
    assert result == 'Sample Talk'

# Test for extract_all function
def test_extract_all_no_fields(mocker):
    mocker.patch('ndlpy.util.yaml.header_fields', return_value={})
    mocker.patch('ndlpy.util.yaml.header_field', side_effect=lambda field, fields, _: fields.get(field))

    result = talk.extract_all('sample_talk.md')
    assert result == []

def test_extract_all_with_fields(mocker):
    fields = {
        'posts': True,
        'ipynb': False,
        'docx': True,
        'notespdf': True,
        'reveal': False,
        'slidesipynb': True,
        'pptx': True
    }
    mocker.patch('ndlpy.util.yaml.header_fields', return_value=fields)
    mocker.patch('ndlpy.util.yaml.header_field', side_effect=lambda field, fields, _: fields.get(field))

    result = talk.extract_all('sample_talk.md')
    assert result == [
        'sample_talk.posts.html',
        'sample_talk.docx',
        'sample_talk.notes.pdf',
        'sample_talk.slides.ipynb',
        'sample_talk.pptx'
    ]


# Test when the file does not exist and is not in the snippets path
def test_extract_inputs_file_not_exist(mocker):
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('os.path.join', side_effect=lambda a, b: os.path.normpath(f"{a}/{b}"))

    result = talk.extract_inputs('nonexistent.md')
    assert result == ['nonexistent.md']

# Test when the file exists and has includes
def test_extract_inputs_with_includes(mocker):
    # Mocking os.path.exists to simulate file existence
    exists_side_effect = lambda filename: filename in ['sample_talk.md', 'include1.md']
    mocker.patch('os.path.exists', side_effect=exists_side_effect)

    # Mocking os.path.join
    mocker.patch('os.path.join', side_effect=lambda a, b: os.path.normpath(f"{a}/{b}"))

    # Mocking latex.extract_inputs to return include filenames
    mocker.patch('ndlpy.util.tex.extract_inputs', return_value=['include1.md', 'missing_include.md'])

    result = talk.extract_inputs('sample_talk.md')
    
    # Checking if the function has recursively included files and skipped non-existent ones
    assert 'include1.md' in result
    assert 'missing_include.md' in result
    assert 'sample_talk.md' not in result  # The original file should not be in the output

# Test for special filename case
def test_extract_inputs_special_filename(mocker):
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('ndlpy.util.tex.extract_inputs', return_value=['\\filename.svg'])
    mocker.patch('builtins.open', mocker.mock_open(read_data=''))

    result = talk.extract_inputs('sample_talk.md')
    
    # Expecting the special filename to be ignored
    assert '\\filename.svg' not in result

def test_extract_bibinputs_not_implemented():
    with pytest.raises(NotImplementedError):
        talk.extract_bibinputs('sample_talk.md')

def test_extract_inputs_file_not_exist(mocker):
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('os.path.join', side_effect=lambda a, b: f"{a}/{b}")
    mocker.patch('ndlpy.util.tex.extract_inputs', return_value=[])

    result = talk.extract_inputs('nonexistent.md')
    assert result == ['nonexistent.md']

def test_extract_inputs_with_includes(mocker):
    mocker.patch('os.path.exists', side_effect=[True, False, True])
    mocker.patch('os.path.join', side_effect=lambda a, b: f"{a}/{b}")
    mocker.patch('ndlpy.util.tex.extract_inputs', return_value=['include1.md', 'include2.md'])
    mocker.patch('builtins.open', mocker.mock_open(read_data='data'))

    result = talk.extract_inputs('sample_talk.md')
    assert 'include1.md' in result
    assert 'include2.md' in result 


def test_extract_diagrams_no_file_warning(mocker):
    mocker.patch('os.path.exists', return_value=False)
    warning_mock = mocker.patch('warnings.warn')

    result = talk.extract_diagrams('nonexistent.md', absolute_path=False)
    assert result is None
    warning_mock.assert_called_once()

def test_extract_diagrams_with_files(mocker):
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.join', side_effect=lambda a, b: f"{a}/{b}")
    mocker.patch('ndlpy.util.tex.extract_inputs', return_value=[])
    mocker.patch('ndlpy.util.tex.extract_diagrams', return_value=['diagram1', 'diagram2'])
    mocker.patch('builtins.open', mocker.mock_open(read_data='data'))

    result = talk.extract_diagrams('sample_talk.md', diagrams_dir='/diagrams', snippets_path='/snippets', absolute_path=False)
    assert 'diagram1.svg' in result
    assert 'diagram2.svg' in result
