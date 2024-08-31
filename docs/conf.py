# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "../src")))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Safeguard.io'
copyright = '2024'
author = 'Alex DR'
release = 'v1.0'
version = '2.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'autoapi.extension',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

extlinks_detect_hardcoded_links = True
source_suffix = {
    '.rst': 'restructuredtext',
}
html_extra_path = ['../README.rst']

# -----------------------------------------------------------------------------#
# autoapi options :

autosummary_generate = True

autoapi_type = 'python'
autoapi_dirs = ['../src']
autoapi_options = ['show-inheritance', 'show-module-summary', 'undoc-members']

autoapi_keep_files = True
autoapi_add_toctree_entry = False
autoapi_python_class_content = 'both'

numfig = False
add_module_names = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'