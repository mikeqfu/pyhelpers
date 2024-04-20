"""
Save data.
"""

import copy
import logging
import os
import pathlib
import pickle
import platform
import subprocess
import sys

import pandas as pd

from .._cache import _check_dependency, _check_file_pathname, _confirmed, _print_failure_msg


def _check_saving_path(path_to_file, verbose=False, print_prefix="", state_verb="Saving",
                       state_prep="to", print_suffix="", print_end=" ... ", ret_info=False):
    # noinspection PyShadowingNames
    """
    Check about a specified file pathname.

    :param path_to_file: Path where a file is saved.
    :type path_to_file: str | pathlib.Path
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param print_prefix: Something prefixed to the default printing message; defaults to ``""`.
    :type print_prefix: str
    :param state_verb: Normally a word indicating either "saving" or "updating" a file;
        defaults to ``"Saving"``.
    :type state_verb: str
    :param state_prep: A preposition associated with ``state_verb``; defaults to ``"to"``.
    :type state_prep: str
    :param print_suffix: Something suffixed to the default printing message; defaults to ``""`.
    :type print_suffix: str
    :param print_end: A string passed to ``end`` for ``print``; defaults to ``" ... "``.
    :type print_end: str
    :param ret_info: Whether to return the file path information; defaults to ``False``.
    :type ret_info: bool
    :return: A relative path and, if ``ret_info=True``, a filename.
    :rtype: tuple

    **Tests**::

        >>> from pyhelpers.store import _check_saving_path
        >>> from pyhelpers.dirs import cd

        >>> path_to_file = cd()
        >>> try:
        ...     _check_saving_path(path_to_file, verbose=True)
        ... except AssertionError as e:
        ...     print(e)
        The input for `path_to_file` may not be a file path.

        >>> path_to_file = "pyhelpers.pdf"
        >>> _check_saving_path(path_to_file, verbose=True)
        >>> print("Passed.")
        Saving "pyhelpers.pdf" ... Passed.

        >>> path_to_file = cd("tests\\documents", "pyhelpers.pdf")
        >>> _check_saving_path(path_to_file, verbose=True)
        >>> print("Passed.")
        Saving "pyhelpers.pdf" to "tests\\" ... Passed.

        >>> path_to_file = "C:\\Windows\\pyhelpers.pdf"
        >>> _check_saving_path(path_to_file, verbose=True)
        >>> print("Passed.")
        Saving "pyhelpers.pdf" to "C:\\Windows\\" ... Passed.

        >>> path_to_file = "C:\\pyhelpers.pdf"
        >>> _check_saving_path(path_to_file, verbose=True)
        >>> print("Passed.")
        Saving "pyhelpers.pdf" to "C:\\" ... Passed.
    """

    abs_path_to_file = pathlib.Path(path_to_file).absolute()
    assert not abs_path_to_file.is_dir(), "The input for `path_to_file` may not be a file path."

    filename = pathlib.Path(abs_path_to_file).name if abs_path_to_file.suffix else ""

    try:
        rel_path = pathlib.Path(os.path.relpath(abs_path_to_file.parent))

        if rel_path == rel_path.parent:
            rel_path = abs_path_to_file.parent
        else:  # In case the specified path does not exist
            os.makedirs(abs_path_to_file.parent, exist_ok=True)

    except ValueError:
        if verbose == 2:
            logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
            logging.warning(f'\n\t"{abs_path_to_file.parent}" is outside the current working directory.')

        rel_path = abs_path_to_file.parent

    if verbose:
        if os.path.exists(abs_path_to_file):
            state_verb, state_prep = "Updating", "at"

        slash = "\\" if platform.system() == 'Windows' else "/"

        end = print_end if print_end else "\n"

        if rel_path == rel_path.parent and rel_path.drive == pathlib.Path.cwd().drive:
            msg_fmt = '{}{} "{}"{}'
            print(msg_fmt.format(
                print_prefix, state_verb, filename, print_suffix).replace(
                ":\\\\", ":\\"), end=end)
        else:
            msg_fmt = '{}{} "{}" {} "{}' + slash + '"{}'
            print(msg_fmt.format(
                print_prefix, state_verb, filename, state_prep, rel_path, print_suffix).replace(
                ":\\\\", ":\\"), end=end)

    if ret_info:
        return rel_path, filename


