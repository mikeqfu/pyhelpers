"""
Saving and loading file-like objects.
"""

import copy
import csv
import json
import operator
import os
import pathlib
import pickle
import subprocess
import warnings
import zipfile

import pandas as pd

from .ops import confirmed, find_executable, is_url


def _check_path_to_file(path_to_file, verbose=False, verbose_end=" ... ", ret_info=False):
    """
    Get information about the path of a file.

    :param path_to_file: path where a file is saved
    :type path_to_file: str or pathlib.Path
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param verbose_end: a string passed to ``end`` for ``print``, defaults to ``" ... "``
    :type verbose_end: str
    :param ret_info: whether to return the file path information, defaults to ``False``
    :type ret_info: bool
    :return: a relative path and a filename (if ``ret_info=True``)
    :rtype: tuple

    **Test**::

        >>> from pyhelpers.dir import cd
        >>> from pyhelpers.store import _check_path_to_file

        >>> file_path = cd()
        >>> try:
        ...     _check_path_to_file(file_path, verbose=True)
        ... except AssertionError as e:
        ...     print(e)
        The input for `path_to_file` may not be a file path.

        >>> file_path = cd("test_store.py")
        >>> _check_path_to_file(file_path, verbose=True)
        >>> print("Passed.")
        Saving "test_store.py" ... Pass.

        >>> file_path = cd("tests", "test_store.py")
        >>> _check_path_to_file(file_path, verbose=True)
        >>> print("Passed.")
        Updating "test_store.py" at "tests\\" ... Passed.
    """

    abs_path_to_file = pathlib.Path(path_to_file).absolute()
    assert not abs_path_to_file.is_dir(), "The input for `path_to_file` may not be a file path."

    filename = pathlib.Path(abs_path_to_file).name if abs_path_to_file.suffix else ""

    try:
        rel_path = pathlib.Path(os.path.relpath(abs_path_to_file.parent))

        if rel_path == rel_path.parent:
            rel_path = abs_path_to_file.parent
            msg_fmt = "{} \"{}\""
        else:
            msg_fmt = "{} \"{}\" {} \"{}\\\""
            # The specified path exists?
            os.makedirs(abs_path_to_file.parent, exist_ok=True)

    except ValueError:
        if verbose == 2:
            warn_msg = "Warning: \"{}\" is outside the current working directory".format(
                str(abs_path_to_file.parent))
            print(warn_msg)

        rel_path = abs_path_to_file.parent
        msg_fmt = "{} \"{}\""

    if verbose:
        if os.path.isfile(abs_path_to_file):
            status_msg, prep = "Updating", "at"
        else:
            status_msg, prep = "Saving", "to"

        if verbose_end:
            verbose_end_ = verbose_end
        else:
            verbose_end_ = "\n"

        if rel_path == rel_path.parent:
            print(msg_fmt.format(status_msg, filename), end=verbose_end_)
        else:
            print(msg_fmt.format(status_msg, filename, prep, rel_path), end=verbose_end_)

    if ret_info:
        return rel_path, filename


""" == Save data ============================================================================= """


# Pickle files

def save_pickle(pickle_data, path_to_pickle, verbose=False, **kwargs):
    """
    Save data to a `Pickle <https://docs.python.org/3/library/pickle.html>`_ file.

    :param pickle_data: data that could be dumped by the built-in module `pickle.dump`_
    :type pickle_data: any
    :param path_to_pickle: path where a pickle file is saved
    :type path_to_pickle: str or os.PathLike[str]
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pickle.dump`_

    .. _`pickle.dump`: https://docs.python.org/3/library/pickle.html#pickle.dump

    **Example**::

        >>> from pyhelpers.store import save_pickle
        >>> from pyhelpers.dir import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> pickle_dat = 1

        >>> pickle_pathname = cd("tests\\data", "dat.pickle")
        >>> save_pickle(pickle_dat, pickle_pathname, verbose=True)
        Saving "dat.pickle" to "tests\\data\\" ... Done.

        >>> # Get an example dataframe
        >>> pickle_dat = example_dataframe()
        >>> pickle_dat
                    Easting  Northing
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953

        >>> save_pickle(pickle_dat, pickle_pathname, verbose=True)
        Updating "dat.pickle" at "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.load_pickle`.
    """

    _check_path_to_file(path_to_pickle, verbose=verbose, ret_info=False)

    try:
        pickle_out = open(path_to_pickle, mode='wb')
        pickle.dump(pickle_data, pickle_out, **kwargs)
        pickle_out.close()
        print("Done.") if verbose else ""

    except Exception as e:
        print("Failed. {}.".format(e))


# Spreadsheets

def save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index=False, engine=None, delimiter=',',
                     verbose=False, **kwargs):
    """
    Save data to a `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_ or
    an `Microsoft Excel <https://en.wikipedia.org/wiki/Microsoft_Excel>`_ file.

    The file extension can be `".txt"`, `".csv"`, `".xlsx"` or `".xls"`;
    engines can include: `xlsxwriter`_ (for .xlsx) and `openpyxl`_ (for .xlsx/.xlsm).

    :param spreadsheet_data: data that could be saved as a spreadsheet
        (e.g. with a file extension ".xlsx" or ".csv")
    :type spreadsheet_data: pandas.DataFrame
    :param path_to_spreadsheet: path where a spreadsheet is saved
    :type path_to_spreadsheet: str or os.PathLike[str] or None
    :param index: whether to include the index as a column, defaults to ``False``
    :type index: bool
    :param engine: options include ``'openpyxl'`` for latest Excel file formats,
        ``'xlrd'`` for .xls ``'odf'`` for OpenDocument file formats (.odf, .ods, .odt), and
        ``'pyxlsb'`` for Binary Excel files; defaults to ``None``
    :type engine: str or None
    :param delimiter: separator for saving a `".xlsx"` (or `".xls"`) file as a `".csv"` file,
        defaults to ``','``
    :type delimiter: str
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.DataFrame.to_excel`_ or `pandas.DataFrame.to_csv`_

    .. _`xlsxwriter`: https://pypi.org/project/XlsxWriter/
    .. _`openpyxl`: https://pypi.org/project/openpyxl/
    .. _`pandas.DataFrame.to_excel`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html
    .. _`pandas.DataFrame.to_csv`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html

    **Examples**::

        >>> from pyhelpers.store import save_spreadsheet
        >>> from pyhelpers.dir import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> # Get an example dataframe
        >>> spreadsheet_dat = example_dataframe()
        >>> spreadsheet_dat
                    Easting  Northing
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953

        >>> spreadsheet_pathname = cd("tests\\data", "dat.csv")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)
        Saving "dat.csv" to "tests\\data\\" ... Done.

        >>> spreadsheet_pathname = cd("tests\\data", "dat.xls")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, verbose=True)
        Saving "dat.xls" to "tests\\data\\" ... Done.

        >>> spreadsheet_pathname = cd("tests\\data", "dat.xlsx")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, verbose=True)
        Saving "dat.xlsx" to "tests\\data\\" ... Done.
    """

    _, spreadsheet_filename = _check_path_to_file(
        path_to_file=path_to_spreadsheet, verbose=verbose, ret_info=True)

    try:  # to save the data
        if spreadsheet_filename.endswith(".xlsx"):  # a .xlsx file
            spreadsheet_data.to_excel(
                excel_writer=path_to_spreadsheet, index=index, engine=engine, **kwargs)

        elif spreadsheet_filename.endswith(".xls"):  # a .xls file
            if engine is None or engine == 'xlwt':
                engine = 'openpyxl'
            spreadsheet_data.to_excel(
                excel_writer=path_to_spreadsheet, index=index, engine=engine, **kwargs)

        elif spreadsheet_filename.endswith((".csv", ".txt")):  # a .csv file
            spreadsheet_data.to_csv(
                path_or_buf=path_to_spreadsheet, index=index, sep=delimiter, **kwargs)

        else:
            raise AssertionError('File extension must be ".txt", ".csv", ".xlsx" or ".xls"')

        print("Done.") if verbose else ""

    except Exception as e:
        print("Failed. {}.".format(e.args[0])) if verbose else ""


