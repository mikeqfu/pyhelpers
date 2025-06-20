"""
Basic data manipulation.
"""

import collections.abc
import copy
import itertools
import math

import numpy as np
import pandas as pd

from .._cache import _check_dependencies, _lazy_check_dependencies


# ==================================================================================================
# Iterable
# ==================================================================================================

def loop_in_pairs(iterable):
    """
    Generates pairs of consecutive elements from the given iterable.

    :param iterable: Iterable object from which to generate pairs.
    :type iterable: typing.Iterable
    :return: Zip object containing pairs of consecutive elements.
    :rtype: zip

    **Examples**::

        >>> from pyhelpers.ops import loop_in_pairs
        >>> res = loop_in_pairs(iterable=[1])
        >>> list(res)
        []
        >>> res = loop_in_pairs(iterable=range(0, 10))
        >>> list(res)
        [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)]
    """

    a, b = itertools.tee(iterable)
    next(b, None)

    return zip(a, b)


def split_list_by_size(lst, sub_len):
    """
    Splits a list into evenly sized sub-lists.

    See also [`OPS-SLBS-1 <https://stackoverflow.com/questions/312443/>`_].

    :param lst: List to be split.
    :type lst: list
    :param sub_len: Length of each sub-list.
    :type sub_len: int
    :return: A generator yielding sub-lists of length ``sub_len`` from ``lst``.
    :rtype: typing.Generator[list]

    **Examples**::

        >>> from pyhelpers.ops import split_list_by_size
        >>> lst_ = list(range(0, 10))
        >>> lst_
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> lists = split_list_by_size(lst_, sub_len=3)
        >>> list(lists)
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    """

    for i in range(0, len(lst), sub_len):
        yield lst[i:i + sub_len]


def split_list(lst, num_of_sub):
    """
    Splits a list into a specified number of equally-sized sub-lists.

    See also [`OPS-SL-1 <https://stackoverflow.com/questions/312443/>`_].

    :param lst: List to be split.
    :type lst: list
    :param num_of_sub: Number of sub-lists to create.
    :type num_of_sub: int
    :return: A generator yielding a total of ``num_of_sub`` sub-lists from ``lst``.
    :rtype: typing.Generator[list]

    **Examples**::

        >>> from pyhelpers.ops import split_list
        >>> lst_ = list(range(0, 10))
        >>> lst_
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> lists = split_list(lst_, num_of_sub=3)
        >>> list(lists)
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]
    """

    chunk_size = math.ceil(len(lst) / num_of_sub)
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def split_iterable(iterable, chunk_size):
    """
    Splits an iterable into evenly sized chunks.

    See also [`OPS-SI-1 <https://stackoverflow.com/questions/24527006/>`_].

    :param iterable: Iterable object to be split.
    :type iterable: typing.Iterable
    :param chunk_size: Size of each chunk.
    :type chunk_size: int
    :return: A generator yielding chunks of size ``chunk_size`` from ``iterable``.
    :rtype: typing.Generator[typing.Iterable]

    **Examples**::

        >>> from pyhelpers.ops import split_iterable
        >>> import pandas
        >>> iterable_1 = list(range(0, 10))
        >>> iterable_1
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> iterable_1_ = split_iterable(iterable_1, chunk_size=3)
        >>> type(iterable_1_)
        generator
        >>> for dat in iterable_1_:
        ...     print(list(dat))
        [0, 1, 2]
        [3, 4, 5]
        [6, 7, 8]
        [9]
        >>> iterable_2 = pandas.Series(range(0, 20))
        >>> iterable_2
        0      0
        1      1
        2      2
        3      3
        4      4
        5      5
        6      6
        7      7
        8      8
        9      9
        10    10
        11    11
        12    12
        13    13
        14    14
        15    15
        16    16
        17    17
        18    18
        19    19
        dtype: int64
        >>> iterable_2_ = split_iterable(iterable_2, chunk_size=5)
        >>> for dat in iterable_2_:
        ...     print(list(dat))
        [0, 1, 2, 3, 4]
        [5, 6, 7, 8, 9]
        [10, 11, 12, 13, 14]
        [15, 16, 17, 18, 19]
    """

    iterator = iter(iterable)
    for x in iterator:
        yield itertools.chain([x], itertools.islice(iterator, chunk_size - 1))


