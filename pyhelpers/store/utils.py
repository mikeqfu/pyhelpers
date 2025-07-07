"""
Utilities that support the main submodules of :mod:`~pyhelpers.store`.
"""

import copy
import logging
import os
import pathlib

from .._cache import _add_slashes, _check_relative_pathname


def _print_wrapped_string(message, filename, end, print_wrap_limit=100):
    """
    Prints a string, splitting it into two lines if it exceeds the threshold, with the second half
    being indented based on the initial indentation level.

    :param message: The string to print.
    :type message: str
    :param filename: The filename to be included in the string.
    :type filename: str
    :param end:
    :param print_wrap_limit: The maximum length before splitting.
    :type print_wrap_limit: int | None
    """

    if print_wrap_limit:
        stripped_text = message.lstrip()  # Remove leading spaces for accurate tab count
        leading_tabs = len(message) - len(stripped_text)

        if len(stripped_text) <= print_wrap_limit:
            print(message, end=end)

        else:
            # Find a suitable split point (preferably at a space)
            split_index = message.find(f'"{filename}"') + len(f'"{filename}"')
            if message[split_index] == " ":
                split_index += 1  # Move to space if it exists

            first_part = message[:split_index].rstrip()  # Trim trailing spaces
            second_part = message[split_index:].lstrip()  # Trim leading spaces

            # Print first part as is
            print(first_part + " ... ")

            # Print second part with increased indentation (original + 1 extra tab)
            print("\t" * (leading_tabs + 1) + second_part, end=end)

    else:
        print(message, end=end)


def _check_saving_path(path_to_file, verbose=False, print_prefix="", state_verb="Saving",
                       state_prep="to", print_suffix="", print_end=" ... ", print_wrap_limit=None,
                       belated=False, ret_info=False):
    # noinspection PyShadowingNames
    """
    Verifies a specified file path before saving.

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
    :param print_wrap_limit: Maximum length of the string before splitting into two lines;
        defaults to ``None``, which disables splitting. If the string exceeds this value,
        e.g. ``100``, it will be split at (before) ``state_prep`` to improve readability
        when printed.
    :type print_wrap_limit: int | None
    :param ret_info: Whether to return file path information; defaults to ``False``.
    :type ret_info: bool
    :return: A tuple containing the relative path and, if ``ret_info=True``, the filename.
    :rtype: tuple

    **Tests**::

        >>> from pyhelpers.store import _check_saving_path
        >>> from pyhelpers.dirs import cd
        >>> path_to_file = cd()
        >>> _check_saving_path(path_to_file, verbose=True)
        Traceback (most recent call last):
            ...
        AssertionError: The input for <path_to_file> may not be a file path.
        >>> path_to_file = "pyhelpers.pdf"
        >>> _check_saving_path(path_to_file, verbose=True); print("Passed.")
        Saving "pyhelpers.pdf" ... Passed.
        >>> path_to_file = cd("tests", "documents", "pyhelpers.pdf")
        >>> _check_saving_path(path_to_file, verbose=True); print("Passed.")
        Saving "pyhelpers.pdf" in "./tests/documents/" ... Passed.
        >>> _check_saving_path(path_to_file, verbose=True, print_wrap_limit=10); print("Passed.")
        Updating "pyhelpers.pdf" ...
            in "./tests/documents/" ... Passed.
        >>> path_to_file = "C:\\Windows\\pyhelpers.pdf"
        >>> _check_saving_path(path_to_file, verbose=True); print("Passed.")
        Saving "pyhelpers.pdf" to "C:/Windows/" ... Passed.
        >>> path_to_file = "C:\\pyhelpers.pdf"
        >>> _check_saving_path(path_to_file, verbose=True); print("Passed.")
        Saving "pyhelpers.pdf" to "C:/" ... Passed.
    """

    abs_path_to_file = pathlib.Path(path_to_file).absolute()
    if abs_path_to_file.is_dir():
        raise ValueError(f"The input for '{path_to_file}' may not be a file path.")

    try:
        rel_dir_path = abs_path_to_file.parent.relative_to(pathlib.Path.cwd())

        if rel_dir_path.is_relative_to(".") and rel_dir_path == rel_dir_path.parent:
            rel_dir_path = abs_path_to_file.parent

    except ValueError:
        if verbose == 2:
            logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
            logging.warning(
                f'\n\t"{abs_path_to_file.parent}" is outside the current working directory.')

        rel_dir_path = abs_path_to_file.parent

    rel_dir_path.mkdir(parents=True, exist_ok=True)  # In case the specified path does not exist

    filename = abs_path_to_file.name if abs_path_to_file.suffix else ""

    if verbose:
        if os.path.isfile(abs_path_to_file) and not belated:
            state_verb, state_prep = "Updating", "in"

        end = print_end if print_end else "\n"

        if (rel_dir_path == rel_dir_path.parent or rel_dir_path == abs_path_to_file.parent) and (
                rel_dir_path.absolute().drive == pathlib.Path.cwd().drive):
            message = f'{print_prefix}{state_verb} "{filename}"{print_suffix}'
            print(message, end=end)

        else:
            message = (f'{print_prefix}{state_verb} "{filename}" '
                       f'{state_prep} {_add_slashes(rel_dir_path)}{print_suffix}')

            _print_wrapped_string(
                message=message, filename=filename, end=end, print_wrap_limit=print_wrap_limit)

    if ret_info:
        return rel_dir_path, filename

    return None


def _autofit_column_width(writer, writer_kwargs, **kwargs):
    """
    Adjusts the column widths in an Excel spreadsheet based on the content length.

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
        ws = writer.sheets[kwargs.get('sheet_name')]
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
    Checks the status of loading a file from a specified path.

    :param path_to_file: Path where the file is located.
    :type path_to_file: str | bytes | pathlib.Path
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_prefix: Prefix added to the default printing message; defaults to ``""``.
    :type print_prefix: str
    :param state_verb: Action verb indicating *loading* or *reading* a file;
        defaults to ``"Loading"``.
    :type state_verb: str
    :param print_suffix: Suffix added to the default printing message; defaults to ``""``.
    :type print_suffix: str
    :param print_end: String passed to ``end`` parameter for ``print()``; defaults to ``" ... "``.
    :type print_end: str

    **Tests**::

        >>> from pyhelpers.store import _check_loading_path
        >>> from pyhelpers.dirs import cd
        >>> path_to_file = cd("test_func.py")
        >>> _check_loading_path(path_to_file, verbose=True); print("Passed.")
        Loading "./test_func.py" ... Passed.
        >>> path_to_file = "C:\\Windows\\pyhelpers.pdf"
        >>> _check_loading_path(path_to_file, verbose=True); print("Passed.")
        Loading "C:/Windows/pyhelpers.pdf" ... Passed.
    """

    if verbose:
        rel_pathname = _check_relative_pathname(path_to_file)
        prt_msg = f'{print_prefix}{state_verb} {_add_slashes(rel_pathname)}{print_suffix}'
        print(prt_msg, end=print_end)


def _set_index(data, index=None):
    """
    Sets the index of a dataframe.

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