def save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, mode='w',
                               index=False, confirmation_required=True, verbose=False, **kwargs):
    """
    Save data to a multi-sheet `Microsoft Excel`_ file.

    The file extension can be `".xlsx"` or `".xls"`.

    :param spreadsheets_data: a sequence of pandas.DataFrame
    :type spreadsheets_data: list or tuple or iterable
    :param sheet_names: all sheet names of an Excel workbook
    :type sheet_names: list or tuple or iterable
    :param path_to_spreadsheet: path where a spreadsheet is saved
    :type path_to_spreadsheet: str or os.PathLike[str]
    :param mode: mode to write to an Excel file; ``'w'`` (default) for 'write' and ``'a'`` for 'append'
    :type mode: str
    :param index: whether to include the index as a column, defaults to ``False``
    :type index: bool
    :param confirmation_required: whether to prompt a message for confirmation to proceed,
        defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.ExcelWriter`_

    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _pandas.ExcelWriter:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.ExcelWriter.html

    **Examples**::

        >>> from pyhelpers.store import save_multiple_spreadsheets
        >>> from pyhelpers.dir import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> # Get an example dataframe
        >>> dat1 = example_dataframe()
        >>> dat1
                    Easting  Northing
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953

        >>> dat2 = dat1.T
        >>> dat2
                  London  Birmingham  Manchester   Leeds
        Easting   530034      406689      383819  582044
        Northing  180381      286822      398052  152953

        >>> dat = [dat1, dat2]
        >>> dat_sheets = ['TestSheet1', 'TestSheet2']
        >>> dat_pathname = cd("tests\\data", "dat.xlsx")

        >>> save_multiple_spreadsheets(dat, dat_sheets, dat_pathname, index=True, verbose=True)
        Saving "dat.xlsx" to "tests\\data\\" ...
            'TestSheet1' ... Done.
            'TestSheet2' ... Done.

        >>> save_multiple_spreadsheets(dat, dat_sheets, dat_pathname, mode='a', index=True,
        ...                            verbose=True)
        Updating "dat.xlsx" at "tests\\data\\" ...
            'TestSheet1' ... This sheet already exists; [pass]|new|replace: new
                saved as 'TestSheet11' ... Done.
            'TestSheet2' ... This sheet already exists; [pass]|new|replace: new
                saved as 'TestSheet21' ... Done.

        >>> save_multiple_spreadsheets(dat, dat_sheets, dat_pathname, mode='a', index=True,
        ...                            confirmation_required=False, verbose=True)
        Updating "dat.xlsx" at "tests\\dataz\" ...
            'TestSheet1' ... Failed. Sheet 'TestSheet1' already exists and if_sheet_exists is se ...
            'TestSheet2' ... Failed. Sheet 'TestSheet2' already exists and if_sheet_exists is se ...

        >>> save_multiple_spreadsheets(dat, dat_sheets, dat_pathname, mode='a', index=True,
        ...                            confirmation_required=False, verbose=True,
        ...                            if_sheet_exists='replace')
        Updating "dat.xlsx" at "tests\\data\\" ...
            'TestSheet1' ... Done.
            'TestSheet2' ... Done.
    """

    assert path_to_spreadsheet.endswith(".xlsx") or path_to_spreadsheet.endswith(".xls")

    _check_path_to_file(path_to_spreadsheet, verbose=verbose, ret_info=False)

    if os.path.isfile(path_to_spreadsheet) and mode == 'a':
        excel_file = pd.ExcelFile(path_or_buffer=path_to_spreadsheet)
        cur_sheet_names = excel_file.sheet_names
        excel_file.close()
    else:
        cur_sheet_names = []

    engine = 'openpyxl' if mode == 'a' else None
    excel_writer = pd.ExcelWriter(path=path_to_spreadsheet, engine=engine, mode=mode, **kwargs)

    def _write_excel():
        try:
            sheet_data.to_excel(excel_writer, sheet_name=sheet_name, index=index)

            try:
                sheet_name_ = excel_writer.sheets[sheet_name].get_name()
            except AttributeError:
                sheet_name_ = excel_writer.sheets[sheet_name].title

            if sheet_name_ in sheet_names:
                msg_ = "Done."
            else:
                msg_ = "saved as '{}' ... Done. ".format(sheet_name_)

            print(msg_) if verbose else ""

        except Exception as e:
            print("Failed. {}".format(e))

    print("") if verbose else ""
    for sheet_data, sheet_name in zip(spreadsheets_data, sheet_names):
        # sheet_data, sheet_name = spreadsheets_data[0], sheet_names[0]
        print("\t'{}'".format(sheet_name), end=" ... ") if verbose else ""

        if (sheet_name in cur_sheet_names) and confirmation_required:
            if_sheet_exists = input(f"This sheet already exists; [pass]|new|replace: ")
            if if_sheet_exists != 'pass':
                excel_writer.if_sheet_exists = if_sheet_exists
                print("\t\t", end="")
                # suffix_msg = "(Note that a suffix has been added to the sheet name.)"
                _write_excel()
        else:
            _write_excel()

    excel_writer.close()


# JSON files

def save_json(json_data, path_to_json, method=None, verbose=False, **kwargs):
    """
    Save data to a `JSON <https://www.json.org/json-en.html>`_ file.

    :param json_data: data that could be dumped by as a JSON file
    :type json_data: any json data
    :param path_to_json: path where a json file is saved
    :type path_to_json: str or os.PathLike[str]
    :param method: an open-source module used for JSON serialization, options include
        ``None`` (default, for the built-in `json module`_), ``'orjson'`` (for `orjson`_) and
        ``'rapidjson'`` (for `python-rapidjson`_)
    :type method: str or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `json.dump`_ (if ``method=None``),
        `orjson.dumps`_ (if ``method='orjson'``) or `rapidjson.dump`_ (if ``method='rapidjson'``)

    .. _`json module`: https://docs.python.org/3/library/json.html
    .. _`orjson`: https://pypi.org/project/orjson/
    .. _`python-rapidjson`: https://pypi.org/project/python-rapidjson
    .. _`json.dump`: https://docs.python.org/3/library/json.html#json.dump
    .. _`orjson.dumps`: https://github.com/ijl/orjson#serialize
    .. _`rapidjson.dump`: https://python-rapidjson.readthedocs.io/en/latest/dump.html

    **Examples**::

        >>> from pyhelpers.store import save_json
        >>> from pyhelpers.dir import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> json_pathname = cd("tests\\data", "dat.json")

        >>> json_dat = {'a': 1, 'b': 2, 'c': 3, 'd': ['a', 'b', 'c']}
        >>> save_json(json_dat, json_pathname, indent=4, verbose=True)
        Saving "dat.json" to "tests\\data\\" ... Done.

        >>> # Get an example dataframe
        >>> example_df = example_dataframe()
        >>> example_df
                    Easting  Northing
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953

        >>> # Convert the dataframe to JSON format
        >>> json_dat = json.loads(example_df.to_json(orient='index'))
        >>> json_dat
        {'London': {'Easting': 530034, 'Northing': 180381},
         'Birmingham': {'Easting': 406689, 'Northing': 286822},
         'Manchester': {'Easting': 383819, 'Northing': 398052},
         'Leeds': {'Easting': 582044, 'Northing': 152953}}

        >>> save_json(json_dat, json_pathname, indent=4, verbose=True)
        Updating "dat.json" at "tests\\data\\" ... Done.

        >>> save_json(json_dat, json_pathname, method='orjson', verbose=True)
        Updating "dat.json" at "tests\\data\\" ... Done.

        >>> save_json(json_dat, json_pathname, method='rapidjson', indent=4, verbose=True)
        Updating "dat.json" at "tests\\data\\" ... Done.
    """

    _check_path_to_file(path_to_json, verbose=verbose, ret_info=False)

    try:
        if method == 'orjson':
            import orjson

            json_out = open(path_to_json, mode='wb')
            json_dumps = orjson.dumps(json_data, **kwargs)
            json_out.write(json_dumps)

        else:
            json_out = open(path_to_json, mode='w')

            if method == 'rapidjson':
                import rapidjson

                rapidjson.dump(json_data, json_out, **kwargs)

            else:
                json.dump(json_data, json_out, **kwargs)

        json_out.close()
        print("Done.") if verbose else ""

    except Exception as e:
        print("Failed. {}.".format(e))