def save_pickle(data, path_to_file, verbose=False, **kwargs):
    """
    Save data to a `Pickle <https://docs.python.org/3/library/pickle.html>`_ file.

    :param data: Data that could be dumped by the built-in module `pickle.dump`_.
    :type data: Any
    :param path_to_file: Path where a pickle file is saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] parameters of `pickle.dump`_.

    .. _`pickle.dump`: https://docs.python.org/3/library/pickle.html#pickle.dump

    **Examples**::

        >>> from pyhelpers.store import save_pickle
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> pickle_dat = 1

        >>> pickle_pathname = cd("tests\\data", "dat.pickle")
        >>> save_pickle(pickle_dat, pickle_pathname, verbose=True)
        Saving "dat.pickle" to "tests\\data\\" ... Done.

        >>> # Get an example dataframe
        >>> pickle_dat = example_dataframe()
        >>> pickle_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> save_pickle(pickle_dat, pickle_pathname, verbose=True)
        Updating "dat.pickle" at "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :func:`pyhelpers.store.load_pickle`.
    """

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        pickle_out = open(path_to_file, mode='wb')
        pickle.dump(data, pickle_out, **kwargs)
        pickle_out.close()

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def _auto_adjust_column_width(writer, writer_kwargs, **kwargs):
    if 'sheet_name' in kwargs and writer_kwargs['engine'] == 'openpyxl':
        # Reference: https://stackoverflow.com/questions/39529662/
        ws = writer.sheets[kwargs['sheet_name']]
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                # noinspection PyBroadException
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception:
                    pass
            ws.column_dimensions[column_letter].width = (max_length + 2) * 1.1


