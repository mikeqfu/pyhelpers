"""
Configuration file for the Sphinx documentation builder.
"""

# == Path setup ====================================================================================
import os
import sys

# If the directory is relative to the documentation root, use os.path.abspath to make it absolute:
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../pyhelpers'))


# == Project information ===========================================================================
from pyhelpers import (__affil__, __author__, __copyright__, __desc__, __pkgname__, __project__,
                       __version__, __first_release__)

# General information about the project:
project = __project__
copyright = __copyright__

# The version info for the project:
version = __version__  # The short X.Y.Z version
release = version  # The full version, including alpha/beta/rc tags


# == General configuration =========================================================================
extensions = [  # Sphinx extension module names, which can be named 'sphinx.ext.*' or custom ones:
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.extlinks',
    'sphinx.ext.githubpages',
    'sphinx.ext.intersphinx',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.linkcode',
    'sphinx.ext.napoleon',
    # 'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx_copybutton',
    'sphinx_new_tab_link',
    'sphinx_toggleprompt',
    # "IPython.sphinxext.ipython_console_highlighting",
    # "IPython.sphinxext.ipython_directive",
]


def linkcode_resolve(domain, info):
    """
    Determine the URL corresponding to Python object.

    (Adapted from https://github.com/pandas-dev/pandas/blob/main/doc/source/conf.py)
    """

    import inspect
    import warnings
    import pyhelpers

    if domain != 'py' or not info['module']:
        return None

    module_name, full_name = info['module'], info['fullname']

    sub_module_name = sys.modules.get(module_name)
    if sub_module_name is None:
        return None

    obj = sub_module_name
    for part in full_name.split('.'):
        try:
            with warnings.catch_warnings():
                # Accessing deprecated objects will generate noisy warnings
                warnings.simplefilter('ignore', FutureWarning)
                obj = getattr(obj, part)
        except AttributeError:
            return None

    try:
        fn = inspect.getsourcefile(inspect.unwrap(obj))
    except TypeError:
        try:  # property
            fn = inspect.getsourcefile(inspect.unwrap(obj.fget))
        except (AttributeError, TypeError):
            fn = None
    if not fn:
        return None

    source = [0]
    try:
        source, line_no = inspect.getsourcelines(obj)
    except TypeError:
        try:  # property
            source, line_no = inspect.getsourcelines(obj.fget)
        except (AttributeError, TypeError):
            line_no = None
    except OSError:
        line_no = None

    if line_no:
        line_spec = f"#L{line_no}-L{line_no + len(source) - 1}"
    else:
        line_spec = ""

    # fn = os.path.relpath(fn, start=os.path.abspath(".."))
    fn = os.path.relpath(fn, start=os.path.dirname(pyhelpers.__file__))

    # f"https://github.com/mikeqfu/pyhelpers/blob/{pyhelpers.__version__}/pyhelpers/{fn}{line_spec}"
    url = f"https://github.com/mikeqfu/pyhelpers/blob/master/pyhelpers/{fn}{line_spec}"

    return url


# noinspection PyUnusedLocal
def remove_module_docstring(app, what, name, obj, options, lines):
    if what == "module" and name == "pyhelpers.dbms.utils":
        del lines[:]


def setup(app):
    app.connect("autodoc-process-docstring", remove_module_docstring)


# Enable to reference numbered figures:
numfig = True
numfig_secnum_depth = 0
numfig_format = {'figure': 'Figure %s', 'table': 'Table %s'}
numfig_format_caption = {'figure': 'Figure %s:', 'table': 'Table %s:'}

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

# Content inserted into the main body of an `autoclass` directive:
autoclass_content = 'both'  # ['class', 'init']

# Automatically documented members are sorted by source order ('bysource'):
autodoc_member_order = 'bysource'


# == Options for HTML and HTMLHelp output ==========================================================
html_theme = 'furo'  # The theme to use for HTML & HTML Help pages  # 'sphinx_rtd_theme'
html_title = __project__

# Hide/show source link:
html_copy_source = False
html_show_sourcelink = False

# The name of the Pygments (syntax highlighting) style to use:
pygments_style = 'sphinx'  # or 'default'

# Paths containing custom static files (e.g. style sheets), relative to this directory:
html_static_path = ['_static']

# Add custom CSS:
html_css_files = [
    'custom.css',
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/brands.min.css",
]