# Joblib

def save_joblib(joblib_data, path_to_joblib, verbose=False, **kwargs):
    """
    Save data to a `Joblib <https://pypi.org/project/joblib/>`_ file.

    :param joblib_data: data that could be dumped by `joblib.dump`_
    :type joblib_data: any
    :param path_to_joblib: path where a pickle file is saved
    :type path_to_joblib: str or os.PathLike[str]
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `joblib.dump`_

    .. _`joblib.dump`: https://joblib.readthedocs.io/en/latest/generated/joblib.dump.html

    **Example**::

        >>> from pyhelpers.store import save_joblib
        >>> from pyhelpers.dir import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> import numpy

        >>> joblib_pathname = cd("tests\\data", "dat.joblib")

        >>> # Example 1:
        >>> joblib_dat = example_dataframe().to_numpy(dtype=int)
        >>> joblib_dat
        array([[530034, 180381],
               [406689, 286822],
               [383819, 398052],
               [582044, 152953]])

        >>> save_joblib(joblib_dat, joblib_pathname, verbose=True)
        Saving "dat.joblib" to "tests\\data\\" ... Done.

        >>> # Example 2:
        >>> numpy.random.seed(0)
        >>> joblib_dat = numpy.random.rand(100, 100)
        >>> joblib_dat
        array([[0.5488135 , 0.71518937, 0.60276338, ..., 0.02010755, 0.82894003,
                0.00469548],
               [0.67781654, 0.27000797, 0.73519402, ..., 0.25435648, 0.05802916,
                0.43441663],
               [0.31179588, 0.69634349, 0.37775184, ..., 0.86219152, 0.97291949,
                0.96083466],
               ...,
               [0.89111234, 0.26867428, 0.84028499, ..., 0.5736796 , 0.73729114,
                0.22519844],
               [0.26969792, 0.73882539, 0.80714479, ..., 0.94836806, 0.88130699,
                0.1419334 ],
               [0.88498232, 0.19701397, 0.56861333, ..., 0.75842952, 0.02378743,
                0.81357508]])

        >>> save_joblib(joblib_dat, joblib_pathname, verbose=True)
        Saving "dat.joblib" to "tests\\data\\" ... Done.
    """

    _check_path_to_file(path_to_joblib, verbose=verbose, ret_info=False)

    try:
        import joblib

        joblib.dump(value=joblib_data, filename=path_to_joblib, **kwargs)
        print("Done.") if verbose else ""

    except Exception as e:
        print("Failed. {}.".format(e))


# Feather files

def save_feather(feather_data, path_to_feather, verbose=False, **kwargs):
    """
    Save a dataframe to a `Feather <https://arrow.apache.org/docs/python/feather.html>`_ file.

    :param feather_data: a dataframe to be saved as a feather-formatted file
    :type feather_data: pandas.DataFrame
    :param path_to_feather: path where a feather file is saved
    :type path_to_feather: str or os.PathLike[str]
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.DataFrame.to_feather`_

    .. _`pandas.DataFrame.to_feather`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_feather.html

    **Example**::

        >>> from pyhelpers.store import save_feather
        >>> from pyhelpers.dir import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> # Get an example dataframe
        >>> feather_dat = example_dataframe()
        >>> feather_dat
                    Easting  Northing
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953

        >>> feather_pathname = cd("tests\\data", "dat.feather")

        >>> save_feather(feather_dat.reset_index(), feather_pathname, verbose=True)
        Saving "dat.feather" to "tests\\data\\" ... Done.

        >>> save_feather(feather_dat, feather_pathname, verbose=True)
        Updating "dat.feather" at "tests\\data\\" ... Done.
    """

    assert isinstance(feather_data, pd.DataFrame)

    _check_path_to_file(path_to_feather, verbose=verbose, ret_info=False)

    try:
        if list(feather_data.index) != range(len(feather_data)):
            feather_data.reset_index().to_feather(path_to_feather, **kwargs)
        else:
            feather_data.to_feather(path_to_feather, **kwargs)

        print("Done.") if verbose else ""

    except Exception as e:
        print("Failed. {}.".format(e)) if verbose else ""


# Images

def save_svg_as_emf(path_to_svg, path_to_emf, verbose=False, inkscape_exe=None, **kwargs):
    """
    Save a `SVG <https://en.wikipedia.org/wiki/Scalable_Vector_Graphics>`_ file (.svg) as
    a `EMF <https://en.wikipedia.org/wiki/Windows_Metafile#EMF>`_ file (.emf).

    :param path_to_svg: path where a .svg file is saved
    :type path_to_svg: str
    :param path_to_emf: path where a .emf file is saved
    :type path_to_emf: str
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param inkscape_exe: absolute path to 'inkscape.exe', defaults to ``None``;
        on Windows, the default installation path
        "*C:\\\\Program Files\\\\Inkscape\\\\bin\\\\inkscape.exe*"
        (or "*C:\\\\Program Files\\\\Inkscape\\\\inkscape.exe*") is used when ``inkscape_exe=None``
    :type inkscape_exe: str or None
    :param kwargs: [optional] parameters of `subprocess.call`_

    .. _`subprocess.call`:
        https://docs.python.org/3/library/subprocess.html#subprocess.call

    **Examples**::

        >>> from pyhelpers.store import save_svg_as_emf
        >>> import matplotlib.pyplot as plt
        >>> from pyhelpers.dir import cd

        >>> x, y = (1, 1), (2, 2)

        >>> plt.figure()
        >>> plt.plot([x[0], y[0]], [x[1], y[1]])
        >>> plt.show()

    The above exmaple is illustrated in :numref:`fig-2`:

    .. figure:: ../_images/fig.*
        :name: fig-2
        :align: center
        :width: 76%

        An example figure created for the function
        :py:func:`save_svg_as_emf()<pyhelpers.store.save_svg_as_emf>`.

    .. code-block:: python

        >>> img_dir = cd("tests\\images")

        >>> svg_file_pathname = cd(img_dir, "fig.svg")
        >>> plt.savefig(svg_file_pathname)  # Save the figure as a .svg file

        >>> emf_file_pathname = cd(img_dir, "fig.emf")
        >>> save_svg_as_emf(svg_file_pathname, emf_file_pathname, verbose=True)
        Saving the .svg file as "tests\\images\\fig.emf" ... Done.

        >>> plt.close()
    """

    abs_svg_path, abs_emf_path = map(pathlib.Path, (path_to_svg, path_to_emf))
    assert abs_svg_path.suffix.lower() == ".svg"

    inkscape_exe_ = copy.copy(inkscape_exe)
    if inkscape_exe_ is None:
        exe_pathnames = [
            "C:\\Program Files\\Inkscape\\inkscape.exe",
            "C:\\Program Files\\Inkscape\\bin\\inkscape.exe",
        ]
        inkscape_exe_ = find_executable(app_name="inkscape.exe", possibilities=exe_pathnames)

    if os.path.isfile(inkscape_exe_):
        if verbose:
            if abs_emf_path.exists():
                msg = f"Updating \"{abs_emf_path.name}\" at \"{os.path.relpath(abs_emf_path.parent)}\\\""
            else:
                msg = f"Saving the {abs_svg_path.suffix} file as \"{os.path.relpath(abs_emf_path)}\""
            print(msg, end=" ... ")

        try:
            abs_emf_path.parent.mkdir(exist_ok=True)

            subprocess.call([inkscape_exe_, '-z', path_to_svg, '-M', path_to_emf], **kwargs)

            if verbose:
                print("Done.")

        except Exception as e:
            print("Failed. {}".format(e))

    else:
        if verbose:
            print("\"Inkscape\" (https://inkscape.org) is required to convert a SVG file to an EMF file;"
                  " however, it is not found on this device.\nInstall it and then try again.")


