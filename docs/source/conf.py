"""
Configuration file for the Sphinx documentation builder.
"""

# Path setup =====================================================================================
import os
import sys

# If the directory is relative to the documentation root, use os.path.abspath to make it absolute
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../pyhelpers'))

# A list of modules to be mocked up.
autodoc_mock_imports = [
    'numpy', 'pyproj', 'Shapely', 'scipy',
    'fake-useragent', 'pandas', 'requests', 'tqdm',
    'psycopg2', 'SQLAlchemy', 'joblib', 'orjson',
    'fuzzywuzzy',
]

# Project information ============================================================================
from pyhelpers import __author__, __package_name__, __project_name__, __version__, __copyright__

# General information about the project:
project = f'{__project_name__}'
copyright = f'{__copyright__}'

# The version info for the project:
version = __version__  # The short X.Y.Z version
release = version  # The full version, including alpha/beta/rc tags

# General configuration ==========================================================================
import sphinx_rtd_theme

_ = sphinx_rtd_theme.get_html_theme_path()

# Sphinx extension module names, which can be named 'sphinx.ext.*' or custom ones:
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.githubpages',
    'sphinx.ext.todo',
    'sphinx_rtd_theme',
]

# Enable to reference numbered figures:
numfig = True
numfig_secnum_depth = 0
numfig_format = {'figure': 'Fig. %s', 'table': 'Table %s', 'code-block': 'Code Block %s'}
numfig_format_caption = {'figure': 'Fig. %s: '}

# The language for content autogenerated by Sphinx:
language = 'en'

# Add any paths that contain templates here, relative to this directory:
templates_path = ['_templates']

# Patterns (relative to source directory) that match files & directories to ignore:
exclude_patterns = ['_build', '../_build', '../build']

# Whether to scan all found documents for autosummary directives, and generate stub pages for each:
autosummary_generate = True

# The suffix(es) of source filenames (For multiple suffix, a list of string:
source_suffix = '.rst'  # e.g. source_suffix = ['.rst', '.md'])

# The master toctree document:
master_doc = 'index'

# Automatically documented members are sorted by source order ('bysource'):
autodoc_member_order = 'bysource'

# Options for HTML and HTMLHelp output ===========================================================
html_theme = 'sphinx_rtd_theme'  # The theme to use for HTML & HTML Help pages

html_theme_options = {
    'collapse_navigation': False,
    'navigation_depth': 3,
}

# Hide/show source link:
html_copy_source = False
html_show_sourcelink = False

# The name of the Pygments (syntax highlighting) style to use:
pygments_style = 'sphinx'  # or 'default'

# Paths containing custom static files (e.g. style sheets), relative to this directory:
html_static_path = ['_static']

# Add custom CSS:
html_css_files = ['rtd_overrides.css']

# Add custom JavaScript:
html_js_files = ['copybutton.js']

# Output file base name for HTML help builder:
htmlhelp_basename = __project_name__ + 'doc'  # Defaults to 'pydoc'

# Options for LaTeX output =======================================================================
from pygments.formatters.latex import LatexFormatter
from sphinx.highlighting import PygmentsBridge


class CustomLatexFormatter(LatexFormatter):
    def __init__(self, **options):
        super(CustomLatexFormatter, self).__init__(**options)
        self.verboptions = r"formatcom=\footnotesize"


PygmentsBridge.latex_formatter = CustomLatexFormatter

# The LaTeX engine to build the docs:
latex_engine = 'pdflatex'

# Grouping the document tree into LaTeX files:
latex_documents = [
    ('index',  # source start file
     f'{__package_name__}.tex',  # target name
     f'{__project_name__} Documentation',  # title
     f'{__author__}',  # author
     'manual',  # document class ['howto', 'manual', or own class]
     1  # toctree only
     ),
]

