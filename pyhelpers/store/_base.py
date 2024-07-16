import copy
import logging
import os
import pathlib
import platform

from .._cache import _check_rel_pathname


def _check_saving_path(path_to_file, verbose=False, print_prefix="", state_verb="Saving",
                       state_prep="to", print_suffix="", print_end=" ... ", ret_info=False):
    # noinspection PyShadowingNames
    """
    Verify a specified file path before saving.

    :param path_to_file: Path where the file will be saved.
    :type path_to_file: str | pathlib.Path
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_prefix: Text prefixed to the default print message; defaults to ``""``.
    :type print_prefix: str
    :param state_verb: Verb indicating the action being performed, e.g. *saving* or *updating*;
        defaults to ``"Saving"``.
    :type state_verb: str
    :param state_prep: Preposition associated with ``state_verb``; defaults to ``"to"``.
    :type state_prep: str
    :param print_suffix: Text suffixed to the default print message; defaults to ``""``.
    :type print_suffix: str
    :param print_end: String passed to the ``end`` parameter of ``print``; defaults to ``" ... "``.
    :type print_end: str
    :param ret_info: Whether to return file path information; defaults to ``False``.
    :type ret_info: bool
    :return: A tuple containing the relative path and, if ``ret_info=True``, the filename.
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
            logging.warning(
                f'\n\t"{abs_path_to_file.parent}" is outside the current working directory.')

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


def _autofit_column_width(writer, writer_kwargs, **kwargs):
    """
    Automatically adjusts the column widths in an Excel spreadsheet based on the content length.

    This function is specifically designed for *openpyxl* engine when working with *Pandas*
    `ExcelWriter`_. It iterates through each column of the specified sheet and calculates
    the maximum length of the content. It then adjusts the column width to accommodate the
    longest content plus some padding.

    :param writer: ExcelWriter object used to write data into Excel file.
    :type writer: pandas.ExcelWriter
    :param writer_kwargs: Keyword arguments passed to the `ExcelWriter`_, including the engine.
    :type writer_kwargs: dict
    :param kwargs: [Optional] Additional parameters.

    .. _ExcelWriter:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.ExcelWriter.html

    .. note::

        - This function assumes that *openpyxl* engine is used
          (i.e. ``writer_kwargs['engine'] == 'openpyxl'``).
        - It modifies the column dimensions directly in the ``pandas.ExcelWriter`` object.

    .. seealso::

        - For more information on *openpyxl*, refer to the official documentation:
          https://openpyxl.readthedocs.io/en/stable/
    """

    if 'sheet_name' in kwargs and writer_kwargs['engine'] == 'openpyxl':
        # Reference: https://stackoverflow.com/questions/39529662/
        ws = writer.sheets[kwargs['sheet_name']]
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            ws.column_dimensions[column_letter].width = (max_length + 2) * 1.1


def _check_loading_path(path_to_file, verbose=False, print_prefix="", state_verb="Loading",
                        print_suffix="", print_end=" ... "):
    # noinspection PyShadowingNames
    """
    Check the status of loading a file from a specified path.

    :param path_to_file: Path where the file is located.
    :type path_to_file: str | bytes | pathlib.Path
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_prefix: Prefix added to the default printing message; defaults to ``""`.
    :type print_prefix: str
    :param state_verb: Action verb indicating *loading* or *reading* a file;
        defaults to ``"Loading"``.
    :type state_verb: str
    :param print_suffix: Suffix added to the default printing message; defaults to ``""`.
    :type print_suffix: str
    :param print_end: String passed to ``end`` parameter for ``print()``; defaults to ``" ... "``.
    :type print_end: str

    **Tests**::

        >>> from pyhelpers.store import _check_loading_path
        >>> from pyhelpers.dirs import cd
        >>> path_to_file = cd("test_func.py")
        >>> _check_loading_path(path_to_file, verbose=True)
        >>> print("Passed.")
        Loading "test_func.py" ... Passed.
    """

    if verbose:
        rel_pathname = _check_rel_pathname(path_to_file)
        print(f'{print_prefix}{state_verb} "{rel_pathname}"{print_suffix}', end=print_end)


def _set_index(data, index=None):
    """
    Set the index of a dataframe.

    :param data: The dataframe to update.
    :type data: pandas.DataFrame
    :param index: Column index or a list of column indices to set as the index;
        when ``index=None`` (default), the function sets the first column as the index
        if its column name is an empty string.
    :type index: int | list | None
    :return: The dataframe with the updated index.
    :rtype: pandas.DataFrame

    **Tests**::

        >>> from pyhelpers.store import _set_index
        >>> from pyhelpers._cache import example_dataframe
        >>> import numpy as np
        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> example_df.equals(_set_index(example_df))
        True
        >>> example_df_1 = _set_index(example_df, index=0)
        >>> example_df_1
                    Latitude
        Longitude
        -0.127647  51.507322
        -1.902691  52.479699
        -2.245115  53.479489
        -1.543794  53.797418
        >>> example_df.iloc[:, 0].to_list() == example_df_1.index.to_list()
        True
        >>> example_df_2 = example_df.copy()
        >>> example_df_2.index.name = ''
        >>> example_df_2.reset_index(inplace=True)
        >>> example_df_2 = _set_index(example_df_2, index=None)
        >>> np.array_equal(example_df_2.values, example_df.values)
        True
    """

    data_ = data.copy()

    if index is None:
        idx_col = data.columns[0]
        if idx_col == '':
            data_ = data.set_index(idx_col)
            data_.index.name = None

    else:
        idx_keys_ = [index] if isinstance(index, (int, list)) else copy.copy(index)
        idx_keys = [data.columns[x] if isinstance(x, int) else x for x in idx_keys_]
        data_ = data.set_index(keys=idx_keys)

    return data_