def save_fig(path_to_fig_file, dpi=None, verbose=False, conv_svg_to_emf=False, **kwargs):
    """
    Save a figure object to a file of a supported file format.

    This function relies on `matplotlib.pyplot.savefig`_ (and `Inkscape`_).

    :param path_to_fig_file: path where a figure file is saved
    :type path_to_fig_file: str or os.PathLike[str]
    :param dpi: the resolution in dots per inch; if ``None`` (default), use ``rcParams['savefig.dpi']``
    :type dpi: int or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param conv_svg_to_emf: whether to convert a .svg file to a .emf file, defaults to ``False``
    :type conv_svg_to_emf: bool
    :param kwargs: [optional] parameters of `matplotlib.pyplot.savefig`_

    .. _`matplotlib.pyplot.savefig`:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html
    .. _`Inkscape`: https://inkscape.org

    **Examples**::

        >>> from pyhelpers.store import save_fig
        >>> from pyhelpers.dir import cd
        >>> import matplotlib.pyplot as plt

        >>> x, y = (1, 1), (2, 2)

        >>> plt.figure()
        >>> plt.plot([x[0], y[0]], [x[1], y[1]])
        >>> plt.show()

    The above exmaple is illustrated in :numref:`fig-1`:

    .. figure:: ../_images/fig.*
        :name: fig-1
        :align: center
        :width: 76%

        An example figure created for the function :py:func:`save_fig()<pyhelpers.store.save_fig>`.

    .. code-block:: python

        >>> img_dir = cd("tests\\images")

        >>> png_file_pathname = cd(img_dir, "fig.png")
        >>> save_fig(png_file_pathname, dpi=300, verbose=True)
        Saving "fig.png" to "tests\\images\\" ... Done.

        >>> svg_file_pathname = cd(img_dir, "fig.svg")
        >>> save_fig(svg_file_pathname, dpi=300, verbose=True, conv_svg_to_emf=True)
        Saving "fig.svg" to "tests\\images\\" ... Done.
        Saving the .svg file as "tests\\images\\fig.emf" ... Done.

        >>> plt.close()
    """

    _check_path_to_file(path_to_fig_file, verbose=verbose, ret_info=False)

    file_ext = pathlib.Path(path_to_fig_file).suffix

    try:
        import matplotlib.pyplot

        matplotlib.pyplot.savefig(path_to_fig_file, dpi=dpi, **kwargs)
        print("Done.") if verbose else ""

    except Exception as e:
        print("Failed. {}.".format(e)) if verbose else ""

    if file_ext == ".svg" and conv_svg_to_emf:
        save_svg_as_emf(path_to_fig_file, path_to_fig_file.replace(file_ext, ".emf"), verbose=verbose)


# Web page

def save_web_page_as_pdf(web_page, path_to_pdf, page_size='A4', zoom=1.0, encoding='UTF-8',
                         verbose=False, wkhtmltopdf_exe=None, **kwargs):
    """
    Save a web page as a `PDF <https://en.wikipedia.org/wiki/PDF>`_ file
    by `wkhtmltopdf <https://wkhtmltopdf.org/>`_.

    :param web_page: URL of a web page or pathname of an HTML file
    :type web_page: str
    :param path_to_pdf: path where a .pdf is saved
    :type path_to_pdf: str
    :param page_size: page size, defaults to ``'A4'``
    :type page_size: str
    :param zoom: a parameter to zoom in/out, defaults to ``1.0``
    :type zoom: float
    :param encoding: encoding format defaults to ``'UTF-8'``
    :type encoding: str
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool
    :param wkhtmltopdf_exe: absolute path to 'wkhtmltopdf.exe', defaults to ``None``;
        on Windows, the default installation path
        "*C:\\\\Program Files\\\\wkhtmltopdf\\\\bin\\\\wkhtmltopdf.exe*" is used
        when ``wkhtmltopdf_exe=None``
    :type wkhtmltopdf_exe: str or None
    :param kwargs: [optional] parameters of `pdfkit.from_url <https://pypi.org/project/pdfkit/>`_

    **Example**::

        >>> from pyhelpers.store import save_web_page_as_pdf
        >>> from pyhelpers.dir import cd
        >>> import subprocess

        >>> pdf_pathname = cd("tests\\documents", "pyhelpers.pdf")

        >>> web_page_url = 'https://pyhelpers.readthedocs.io/en/latest/'
        >>> save_web_page_as_pdf(web_page_url, pdf_pathname, verbose=True)
        Saving "pyhelpers.pdf" to "tests\\documents\\" ...
        Loading pages (1/6)
        Counting pages (2/6)
        Resolving links (4/6)
        Loading headers and footers (5/6)
        Printing pages (6/6)
        Done

        >>> # Open the PDF file using the system's default application
        >>> subprocess.Popen(pdf_pathname, shell=True)

        >>> web_page_file = cd("docs\\build\\html\\index.html")
        >>> save_web_page_as_pdf(web_page_file, pdf_pathname, verbose=True)
        Updating "pyhelpers.pdf" at "tests\\documents\\" ...
        Loading pages (1/6)
        Counting pages (2/6)
        Resolving links (4/6)
        Loading headers and footers (5/6)
        Printing pages (6/6)
        Done

        >>> subprocess.Popen(pdf_pathname, shell=True)
    """

    import pdfkit

    wkhtmltopdf_exe_ = copy.copy(wkhtmltopdf_exe)
    if wkhtmltopdf_exe_ is None:
        wkhtmltopdf_exe_ = find_executable(
            "wkhtmltopdf.exe", possibilities=["C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"])

    if os.path.isfile(wkhtmltopdf_exe_):
        pdfkit_configuration = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_exe)

    else:
        try:
            pdfkit_configuration = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_exe_)
        except (FileNotFoundError, OSError):
            print("\"wkhtmltopdf\" (https://wkhtmltopdf.org/) is required to run this function; "
                  "however, it is not found on this device.\nInstall it and then try again.")
            return None

    try:
        _check_path_to_file(
            path_to_file=path_to_pdf, verbose=verbose, verbose_end=" ... \n", ret_info=False)

        wkhtmltopdf_options = {
            'enable-local-file-access': None,
            'page-size': page_size,
            'zoom': str(float(zoom)),
            'encoding': encoding,
            # 'margin-top': '0',
            # 'margin-right': '0',
            # 'margin-left': '0',
            # 'margin-bottom': '0',
        }

        os.makedirs(os.path.dirname(path_to_pdf), exist_ok=True)

        if os.path.isfile(path_to_pdf):
            os.remove(path_to_pdf)

        kwargs.update({'configuration': pdfkit_configuration, 'options': wkhtmltopdf_options})

        if os.path.isfile(web_page):
            status = pdfkit.from_file(web_page, path_to_pdf, verbose=verbose, **kwargs)
        elif is_url(web_page):
            status = pdfkit.from_url(web_page, path_to_pdf, verbose=verbose, **kwargs)
        else:
            status = None

        if verbose and not status:
            print("Failed. Check if the URL is available.")

    except Exception as e:
        if verbose:
            print("Failed. {}".format(e), end="")