def update_dict(dictionary, updates, inplace=False):
    """
    Updates a (nested) dictionary with another dictionary.

    See also [`OPS-UD-1 <https://stackoverflow.com/questions/3232943/>`_].

    :param dictionary: The (nested) dictionary to be updated.
    :type dictionary: dict
    :param updates: The dictionary containing updates.
    :type updates: dict
    :param inplace: Whether to update the original ``dictionary`` in place; defaults to ``False``.
    :type inplace: bool
    :return: The updated dictionary.
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.ops import update_dict
        >>> source_dict = {'key_1': 1}
        >>> update_data = {'key_2': 2}
        >>> upd_dict = update_dict(source_dict, updates=update_data)
        >>> upd_dict
        {'key_1': 1, 'key_2': 2}
        >>> source_dict
        {'key_1': 1}
        >>> update_dict(source_dict, updates=update_data, inplace=True)
        >>> source_dict
        {'key_1': 1, 'key_2': 2}
        >>> source_dict = {'key': 'val_old'}
        >>> update_data = {'key': 'val_new'}
        >>> upd_dict = update_dict(source_dict, updates=update_data)
        >>> upd_dict
        {'key': 'val_new'}
        >>> source_dict = {'key': {'k1': 'v1_old', 'k2': 'v2'}}
        >>> update_data = {'key': {'k1': 'v1_new'}}
        >>> upd_dict = update_dict(source_dict, updates=update_data)
        >>> upd_dict
        {'key': {'k1': 'v1_new', 'k2': 'v2'}}
        >>> source_dict = {'key': {'k1': {}, 'k2': 'v2'}}
        >>> update_data = {'key': {'k1': 'v1'}}
        >>> upd_dict = update_dict(source_dict, updates=update_data)
        >>> upd_dict
        {'key': {'k1': 'v1', 'k2': 'v2'}}
        >>> source_dict = {'key': {'k1': 'v1', 'k2': 'v2'}}
        >>> update_data = {'key': {'k1': {}}}
        >>> upd_dict = update_dict(source_dict, updates=update_data)
        >>> upd_dict
        {'key': {'k1': 'v1', 'k2': 'v2'}}
    """

    if inplace:
        updated_dict = dictionary
    else:
        updated_dict = copy.copy(dictionary)

    for key, val in updates.items():
        if isinstance(val, collections.abc.Mapping) or isinstance(val, dict):
            try:
                updated_dict[key] = update_dict(dictionary.get(key, {}), val)
            except TypeError:
                updated_dict.update({key: val})

        elif isinstance(val, list):
            updated_dict[key] = (updated_dict.get(key, []) + val)

        else:
            updated_dict[key] = updates[key]

    if not inplace:
        return updated_dict

    return None


def update_dict_keys(dictionary, replacements=None):
    """
    Updates keys in a (nested) dictionary based on a given replacements dictionary.

    See also
    [`OPS-UDK-1 <https://stackoverflow.com/questions/4406501/>`_] and
    [`OPS-UDK-2 <https://stackoverflow.com/questions/38491318/>`_].

    :param dictionary: The (nested) dictionary in which certain keys are to be updated.
    :type dictionary: dict
    :param replacements: A dictionary in the form of ``{<current_key>: <new_key>}``
        describing which keys are to be updated; defaults to ``None``.
    :type replacements: dict | None
    :return: The dictionary with updated keys.
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.ops import update_dict_keys
        >>> source_dict = {'a': 1, 'b': 2, 'c': 3}
        >>> upd_dict = update_dict_keys(source_dict, replacements=None)
        >>> upd_dict  # remain unchanged
        {'a': 1, 'b': 2, 'c': 3}
        >>> repl_keys = {'a': 'd', 'c': 'e'}
        >>> upd_dict = update_dict_keys(source_dict, replacements=repl_keys)
        >>> upd_dict
        {'d': 1, 'b': 2, 'e': 3}
        >>> source_dict = {'a': 1, 'b': 2, 'c': {'d': 3, 'e': {'f': 4, 'g': 5}}}
        >>> repl_keys = {'d': 3, 'f': 4}
        >>> upd_dict = update_dict_keys(source_dict, replacements=repl_keys)
        >>> upd_dict
        {'a': 1, 'b': 2, 'c': {3: 3, 'e': {4: 4, 'g': 5}}}
    """

    if replacements is None:
        updated_dict = dictionary.copy()

    else:
        updated_dict = {}

        if isinstance(dictionary, list):
            updated_dict = list()
            for x in dictionary:
                updated_dict.append(update_dict_keys(x, replacements))

        else:
            for k in dictionary.keys():
                v = dictionary[k]
                k_ = replacements.get(k, k)

                if isinstance(v, (dict, list)):
                    updated_dict[k_] = update_dict_keys(v, replacements)
                else:
                    updated_dict[k_] = v

    return updated_dict


