"""
Cache.
"""

import importlib
import importlib.util
import json
import sys

import pkg_resources

# import name: (package/module name, install name)
_OPTIONAL_DEPENDENCY = {
    "fuzzywuzzy": ("FuzzyWuzzy", "fuzzywuzzy"),
    "Levenshtein": ("python-Levenshtein", "python-Levenshtein"),
    "tqdm": ("tqdm", "tqdm"),
    "matplotlib": ("Matplotlib", "matplotlib"),
    "nltk": ("NLTK", "nltk"),
    "joblib": ("Joblib", "joblib"),
    "openpyxl": ("openpyxl", "openpyxl"),
    "xlsxwriter": ("XlsxWriter", "xlsxwriter"),
    "xlrd": ("xlrd", "xlrd"),
    "pyxlsb": ("pyxlsb", "pyxlsb"),
    "pyarrow": ("PyArrow", "pyarrow"),
    "orjson": ("orjson", "orjson"),
    "rapidjson": ("python-rapidjson", "python-rapidjson"),
    "osgeo.gdal": ("GDAL", "gdal"),
    "pyproj": ("pyproj", "pyproj"),
    "pypandoc": ("Pypandoc", "pypandoc"),
    "pdfkit": ("pdfkit", "pdfkit"),
    "psycopg2": ("psycopg2", "psycopg2"),
    "pyodbc": ("pyodbc", "pyodbc"),
    "ujson": ("UltraJSON", "ujson"),
}


def _check_dependency(name):
    """
    Import optional dependency package.

    :param name: name of a package as an optional dependency of pyhelpers
    :type name: str

    **Examples**::

        _check_dependency(dependency='psycopg2')

        _check_dependency(dependency='pyodbc')
    """

    import_name = name.replace('-', '_')

    if import_name in sys.modules:  # The optional dependency has already been imported
        return sys.modules.get(import_name)

    # elif (package_spec := importlib.util.find_spec(import_name)) is not None:
    elif importlib.util.find_spec(import_name) is not None:
        # import_package = importlib.util.module_from_spec(package_spec)
        # sys.modules[import_name] = import_package
        # package_spec.loader.exec_module(import_package)
        return importlib.import_module(import_name)

    else:
        if import_name in _OPTIONAL_DEPENDENCY:
            package_name, install_name = _OPTIONAL_DEPENDENCY[import_name]
        else:
            package_name, install_name = name, name.split('.')[0]

        raise ModuleNotFoundError(
            f"The specified dependency '{package_name}' is not available. "
            f"Use pip or conda to install it, e.g. 'pip install {install_name}'.")


# An example DataFrame
def example_dataframe(osgb36=True):
    """
    Create an example dataframe.

    :param osgb36: whether to use data based on OSGB36 National Grid, defaults to ``True``
    :type osgb36: bool
    :return: an example dataframe
    :rtype: pandas.DataFrame
    """

    pd_ = _check_dependency(name='pandas')

    if osgb36:
        _example_df = [
            (530034, 180381),  # London
            (406689, 286822),  # Birmingham
            (383819, 398052),  # Manchester
            (582044, 152953),  # Leeds
        ]
    else:
        _example_df = [
            (-0.12772401, 51.50740693),  # London
            (-1.90294064, 52.47928436),  # Birmingham
            (-2.24527795, 53.47894006),  # Manchester
            (0.60693267, 51.24669501),  # Leeds
        ]

    _index = ['London', 'Birmingham', 'Manchester', 'Leeds']
    _columns = ['Easting', 'Northing']

    _example_dataframe = pd_.DataFrame(data=_example_df, index=_index, columns=_columns)

    _example_dataframe.index.name = 'City'

    return _example_dataframe


# == For ops.py ====================================================================================

def _load_user_agent_strings():
    """
    Load (fake) user agent strings.

    :return: (fake) user agent strings
    :rtype: dict
    """

    path_to_json = pkg_resources.resource_filename(__name__, "data/user-agent-strings.json")

    with open(path_to_json, mode='r') as f:
        user_agent_strings = json.loads(f.read())

    return user_agent_strings


_USER_AGENT_STRINGS = _load_user_agent_strings()


# == For text.py ===================================================================================

def _english_written_numbers():
    metadata = dict()

    # Singles
    units = [
        'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
        'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
        'sixteen', 'seventeen', 'eighteen', 'nineteen', 'a',
    ]

    # Tens
    tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']

    # Larger scales
    scales = ['hundred', 'thousand', 'million', 'billion', 'trillion']

    # divisors
    metadata['and'] = (1, 0)

    # perform our loops and start the swap
    for i, word in enumerate(units):
        if word == 'a':
            metadata[word] = (1, 1)
        else:
            metadata[word] = (1, i)
    for i, word in enumerate(tens):
        metadata[word] = (1, i * 10)
    for i, word in enumerate(scales):
        metadata[word] = (10 ** (i * 3 or 2), 0)

    return metadata


_ENGLISH_WRITTEN_NUMBERS = _english_written_numbers()
