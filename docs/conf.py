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

release = project_metadata['version']

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    # Add other Sphinx extensions here
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------