def get_dict_values(key, dictionary):
    """
    Retrieves all values in a (nested) dictionary for a given key.

    See also
    [`OPS-GDV-1 <https://gist.github.com/douglasmiranda/5127251>`_] and
    [`OPS-GDV-2 <https://stackoverflow.com/questions/9807634/>`_].

    :param key: The key to search for in the dictionary.
    :type key: any
    :param dictionary: The (nested) dictionary to search within.
    :type dictionary: dict
    :return: A generator yielding all values associated with the given ``key``
        within the ``dictionary``.
    :rtype: typing.Generator[typing.Iterable]

    **Examples**::

        >>> from pyhelpers.ops import get_dict_values
        >>> key_ = 'key'
        >>> target_dict_ = {'key': 'val'}
        >>> val = get_dict_values(key_, target_dict_)
        >>> list(val)
        [['val']]
        >>> key_ = 'k1'
        >>> target_dict_ = {'key': {'k1': 'v1', 'k2': 'v2'}}
        >>> val = get_dict_values(key_, target_dict_)
        >>> list(val)
        [['v1']]
        >>> key_ = 'k1'
        >>> target_dict_ = {'key': {'k1': ['v1', 'v1_1']}}
        >>> val = get_dict_values(key_, target_dict_)
        >>> list(val)
        [['v1', 'v1_1']]
        >>> key_ = 'k2'
        >>> target_dict_ = {'key': {'k1': 'v1', 'k2': ['v2', 'v2_1']}}
        >>> val = get_dict_values(key_, target_dict_)
        >>> list(val)
        [['v2', 'v2_1']]
    """

    for k, v in dictionary.items():
        if key == k:
            yield [v] if isinstance(v, str) else v

        elif isinstance(v, dict):
            for x in get_dict_values(key, v):
                yield x

        elif isinstance(v, collections.abc.Iterable):
            for d in v:
                if isinstance(d, dict):
                    for y in get_dict_values(key, d):
                        yield y


def remove_dict_keys(dictionary, *keys):
    """
    Removes multiple keys from a dictionary.

    :param dictionary: The dictionary from which keys should be removed.
    :type dictionary: dict
    :param keys: The keys to be removed from the dictionary.

    **Examples**::

        >>> from pyhelpers.ops import remove_dict_keys
        >>> target_dict_ = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'k4': 'v4', 'k5': 'v5'}
        >>> remove_dict_keys(target_dict_, 'k1', 'k3', 'k4')
        >>> target_dict_
        {'k2': 'v2', 'k5': 'v5'}
    """

    # assert isinstance(dictionary, dict)
    for k in keys:
        if k in dictionary.keys():
            dictionary.pop(k)


def compare_dicts(dict1, dict2):
    """
    Compares the differences between two dictionaries.

    See also [`OPS-CD-1 <https://stackoverflow.com/questions/23177439>`_].

    :param dict1: The first dictionary for comparison.
    :type dict1: dict
    :param dict2: The second dictionary for comparison.
    :type dict2: dict
    :return: A tuple containing the main differences between ``dict1`` and ``dict2``:
        modified items, common keys with different values,
        unchanged keys (same value in both dictionaries), new keys added in ``dict2`` and
        keys removed from ``dict1``.
    :rtype: tuple

    **Examples**::

        >>> from pyhelpers.ops import compare_dicts
        >>> d1 = {'a': 1, 'b': 2, 'c': 3}
        >>> d2 = {'b': 2, 'c': 4, 'd': [5, 6]}
        >>> items_modified, k_shared, k_unchanged, k_new, k_removed = compare_dicts(d1, d2)
        >>> items_modified
        {'c': [3, 4]}
        >>> k_shared
        ['b', 'c']
        >>> k_unchanged
        ['b']
        >>> k_new
        ['d']
        >>> k_removed
        ['a']
    """

    dk1, dk2 = map(lambda x: set(x.keys()), (dict1, dict2))

    shared_keys = dk1.intersection(dk2)

    added_keys, removed_keys = list(dk2 - dk1), list(dk1 - dk2)

    modified_items = {k: [dict1[k], dict2[k]] for k in shared_keys if dict1[k] != dict2[k]}
    unchanged_keys = list(set(k for k in shared_keys if dict1[k] == dict2[k]))

    return modified_items, list(shared_keys), unchanged_keys, added_keys, removed_keys


