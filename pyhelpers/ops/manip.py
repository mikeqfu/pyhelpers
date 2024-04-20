"""
Basic data manipulation.
"""

import collections.abc
import copy
import itertools
import math

import numpy as np
import pandas as pd

from .._cache import _check_dependency, _check_rel_pathname, _print_failure_msg


# Iterable

def loop_in_pairs(iterable):
    """
    Get every pair (current, next).

    :param iterable: iterable object
    :type iterable: typing.Iterable
    :return: a `zip <https://docs.python.org/3.9/library/functions.html#zip>`_-type variable
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
    Split a list into (evenly sized) sub-lists.

    See also [`OPS-SLBS-1 <https://stackoverflow.com/questions/312443/>`_].

    :param lst: a list of any
    :type lst: list
    :param sub_len: length of a sub-list
    :type sub_len: int
    :return: a sequence of ``sub_len``-sized sub-lists from ``lst``
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
    Split a list into a number of equally-sized sub-lists.

    See also [`OPS-SL-1 <https://stackoverflow.com/questions/312443/>`_].

    :param lst: a list of any
    :type lst: list
    :param num_of_sub: number of sub-lists
    :type num_of_sub: int
    :return: a total of ``num_of_sub`` sub-lists from ``lst``
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
    Split a list into (evenly sized) chunks.

    See also [`OPS-SI-1 <https://stackoverflow.com/questions/24527006/>`_].

    :param iterable: iterable object
    :type iterable: typing.Iterable
    :param chunk_size: length of a chunk
    :type chunk_size: int
    :return: a sequence of equally-sized chunks from ``iterable``
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
    Update a (nested) dictionary or similar mapping.

    See also [`OPS-UD-1 <https://stackoverflow.com/questions/3232943/>`_].

    :param dictionary: a (nested) dictionary that needs to be updated
    :type dictionary: dict
    :param updates: a dictionary with new data
    :type updates: dict
    :param inplace: whether to replace the original ``dictionary`` with the updated one,
        defaults to ``False``
    :type inplace: bool
    :return: an updated dictionary
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


def update_dict_keys(dictionary, replacements=None):
    """
    Update keys in a (nested) dictionary.

    See also
    [`OPS-UDK-1 <https://stackoverflow.com/questions/4406501/>`_] and
    [`OPS-UDK-2 <https://stackoverflow.com/questions/38491318/>`_].

    :param dictionary: a (nested) dictionary in which certain keys are to be updated
    :type dictionary: dict
    :param replacements: a dictionary in the form of ``{<current_key>: <new_key>}``,
        describing which keys are to be updated, defaults to ``None``
    :type replacements: dict | None
    :return: an updated dictionary
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
    Get all values in a (nested) dictionary for a given key.

    See also
    [`OPS-GDV-1 <https://gist.github.com/douglasmiranda/5127251>`_] and
    [`OPS-GDV-2 <https://stackoverflow.com/questions/9807634/>`_].

    :param key: any that can be the key of a dictionary
    :type key: any
    :param dictionary: a (nested) dictionary
    :type dictionary: dict
    :return: all values of the ``key`` within the given ``target_dict``
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
    Remove multiple keys from a dictionary.

    :param dictionary: a dictionary
    :type dictionary: dict
    :param keys: (a sequence of) any that can be the key of a dictionary
    :type keys: any

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
    Compare the difference between two dictionaries.

    See also [`OPS-CD-1 <https://stackoverflow.com/questions/23177439>`_].

    :param dict1: a dictionary
    :type dict1: dict
    :param dict2: another dictionary
    :type dict2: dict
    :return: in comparison to ``dict1``, the main difference on ``dict2``, including:
        modified items, keys that are the same, keys where values remain unchanged, new keys and
        keys that are removed
    :rtype: typing.Tuple[dict, list]

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
    Merge multiple dictionaries.

    :param dicts: (one or) multiple dictionaries
    :type dicts: dict
    :return: a single dictionary containing all elements of the input
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


# Tabular data