# Customised title page
latex_maketitle = r'''
    \pagenumbering{roman}

    \begin{titlepage}
        \flushleft

        \vspace*{30mm}
        \textbf{\Huge {{PyHelpers Documentation}}}
        
        \vspace{5mm}
        \LARGE A lite toolkit for facilitating data manipulations \par
        \textit{\Large {{Release %s}}}

        \makeatletter
        \bookmark[named=FirstPage]{Title}
        \makeatother

        \vspace{60mm}
        \Large \textbf{{%s}}

        \vspace{10mm}
        \large School of Engineering \par
        \large University of Birmingham \par

        \vspace{55mm}
        \small First release: September 2019 \par
        \small Last updated: \MonthYearFormat\today

    \end{titlepage}

    \clearpage
    \pagenumbering{roman}

    \cleardoublepage
    \makeatletter
    \hypertarget{tocpage}{}
    \tableofcontents
    \bookmark[dest=tocpage]{Table of Contents}
    \makeatother
    
    \cleardoublepage
    \makeatletter
    \hypertarget{lofpage}{}
    \listoffigures
    \bookmark[dest=lofpage]{List of Figures}
    \makeatother

    \clearpage
    \pagenumbering{arabic}
    ''' % (release, __author__)

latex_preamble = r'''
    \setlength{\headheight}{14pt}
    \DeclareUnicodeCharacter{229E}{\ensuremath{\boxplus}}
    \setcounter{tocdepth}{2}
    \setcounter{secnumdepth}{2}
    \usepackage{float,textcomp,textgreek,graphicx,blindtext,color,svg,booktabs,newunicodechar}
    \usepackage{datetime}
    \newdateformat{MonthYearFormat}{%
        \monthname[\THEMONTH] \THEYEAR}
    \usepackage[none]{hyphenat}
    \usepackage[document]{ragged2e}
    \usepackage[utf8]{inputenc}
    \usepackage[sc,osf]{mathpazo}
    \linespread{1.05}
    \renewcommand{\sfdefault}{pplj}
    \newunicodechar{≤}{\ensuremath{\leq}}
    \IfFileExists{zlmtt.sty}
                 {\usepackage[light,scaled=1.05]{zlmtt}}
                 {\renewcommand{\ttdefault}{lmtt}}
    \let\oldlongtable\longtable
    \let\endoldlongtable\endlongtable
    \renewenvironment{longtable}
                     {\rowcolors{1}{anti-flashwhite}{white}\oldlongtable}
                     {\endoldlongtable}
    \usepackage[open]{bookmark}
    \bookmarksetup{numbered}

    \addto\captionsenglish{\renewcommand{\contentsname}{Table of contents}}
    '''

# LaTeX customization:
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '11pt',
    'pxunit': '0.25bp',

    'fontpkg': '\\usepackage{amsmath,amsfonts,amssymb,amsthm}',
    'fncychap': '\\usepackage{fncychap}',  # '\\usepackage[Bjarne]{fncychap}'

    'preamble': latex_preamble,

    'figure_align': 'H',  # 'htbp',
    'extraclassoptions': 'openany,oneside',

    'maketitle': latex_maketitle,

    'releasename': ' ',
    'tableofcontents': ' ',

    # 'makeindex': ' ',
    'printindex': r'''
        \IfFileExists{\jobname.ind}
                     {\footnotesize\raggedright\printindex}
                     {\begin{sphinxtheindex}\end{sphinxtheindex}}
        ''',

    'fvset': r'\fvset{fontsize=auto}',

    'sphinxsetup': r'''
        %verbatimwithframe=false,
        %verbatimwrapslines=false,
        %verbatimhintsturnover=false,
        VerbatimColor={HTML}{F5F5F5},
        VerbatimBorderColor={HTML}{E0E0E0},
        noteBorderColor={HTML}{E0E0E0},
        noteborder=1.5pt,
        warningBorderColor={HTML}{E0E0E0},
        warningborder=1.5pt,
        warningBgColor={HTML}{FBFBFB},
        hmargin={0.7in,0.7in}, vmargin={1.1in,1.1in},
        ''',

    'passoptionstopackages': r'\PassOptionsToPackage{svgnames}{xcolor}',
}