def merge_dicts(*dicts):
    """
    Merges multiple dictionaries into a single dictionary.

    :param dicts: One or multiple dictionaries to merge.
    :type dicts: dict
    :return: A dictionary containing all elements from the input dictionaries.
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.ops import merge_dicts
        >>> dict_a = {'a': 1}
        >>> dict_b = {'b': 2}
        >>> dict_c = {'c': 3}
        >>> merged_dict = merge_dicts(dict_a, dict_b, dict_c)
        >>> merged_dict
        {'a': 1, 'b': 2, 'c': 3}
        >>> dict_c_ = {'c': 4}
        >>> merged_dict = merge_dicts(merged_dict, dict_c_)
        >>> merged_dict
        {'a': 1, 'b': 2, 'c': [3, 4]}
        >>> dict_1 = merged_dict
        >>> dict_2 = {'b': 2, 'c': 4, 'd': [5, 6]}
        >>> merged_dict = merge_dicts(dict_1, dict_2)
        >>> merged_dict
        {'a': 1, 'b': 2, 'c': [[3, 4], 4], 'd': [5, 6]}
    """

    new_dict = {}
    for d in dicts:
        d_ = d.copy()
        # dk1, dk2 = map(lambda x: set(x.keys()), (new_dict, d_))
        # modified = {k: [new_dict[k], d_[k]] for k in dk1.intersection(dk2) if new_dict[k] != d_[k]}
        modified_items, _, _, _, _, = compare_dicts(new_dict, d_)

        if bool(modified_items):
            new_dict.update(modified_items)
            for k_ in modified_items.keys():
                remove_dict_keys(d_, k_)

        new_dict.update(d_)

    return new_dict


# ==================================================================================================
# Tabular data
# ==================================================================================================

def detect_nan_for_str_column(data_frame, column_names=None):
    """
    Detects if a column with string type contains ``NaN`` values for a given dataframe.

    :param data_frame: A dataframe to be examined.
    :type data_frame: pandas.DataFrame
    :param column_names: A sequence of column names to check;
        if ``column_names=None`` (default), all columns are checked.
    :type column_names: collections.abc.Iterable | None
    :return: Generator yielding position index of columns that contain ``NaN``.
    :rtype: typing.Generator

    **Examples**::

        >>> from pyhelpers.ops import detect_nan_for_str_column
        >>> from pyhelpers._cache import example_dataframe
        >>> dat = example_dataframe()
        >>> dat
                    Easting  Northing
        City
        London       530034    180381
        Birmingham   406689    286822
        Manchester   383819    398052
        Leeds        582044    152953
        >>> dat.loc['Leeds', 'Latitude'] = None
        >>> dat
                    Easting  Northing
        City
        London       530034  180381.0
        Birmingham   406689  286822.0
        Manchester   383819  398052.0
        Leeds        582044       NaN
        >>> nan_col_pos = detect_nan_for_str_column(data_frame=dat, column_names=None)
        >>> list(nan_col_pos)
        [1]
    """

    if column_names is None:
        column_names = data_frame.columns

    for x in column_names:
        temp = [str(v) for v in data_frame[x].unique() if isinstance(v, str) or np.isnan(v)]
        if 'nan' in temp:
            yield data_frame.columns.get_loc(x)


def create_rotation_matrix(theta):
    """
    Creates a 2D rotation matrix for counterclockwise rotation.

    :param theta: Rotation angle in radians.
    :type theta: float | int
    :return: Rotation matrix of shape (2, 2).
    :rtype: numpy.ndarray

    .. note::

        - The rotation matrix is defined as:

            .. code-block:: python

                [[cos(theta), -sin(theta)],
                 [sin(theta), cos(theta)]]

        - For counterclockwise rotation, the matrix rotates points in the positive direction
          (i.e. the positive x-axis rotates towards the positive y-axis).

    **Examples**::

        >>> from pyhelpers.ops import create_rotation_matrix
        >>> rot_mat = create_rotation_matrix(theta=30)
        >>> rot_mat
        array([[-0.98803162,  0.15425145],
               [-0.15425145, -0.98803162]])
    """

    sin_theta, cos_theta = np.sin(theta), np.cos(theta)

    rotation_mat = np.array([[sin_theta, cos_theta], [-cos_theta, sin_theta]])

    return rotation_mat


def dict_to_dataframe(input_dict, k='key', v='value'):
    """
    Converts a dictionary to a dataframe.

    :param input_dict: Dictionary to be converted to a dataframe.
    :type input_dict: dict
    :param k: Column name for keys; defaults to ``'key'``.
    :type k: str
    :param v: Column name for values; defaults to ``'value'``.
    :type v: str
    :return: Dataframe converted from the input dictionary.
    :rtype: pandas.DataFrame

    **Examples**::

        >>> from pyhelpers.ops import dict_to_dataframe
        >>> test_dict = {'a': 1, 'b': 2}
        >>> dat = dict_to_dataframe(input_dict=test_dict)
        >>> dat
          key  value
        0   a      1
        1   b      2
    """

    dict_keys = list(input_dict.keys())
    dict_vals = list(input_dict.values())

    data_frame = pd.DataFrame({k: dict_keys, v: dict_vals})

    return data_frame