def detect_nan_for_str_column(data_frame, column_names=None):
    """
    Detect if a str type column contains ``NaN`` when reading csv files.

    :param data_frame: a data frame to be examined
    :type data_frame: pandas.DataFrame
    :param column_names: a sequence of column names, if ``None`` (default), all columns
    :type column_names: None | collections.abc.Iterable
    :return: position index of the column that contains ``NaN``
    :rtype: typing.Generator[typing.Iterable]

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
    Create a rotation matrix (counterclockwise).

    :param theta: rotation angle (in radian)
    :type theta: int | float
    :return: a rotation matrix of shape (2, 2)
    :rtype: numpy.ndarray

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
    Convert a dictionary to a data frame.

    :param input_dict: a dictionary to be converted to a data frame
    :type input_dict: dict
    :param k: column name for keys
    :type k: str
    :param v: column name for values
    :type v: str
    :return: a data frame converted from the ``input_dict``
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


def parse_csr_matrix(path_to_csr, verbose=False, **kwargs):
    """
    Load in a compressed sparse row (CSR) or compressed row storage (CRS).

    :param path_to_csr: path where a CSR file (e.g. with a file extension ".npz") is saved
    :type path_to_csr: str | os.PathLike
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``False``
    :type verbose: bool | int
    :param kwargs: [optional] parameters of `numpy.load`_
    :return: a compressed sparse row
    :rtype: scipy.sparse.csr.csr_matrix

    .. _`numpy.load`: https://numpy.org/doc/stable/reference/generated/numpy.load

    **Examples**::

        >>> from pyhelpers.ops import parse_csr_matrix
        >>> from pyhelpers.dirs import cd
        >>> from scipy.sparse import csr_matrix, save_npz

        >>> data_ = [1, 2, 3, 4, 5, 6]
        >>> indices_ = [0, 2, 2, 0, 1, 2]
        >>> indptr_ = [0, 2, 3, 6]

        >>> csr_m = csr_matrix((data_, indices_, indptr_), shape=(3, 3))
        >>> csr_m
        <3x3 sparse matrix of type '<class 'numpy.int32'>'
            with 6 stored elements in Compressed Sparse Row format>

        >>> path_to_csr_npz = cd("tests\\data", "csr_mat.npz")
        >>> save_npz(path_to_csr_npz, csr_m)

        >>> parsed_csr_mat = parse_csr_matrix(path_to_csr_npz, verbose=True)
        Loading "\\tests\\data\\csr_mat.npz" ... Done.

        >>> # .nnz gets the count of explicitly-stored values (non-zeros)
        >>> (parsed_csr_mat != csr_m).count_nonzero() == 0
        True

        >>> (parsed_csr_mat != csr_m).nnz == 0
        True
    """

    scipy_sparse = _check_dependency(name='scipy.sparse')

    if verbose:
        rel_path_to_csr = _check_rel_pathname(path_to_csr)
        print(f'Loading "\\{rel_path_to_csr}"', end=" ... ")

    try:
        csr_loader = np.load(path_to_csr, **kwargs)
        data = csr_loader['data']
        indices = csr_loader['indices']
        indptr = csr_loader['indptr']
        shape = csr_loader['shape']

        csr_mat = scipy_sparse.csr_matrix((data, indices, indptr), shape)

        if verbose:
            print("Done.")

        return csr_mat

    except Exception as e:
        _print_failure_msg(e, msg="Failed.", verbose=verbose)


def swap_cols(array, c1, c2, as_list=False):
    """
    Swap positions of two columns in an array.

    :param array: an array
    :type array: numpy.ndarray
    :param c1: index of a column
    :type c1: int
    :param c2: index of another column
    :type c2: int
    :param as_list: whether to return a list
    :type as_list: bool
    :return: a new array/list in which the positions of the c1-th and c2-th columns are swapped
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
    Swap positions of two rows in an array.

    :param array: an array
    :type array: numpy.ndarray
    :param r1: index of a row
    :type r1: int
    :param r2: index of another row
    :type r2: int
    :param as_list: whether to return a list
    :type as_list: bool
    :return: a new array/list in which the positions of the r1-th and r2-th rows are swapped
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
    Shift an array by desired number of rows.

    See also [`OPS-NS-1 <https://stackoverflow.com/questions/30399534/>`_]

    :param array: an array of numbers
    :type array: numpy.ndarray
    :param step: number of rows to shift
    :type step: int
    :param fill_value: values to fill missing rows due to the shift, defaults to ``NaN``
    :type fill_value: float | int
    :return: shifted array
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


# Graph plotting

