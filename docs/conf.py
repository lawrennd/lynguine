# -- Path setup --------------------------------------------------------------

import os
import sys
from pathlib import Path
import toml  # You might need to install the 'toml' package

# Assuming your docs are in a 'docs' folder at the root of your project
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Load the project metadata from the pyproject.toml file
pyproject = toml.load(root_dir / 'pyproject.toml')
project_metadata = pyproject['tool']['poetry']

# -- Project information -----------------------------------------------------

project = project_metadata['name']
author = project_metadata['authors'][0]  # Adjust if you have multiple authors
copyright = f"2023, {author}"

release = project_metadata['version']
version = '.'.join(release.split('.')[:2])  # Major.Minor version

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.coverage',
    'sphinx.ext.intersphinx',
    'myst_parser',  # For Markdown support
]

# Extension settings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable', None),
    'numpy': ('https://numpy.org/doc/stable', None),
}

autodoc_member_order = 'bysource'  # Keep the same order as in the source file
autodoc_typehints = 'description'  # Put type hints in the description

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.ipynb_checkpoints']

# MyST settings for Markdown support
myst_enable_extensions = [
    'colon_fence',
    'deflist',
]
source_suffix = ['.rst', '.md']

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'  # Use the Read the Docs theme
html_static_path = ['_static']
html_title = f"{project} {version} Documentation"

# Theme options
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
}

# -- Extension configuration -------------------------------------------------
# This tells Sphinx to show the full module names on the API docs
add_module_names = True