def swap_cols(array, c1, c2, as_list=False):
    """
    Swaps positions of two columns in an array.

    :param array: An array.
    :type array: numpy.ndarray
    :param c1: Index of the first (i.e. the ``c1``-th) column to swap.
    :type c1: int
    :param c2: Index of the second (i.e. the ``c2``-th) column to swap.
    :type c2: int
    :param as_list: Whether to return a list instead of an array; defaults to ``False``.
    :type as_list: bool
    :return: A new array or list
        where the positions of the ``c1``-th and ``c2``-th columns are swapped.
    :rtype: numpy.ndarray | list

    **Examples**::

        >>> from pyhelpers.ops import swap_cols
        >>> from pyhelpers._cache import example_dataframe
        >>> example_arr = example_dataframe(osgb36=True).to_numpy(dtype=int)
        >>> example_arr
        array([[530039, 180371],
               [406705, 286868],
               [383830, 398113],
               [430147, 433553]])
        >>> # Swap the 0th and 1st columns
        >>> new_arr = swap_cols(example_arr, c1=0, c2=1)
        >>> new_arr
        array([[180371, 530039],
               [286868, 406705],
               [398113, 383830],
               [433553, 430147]])
        >>> new_list = swap_cols(example_arr, c1=0, c2=1, as_list=True)
        >>> new_list
        [[180371, 530039], [286868, 406705], [398113, 383830], [433553, 430147]]
    """

    array_ = array.copy()
    array_[:, c1], array_[:, c2] = array[:, c2], array[:, c1]

    if as_list:
        array_ = array_.tolist()

    return array_


def swap_rows(array, r1, r2, as_list=False):
    """
    Swaps positions of two rows in an array.

    :param array: An array.
    :type array: numpy.ndarray
    :param r1: Index of the first (i.e. the ``r1``-th) row to swap.
    :type r1: int
    :param r2: Index of the second (i.e. the ``r2``-th) row to swap.
    :type r2: int
    :param as_list: Whether to return a list instead of an array; defaults to ``False``.
    :type as_list: bool
    :return: A new array or list
        where the positions of the ``r1``-th and ``r2``-th rows are swapped.
    :rtype: numpy.ndarray | list

    **Examples**::

        >>> from pyhelpers.ops import swap_rows
        >>> from pyhelpers._cache import example_dataframe
        >>> example_arr = example_dataframe(osgb36=True).to_numpy(dtype=int)
        >>> example_arr
        array([[406705, 286868],
               [530039, 180371],
               [383830, 398113],
               [430147, 433553]])
        >>> # Swap the 0th and 1st rows
        >>> new_arr = swap_rows(example_arr, r1=0, r2=1)
        >>> new_arr
        array([[406705, 286868],
               [530039, 180371],
               [383830, 398113],
               [430147, 433553]])
        >>> new_list = swap_rows(example_arr, r1=0, r2=1, as_list=True)
        >>> new_list
        [[406705, 286868], [530039, 180371], [383830, 398113], [430147, 433553]]
    """

    array_ = array.copy()
    array_[r1, :], array_[r2, :] = array[r2, :], array[r1, :]

    if as_list:
        array_ = array_.tolist()

    return array_


def np_shift(array, step, fill_value=np.nan):
    """
    Shifts an array by a desired number of rows.

    See also [`OPS-NS-1 <https://stackoverflow.com/questions/30399534/>`_].

    :param array: An array of numbers.
    :type array: numpy.ndarray
    :param step: Number of rows to shift. Positive value shifts downwards; negative shifts upwards.
    :type step: int
    :param fill_value: Value to fill missing rows due to the shift; defaults to ``NaN``.
    :type fill_value: float | int
    :return: Shifted array.
    :rtype: numpy.ndarray

    **Examples**::

        >>> from pyhelpers.ops import np_shift
        >>> from pyhelpers._cache import example_dataframe
        >>> arr = example_dataframe(osgb36=True).to_numpy()
        >>> arr
        array([[530039.5588445, 180371.6801655],
               [406705.8870136, 286868.1666422],
               [383830.0390357, 398113.0558309],
               [430147.4473539, 433553.3271173]])
        >>> np_shift(arr, step=-1)
        array([[406705.8870136, 286868.1666422],
               [383830.0390357, 398113.0558309],
               [430147.4473539, 433553.3271173],
               [           nan,            nan]])
        >>> np_shift(arr, step=1, fill_value=0)
        array([[     0,      0],
               [530039, 180371],
               [406705, 286868],
               [383830, 398113]])
    """

    result = np.empty_like(array, dtype=type(fill_value))  # np.zeros_like(array)

    if step > 0:
        result[:step] = fill_value
        result[step:] = array[:-step]

    elif step < 0:
        result[step:] = fill_value
        result[:step] = array[-step:]

    else:
        result[:] = array

    return result


