import importlib
import json

import pkg_resources


# An example DataFrame
def example_dataframe(osgb36=True):
    """
    Create an example dataframe.

    :param osgb36: whether to use data based on OSGB36 National Grid, defaults to ``True``
    :type osgb36: bool
    :return: an example dataframe
    :rtype: pandas.DataFrame
    """
    import pandas as pd

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

    _example_dataframe = pd.DataFrame(data=_example_df, index=_index, columns=_columns)

    return _example_dataframe


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
}


def _import_optional_dependency(optional_dependency: str):
    # if optional_dependency not in sys.modules:
    try:
        importlib.import_module(optional_dependency)

    except (ImportError, ModuleNotFoundError):
        import_package_name = optional_dependency.split(".")[0]
        if import_package_name == 'osgeo':
            import_package_name = 'osgeo.gdal'

        package_name, install_name = _OPTIONAL_DEPENDENCY[import_package_name]
        msg = f"Missing optional dependency \"{package_name}\". " \
              f"Use pip or conda to install it, e.g. 'pip install {install_name}'."

        print(msg)


# == ops.py ======================================================================================

def _load_user_agent_strings():
    try:
        path_to_json = pkg_resources.resource_filename(__name__, "data/user-agent-strings.json")
        json_in = open(path_to_json, mode='r')
    except FileNotFoundError:
        json_in = open("pyhelpers/data/user-agent-strings.json", mode='r')

    user_agent_strings = json.loads(json_in.read())

    return user_agent_strings


_USER_AGENT_STRINGS = _load_user_agent_strings()


# == text.py =====================================================================================

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
