# Configuration file for the Sphinx documentation builder.

import os
import sys

# -- Path setup ------------------------------------------------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory, add these directories to sys.path here.
# If the directory is relative to the documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('../..'))


# -- Project information ---------------------------------------------------------------------------------------------

project = u'PyHelpers'
copyright = u'2019-2020, Qian Fu'
author = u'Qian Fu'
description = u'A Python toolkit for facilitating data manipulation.'

# The full version, including alpha/beta/rc tags
from pyhelpers import __version__

version = 'v' + __version__
release = version


# -- General configuration -------------------------------------------------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions coming with
# Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.githubpages',
    'sphinx_rtd_theme',
]


# Automatically documented members are sorted by source order ('bysource')
autodoc_member_order = 'bysource'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

autosummary_generate = True

# The suffix(es) of source filenames.
# (Specify multiple suffix as a list of string, e.g. source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# List of patterns, relative to source directory,
#  that match files and directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

gettext_compact = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'  # or 'default'

# -- Options for HTML output -----------------------------------------------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Theme options are theme-specific and customize the look and feel of a theme further.
# For a list of options available for each theme, see the documentation.
# html_theme_options = {
#     'logo_only': True,
#     'navigation_depth': 5,
# }

# html_context = {}

# Custom sidebar templates, must be a dictionary that maps document names to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html', 'searchbox.html']``.
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = project.lower() + 'doc'

# -- Options for LaTeX output ----------------------------------------------------------------------------------------

latex_elements = {
    'papersize': 'letterpaper',  # The paper size ('letterpaper' or 'a4paper').
    'pointsize': '10pt',  # The font size ('10pt', '11pt' or '12pt').
    # Additional stuff for the LaTeX preamble.
    'preamble': '''
        \\setlength{\\headheight}{14pt}
        \\usepackage[utf8]{inputenc}
        \\usepackage{textcomp}
        \\usepackage{amsfonts}
        \\usepackage{textgreek}
        \\usepackage{graphicx}
        \\usepackage{svg}
        ''',
    # 'figure_align': 'htbp',  # Latex figure (float) alignment
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto, manual, or own class]).
latex_documents = [
    ('index', '{}.tex'.format(project.lower()), project + ' Documentation', author, 'manual'),
]

# -- Options for manual page output ----------------------------------------------------------------------------------

# One entry per manual page. List of tuples (source start file, name, description, authors, manual section).
man_pages = [
    ('index', project.lower(), project + ' Documentation', [author], 1)
]

# -- Options for Texinfo output --------------------------------------------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author, dir menu entry, description, category)
texinfo_documents = [
    (master_doc, project, project + ' Documentation',
     author, project.lower(), description, 'miscellaneous'),
]

latex_engine = 'pdflatex'