# noinspection PyUnresolvedReferences
@_lazy_check_dependencies(polars='pl')
def downcast_numeric_columns(*dataframes):
    # noinspection PyShadowingNames
    """
    Downcasts numeric columns in pandas DataFrames to optimal dtypes to reduce memory usage.

    This function processes multiple DataFrames in one pass, converting:
        - Integer columns to the smallest signed integer dtype (int8, int16, int32, or int64)
        - Floating-point columns to the smallest floating dtype (float32 or float64)
          that can safely represent their values.

    :param dataframes: One or more pandas DataFrames to optimize
    :type dataframes: pandas.DataFrame | polars.DataFrame
    :return: New DataFrame(s) with downcasted numeric columns.
    :rtype: None | pandas.DataFrame | polars.DataFrame | tuple[pandas.DataFrame | polars.DataFrame]

    .. note::

        - Modifies DataFrames in place for memory efficiency.
        - Skips non-numeric columns automatically.
        - Uses pandas' built-in optimisations for batch processing.

    **Examples**::

        >>> from pyhelpers.ops import downcast_numeric_columns
        >>> from pyhelpers._cache import example_dataframe
        >>> import polars as pl
        >>> df1 = example_dataframe().copy()
        >>> df1.dtypes
        Longitude    float64
        Latitude     float64
        dtype: object
        >>> df2 = example_dataframe().T.copy()
        >>> df2.dtypes
        City
        London        float64
        Birmingham    float64
        Manchester    float64
        Leeds         float64
        dtype: object

        >>> df11, df21 = downcast_numeric_columns(df1, df2)
        >>> df11.dtypes
        Longitude    float32
        Latitude     float32
        dtype: object
        >>> df21.dtypes
        City
        London        float32
        Birmingham    float32
        Manchester    float32
        Leeds         float32
        dtype: object

        >>> df1, df2 = map(pl.from_pandas, (df1, df2))
        >>> df1.dtypes
        [Float64, Float64]
        >>> df2.dtypes
        [Float64, Float64, Float64, Float64]
        >>> df21, df22 = downcast_numeric_columns(df1, df2)
        >>> df21.dtypes
        [Float32, Float32]
        >>> df22.dtypes
        [Float32, Float32, Float32, Float32]
        """

    results = []

    for df in dataframes:
        if isinstance(df, pd.DataFrame):
            df_ = df.copy()
            # Process all integer columns
            int_cols = df_.select_dtypes(include=['integer']).columns
            if not int_cols.empty:
                df_[int_cols] = df_[int_cols].apply(pd.to_numeric, downcast='integer')

            # Process all float columns
            float_cols = df_.select_dtypes(include=['floating']).columns
            if not float_cols.empty:
                df_[float_cols] = df_[float_cols].apply(pd.to_numeric, downcast='float')

            results.append(df_)

        elif isinstance(df, pl.DataFrame):  # Handle polars DataFrames
            df_ = df.clone()
            # Process integer columns
            int_cols = [col for col in df.columns if df[col].dtype.is_integer()]
            if int_cols:
                df_ = df_.with_columns([pl.col(col).shrink_dtype() for col in int_cols])

            # Process float columns
            float_cols = [col for col in df.columns if df[col].dtype.is_float()]
            if float_cols:
                df_ = df_.with_columns([pl.col(col).shrink_dtype() for col in float_cols])

            results.append(df_)

        else:
            raise TypeError(f"Unsupported DataFrame type: {type(df)}")

    return results[0] if len(results) == 1 else tuple(results)