# A comprehensive function

def save_data(data, path_to_file, warning=True, **kwargs):
    """
    Save data to a file of a specific format.

    :param data: data that could be saved to
        a file of `Pickle`_, `CSV`_, `Microsoft Excel`_, `JSON`_, `Joblib`_ or `Feather`_ format;
        a URL of a web page or an `HTML file`_; or an image file of a `Matplotlib`-supported format
    :type data: any
    :param path_to_file: pathname of a file that stores the ``data``
    :type path_to_file: str or os.PathLike[str]
    :param warning: whether to show a warning messages, defaults to ``True``
    :type warning: bool
    :param kwargs: [optional] parameters of one of the following functions:
        :py:func:`save_pickle()<pyhelpers.store.save_pickle>`,
        :py:func:`save_spreadsheet()<pyhelpers.store.save_spreadsheet>`,
        :py:func:`save_json()<pyhelpers.store.save_json>`,
        :py:func:`save_joblib()<pyhelpers.store.save_joblib>`,
        :py:func:`save_feather()<pyhelpers.store.save_feather>`,
        :py:func:`save_fig()<pyhelpers.store.save_fig>` or
        :py:func:`save_web_page_as_pdf()<pyhelpers.store.save_web_page_as_pdf>`

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`JSON`: https://www.json.org/json-en.html
    .. _`Joblib`: https://pypi.org/project/joblib/
    .. _`Feather`: https://arrow.apache.org/docs/python/feather.html
    .. _`HTML file`: https://fileinfo.com/extension/html
    .. _`Matplotlib`:
        https://matplotlib.org/stable/api/backend_bases_api.html#
        matplotlib.backend_bases.FigureCanvasBase.get_supported_filetypes

    **Examples**::

        >>> from pyhelpers.store import save_data
        >>> from pyhelpers.dir import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> data_dir = cd("tests\\data")

        >>> # Get an example dataframe
        >>> dat = example_dataframe()
        >>> dat
                    Easting  Northing
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953

        >>> # Save the data to files different formats:

        >>> dat_pathname = cd(data_dir, "dat.pickle")
        >>> save_data(dat, dat_pathname, verbose=True)
        Saving "dat.pickle" to "tests\\data\\" ... Done.

        >>> dat_pathname = cd(data_dir, "dat.csv")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.csv" to "tests\\data\\" ... Done.

        >>> dat_pathname = cd(data_dir, "dat.xlsx")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.xlsx" to "tests\\data\\" ... Done.

        >>> dat_pathname = cd(data_dir, "dat.txt")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.txt" to "tests\\data\\" ... Done.

        >>> dat_pathname = cd(data_dir, "dat.feather")
        >>> save_data(dat, dat_pathname, verbose=True)
        Saving "dat.feather" to "tests\\data\\" ... Done.

        >>> # Convert `dat` to JSON format
        >>> import json

        >>> dat_ = json.loads(dat.to_json(orient='index'))
        >>> dat_
        {'London': {'Easting': 530034, 'Northing': 180381},
         'Birmingham': {'Easting': 406689, 'Northing': 286822},
         'Manchester': {'Easting': 383819, 'Northing': 398052},
         'Leeds': {'Easting': 582044, 'Northing': 152953}}

        >>> dat_pathname = cd(data_dir, "dat.json")
        >>> save_data(dat_, dat_pathname, indent=4, verbose=True)
        Saving "dat.json" to "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.load_data`.
    """

    path_to_file_ = path_to_file.lower()

    if path_to_file_.endswith(".pickle"):
        save_pickle(data, path_to_file, **kwargs)

    elif path_to_file_.endswith((".csv", ".xlsx", ".xls", ".txt")):
        save_spreadsheet(data, path_to_file, **kwargs)

    elif path_to_file_.endswith(".json"):
        save_json(data, path_to_file, **kwargs)

    elif path_to_file_.endswith(".joblib"):
        save_joblib(data, path_to_file, **kwargs)

    elif path_to_file_.endswith(".feather"):
        save_feather(data, path_to_file, **kwargs)

    elif (is_url(data) or os.path.isfile(data)) and path_to_file_.endswith(".pdf"):
        save_web_page_as_pdf(data, path_to_file_, **kwargs)

    elif path_to_file_.endswith(
            ('eps', 'jpeg', 'jpg', 'pdf', 'pgf', 'png', 'ps',
             'raw', 'rgba', 'svg', 'svgz', 'tif', 'tiff')):
        save_fig(path_to_file, **kwargs)

    else:
        if warning:
            warnings.warn(
                "The specified file format (extension) is not recognisable by "
                "`pyhelpers.store.save_data`.")

        if confirmed("To save the data as a .pickle file\n?"):
            save_pickle(data, path_to_file, **kwargs)


""" == Load data ============================================================================= """


def load_pickle(path_to_pickle, verbose=False, **kwargs):
    """
    Load data from a `Pickle`_ file.

    :param path_to_pickle: path where a pickle file is saved
    :type path_to_pickle: str or os.PathLike[str]
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pickle.load`_
    :return: data retrieved from the specified path ``path_to_pickle``
    :rtype: any

    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`pickle.load`: https://docs.python.org/3/library/pickle.html#pickle.load

    **Example**::

        >>> from pyhelpers.store import load_pickle
        >>> from pyhelpers.dir import cd

        >>> pickle_pathname = cd("tests\\data", "dat.pickle")
        >>> pickle_dat = load_pickle(pickle_pathname, verbose=True)
        Loading "tests\\data\\dat.pickle" ... Done.
        >>> pickle_dat
                    Easting  Northing
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.save_pickle`.
    """

    if verbose:
        print("Loading \"{}\"".format(os.path.relpath(path_to_pickle)), end=" ... ")

    try:
        pickle_in = open(path_to_pickle, mode='rb')
        pickle_data = pickle.load(pickle_in, **kwargs)
        pickle_in.close()
        print("Done.") if verbose else ""
        return pickle_data

    except Exception as e:
        print("Failed. {}".format(e))


