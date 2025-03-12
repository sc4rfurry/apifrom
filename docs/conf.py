# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import datetime

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'APIFromAnything'
copyright = f'{datetime.datetime.now().year}, APIFromAnything Team'
author = 'APIFromAnything Team'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',
    'sphinx_rtd_theme',
    'myst_parser',
    'sphinx_autodoc_typehints',
    'sphinx_copybutton',
    'sphinx_tabs.tabs',
    'sphinx_togglebutton',
    'sphinx_design',
    'notfound.extension',
    'sphinx_prompt',
    'sphinx_inline_tabs',
    'autoapi.extension',
]

# MyST Parser configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'venv', 'env', 'backup_rst_files*']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '_static/logo.png'
html_favicon = '_static/favicon.ico'
html_theme_options = {
    'logo_only': True,
    # Removed 'display_version' as it's not supported by the theme
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'style_nav_header_background': '#2980B9',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# -- Options for markdown ---------------------------------------------------
source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

# Explicitly prioritize Markdown files over RST files
source_file_priority = ['.md', '.rst', '.txt']

# When both .md and .rst exist, prefer .md files
source_parsers = {
    '.md': 'myst_parser.sphinx_',
}

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}

# AutoAPI configuration
autoapi_dirs = ['../src']  # Path to the source code
autoapi_type = 'python'
autoapi_file_patterns = ['*.py']
autoapi_options = [
    'members',
    'undoc-members',
    'private-members',
    'show-inheritance',
    'show-module-summary',
    'special-members',
    'imported-members',
    'no-index',
]
# Custom template configuration to fix duplicate object descriptions
autoapi_template_dir = '_templates/autoapi'
autoapi_python_class_template = 'python/custom_class.rst'
autoapi_python_module_template = 'python/module.rst'
autoapi_python_package_template = 'python/index.rst'
# Exclude specific attributes from APIFromAnything class in autoapi documentation
autoapi_python_class_content = 'both'
autoapi_member_order = 'groupwise'
autoapi_exclude_members = ['config', 'routes', 'middleware']

# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration

todo_include_todos = True

# -- Additional configuration ------------------------------------------------

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    'css/custom.css',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The master toctree document.
master_doc = 'index'

# -- Options for autodoc extension ------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration

autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_typehints_format = 'short'
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
    }

# Function to skip members with duplicate object descriptions
def autodoc_skip_member(app, what, name, obj, skip, options):
    # Print statement to verify function is being called
    print(f"autodoc_skip_member called for: {what} {name}")
    # Skip config, routes, and middleware in APIFromAnything class
    if name in ['config', 'routes', 'middleware'] and what == 'class' and 'APIFromAnything' in str(obj.__qualname__):
        print(f"Skipping {name} in {obj.__qualname__}")
        return True
    return skip
# Register the skip function with autodoc-skip-member event
def setup(app):
    # Connect the autodoc_skip_member function to the autodoc-skip-member event
    app.connect('autodoc-skip-member', autodoc_skip_member)
    return {
        'version': release,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

# -- Options for napoleon extension -----------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#configuration

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
napoleon_custom_sections = None