def save_spreadsheet(data, path_to_file, index=False, engine=None, delimiter=',',
                     writer_kwargs=None, verbose=False, **kwargs):
    """
    Save data to a `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_,
    an `Microsoft Excel <https://en.wikipedia.org/wiki/Microsoft_Excel>`_, or
    an `OpenDocument <https://en.wikipedia.org/wiki/OpenDocument>`_ format file.

    The file extension can be `".txt"`, `".csv"`, `".xlsx"`, or `".xls"`;
    and engines may rely on `xlsxwriter`_, `openpyxl`_, or `odfpy`_.

    :param data: Data that could be saved as a spreadsheet
        (e.g. with a file extension ".xlsx" or ".csv").
    :type data: pandas.DataFrame
    :param path_to_file: Path where a spreadsheet is saved.
    :type path_to_file: str | os.PathLike | None
    :param index: Whether to include the index as a column; defaults to ``False``.
    :type index: bool
    :param engine: Valid options include ``'openpyxl'`` and `'xlsxwriter'` for Excel file formats
        such as ".xlsx" (or ".xls"), and ``'odf'`` for OpenDocument file format such as ".ods";
        defaults to ``None``.
    :type engine: str | None
    :param delimiter: A separator for saving ``data`` as a `".csv"`, `".txt"`, or `".odt"` file;
        defaults to ``','``.
    :type delimiter: str
    :param writer_kwargs: Optional parameters for `pandas.ExcelWriter`_; defatuls to ``None``.
    :type writer_kwargs: dict | None
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] parameters of `pandas.DataFrame.to_excel`_ or `pandas.DataFrame.to_csv`_.

    .. _`xlsxwriter`: https://pypi.org/project/XlsxWriter/
    .. _`openpyxl`: https://pypi.org/project/openpyxl/
    .. _`odfpy`: https://pypi.org/project/odfpy/
    .. _`pandas.ExcelWriter`: https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html
    .. _`pandas.DataFrame.to_excel`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html
    .. _`pandas.DataFrame.to_csv`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html

    **Examples**::

        >>> from pyhelpers.store import save_spreadsheet
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> # Get an example dataframe
        >>> spreadsheet_dat = example_dataframe()
        >>> spreadsheet_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> spreadsheet_pathname = cd("tests\\data", "dat.csv")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)
        Saving "dat.csv" to "tests\\data\\" ... Done.

        >>> spreadsheet_pathname = cd("tests\\data", "dat.xlsx")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)
        Saving "dat.xlsx" to "tests\\data\\" ... Done.

        >>> spreadsheet_pathname = cd("tests\\data", "dat.ods")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)
        Saving "dat.ods" to "tests\\data\\" ... Done.
    """

    _, filename = _check_saving_path(path_to_file=path_to_file, verbose=verbose, ret_info=True)
    _, ext = os.path.splitext(filename)

    valid_extensions = {".txt", ".csv", ".xlsx", ".xls", ".ods", ".odt"}
    assert ext in valid_extensions, f"File extension must be one of {valid_extensions}."

    try:  # to save the data
        if ext in {".csv", ".txt", ".odt"}:  # a .csv file
            data.to_csv(path_or_buf=path_to_file, sep=delimiter, **kwargs)

        else:
            if writer_kwargs is None:
                writer_kwargs = {'path': path_to_file}
            else:
                writer_kwargs.update({'path': path_to_file})

            if ext.startswith(".xls"):  # a .xlsx file or a .xls file
                _ = _check_dependency(name='openpyxl')
                writer_kwargs.update({'engine': 'openpyxl'})
            elif ext == ".ods":
                _ = _check_dependency(name='odf')
                writer_kwargs.update({'engine': 'odf'})  # kwargs.update({'engine': None})
            else:
                writer_kwargs.update({'engine': engine})

            with pd.ExcelWriter(**writer_kwargs) as writer:
                kwargs.update({'excel_writer': writer, 'index': index})
                data.to_excel(**kwargs)
                _auto_adjust_column_width(writer, writer_kwargs, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def save_spreadsheets(data, path_to_file, sheet_names, mode='w', if_sheet_exists=None,
                      writer_kwargs=None, verbose=False, **kwargs):
    """
    Save data to a multi-sheet `Microsoft Excel`_ or `OpenDocument`_ format file.

    The file extension can be `".xlsx"` (or `".xls"`) or `".ods"`.

    :param data: A sequence of dataframes.
    :type data: list | tuple | iterable
    :param path_to_file: Path where a spreadsheet is saved.
    :type path_to_file: str | os.PathLike
    :param sheet_names: All sheet names of an Excel workbook.
    :type sheet_names: list | tuple | iterable
    :param mode: Mode to write to an Excel file;
        ``'w'`` (default) for 'write' and ``'a'`` for 'append';
        note that the 'append' mode is not supported with OpenDocument.
    :type mode: str
    :param if_sheet_exists: Indicate the behaviour when trying to write to an existing sheet;
        see also the parameter ``if_sheet_exists`` of `pandas.ExcelWriter`_.
    :type if_sheet_exists: None | str
    :param writer_kwargs: Optional parameters for `pandas.ExcelWriter`_; defatuls to ``None``.
    :type writer_kwargs: dict | None
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] parameters of `pandas.DataFrame.to_excel`_.

    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`OpenDocument`: https://en.wikipedia.org/wiki/OpenDocument
    .. _`pandas.ExcelWriter`:
        https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html
    .. _`pandas.DataFrame.to_excel`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html

    **Examples**::

        >>> from pyhelpers.store import save_spreadsheets
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> dat1 = example_dataframe()  # Get an example dataframe
        >>> dat1
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> dat2 = dat1.T
        >>> dat2
        City          London  Birmingham  Manchester      Leeds
        Longitude  -0.127647   -1.902691   -2.245115  -1.543794
        Latitude   51.507322   52.479699   53.479489  53.797418

        >>> dat = [dat1, dat2]
        >>> sheets = ['TestSheet1', 'TestSheet2']

        >>> pathname = cd("tests\\data", "dat.ods")
        >>> save_spreadsheets(dat, pathname, sheets, verbose=True)
        Saving "dat.ods" to "tests\\data\\" ...
            'TestSheet1' ... Done.
            'TestSheet2' ... Done.

        >>> pathname = cd("tests\\data", "dat.xlsx")
        >>> save_spreadsheets(dat, pathname, sheets, verbose=True)
        Saving "dat.xlsx" to "tests\\data\\" ...
            'TestSheet1' ... Done.
            'TestSheet2' ... Done.

        >>> save_spreadsheets(dat, pathname, sheets, mode='a', verbose=True)
        Updating "dat.xlsx" at "tests\\data\\" ...
            'TestSheet1' ... This sheet already exists; [pass]|new|replace: new
                saved as 'TestSheet11' ... Done.
            'TestSheet2' ... This sheet already exists; [pass]|new|replace: new
                saved as 'TestSheet21' ... Done.

        >>> save_spreadsheets(dat, pathname, sheets, 'a', if_sheet_exists='replace', verbose=True)
        Updating "dat.xlsx" at "tests\\data\\" ...
            'TestSheet1' ... Done.
            'TestSheet2' ... Done.

        >>> save_spreadsheets(dat, pathname, sheets, 'a', if_sheet_exists='new', verbose=True)
        Updating "dat.xlsx" at "tests\\data\\" ...
            'TestSheet1' ... saved as 'TestSheet12' ... Done.
            'TestSheet2' ... saved as 'TestSheet22' ... Done.
    """

    assert path_to_file.endswith((".xlsx", ".xls", ".ods"))

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    if os.path.isfile(path_to_file) and mode == 'a':
        with pd.ExcelFile(path_or_buffer=path_to_file) as f:
            cur_sheet_names = f.sheet_names
    else:
        cur_sheet_names = []

    if path_to_file.endswith((".xlsx", ".xls")):
        engine = 'openpyxl'
    else:
        engine = 'odf'

    if writer_kwargs is None:
        writer_kwargs = {}
    writer_kwargs.update(
        {'path': path_to_file, 'engine': engine, 'mode': mode, 'if_sheet_exists': if_sheet_exists})

    with pd.ExcelWriter(**writer_kwargs) as writer:
        if verbose:
            print("")

        for sheet_data, sheet_name in zip(data, sheet_names):
            # sheet_data, sheet_name = spreadsheets_data[0], sheet_names[0]
            if verbose:
                print(f"\t'{sheet_name}'", end=" ... ")

            if sheet_name in cur_sheet_names:
                if if_sheet_exists is None:
                    if_sheet_exists_ = input("This sheet already exists; [pass]|new|replace: ")
                else:
                    assert if_sheet_exists in {'error', 'new', 'replace', 'overlay'}
                    if_sheet_exists_ = copy.copy(if_sheet_exists)

                if if_sheet_exists_ != 'pass':
                    writer._if_sheet_exists = if_sheet_exists_

            try:
                kwargs.update({'excel_writer': writer, 'sheet_name': sheet_name})
                sheet_data.to_excel(**kwargs)
                _auto_adjust_column_width(writer, writer_kwargs, **kwargs)

                if writer._if_sheet_exists == 'new':
                    new_sheet_name = [x for x in writer.sheets if x not in cur_sheet_names][0]
                    prefix = "\t\t" if if_sheet_exists is None else ""
                    add_msg = f"{prefix}saved as '{new_sheet_name}' ... Done."
                else:
                    add_msg = "Done."

                if verbose:
                    print(add_msg)

                cur_sheet_names = list(writer.sheets.keys())

            except Exception as e:
                _print_failure_msg(e=e, msg="Failed.")


def save_json(data, path_to_file, engine=None, verbose=False, **kwargs):
    """
    Save data to a `JSON <https://www.json.org/json-en.html>`_ file.

    :param data: Data that could be dumped by as a JSON file.
    :type data: Any
    :param path_to_file: Path where a JSON file is saved.
    :type path_to_file: str | os.PathLike
    :param engine: An open-source module used for JSON serialization; valid options include
        ``None`` (default, for the built-in `json module`_), ``'ujson'`` (for `UltraJSON`_),
        ``'orjson'`` (for `orjson`_) and ``'rapidjson'`` (for `python-rapidjson`_).
    :type engine: str | None
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] parameters of `json.dump()`_ (if ``engine=None``),
        `orjson.dumps()`_ (if ``engine='orjson'``), `ujson.dump()`_ (if ``engine='ujson'``) or
        `rapidjson.dump()`_ (if ``engine='rapidjson'``).

    .. _`json module`: https://docs.python.org/3/library/json.html
    .. _`UltraJSON`: https://pypi.org/project/ujson/
    .. _`orjson`: https://pypi.org/project/orjson/
    .. _`python-rapidjson`: https://pypi.org/project/python-rapidjson
    .. _`orjson.dumps()`: https://github.com/ijl/orjson#serialize
    .. _`ujson.dump()`: https://github.com/ultrajson/ultrajson#encoder-options
    .. _`rapidjson.dump()`: https://python-rapidjson.readthedocs.io/en/latest/dump.html
    .. _`json.dump()`: https://docs.python.org/3/library/json.html#json.dump

    **Examples**::

        >>> from pyhelpers.store import save_json
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> import json

        >>> json_pathname = cd("tests\\data", "dat.json")

        >>> json_dat = {'a': 1, 'b': 2, 'c': 3, 'd': ['a', 'b', 'c']}
        >>> save_json(json_dat, json_pathname, indent=4, verbose=True)
        Saving "dat.json" to "tests\\data\\" ... Done.

        >>> # Get an example dataframe
        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> # Convert the dataframe to JSON format
        >>> json_dat = json.loads(example_df.to_json(orient='index'))
        >>> json_dat
        {'London': {'Longitude': -0.1276474, 'Latitude': 51.5073219},
         'Birmingham': {'Longitude': -1.9026911, 'Latitude': 52.4796992},
         'Manchester': {'Longitude': -2.2451148, 'Latitude': 53.4794892},
         'Leeds': {'Longitude': -1.5437941, 'Latitude': 53.7974185}}

        >>> # Use built-in json module
        >>> save_json(json_dat, json_pathname, indent=4, verbose=True)
        Updating "dat.json" at "tests\\data\\" ... Done.

        >>> save_json(json_dat, json_pathname, engine='orjson', verbose=True)
        Updating "dat.json" at "tests\\data\\" ... Done.

        >>> save_json(json_dat, json_pathname, engine='ujson', indent=4, verbose=True)
        Updating "dat.json" at "tests\\data\\" ... Done.

        >>> save_json(json_dat, json_pathname, engine='rapidjson', indent=4, verbose=True)
        Updating "dat.json" at "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :func:`pyhelpers.store.load_json`.
    """

    if engine is not None:
        valid_engines = {'ujson', 'orjson', 'rapidjson'}
        assert engine in valid_engines, f"`engine` must be on one of {valid_engines}"
        mod = _check_dependency(name=engine)
    else:
        mod = sys.modules.get('json')

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        if engine == 'orjson':
            with open(path_to_file, mode='wb') as json_out:
                json_out.write(mod.dumps(data, **kwargs))

        else:
            with open(path_to_file, mode='w') as json_out:
                mod.dump(data, json_out, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def save_joblib(data, path_to_file, verbose=False, **kwargs):
    """
    Save data to a `Joblib <https://pypi.org/project/joblib/>`_ file.

    :param data: Data that could be dumped by `joblib.dump`_.
    :type data: Any
    :param path_to_file: Path where a pickle file is saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] parameters of `joblib.dump`_.

    .. _`joblib.dump`: https://joblib.readthedocs.io/en/latest/generated/joblib.dump.html

    **Examples**::

        >>> from pyhelpers.store import save_joblib
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> import numpy as np

        >>> joblib_pathname = cd("tests\\data", "dat.joblib")

        >>> # Example 1:
        >>> joblib_dat = example_dataframe().to_numpy()
        >>> joblib_dat
        array([[-0.1276474, 51.5073219],
               [-1.9026911, 52.4796992],
               [-2.2451148, 53.4794892],
               [-1.5437941, 53.7974185]])

        >>> save_joblib(joblib_dat, joblib_pathname, verbose=True)
        Saving "dat.joblib" to "tests\\data\\" ... Done.

        >>> # Example 2:
        >>> np.random.seed(0)
        >>> joblib_dat = np.random.rand(100, 100)
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
        Updating "dat.joblib" at "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :func:`pyhelpers.store.load_joblib`.
    """

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        joblib_ = _check_dependency(name='joblib')

        joblib_.dump(value=data, filename=path_to_file, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def save_feather(data, path_to_file, index=False, verbose=False, **kwargs):
    """
    Save a dataframe to a `Feather <https://arrow.apache.org/docs/python/feather.html>`_ file.

    :param data: A dataframe to be saved as a feather-formatted file
    :type data: pandas.DataFrame
    :param path_to_file: Path where a feather file is saved
    :type path_to_file: str | os.PathLike
    :param index: Whether to include the index as a column; defaults to ``False``.
    :type index: bool
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] parameters of `pandas.DataFrame.to_feather`_

    .. _`pandas.DataFrame.to_feather`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_feather.html

    **Examples**::

        >>> from pyhelpers.store import save_feather
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> feather_dat = example_dataframe()  # Get an example dataframe
        >>> feather_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> feather_pathname = cd("tests\\data", "dat.feather")

        >>> save_feather(feather_dat, feather_pathname, verbose=True)
        Saving "dat.feather" to "tests\\data\\" ... Done.

        >>> save_feather(feather_dat, feather_pathname, index=True, verbose=True)
        Updating "dat.feather" at "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :func:`pyhelpers.store.load_feather`.
    """

    assert isinstance(data, pd.DataFrame)

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        if list(data.index) != range(len(data)) or index is True:
            data.reset_index().to_feather(path_to_file, **kwargs)
        else:
            data.to_feather(path_to_file, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def save_svg_as_emf(path_to_svg, path_to_emf, verbose=False, inkscape_exe=None, **kwargs):
    """
    Save a `SVG <https://en.wikipedia.org/wiki/Scalable_Vector_Graphics>`_ file (.svg) as
    a `EMF <https://en.wikipedia.org/wiki/Windows_Metafile#EMF>`_ file (.emf).

    :param path_to_svg: Path where a .svg file is saved.
    :type path_to_svg: str
    :param path_to_emf: Path where a .emf file is saved.
    :type path_to_emf: str
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param inkscape_exe: An absolute path to 'inkscape.exe'; defaults to ``None``;
        when ``inkscape_exe=None``, use the default installation path, e.g. (on Windows)
        "*C:\\\\Program Files\\\\Inkscape\\\\bin\\\\inkscape.exe*"
        or "*C:\\\\Program Files\\\\Inkscape\\\\inkscape.exe*".
    :type inkscape_exe: str | None
    :param kwargs: [Optional] parameters of `subprocess.run`_.

    .. _`subprocess.run`:
        https://docs.python.org/3/library/subprocess.html#subprocess.run

    **Examples**::

        >>> from pyhelpers.store import save_svg_as_emf
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt

        >>> mpl_preferences()

        >>> x, y = (1, 1), (2, 2)

        >>> plt.figure()
        >>> plt.plot([x[0], y[0]], [x[1], y[1]])
        >>> plt.show()

    The above exmaple is illustrated in :numref:`store-save_fig-demo-1`:

    .. figure:: ../_images/store-save_fig-demo.*
        :name: store-save_fig-demo-1
        :align: center
        :width: 75%

        An example figure created for the function :func:`~pyhelpers.store.save_svg_as_emf`.

    .. code-block:: python

        >>> img_dir = cd("tests\\images")

        >>> svg_file_pathname = cd(img_dir, "store-save_fig-demo.svg")
        >>> plt.savefig(svg_file_pathname)  # Save the figure as a .svg file

        >>> emf_file_pathname = cd(img_dir, "store-save_fig-demo.emf")
        >>> save_svg_as_emf(svg_file_pathname, emf_file_pathname, verbose=True)
        Saving the .svg file as "tests\\images\\store-save_fig-demo.emf" ... Done.

        >>> plt.close()
    """

    exe_name = "inkscape.exe"
    optional_pathnames = {
        f"C:\\Program Files\\Inkscape\\{exe_name}",
        f"C:\\Program Files\\Inkscape\\bin\\{exe_name}",
    }
    inkscape_exists, inkscape_exe_ = _check_file_pathname(exe_name, optional_pathnames, inkscape_exe)

    abs_svg_path, abs_emf_path = map(pathlib.Path, (path_to_svg, path_to_emf))
    assert abs_svg_path.suffix.lower() == ".svg"

    if inkscape_exists:
        # if verbose:
        #     if abs_emf_path.exists():
        #         msg = f"Updating \"{abs_emf_path.name}\" at " \
        #               f"\"{os.path.relpath(abs_emf_path.parent)}\\\""
        #     else:
        #         msg = f"Saving the {abs_svg_path.suffix} file as \"{os.path.relpath(abs_emf_path)}\""
        #     print(msg, end=" ... ")
        _check_saving_path(abs_emf_path, verbose=verbose)

        try:
            abs_emf_path.parent.mkdir(exist_ok=True)

            command_args = [inkscape_exe_, '-z', path_to_svg, '-M', path_to_emf]
            rslt = subprocess.run(command_args, **kwargs)
            ret_code = rslt.returncode

            if ret_code != 0:
                command_args = [inkscape_exe_, '-z', path_to_svg, '--export-filename', path_to_emf]
                rslt = subprocess.run(command_args, **kwargs)
                ret_code = rslt.returncode

            if verbose:
                if ret_code == 0:
                    print("Done.")
                else:
                    print("Failed.", end=" ")

        except Exception as e:
            print(e)

    else:
        if verbose:
            print(
                "\"Inkscape\" (https://inkscape.org) is required to convert a SVG file to an EMF file;"
                " however, it is not found on this device.\nInstall it and then try again.")


def save_fig(path_to_file, dpi=None, verbose=False, conv_svg_to_emf=False, **kwargs):
    """
    Save a figure object to a file of a supported file format.

    This function relies on `matplotlib.pyplot.savefig`_ (and `Inkscape`_).

    :param path_to_file: Path where a figure file is saved.
    :type path_to_file: str | os.PathLike
    :param dpi: Resolution in dots per inch;
        when ``dpi=None`` (default), it uses ``rcParams['savefig.dpi']``.
    :type dpi: int | None
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param conv_svg_to_emf: Whether to convert a .svg file to a .emf file; defaults to ``False``.
    :type conv_svg_to_emf: bool
    :param kwargs: [Optional] parameters of `matplotlib.pyplot.savefig`_.

    .. _`matplotlib.pyplot.savefig`:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html
    .. _`Inkscape`: https://inkscape.org

    **Examples**::

        >>> from pyhelpers.store import save_fig
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt

        >>> mpl_preferences()

        >>> x, y = (1, 1), (2, 2)

        >>> plt.figure()
        >>> plt.plot([x[0], y[0]], [x[1], y[1]])
        >>> plt.show()

    The above exmaple is illustrated in :numref:`store-save_fig-demo-2`:

    .. figure:: ../_images/store-save_fig-demo.*
        :name: store-save_fig-demo-2
        :align: center
        :width: 75%

        An example figure created for the function :func:`~pyhelpers.store.save_fig`.

    .. code-block:: python

        >>> img_dir = cd("tests\\images")

        >>> png_file_pathname = cd(img_dir, "store-save_fig-demo.png")
        >>> save_fig(png_file_pathname, dpi=600, verbose=True)
        Saving "store-save_fig-demo.png" to "tests\\images\\" ... Done.

        >>> svg_file_pathname = cd(img_dir, "store-save_fig-demo.svg")
        >>> save_fig(svg_file_pathname, verbose=True, conv_svg_to_emf=True)
        Saving "store-save_fig-demo.svg" to "tests\\images\\" ... Done.
        Saving the .svg file as "tests\\images\\store-save_fig-demo.emf" ... Done.

        >>> plt.close()
    """

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        mpl_plt = _check_dependency(name='matplotlib.pyplot')

        mpl_plt.savefig(path_to_file, dpi=dpi, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")

    file_ext = pathlib.Path(path_to_file).suffix
    if file_ext == ".svg" and conv_svg_to_emf:
        save_svg_as_emf(path_to_file, path_to_file.replace(file_ext, ".emf"), verbose=verbose)


def save_figure(data, path_to_file, verbose=False, conv_svg_to_emf=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Save a figure object to a file of a supported file format.
    (An alternative to :func:`~pyhelpers.store.save_fig`.)

    :param data: A figure object.
    :type data: matplotlib.Figure | seaborn.FacetGrid
    :param path_to_file: Path where a figure file is saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param conv_svg_to_emf: Whether to convert a .svg file to a .emf file; defaults to ``False``.
    :type conv_svg_to_emf: bool
    :param kwargs: [Optional] parameters of `matplotlib.pyplot.savefig`_.

    .. _`matplotlib.pyplot.savefig`:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html

    **Examples**::

        >>> from pyhelpers.store import save_figure
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np

        >>> mpl_preferences()

        >>> x = np.linspace(-5, 5)
        >>> y = 1 / (1 + np.exp(-x))

        >>> fig = plt.figure()
        >>> plt.plot(x, y)
        >>> plt.show()

    The above exmaple is illustrated in :numref:`store-save_figure-demo-3`:

    .. figure:: ../_images/store-save_figure-demo.*
        :name: store-save_figure-demo-3
        :align: center
        :width: 75%

        An example figure created for the function :func:`~pyhelpers.store.save_figure`.

    .. code-block:: python

        >>> img_dir = cd("tests\\images")

        >>> png_file_pathname = cd(img_dir, "store-save_figure-demo.png")
        >>> save_figure(fig, png_file_pathname, dpi=600, verbose=True)
        Saving "store-save_figure-demo.png" to "tests\\images\\" ... Done.

        >>> svg_file_pathname = cd(img_dir, "store-save_figure-demo.svg")
        >>> save_figure(fig, svg_file_pathname, verbose=True, conv_svg_to_emf=True)
        Saving "store-save_figure-demo.svg" to "tests\\images\\" ... Done.
        Saving the .svg file as "tests\\images\\store-save_figure-demo.emf" ... Done.

        >>> plt.close()
    """

    assert 'savefig' in dir(data), \
        ("The `fig` object does not have attribute `.savefig`. \n"
         "Check `fig`, or try `save_fig()` instead.")

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        data.savefig(path_to_file, **kwargs)
        if verbose:
            print("Done.")
    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")

    if conv_svg_to_emf:
        file_ext = pathlib.Path(path_to_file).suffix
        if file_ext != ".svg":
            kwargs.update({'conv_svg_to_emf': False})
            save_figure(data, path_to_file.replace(file_ext, ".svg"), **kwargs)

        save_svg_as_emf(path_to_file, path_to_file.replace(file_ext, ".emf"), verbose=verbose)


def save_html_as_pdf(data, path_to_file, if_exists='replace', page_size='A4', zoom=1.0,
                     encoding='UTF-8', wkhtmltopdf_options=None, wkhtmltopdf_path=None,
                     verbose=False, **kwargs):
    """
    Save a web page as a `PDF <https://en.wikipedia.org/wiki/PDF>`_ file
    by `wkhtmltopdf <https://wkhtmltopdf.org/>`_.

    :param data: URL of a web page or pathname of an HTML file.
    :type data: str
    :param path_to_file: Path where a PDF file is saved.
    :type path_to_file: str
    :param if_exists: Indicate the action if the .pdf file exsits; defaults to ``'replace'``;
        valid options include ``'replace'``, ``'pass'`` and ``'append'``.
    :type if_exists: str
    :param page_size: Page size; defaults to ``'A4'``.
    :type page_size: str
    :param zoom: Magnification for zooming in/out; defaults to ``1.0``.
    :type zoom: float
    :param encoding: Encoding format; defaults to ``'UTF-8'``.
    :type encoding: str
    :param wkhtmltopdf_options: Specify `wkhtmltopdf options`_; defaults to ``None``;
        check also the project description of `pdfkit`_.
    :type wkhtmltopdf_options: dict | None
    :param wkhtmltopdf_path: An absolute path to 'wkhtmltopdf.exe'; defaults to ``None``;
        when ``wkhtmltopdf_exe=None``, use the default installation path, such as
        "*C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe*" (on Windows).
    :type wkhtmltopdf_path: str | None
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] parameters of `pdfkit.from_url`_.

    .. _`wkhtmltopdf options`: https://wkhtmltopdf.org/usage/wkhtmltopdf.txt
    .. _`pdfkit`: https://pypi.org/project/pdfkit/
    .. _`pdfkit.from_url`: https://pypi.org/project/pdfkit/

    **Examples**::

        >>> from pyhelpers.store import save_html_as_pdf
        >>> from pyhelpers.dirs import cd
        >>> import subprocess

        >>> pdf_pathname = cd("tests\\documents", "pyhelpers.pdf")

        >>> web_page_url = 'https://pyhelpers.readthedocs.io/en/latest/'
        >>> save_html_as_pdf(web_page_url, pdf_pathname)
        >>> # Open the PDF file using the system's default application
        >>> subprocess.Popen(pdf_pathname, shell=True)

        >>> web_page_file = cd("docs\\build\\html\\index.html")
        >>> save_html_as_pdf(web_page_file, pdf_pathname, verbose=True)
        Updating "pyhelpers.pdf" at "tests\\documents\\" ... Done.
        >>> subprocess.Popen(pdf_pathname, shell=True)

        >>> save_html_as_pdf(web_page_file, pdf_pathname, verbose=2)
        Updating "pyhelpers.pdf" at "tests\\documents\\" ...
        Loading pages (1/6)
        Counting pages (2/6)
        Resolving links (4/6)
        Loading headers and footers (5/6)
        Printing pages (6/6)
        Done
        >>> subprocess.Popen(pdf_pathname, shell=True)
    """

    if os.path.isfile(path_to_file) and if_exists == 'pass':
        return None

    else:
        exe_name = "wkhtmltopdf.exe"
        optional_pathnames = {
            f"C:\\Program Files\\wkhtmltopdf\\{exe_name}",
            f"C:\\Program Files\\wkhtmltopdf\\bin\\{exe_name}",
        }
        wkhtmltopdf_exists, wkhtmltopdf_exe = _check_file_pathname(
            name=exe_name, options=optional_pathnames, target=wkhtmltopdf_path)

        if wkhtmltopdf_exists:
            pdfkit_ = _check_dependency(name='pdfkit')

            if os.path.dirname(path_to_file):
                os.makedirs(os.path.dirname(path_to_file), exist_ok=True)

            verbose_, print_end = (True, " ... \n") if verbose == 2 else (False, " ... ")

            _check_saving_path(
                path_to_file=path_to_file, verbose=verbose, print_end=print_end, ret_info=False)

            options = {
                'enable-local-file-access': None,
                'page-size': page_size,
                'zoom': str(float(zoom)),
                'encoding': encoding,
                # 'margin-top': '0',
                # 'margin-right': '0',
                # 'margin-left': '0',
                # 'margin-bottom': '0',
            }
            if isinstance(wkhtmltopdf_options, dict):
                options.update(wkhtmltopdf_options)
            configuration = pdfkit_.configuration(wkhtmltopdf=wkhtmltopdf_exe)
            kwargs.update({'configuration': configuration, 'options': options, 'verbose': verbose_})

            from pyhelpers.ops import is_url

            try:
                if is_url(data):
                    status = pdfkit_.from_url(data, path_to_file, **kwargs)
                elif os.path.isfile(data):
                    status = pdfkit_.from_file(data, path_to_file, **kwargs)
                else:
                    status = None

                if verbose:
                    if not status:
                        print("Failed. Check if the URL is available.")
                    elif not verbose_:
                        print("Done.")

            except Exception as e:
                _print_failure_msg(e=e, msg="Failed.")

        else:
            print("\"wkhtmltopdf\" (https://wkhtmltopdf.org/) is required to run this function; "
                  "however, it is not found on this device.\nInstall it and then try again.")


def save_data(data, path_to_file, err_warning=True, confirmation_required=True, **kwargs):
    """
    Save data to a file of a specific format.

    :param data: Data that could be saved to
        a file of `Pickle`_, `CSV`_, `Microsoft Excel`_, `JSON`_, `Joblib`_ or `Feather`_ format;
        a URL of a web page or an `HTML file`_; or an image file of a `Matplotlib`_-supported format.
    :type data: Any
    :param path_to_file: Pathname of a file that stores the ``data``.
    :type path_to_file: str | os.PathLike
    :param err_warning: Whether to show a warning message if any unknown error occurs;
        defaults to ``True``.
    :type err_warning: bool
    :param confirmation_required: Whether to require users to confirm and proceed;
        defaults to ``True``.
    :type confirmation_required: bool
    :param kwargs: [Optional] parameters of one of the following functions:
        :func:`~pyhelpers.store.save_pickle`,
        :func:`~pyhelpers.store.save_spreadsheet`,
        :func:`~pyhelpers.store.save_json`,
        :func:`~pyhelpers.store.save_joblib`,
        :func:`~pyhelpers.store.save_feather`,
        :func:`~pyhelpers.store.save_fig` or
        :func:`~pyhelpers.store.save_web_page_as_pdf`.

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
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> data_dir = cd("tests\\data")

        >>> # Get an example dataframe
        >>> dat = example_dataframe()
        >>> dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

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
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.feather" to "tests\\data\\" ... Done.

        >>> # Convert `dat` to JSON format
        >>> import json

        >>> dat_ = json.loads(dat.to_json(orient='index'))
        >>> dat_
        {'London': {'Longitude': -0.1276474, 'Latitude': 51.5073219},
         'Birmingham': {'Longitude': -1.9026911, 'Latitude': 52.4796992},
         'Manchester': {'Longitude': -2.2451148, 'Latitude': 53.4794892},
         'Leeds': {'Longitude': -1.5437941, 'Latitude': 53.7974185}}

        >>> dat_pathname = cd(data_dir, "dat.json")
        >>> save_data(dat_, dat_pathname, indent=4, verbose=True)
        Saving "dat.json" to "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :func:`pyhelpers.store.load_data`.
    """

    path_to_file_ = str(path_to_file).lower()

    kwargs.update({'data': data, 'path_to_file': path_to_file})

    if path_to_file_.endswith((".pkl", ".pickle")):
        save_pickle(**kwargs)

    elif path_to_file_.endswith((".csv", ".xlsx", ".xls", ".txt")):
        save_spreadsheet(**kwargs)

    elif path_to_file_.endswith(".json"):
        save_json(**kwargs)

    elif path_to_file_.endswith((".joblib", ".sav", ".z", ".gz", ".bz2", ".xz", ".lzma")):
        save_joblib(**kwargs)

    elif path_to_file_.endswith((".fea", ".feather")):
        save_feather(**kwargs)

    elif (path_to_file_.endswith(".pdf") and
          all(x not in data.__class__.__module__ for x in {'seaborn', 'matplotlib'})):
        # noinspection PyBroadException
        save_html_as_pdf(**kwargs)

    elif path_to_file_.endswith(
            ('.eps', '.jpeg', '.jpg', '.pdf', '.pgf', '.png', '.ps',
             '.raw', '.rgba', '.svg', '.svgz', '.tif', '.tiff')):
        # noinspection PyBroadException
        try:
            save_figure(**kwargs)
        except Exception:
            save_fig(path_to_file=path_to_file, **kwargs)

    else:
        if err_warning:
            logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
            logging.warning(
                "\n\tThe specified file format (extension) is not recognisable by "
                "`pyhelpers.store.save_data`.")

        if _confirmed("To save the data as a pickle file\n?", confirmation_required):
            save_pickle(**kwargs)