def load_csv(path_to_csv, delimiter=',', header=0, index=None, verbose=False, **kwargs):
    """
    Load data from a `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_ file.

    :param path_to_csv: path where a `CSV`_ file is saved
    :type path_to_csv: str or os.PathLike[str]
    :param delimiter: delimiter used between values in the data file, defaults to ``','``
    :type delimiter: str
    :param header: index number of the rows used as column names, defaults to ``0``
    :type header: int or typing.List[int] or None
    :param index: index number of the column(s) to use as the row labels of the dataframe,
        defaults to ``None``
    :type index: str or list or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `csv.reader`_
    :return: data retrieved from the specified path ``path_to_csv``
    :rtype: pandas.DataFrame or None

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`csv.reader`: https://docs.python.org/3/library/pickle.html#pickle.load

    **Example**::

        >>> from pyhelpers.store import load_csv
        >>> from pyhelpers.dir import cd

        >>> csv_pathname = cd("tests\\data", "dat.csv")
        >>> csv_dat = load_csv(csv_pathname, verbose=True)
        Loading "tests\\data\\dat.csv" ... Done.
        >>> csv_dat
                   Easting Northing
        London      530034   180381
        Birmingham  406689   286822
        Manchester  383819   398052
        Leeds       582044   152953

        >>> csv_pathname = cd("tests\\data", "dat.txt")
        >>> csv_dat = load_csv(csv_pathname, verbose=True)
        Loading "tests\\data\\dat.txt" ... Done.
        >>> csv_dat
                   Easting Northing
        London      530034   180381
        Birmingham  406689   286822
        Manchester  383819   398052
        Leeds       582044   152953

        >>> csv_dat = load_csv(csv_pathname, header=[0, 1], verbose=True)
        Loading "tests\\data\\dat.txt" ... Done.
        >>> csv_dat
                      Easting Northing
               London  530034   180381
        0  Birmingham  406689   286822
        1  Manchester  383819   398052
        2       Leeds  582044   152953

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.save_spreadsheet`.
    """

    if verbose:
        print("Loading \"{}\"".format(os.path.relpath(path_to_csv)), end=" ... ")

    try:
        with open(path_to_csv, mode='r') as csv_file:
            csv_data_ = csv.reader(csv_file, delimiter=delimiter, **kwargs)
            csv_rows = [row for row in csv_data_]

        if header is not None:
            col_names = operator.itemgetter(*[header] if isinstance(header, int) else header)(csv_rows)
            dat = [x for x in csv_rows if (x not in col_names and x != col_names)]
            csv_data = pd.DataFrame(data=dat, columns=list(col_names))
        else:
            csv_data = pd.DataFrame(csv_rows)

        if index is None:
            idx_col = csv_data.columns[0]
            if idx_col == '':
                csv_data.set_index(idx_col, inplace=True)
                csv_data.index.name = None
        else:
            csv_data.set_index(keys=index, inplace=True)

        if verbose:
            print("Done.")

        return csv_data

    except Exception as e:
        print("Failed. {}".format(e))


def load_multiple_spreadsheets(path_to_spreadsheet, as_dict=True, verbose=False, **kwargs):
    """
    Load multiple sheets of an `Microsoft Excel`_ file.

    :param path_to_spreadsheet: path where a spreadsheet is saved
    :type path_to_spreadsheet: str or os.PathLike[str]
    :param as_dict: whether to return the retrieved data as a dictionary type, defaults to ``True``
    :type as_dict: bool
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.ExcelFile.parse`_
    :return: all worksheet in an Excel workbook from the specified file path ``path_to_spreadsheet``
    :rtype: list or dict

    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`pandas.ExcelFile.parse`:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.ExcelFile.parse.html

    **Examples**::

        >>> from pyhelpers.store import load_multiple_spreadsheets
        >>> from pyhelpers.dir import cd

        >>> dat_dir = cd("tests\\data")
        >>> path_to_xlsx = cd(dat_dir, "dat.xlsx")

        >>> wb_data = load_multiple_spreadsheets(path_to_xlsx, verbose=True, index_col=0)
        Loading "tests\\data\\dat.xlsx" ...
            'TestSheet1'. ... Done.
            'TestSheet2'. ... Done.
            'TestSheet11'. ... Done.
            'TestSheet21'. ... Done.
        >>> list(wb_data.keys())
        ['TestSheet1', 'TestSheet2', 'TestSheet11', 'TestSheet21']

        >>> wb_data = load_multiple_spreadsheets(path_to_xlsx, as_dict=False, index_col=0)
        >>> type(wb_data)
        list
        >>> len(wb_data)
        4
        >>> wb_data[0]
                    Easting  Northing
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953

    .. seealso::

        - Examples for the functions :py:func:`pyhelpers.store.save_multiple_spreadsheets` and
          :py:func:`pyhelpers.store.save_spreadsheet`.
    """

    excel_file_reader = pd.ExcelFile(path_to_spreadsheet)

    sheet_names = excel_file_reader.sheet_names
    workbook_dat = []

    if verbose:
        print("Loading \"{}\" ... ".format(os.path.relpath(path_to_spreadsheet)))

    for sheet_name in sheet_names:
        print("\t'{}'.".format(sheet_name), end=" ... ") if verbose else ""

        try:
            sheet_dat = excel_file_reader.parse(sheet_name, **kwargs)
            print("Done.") if verbose else ""

        except Exception as e:
            sheet_dat = None
            print("Failed. {}.".format(e)) if verbose else ""

        workbook_dat.append(sheet_dat)

    excel_file_reader.close()

    if as_dict:
        workbook_data = dict(zip(sheet_names, workbook_dat))
    else:
        workbook_data = workbook_dat

    return workbook_data


def load_json(path_to_json, method=None, verbose=False, **kwargs):
    """
    Load data from a `JSON`_ file.

    :param path_to_json: path where a json file is saved
    :type path_to_json: str or os.PathLike[str]
    :param method: an open-source Python package for JSON serialization, options include
        ``None`` (default, for the built-in `json module`_), ``'orjson'`` (for `orjson`_) and
        ``'rapidjson'`` (for `python-rapidjson`_)
    :type method: str or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `open`_ (if ``method='orjson'``),
        `rapidjson.load`_ (if ``method='rapidjson'``) or `json.load`_ (if ``method=None``)
    :return: data retrieved from the specified path ``path_to_json``
    :rtype: dict

    .. _`JSON`: https://www.json.org/json-en.html
    .. _`json module`: https://docs.python.org/3/library/json.html
    .. _`orjson`: https://pypi.org/project/orjson/
    .. _`python-rapidjson`: https://pypi.org/project/python-rapidjson
    .. _`open`: https://docs.python.org/3/library/functions.html#open
    .. _`rapidjson.load`: https://docs.python.org/3/library/functions.html#open
    .. _`json.load`: https://docs.python.org/3/library/json.html#json.load

    **Example**::

        >>> from pyhelpers.store import load_json
        >>> from pyhelpers.dir import cd

        >>> json_path = cd("tests\\data", "dat.json")
        >>> json_dat = load_json(json_path, verbose=True)
        Loading "tests\\data\\dat.json" ... Done.
        >>> json_dat
        {'London': {'Easting': 530034, 'Northing': 180381},
         'Birmingham': {'Easting': 406689, 'Northing': 286822},
         'Manchester': {'Easting': 383819, 'Northing': 398052},
         'Leeds': {'Easting': 582044, 'Northing': 152953}}

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.save_json`.
    """

    if verbose:
        print("Loading \"{}\"".format(os.path.relpath(path_to_json)), end=" ... ")

    try:
        if method == 'orjson':
            import orjson

            json_in = open(path_to_json, mode='rb', **kwargs)
            json_data = orjson.loads(json_in.read())

        else:
            json_in = open(path_to_json, mode='r')

            if method == 'rapidjson':
                import rapidjson

                # noinspection PyUnresolvedReferences
                json_data = rapidjson.load(json_in, **kwargs)

            else:
                json_data = json.load(json_in, **kwargs)

        json_in.close()

        print("Done.") if verbose else ""

        return json_data

    except Exception as e:
        print("Failed. {}".format(e))