html_theme_options = {
    "navigation_with_keys": True,
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/mikeqfu/pyhelpers",
            "class": "fa-brands fa-github",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/pyhelpers/",
            "class": "fa-brands fa-python",
        },
        {
            "name": "LinkedIn",
            "url": "https://www.linkedin.com/in/qianfu",
            "class": "fa-brands fa-linkedin-in",
        },
        {
            "name": "Email",
            "url": "mailto:q.fu@bham.ac.uk",
            "class": "fa-regular fa-envelope",
        },
        # {
        #     "name": "Cite",
        #     "url": "https://zenodo.org/doi/10.5281/zenodo.4017438",
        #     "class": "fa-solid fa-quote-right",
        # },
        # {
        #     "name": "X",
        #     "url": "https://x.com/mikeqfu",
        #     "class": "fa-brands fa-x-twitter fa-solid",
        # },
    ],
}

# Add custom JavaScript:
html_js_files = ['custom.js']

# Configuration for sphinx-toggleprompt
toggleprompt_offset_right = -30

# Output file base name for HTML help builder:
htmlhelp_basename = __project__ + 'doc'  # Defaults to 'pydoc'

# Do not execute cells
jupyter_execute_notebooks = "off"

# Allow myst admonition style
myst_admonition_enable = True

# Copy code only:
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True


# == Options for LaTeX output ======================================================================
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
    ('latexindex',  # source start file
     f'{__pkgname__}.tex',  # target name
     f'{__project__} Documentation',  # title
     __author__,  # author
     'manual',  # document class ['howto', 'manual', or own class]
     1  # toctree only
     ),
]

affil_dept, affil_univ = __affil__.split(', ')

# Custom title page:
latex_maketitle = r'''
    \newgeometry{top=1.1in,bottom=1.1in,right=1.0in,left=1.0in}
    \pagenumbering{roman}
    \makeatletter
    \hypertarget{titlepage}{}
    \begin{titlepage}
        \flushright

        \vspace*{22mm}
        \textbf{\Huge {{%s}}}
        
        \vspace{5mm}
        \textit{\Large {{%s}}} \par
        \vspace{5mm}
        \LARGE \textbf{\textit{{Release %s}}} \par

        \vspace{45mm}
        \LARGE \textbf{{%s}} \par
        \Large \textit{{%s}} \par
        \Large \textit{{%s}} \par

        \vspace{50mm}
        \Large {{First release:}} \large \textbf{{%s}} \par
        \Large {{Last updated:}} \large \textbf{{\MonthYearFormat\today}} \par
        
        \vspace{20mm}
        \large \textcopyright \space Copyright %s \par

    \end{titlepage}
    \restoregeometry
    \bookmark[dest=titlepage]{Title}
    \makeatother

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
    \renewcommand*{\addvspace}[1]{}
    \listoffigures
    \bookmark[dest=lofpage]{List of Figures}
    \makeatother

    \clearpage
    \pagenumbering{arabic}
    ''' % (project,
           __desc__,
           __version__,
           __author__,
           affil_dept,
           affil_univ,
           __first_release__,
           __copyright__)

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
    \newunicodechar{≈}{\ensuremath{\approx}}
    \newunicodechar{≥}{\ensuremath{\geq}}
    \IfFileExists{zlmtt.sty}
                 {\usepackage[light,scaled=1.05]{zlmtt}}
                 {\renewcommand{\ttdefault}{lmtt}}
    \let\oldlongtable\longtable
    \let\endoldlongtable\endlongtable
    \renewenvironment{longtable}
                     {\rowcolors{1}{anti-flashwhite}{white}\oldlongtable}
                     {\endoldlongtable}
    \usepackage[open,openlevel=1]{bookmark}
    \bookmarksetup{numbered}
    \addto\captionsenglish{\renewcommand{\contentsname}{Table of Contents}}
    \usepackage{xcolor}
    \usepackage{newunicodechar}
    \definecolor{ansiGreen}{RGB}{34, 139, 34}
    \newunicodechar{█}{\textcolor{ansiGreen}{\rule{0.6em}{0.6em}}}
    '''

# LaTeX customisation:
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '11pt',
    'pxunit': '0.25bp',

    'fontpkg': '\\usepackage{amsmath,amsfonts,amssymb,amsthm}',
    'fncychap': '\\usepackage{fncychap}',  # '\\usepackage[Bjarne]{fncychap}'

    'preamble': latex_preamble,

    'figure_align': 'H',  # Latex figure (float) alignment; optional: 'htbp'
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
