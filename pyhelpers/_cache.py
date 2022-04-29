"""
Cache.
"""

import copy
import importlib
import importlib.util
import json
import os
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


def _check_rel_pathname(pathname):
    try:
        pathname_ = os.path.relpath(pathname)
    except ValueError:
        pathname_ = copy.copy(pathname)

    return pathname_


# An example DataFrame
def example_dataframe(osgb36=False):
    """
    Create an example dataframe.

    :param osgb36: whether to use data based on OSGB36 National Grid, defaults to ``True``
    :type osgb36: bool
    :return: an example dataframe
    :rtype: pandas.DataFrame

    **Tests**::

        >>> from pyhelpers._cache import example_dataframe

        >>> example_dataframe()
                          Easting       Northing
        City
        London      530039.558844  180371.680166
        Birmingham  406705.887014  286868.166642
        Manchester  383830.039036  398113.055831
        Leeds       430147.447354  433553.327117

        >>> example_dataframe(osgb36=False)
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
    """

    pd_ = _check_dependency(name='pandas')

    if osgb36:
        _columns = ['Easting', 'Northing']
        _example_df = [
            (530039.5588445, 180371.6801655),  # London
            (406705.8870136, 286868.1666422),  # Birmingham
            (383830.0390357, 398113.0558309),  # Manchester
            (430147.4473539, 433553.3271173),  # Leeds
        ]
    else:
        _columns = ['Longitude', 'Latitude']
        _example_df = [
            (-0.1276474, 51.5073219),  # London
            (-1.9026911, 52.4796992),  # Birmingham
            (-2.2451148, 53.4794892),  # Manchester
            (-1.5437941, 53.7974185),  # Leeds
        ]

    _index = ['London', 'Birmingham', 'Manchester', 'Leeds']

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