def load_joblib(path_to_joblib, verbose=False, **kwargs):
    """
    Load data from a `joblib`_ file.

    :param path_to_joblib: path where a joblib file is saved
    :type path_to_joblib: str or os.PathLike[str]
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `joblib.load`_
    :return: data retrieved from the specified path ``path_to_joblib``
    :rtype: any

    .. _`joblib`: https://pypi.org/project/joblib/
    .. _`joblib.load`: https://joblib.readthedocs.io/en/latest/generated/joblib.load.html

    **Example**::

        >>> from pyhelpers.store import load_joblib
        >>> from pyhelpers.dir import cd

        >>> joblib_pathname = cd("tests\\data", "dat.joblib")
        >>> joblib_dat = load_joblib(joblib_pathname, verbose=True)
        Loading "tests\\data\\dat.joblib" ... Done.
        >>> joblib_dat
        array([[0.5488135 , 0.71518937, 0.60276338, ..., 0.02010755, 0.82894003,
                0.00469548],
               [0.67781654, 0.27000797, 0.73519402, ..., 0.25435648, 0.05802916,
                0.43441663],
               [0.31179588, 0.69634349, 0.37775184, ..., 0.86219152, 0.97291949,
                0.96083466],
               ...,
               [0.89111234, 0.26867428, 0.84028499, ..., 0.5736796 , 0.73729114,
                0.22519844],
               [0.26969792, 0.73882539, 0.80714479, ..., 0.94836806, 0.88130699,
                0.1419334 ],
               [0.88498232, 0.19701397, 0.56861333, ..., 0.75842952, 0.02378743,
                0.81357508]])

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.save_joblib`.
    """

    import joblib

    if verbose:
        print("Loading \"{}\"".format(os.path.relpath(path_to_joblib)), end=" ... ")

    try:
        # noinspection PyUnresolvedReferences
        joblib_data = joblib.load(filename=path_to_joblib, **kwargs)
        print("Done.") if verbose else ""

        return joblib_data

    except Exception as e:
        print("Failed. {}".format(e))


def load_feather(path_to_feather, verbose=False, **kwargs):
    """
    Load a dataframe from a `Feather`_ file.

    :param path_to_feather: path where a feather file is saved
    :type path_to_feather: str or os.PathLike[str]
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.read_feather`_

        * columns: a sequence of column names, if ``None``, all columns
        * use_threads: whether to parallelize reading using multiple threads, defaults to ``True``

    :return: data retrieved from the specified path ``path_to_feather``
    :rtype: pandas.DataFrame

    .. _`Feather`: https://arrow.apache.org/docs/python/feather.html
    .. _`pandas.read_feather`:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_feather.html

    **Example**::

        >>> from pyhelpers.store import load_feather
        >>> from pyhelpers.dir import cd

        >>> feather_path = cd("tests\\data", "dat.feather")
        >>> feather_dat = load_feather(feather_path, verbose=True)
        Loading "tests\\data\\dat.feather" ... Done.
        >>> feather_dat
                    Easting  Northing
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.save_feather`.
    """

    if verbose:
        print("Loading \"{}\"".format(os.path.relpath(path_to_feather)), end=" ... ")

    try:
        feather_data = pd.read_feather(path_to_feather, **kwargs)

        if isinstance(feather_data, pd.DataFrame):
            col_0 = feather_data.columns[0]

            if col_0.startswith('level_') and all(feather_data[col_0] == range(feather_data.shape[0])):
                del feather_data[col_0]

            if feather_data.columns[0] == 'index':
                feather_data.set_index('index', inplace=True)
                # feather_data = feather_data.rename_axis(None, axis=1)
                feather_data.index.name = None

        print("Done.") if verbose else ""

        return feather_data

    except Exception as e:
        print("Failed. {}".format(e))


def load_data(path_to_file, warning=True, **kwargs):
    """
    Load data from a file.

    :param path_to_file: pathname of a file;
        supported file formats include
        `Pickle`_, `CSV`_, `Microsoft Excel`_ spreadsheet, `JSON`_, `Joblib`_ and `Feather`_
    :type path_to_file: str or os.PathLike[str]
    :param warning: whether to show a warning messages, defaults to ``True``
    :type warning: bool
    :param kwargs: [optional] parameters of one of the following functions:
        :py:func:`load_pickle()<pyhelpers.store.load_pickle>`,
        :py:func:`load_csv()<pyhelpers.store.load_csv>`,
        :py:func:`load_spreadsheet()<pyhelpers.store.load_multiple_spreadsheets>`,
        :py:func:`load_json()<pyhelpers.store.load_json>`,
        :py:func:`load_joblib()<pyhelpers.store.load_joblib>` or
        :py:func:`load_feather()<pyhelpers.store.load_feather>`
    :return: loaded data
    :rtype: any

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`JSON`: https://www.json.org/json-en.html
    .. _`Joblib`: https://pypi.org/project/joblib/
    .. _`Feather`: https://arrow.apache.org/docs/python/feather.html

    **Examples**::

        >>> from pyhelpers.store import load_data
        >>> from pyhelpers.dir import cd

        >>> data_dir = cd("tests\\data")

        >>> pickle_dat = load_data(cd(data_dir, "dat.pickle"), verbose=True)
        Loading "tests\\data\\dat.pickle" ... Done.
        >>> pickle_dat
                    Easting  Northing
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953

        >>> csv_dat = load_data(path_to_file=cd(data_dir, "dat.csv"), verbose=True)
        Loading "tests\\data\\dat.csv" ... Done.
        >>> csv_dat
                   Easting Northing
        London      530034   180381
        Birmingham  406689   286822
        Manchester  383819   398052
        Leeds       582044   152953

        >>> json_dat = load_data(cd(data_dir, "dat.json"), verbose=True)
        Loading "tests\\data\\dat.json" ... Done.
        >>> json_dat
        {'London': {'Easting': 530034, 'Northing': 180381},
         'Birmingham': {'Easting': 406689, 'Northing': 286822},
         'Manchester': {'Easting': 383819, 'Northing': 398052},
         'Leeds': {'Easting': 582044, 'Northing': 152953}}

        >>> feather_dat = load_data(path_to_file=cd(data_dir, "dat.feather"), verbose=True)
        Loading "tests\\data\\dat.feather" ... Done.
        >>> feather_dat
                   Easting Northing
        London      530034   180381
        Birmingham  406689   286822
        Manchester  383819   398052
        Leeds       582044   152953

        >>> joblib_dat = load_data(path_to_file=cd(data_dir, "dat.joblib"), verbose=True)
        Loading "tests\\data\\dat.joblib" ... Done.
        >>> joblib_dat
        array([[0.5488135 , 0.71518937, 0.60276338, ..., 0.02010755, 0.82894003,
                0.00469548],
               [0.67781654, 0.27000797, 0.73519402, ..., 0.25435648, 0.05802916,
                0.43441663],
               [0.31179588, 0.69634349, 0.37775184, ..., 0.86219152, 0.97291949,
                0.96083466],
               ...,
               [0.89111234, 0.26867428, 0.84028499, ..., 0.5736796 , 0.73729114,
                0.22519844],
               [0.26969792, 0.73882539, 0.80714479, ..., 0.94836806, 0.88130699,
                0.1419334 ],
               [0.88498232, 0.19701397, 0.56861333, ..., 0.75842952, 0.02378743,
                0.81357508]])

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.save_data`.
    """

    path_to_file_ = path_to_file.lower()

    if path_to_file_.endswith(".pickle"):
        data = load_pickle(path_to_file, **kwargs)

    elif path_to_file_.endswith((".csv", ".txt")):
        data = load_csv(path_to_file, **kwargs)

    elif path_to_file_.endswith((".xlsx", ".xls")):
        data = load_multiple_spreadsheets(path_to_file, **kwargs)

    elif path_to_file_.endswith(".json"):
        data = load_json(path_to_file, **kwargs)

    elif path_to_file_.endswith(".joblib"):
        data = load_joblib(path_to_file, **kwargs)

    elif path_to_file_.endswith(".feather"):
        data = load_feather(path_to_file, **kwargs)

    else:
        data = None

        if warning:
            warnings.warn(
                "The specified file format (extension) is not recognisable by "
                "`pyhelpers.store.load_data`.")

    return data