def cmap_discretisation(cmap, n_colours):
    # noinspection PyShadowingNames
    """
    Create a discrete colour ramp.

    See also [`OPS-CD-1
    <https://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: a colormap instance,
        e.g. built-in `colormaps`_ that is available via `matplotlib.colormaps.get_cmap`_
    :type cmap: matplotlib.colors.ListedColormap | matplotlib.colors.LinearSegmentedColormap | str
    :param n_colours: number of colours
    :type n_colours: int
    :return: a discrete colormap from (the continuous) ``cmap``
    :rtype: matplotlib.colors.LinearSegmentedColormap

    .. _`colormaps`: https://matplotlib.org/stable/tutorials/colors/colormaps.html
    .. _`matplotlib.colormaps.get_cmap`:
        https://matplotlib.org/stable/api/cm_api.html#matplotlib.cm.ColormapRegistry.get_cmap

    **Examples**::

        >>> from pyhelpers.ops import cmap_discretisation
        >>> from pyhelpers.settings import mpl_preferences

        >>> mpl_preferences(backend='TkAgg', font_name='Times New Roman')

        >>> import matplotlib
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np

        >>> cm_accent = cmap_discretisation(cmap=matplotlib.colormaps['Accent'], n_colours=5)
        >>> cm_accent.name
        'Accent_5'
        >>> cm_accent = cmap_discretisation(cmap='Accent', n_colours=5)
        >>> cm_accent.name
        'Accent_5'

        >>> fig = plt.figure(figsize=(10, 2), constrained_layout=True)
        >>> ax = fig.add_subplot()

        >>> ax.imshow(np.resize(range(100), (5, 100)), cmap=cm_accent, interpolation='nearest')

        >>> plt.axis('off')
        >>> plt.show()

    The exmaple is illustrated in :numref:`ops-cmap_discretisation-demo`:

    .. figure:: ../_images/ops-cmap_discretisation-demo.*
        :name: ops-cmap_discretisation-demo
        :align: center
        :width: 60%

        An example of discrete colour ramp, created by the function
        :func:`~pyhelpers.ops.cmap_discretisation`.

    .. code-block:: python

        >>> plt.close()
    """

    mpl, mpl_colors = map(_check_dependency, ['matplotlib', 'matplotlib.colors'])

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
            (indices[x], colours_rgba[x - 1, ki], colours_rgba[x, ki]) for x in range(n_colours + 1)]

    colour_map = mpl_colors.LinearSegmentedColormap(cmap_.name + '_%d' % n_colours, c_dict, 1024)

    return colour_map


def colour_bar_index(cmap, n_colours, labels=None, **kwargs):
    """
    Create a colour bar.

    To stop making off-by-one errors. Takes a standard colour ramp, and discretizes it,
    then draws a colour bar with correctly aligned labels.

    See also [`OPS-CBI-1
    <https://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: a colormap instance,
        e.g. built-in `colormaps`_ that is accessible via `matplotlib.cm.get_cmap`_
    :type cmap: matplotlib.colors.ListedColormap
    :param n_colours: number of colours
    :type n_colours: int
    :param labels: a list of labels for the colour bar, defaults to ``None``
    :type labels: list | None
    :param kwargs: [optional] parameters of `matplotlib.pyplot.colorbar`_
    :return: a colour bar object
    :rtype: matplotlib.colorbar.Colorbar

    .. _`colormaps`: https://matplotlib.org/tutorials/colors/colormaps.html
    .. _`matplotlib.cm.get_cmap`: https://matplotlib.org/api/cm_api.html#matplotlib.cm.get_cmap
    .. _`matplotlib.pyplot.colorbar`: https://matplotlib.org/api/_as_gen/matplotlib.pyplot.colorbar.html

    **Examples**::

        >>> from pyhelpers.ops import colour_bar_index
        >>> from pyhelpers.settings import mpl_preferences

        >>> mpl_preferences(backend='TkAgg', font_name='Times New Roman')

        >>> import matplotlib
        >>> import matplotlib.pyplot as plt

        >>> fig = plt.figure(figsize=(2, 6), constrained_layout=True)
        >>> ax = fig.add_subplot()

        >>> cbar = colour_bar_index(cmap=matplotlib.colormaps['Accent'], n_colours=5)

        >>> ax.tick_params(axis='both', which='major', labelsize=14)
        >>> cbar.ax.tick_params(labelsize=14)

        >>> # ax.axis('off')
        >>> plt.show()

    The above example is illustrated in :numref:`ops-colour_bar_index-demo-1`:

    .. figure:: ../_images/ops-colour_bar_index-demo-1.*
        :name: ops-colour_bar_index-demo-1
        :align: center
        :width: 23%

        An example of colour bar with numerical index,
        created by the function :func:`~pyhelpers.ops.colour_bar_index`.

    .. code-block:: python

        >>> fig = plt.figure(figsize=(2, 6), constrained_layout=True)
        >>> ax = fig.add_subplot()

        >>> labels_ = list('abcde')
        >>> cbar = colour_bar_index(matplotlib.colormaps['Accent'], n_colours=5, labels=labels_)

        >>> ax.tick_params(axis='both', which='major', labelsize=14)
        >>> cbar.ax.tick_params(labelsize=14)

        >>> # ax.axis('off')
        >>> plt.show()

    This second example is illustrated in :numref:`ops-colour_bar_index-demo-2`:

    .. figure:: ../_images/ops-colour_bar_index-demo-2.*
        :name: ops-colour_bar_index-demo-2
        :align: center
        :width: 23%

        An example of colour bar with textual index,
        created by the function :func:`~pyhelpers.ops.colour_bar_index`.

    .. code-block:: python

        >>> plt.close(fig='all')
    """

    mpl_cm, mpl_plt = map(_check_dependency, ['matplotlib.cm', 'matplotlib.pyplot'])

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