def flatten_columns(columns, ignore_linear_level=False):
    """
    Flattens multi-level column names into single-level strings.

    This function processes column names (either as tuples or lists of strings) by joining them with
    underscores; optionally, it simplifies column names when they represent linear hierarchies.

    :param columns: Iterable of multi-level column names (each column is a sequence of strings).
    :type columns: Iterable[Sequence[str]]
    :param ignore_linear_level: If ``ignore_linear_level=True``,
        the function simplifies linear hierarchies by omitting single-child levels;
        defaults to ``False``.
    :type ignore_linear_level: bool
    :return: List of flattened column names.
    :rtype: List[str]

    .. note::

        - For MultiIndex columns, passes the result of ``df.columns.tolist()``.
        - When ``ignore_linear_level=True``, parent levels with only one child are collapsed.
        - Preserves original order of columns.

    **Examples**::

        >>> from pyhelpers.ops import flatten_columns
        >>> flatten_columns([('A', 'B'), ('A', 'C')])
        ['A_B', 'A_C']
        >>> flatten_columns([('A', 'B', 'C'), ('A', 'B', 'D')], ignore_linear_level=True)
        ['A_B_C', 'A_B_D']
        >>> flatten_columns([('A', 'C'), ('B', 'C')], ignore_linear_level=True)
        ['A', 'B']
        >>> flatten_columns([('A',), ('B', 'C')], ignore_linear_level=True)
        ['A', 'B']
    """

    if not ignore_linear_level:
        return ['_'.join(col) for col in columns]

    col_groups = collections.defaultdict(list)
    for col in columns:
        if len(col) < 2:
            col_groups[col].append(None)  # Single-level columns stay as-is
            continue
        parent_levels, last_level = col[:-1], col[-1]
        col_groups[parent_levels].append(last_level)

    # Build new column names
    flattened_columns = []
    for col in columns:
        if len(col) < 2:
            flattened_columns.append(col[0])
            continue

        parent_levels = col[:-1]
        if len(col_groups[parent_levels]) == 1:
            # Join parent levels only if multiple exist
            name = '_'.join(parent_levels) if len(parent_levels) > 1 else parent_levels[0]
            flattened_columns.append(name)
        else:
            flattened_columns.append('_'.join(col))

    return flattened_columns


# ==================================================================================================
# Graph plotting
# ==================================================================================================

def cmap_discretisation(cmap, n_colours):
    # noinspection PyShadowingNames
    """
    Creates a discrete colour ramp.

    See also [`OPS-CD-1
    <https://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: A colormap instance, e.g. built-in `colormaps`_ available via
        `matplotlib.colormaps.get_cmap`_.
    :type cmap:
        matplotlib.colors.ListedColormap | matplotlib.colors.LinearSegmentedColormap |
        matplotlib.colors.Colormap | str
    :param n_colours: Number of colours to discretise the colormap.
    :type n_colours: int
    :return: A discrete colormap derived from the continuous ``cmap``.
    :rtype: matplotlib.colors.LinearSegmentedColormap

    .. _`colormaps`:
        https://matplotlib.org/stable/tutorials/colors/colormaps.html
    .. _`matplotlib.colormaps.get_cmap`:
        https://matplotlib.org/stable/api/cm_api.html#matplotlib.cm.ColormapRegistry.get_cmap

    **Examples**::

        >>> from pyhelpers.ops import cmap_discretisation
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np
        >>> mpl_preferences()
        >>> cm_accent = cmap_discretisation(cmap=matplotlib.colormaps['Accent'], n_colours=5)
        >>> cm_accent.name
        'Accent_5'
        >>> cm_accent = cmap_discretisation(cmap='Accent', n_colours=5)
        >>> cm_accent.name
        'Accent_5'
        >>> fig = plt.figure(figsize=(10, 2), constrained_layout=True)
        >>> ax = fig.add_subplot()
        >>> ax.imshow(np.resize(range(100), (5, 100)), cmap=cm_accent, interpolation='nearest')
        >>> ax.axis('off')
        >>> fig.show()
        >>> # from pyhelpers.store import save_figure
        >>> # path_to_fig_ = "docs/source/_images/ops-cmap_discretisation-demo"
        >>> # save_figure(fig, f"{path_to_fig_}.svg", verbose=True)
        >>> # save_figure(fig, f"{path_to_fig_}.pdf", verbose=True)

    The exmaple is illustrated in :numref:`ops-cmap_discretisation-demo`:

    .. figure:: ../_images/ops-cmap_discretisation-demo.*
        :name: ops-cmap_discretisation-demo
        :align: center
        :width: 60%

        An example of discrete colour ramp, created by the function
        :func:`~pyhelpers.ops.cmap_discretisation`.
    """

    mpl, mpl_colors = _check_dependencies('matplotlib', 'matplotlib.colors')

    if isinstance(cmap, str):
        cmap_ = mpl.colormaps[cmap]
    else:
        cmap_ = cmap

    colours_ = np.concatenate((np.linspace(0, 1., n_colours), (0., 0., 0., 0.)))
    # noinspection PyTypeChecker
    colours_rgba = cmap_(colours_)
    indices = np.linspace(0, 1., n_colours + 1)
    c_dict = {}

    for ki, key in enumerate(('red', 'green', 'blue')):
        c_dict[key] = [
            (indices[x], colours_rgba[x - 1, ki], colours_rgba[x, ki])
            for x in range(n_colours + 1)]

    colour_map = mpl_colors.LinearSegmentedColormap(cmap_.name + '_%d' % n_colours, c_dict, 1024)

    return colour_map