""" == Uncompress data ======================================================================= """


def unzip(path_to_zip_file, out_dir=None, verbose=False, **kwargs):
    """
    Extract data from a `zipped (compressed)
    <https://support.microsoft.com/en-gb/help/14200/windows-compress-uncompress-zip-files>`_ file.

    :param path_to_zip_file: path where a Zip file is saved
    :type path_to_zip_file: str
    :param out_dir: path to a directory where the extracted data is saved, defaults to ``None``
    :type out_dir: str or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `zipfile.ZipFile.extractall`_

    .. _`zipfile.ZipFile.extractall`:
        https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile.extractall

    **Examples**::

        >>> from pyhelpers.store import unzip
        >>> from pyhelpers.dir import cd, delete_dir

        >>> zip_file_path = cd("tests\\data", "zipped.zip")

        >>> unzip(path_to_zip_file=zip_file_path, verbose=True)
        Extracting "tests\\data\\zipped.zip" to "tests\\data\\zipped\\" ... Done.
        >>> out_file_pathname = cd("tests\\data\\zipped", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test

        >>> output_dir = cd("tests\\data\\zipped_alt")
        >>> unzip(path_to_zip_file=zip_file_path, out_dir=output_dir, verbose=True)
        Extracting "tests\\data\\zipped.zip" to "tests\\data\\zipped_alt\\" ... Done.
        >>> out_file_pathname = cd("tests\\data\\zipped_alt", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test

        >>> # Delete the directory "tests\\data\\zipped\\"
        >>> delete_dir(cd("tests\\data\\zipped"), verbose=True)
        The directory "tests\\data\\zipped\\" is not empty.
        Confirmed to delete it
        ? [No]|Yes: yes
        Deleting "tests\\data\\zipped\\" ... Done.

        >>> # Delete the directory "tests\\data\\zipped_alt\\"
        >>> delete_dir(output_dir, verbose=True)
        The directory "tests\\data\\zipped_alt\\" is not empty.
        Confirmed to delete it
        ? [No]|Yes: yes
        Deleting "tests\\data\\zipped_alt\\" ... Done.
    """

    if out_dir is None:
        out_dir = os.path.splitext(path_to_zip_file)[0]

    if not os.path.exists(out_dir):
        os.makedirs(name=out_dir)

    if verbose:
        rel_path = os.path.relpath(path=path_to_zip_file)
        out_dir_ = os.path.relpath(path=out_dir) + ("\\" if not out_dir.endswith("\\") else "")
        print("Extracting \"{}\" to \"{}\"".format(rel_path, out_dir_), end=" ... ")

    try:
        with zipfile.ZipFile(file=path_to_zip_file) as zf:
            zf.extractall(path=out_dir, **kwargs)
        zf.close()

        print("Done.") if verbose else ""

    except Exception as e:
        print("Failed. {}".format(e))


def seven_zip(path_to_zip_file, out_dir=None, mode='aoa', verbose=False, seven_zip_exe=None, **kwargs):
    """
    Extract data from a compressed file by using `7-Zip <https://www.7-zip.org/>`_.

    :param path_to_zip_file: path where a compressed file is saved
    :type path_to_zip_file: str
    :param out_dir: path to a directory where the extracted data is saved, defaults to ``None``
    :type out_dir: str or None
    :param mode: defaults to ``'aoa'``
    :type mode: str
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param seven_zip_exe: absolute path to '7z.exe', defaults to ``None``;
        on Windows, the default installation path "*C:\\\\Program Files\\\\7-Zip\\\\7z.exe*" is used
        when ``seven_zip_exe=None``
    :type seven_zip_exe: str or None
    :param kwargs: [optional] parameters of `subprocess.call`_

    .. _`subprocess.call`: https://docs.python.org/3/library/subprocess.html#subprocess.call

    **Examples**::

        >>> from pyhelpers.store import seven_zip
        >>> from pyhelpers.dir import cd, delete_dir

        >>> zip_file_pathname = cd("tests\\data", "zipped.zip")

        >>> seven_zip(path_to_zip_file=zip_file_pathname, verbose=True)
        7-Zip 20.00 alpha (x64) : Copyright (c) 1999-2020 Igor Pavlov : 2020-02-06

        Scanning the drive for archives:
        1 file, 158 bytes (1 KiB)

        Extracting archive: \\tests\\data\\zipped.zip
        --
        Path = \\tests\\data\\zipped.zip
        Type = zip
        Physical Size = 158

        Everything is Ok

        Size:       4
        Compressed: 158

        File extracted successfully.

        >>> out_file_pathname = cd("tests\\data\\zipped", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test

        >>> output_dir = cd("tests\\data\\zipped_alt")
        >>> seven_zip(path_to_zip_file=zip_file_pathname, out_dir=output_dir, verbose=True)
        7-Zip 20.00 alpha (x64) : Copyright (c) 1999-2020 Igor Pavlov : 2020-02-06

        Scanning the drive for archives:
        1 file, 158 bytes (1 KiB)

        Extracting archive: \\tests\\data\\zipped.zip
        --
        Path = \\tests\\data\\zipped.zip
        Type = zip
        Physical Size = 158

        Everything is Ok

        Size:       4
        Compressed: 158

        File extracted successfully.

        >>> out_file_pathname = cd("tests\\data\\zipped_alt", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test

        >>> # Extract a .7z file
        >>> zip_file_path = cd("tests\\data", "zipped.7z")
        >>> seven_zip(path_to_zip_file=zip_file_path, out_dir=output_dir, verbose=True)
        7-Zip 20.00 alpha (x64) : Copyright (c) 1999-2020 Igor Pavlov : 2020-02-06

        Scanning the drive for archives:
        1 file, 138 bytes (1 KiB)

        Extracting archive: .\\tests\\data\\zipped.7z
        --
        Path = .\\tests\\data\\zipped.7z
        Type = 7z
        Physical Size = 138
        Headers Size = 130
        Method = LZMA2:12
        Solid = -
        Blocks = 1

        Everything is Ok

        Size:       4

        Compressed: 138

        File extracted successfully.

        >>> out_file_pathname = cd("tests\\data\\zipped", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test

        >>> # Delete the directory "tests\\data\\zipped\\"
        >>> delete_dir(cd("tests\\data\\zipped"), verbose=True)
        The directory "tests\\data\\zipped\\" is not empty.
        Confirmed to delete it
        ? [No]|Yes: yes
        Deleting "tests\\data\\zipped\\" ... Done.

        >>> # Delete the directory "tests\\data\\zipped_alt\\"
        >>> delete_dir(output_dir, verbose=True)
        The directory "tests\\data\\zipped_alt\\" is not empty.
        Confirmed to delete it
        ? [No]|Yes: yes
        Deleting "tests\\data\\zipped_alt\\" ... Done.
    """

    seven_zip_exe_ = copy.copy(seven_zip_exe)
    if seven_zip_exe_ is None:
        seven_zip_exe_ = find_executable(
            app_name="inkscape.exe", possibilities=["C:\\Program Files\\7-Zip\\7z.exe"])

    if out_dir is None:
        out_dir = os.path.splitext(path_to_zip_file)[0]

    try:
        subprocess.call(
            '"{}" x "{}" -o"{}" -{}'.format(seven_zip_exe_, path_to_zip_file, out_dir, mode), **kwargs)

        print("\nFile extracted successfully.")

    except Exception as e:
        print("\nFailed to extract \"{}\". {}.".format(path_to_zip_file, e))
        if verbose:
            print("\"7-Zip\" (https://www.7-zip.org/) is required to run this function; "
                  "however, it is not found on this device.\nInstall it and then try again.")