def colour_bar_index(cmap, n_colours, labels=None, **kwargs):
    """
    Creates a colour bar with correctly aligned labels.

    .. note::

        - To avoid off-by-one errors, this function takes a standard colour ramp,
          discretizes it, and then draws a colour bar with labels aligned correctly.
        - See also [`OPS-CBI-1
          <https://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html
          #.WbpP0T6GNQB>`_].

    :param cmap: A colormap instance,
        e.g. built-in `colormaps`_ accessible via `matplotlib.cm.get_cmap()`_.
    :type cmap: matplotlib.colors.ListedColormap | matplotlib.colors.Colormap
    :param n_colours: Number of discrete colours to use in the colour bar.
    :type n_colours: int
    :param labels: Optional list of labels for the colour bar; defaults to ``None``.
    :type labels: list | None
    :param kwargs: [Optional] Additional optional parameters for the funtion
        `matplotlib.pyplot.colorbar()`_.
    :return: A colour bar object.
    :rtype: matplotlib.colorbar.Colorbar

    .. _`colormaps`:
        https://matplotlib.org/tutorials/colors/colormaps.html
    .. _`matplotlib.cm.get_cmap()`:
        https://matplotlib.org/api/cm_api.html#matplotlib.cm.get_cmap
    .. _`matplotlib.pyplot.colorbar()`:
        https://matplotlib.org/api/_as_gen/matplotlib.pyplot.colorbar.html

    **Examples**::

        >>> from pyhelpers.ops import colour_bar_index
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt
        >>> mpl_preferences()
        >>> fig1 = plt.figure(figsize=(2, 6), constrained_layout=True)
        >>> ax1 = fig1.add_subplot()
        >>> cbar1 = colour_bar_index(cmap=plt.colormaps['Accent'], n_colours=5)
        >>> ax1.tick_params(axis='both', which='major', labelsize=14)
        >>> cbar1.ax.tick_params(labelsize=14)
        >>> # ax.axis('off')
        >>> fig1.show()
        >>> # from pyhelpers.store import save_figure
        >>> # path_to_fig1_ = "docs/source/_images/ops-colour_bar_index-demo-1"
        >>> # save_figure(fig1, f"{path_to_fig1_}.svg", verbose=True)
        >>> # save_figure(fig1, f"{path_to_fig1_}.pdf", verbose=True)

    The above example is illustrated in :numref:`ops-colour_bar_index-demo-1`:

    .. figure:: ../_images/ops-colour_bar_index-demo-1.*
        :name: ops-colour_bar_index-demo-1
        :align: center
        :width: 32%

        An example of colour bar with numerical index.

    .. code-block:: python

        >>> fig2 = plt.figure(figsize=(2, 6), constrained_layout=True)
        >>> ax2 = fig2.add_subplot()
        >>> labels_ = list('abcde')
        >>> cbar2 = colour_bar_index(cmap=plt.colormaps['Accent'], n_colours=5, labels=labels_)
        >>> ax2.tick_params(axis='both', which='major', labelsize=14)
        >>> cbar2.ax.tick_params(labelsize=14)
        >>> # ax.axis('off')
        >>> fig2.show()
        >>> # path_to_fig2_ = "docs/source/_images/ops-colour_bar_index-demo-2"
        >>> # save_figure(fig2, f"{path_to_fig2_}.svg", verbose=True)
        >>> # save_figure(fig2, f"{path_to_fig2_}.pdf", verbose=True)

    This second example is illustrated in :numref:`ops-colour_bar_index-demo-2`:

    .. figure:: ../_images/ops-colour_bar_index-demo-2.*
        :name: ops-colour_bar_index-demo-2
        :align: center
        :width: 32%

        An example of colour bar with textual index.
    """

    mpl_cm, mpl_plt = _check_dependencies('matplotlib.cm', 'matplotlib.pyplot')

    # assert isinstance(cmap, mpl_cm.ListedColormap)
    cmap_ = cmap_discretisation(cmap, n_colours)

    mappable = mpl_cm.ScalarMappable(cmap=cmap_)
    mappable.set_array(np.array([]))
    mappable.set_clim(-0.5, n_colours + 0.5)

    colour_bar = mpl_plt.colorbar(mappable=mappable, ax=mpl_plt.gca(), **kwargs)
    colour_bar.set_ticks(np.linspace(0, n_colours, n_colours))
    colour_bar.set_ticklabels(range(n_colours))

    if labels:
        colour_bar.set_ticklabels(labels)

    return colour_bar
