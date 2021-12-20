"""
Miscellaneous operations.
"""

import ast
import collections.abc
import copy
import datetime
import html.parser
import inspect
import itertools
import json
import math
import os
import random
import re
import shutil
import socket
import sys
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd
import pkg_resources
import requests
import requests.adapters
import urllib3.util.retry

""" == General use =========================================================================== """


def confirmed(prompt=None, confirmation_required=True, resp=False):
    """
    Type to confirm whether to proceed or not.

    See also
    [`OPS-C-1 <https://code.activestate.com/recipes/541096-prompt-the-user-for-confirmation/>`_].

    :param prompt: a message that prompts a response (Yes/No), defaults to ``None``
    :type prompt: str or None
    :param confirmation_required: whether to require users to confirm and proceed, defaults to ``True``
    :type confirmation_required: bool
    :param resp: default response, defaults to ``False``
    :type resp: bool
    :return: a response
    :rtype: bool

    **Example**::

        >>> from pyhelpers.ops import confirmed

        >>> if confirmed(prompt="Testing if the function works?", resp=True):
        ...     print("Passed.")
        Testing if the function works? [Yes]|No: yes
        Passed.
    """

    if confirmation_required:
        if prompt is None:
            prompt_ = "Confirmed? "
        else:
            prompt_ = copy.copy(prompt)

        if resp is True:  # meaning that default response is True
            prompt_ = "{} [{}]|{}: ".format(prompt_, "Yes", "No")
        else:
            prompt_ = "{} [{}]|{}: ".format(prompt_, "No", "Yes")

        ans = input(prompt_)
        if not ans:
            return resp

        if re.match('[Yy](es)?', ans):
            return True
        if re.match('[Nn](o)?', ans):
            return False

    else:
        return True


def get_obj_attr(obj, col_names=None):
    """
    Get main attributes of an object.

    :param obj: an object, e.g. a class
    :type obj: object
    :param col_names: a list of column names
    :type col_names: list
    :return: tabular data of the main attributes of the given object
    :rtype: pandas.DataFrame

    **Examples**::

        >>> from pyhelpers.ops import get_obj_attr
        >>> from pyhelpers.sql import PostgreSQL

        >>> postgres = PostgreSQL('localhost', 5432, 'postgres', database_name='postgres')
        Password (postgres@localhost:5432): ***
        Connecting postgres:***@localhost:5432/postgres ... Successfully.

        >>> obj_attr = get_obj_attr(postgres)
        >>> obj_attr.head()
               Attribute                                 Value
        0  DATABASE_NAME                              postgres
        1           HOST                             localhost
        2           PORT                                  5432
        3       USERNAME                              postgres
        4        address  postgres:***@localhost:5432/postgres

        >>> obj_attr.Attribute.to_list()
        ['DATABASE_NAME',
         'HOST',
         'PORT',
         'USERNAME',
         'address',
         'backend',
         'database_info',
         'database_name',
         'dialect',
         'driver',
         'engine',
         'host',
         'port',
         'url',
         'user']
    """

    if col_names is None:
        col_names = ['Attribute', 'Value']

    all_attrs = inspect.getmembers(obj, lambda x: not (inspect.isroutine(x)))

    attrs = [x for x in all_attrs if not re.match(r'^__?', x[0])]

    attrs_tbl = pd.DataFrame(attrs, columns=col_names)

    return attrs_tbl


def eval_dtype(str_val):
    """
    Convert a string to its intrinsic data type.

    :param str_val: a string-type variable
    :type str_val: str
    :return: converted value
    :rtype: any

    **Examples**::

        >>> from pyhelpers.ops import eval_dtype

        >>> val_1 = '1'
        >>> origin_val = eval_dtype(val_1)
        >>> origin_val
        1

        >>> val_2 = '1.1.1'
        >>> origin_val = eval_dtype(val_2)
        >>> origin_val
        '1.1.1'
    """

    try:
        val = ast.literal_eval(str_val)
    except (ValueError, SyntaxError):
        val = str_val

    return val


def gps_to_utc(gps_time):
    """
    Convert standard GPS time to UTC time.

    :param gps_time: standard GPS time
    :type gps_time: float
    :return: UTC time
    :rtype: datetime.datetime

    **Example**::

        >>> from pyhelpers.ops import gps_to_utc

        >>> utc_dt = gps_to_utc(gps_time=1271398985.7822514)
        >>> utc_dt
        datetime.datetime(2020, 4, 20, 6, 23, 5, 782251)
    """

    gps_from_utc = (datetime.datetime(1980, 1, 6) - datetime.datetime(1970, 1, 1)).total_seconds()

    utc_time = datetime.datetime.utcfromtimestamp(gps_time + gps_from_utc)

    return utc_time


def parse_size(size, binary=True, precision=1):
    """
    Parse size from / into readable format of bytes.

    :param size: human- or machine-readable format of size
    :type size: str or int or float
    :param binary: whether to use binary (i.e. factorized by 1024) representation, defaults to ``True``;
        if ``binary=False``, use the decimal (or metric) representation (i.e. factorized by 10 ** 3)
    :type binary: bool
    :param precision: number of decimal places (when converting ``size`` to human-readable format),
        defaults to ``1``
    :type precision: int
    :return: parsed size
    :rtype: int or str

    **Examples**::

        >>> from pyhelpers.ops import parse_size

        >>> parse_size(size='123.45 MB')
        129446707

        >>> parse_size(size='123.45 MB', binary=False)
        123450000

        >>> parse_size(size='123.45 MiB', binary=True)
        129446707
        >>> # If a metric unit (e.g. 'MiB') is specified in the input,
        >>> # the function returns a result accordingly, no matter whether `binary` is True or False
        >>> parse_size(size='123.45 MiB', binary=False)
        129446707

        >>> parse_size(size=129446707, precision=2)
        '123.45 MiB'

        >>> parse_size(size=129446707, binary=False, precision=2)
        '129.45 MB'
    """

    min_unit, units_prefixes = 'B', ['K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    if binary is True:  # Binary system
        factor, units = 2 ** 10, [x + 'i' + min_unit for x in units_prefixes]
    else:  # Decimal (or metric) system
        factor, units = 10 ** 3, [x + min_unit for x in units_prefixes]

    if isinstance(size, str):
        val, sym = [x.strip() for x in size.split()]
        if re.match(r'.*i[Bb]', sym):
            factor, units = 2 ** 10, [x + 'i' + min_unit for x in units_prefixes]
        unit = [s for s in units if s[0] == sym[0].upper()][0]

        unit_dict = dict(zip(units, [factor ** i for i in range(1, len(units) + 1)]))
        parsed_size = int(float(val) * unit_dict[unit])  # in byte

    else:
        is_negative = size < 0
        temp_size, parsed_size = map(copy.copy, (abs(size), size))

        for unit in [min_unit] + units:
            if abs(temp_size) < factor:
                parsed_size = f"{'-' if is_negative else ''}{temp_size:.{precision}f} {unit}"
                break
            if unit != units[-1]:
                temp_size /= factor

    return parsed_size


def get_number_of_chunks(file_or_obj, chunk_size_limit=50, binary=True):
    """
    Get total number of chunks of a data file, given a minimum limit of chunk size.

    :param file_or_obj: absolute path to a file
    :type file_or_obj: str
    :param chunk_size_limit: the minimum limit of file size (in mebibyte i.e. MiB, or megabyte, i.e. MB)
        above which the function counts how many chunks there could be, defaults to ``50``;
    :type chunk_size_limit: int
    :param binary: whether to use binary (i.e. factorized by 1024) representation, defaults to ``True``;
        if ``binary=False``, use the decimal (or metric) representation (i.e. factorized by 10 ** 3)
    :type binary: bool
    :return: number of chunks
    :rtype: int or None

    **Examples**::

        >>> from pyhelpers.ops import get_number_of_chunks
        >>> import os

        >>> file_path = "C:\\Program Files\\Python39\\python39.pdb"

        >>> os.path.getsize(file_path)
        13611008
        >>> get_number_of_chunks(file_path, chunk_size_limit=2)
        7
    """

    factor = 2 ** 10 if binary is True else 10 ** 3

    if isinstance(file_or_obj, str) and os.path.exists(file_or_obj):
        size = os.path.getsize(file_or_obj)
    else:
        size = sys.getsizeof(file_or_obj)

    file_size_in_mb = round(size / (factor ** 2), 1)

    if chunk_size_limit and file_size_in_mb > chunk_size_limit:
        number_of_chunks = math.ceil(file_size_in_mb / chunk_size_limit)
    else:
        number_of_chunks = None

    return number_of_chunks


""" == Basic data manipulation =============================================================== """


# Iterable

def loop_in_pairs(iterable):
    """
    A function to iterate a list as pair (current, next).

    :param iterable: iterable object
    :type iterable: typing.Iterable
    :return: a `zip <https://docs.python.org/3.9/library/functions.html#zip>`_-type variable
    :rtype: zip

    **Examples**::

        >>> from pyhelpers.ops import loop_in_pairs

        >>> res = loop_in_pairs(iterable=[1])
        >>> list(res)
        []

        >>> res = loop_in_pairs(iterable=[1, 2])
        >>> list(res)
        [(1, 2)]
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

    **Example**::

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

    **Example**::

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
            updated_dict[key] = update_dict(dictionary.get(key, {}), val)

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
    :type replacements: dict or None
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

    **Example**::

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


def merge_dicts(*dicts):
    """
    Merge multiple dictionaries.

    :param dicts: (one or) multiple dictionaries
    :type dicts: dict
    :return: a single dictionary containing all elements of the input
    :rtype: dict

    **Example**::

        >>> from pyhelpers.ops import merge_dicts

        >>> dict_a = {'a': 1}
        >>> dict_b = {'b': 2}
        >>> dict_c = {'c': 3}

        >>> merged_dict = merge_dicts(dict_a, dict_b, dict_c)
        >>> merged_dict
        {'a': 1, 'b': 2, 'c': 3}
    """

    super_dict = {}
    for d in dicts:
        super_dict.update(d)

    return super_dict


# Tabular data

def detect_nan_for_str_column(data_frame, column_names=None):
    """
    Detect if a str type column contains ``NaN`` when reading csv files.

    :param data_frame: a data frame to be examined
    :type data_frame: pandas.DataFrame
    :param column_names: a sequence of column names, if ``None`` (default), all columns
    :type column_names: None or collections.abc.Iterable
    :return: position index of the column that contains ``NaN``
    :rtype: typing.Generator[typing.Iterable]

    **Example**::

        >>> from pyhelpers.ops import detect_nan_for_str_column
        >>> import numpy
        >>> import pandas

        >>> df = pandas.DataFrame(numpy.resize(range(10), (10, 2)), columns=['a', 'b'])
        >>> df
           a  b
        0  0  1
        1  2  3
        2  4  5
        3  6  7
        4  8  9
        5  0  1
        6  2  3
        7  4  5
        8  6  7
        9  8  9

        >>> df.iloc[3, 1] = numpy.nan
        >>> df
           a    b
        0  0  1.0
        1  2  3.0
        2  4  5.0
        3  6  NaN
        4  8  9.0
        5  0  1.0
        6  2  3.0
        7  4  5.0
        8  6  7.0
        9  8  9.0

        >>> nan_col_pos = detect_nan_for_str_column(df, column_names=None)
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
    :type theta: int or float
    :return: a rotation matrix of shape (2, 2)
    :rtype: numpy.ndarray

    **Example**::

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

    **Example**::

        >>> from pyhelpers.ops import dict_to_dataframe

        >>> input_dict_ = {'a': 1, 'b': 2}

        >>> df = dict_to_dataframe(input_dict_)
        >>> df
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
    :type path_to_csr: str
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `numpy.load`_
    :return: a compressed sparse row
    :rtype: scipy.sparse.csr.csr_matrix

    .. _`numpy.load`: https://numpy.org/doc/stable/reference/generated/numpy.load

    **Example**::

        >>> from pyhelpers.ops import parse_csr_matrix
        >>> from pyhelpers.dir import cd
        >>> import numpy
        >>> import scipy.sparse

        >>> data_ = numpy.array([1, 2, 3, 4, 5, 6])
        >>> indices_ = numpy.array([0, 2, 2, 0, 1, 2])
        >>> indptr_ = numpy.array([0, 2, 3, 6])

        >>> csr_m = scipy.sparse.csr_matrix((data_, indices_, indptr_), shape=(3, 3))
        >>> csr_m
        <3x3 sparse matrix of type '<class 'numpy.int32'>'
            with 6 stored elements in Compressed Sparse Row format>

        >>> path_to_csr_npz = cd("tests\\data", "csr_mat.npz")
        >>> numpy.savez_compressed(path_to_csr_npz, indptr=csr_m.indptr,
        ...                        indices=csr_m.indices, data=csr_m.data,
        ...                        shape=csr_m.shape)

        >>> csr_mat_ = parse_csr_matrix(path_to_csr_npz, verbose=True)
        Loading "\\tests\\data\\csr_mat.npz" ... Done.

        >>> # .nnz gets the count of explicitly-stored values (non-zeros)
        >>> (csr_mat_ != csr_m).count_nonzero() == 0
        True

        >>> (csr_mat_ != csr_m).nnz == 0
        True
    """

    if verbose:
        print("Loading \"\\{}\"".format(os.path.relpath(path_to_csr)), end=" ... ")

    try:
        csr_loader = np.load(path_to_csr, **kwargs)
        data = csr_loader['data']
        indices = csr_loader['indices']
        indptr = csr_loader['indptr']
        shape = csr_loader['shape']

        import scipy.sparse
        csr_mat = scipy.sparse.csr_matrix((data, indices, indptr), shape)

        print("Done.") if verbose else ""

        return csr_mat

    except Exception as e:
        print("Failed. {}".format(e))


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
    :rtype: numpy.ndarray or list

    **Examples**::

        >>> from pyhelpers.ops import swap_cols
        >>> import numpy

        >>> arr = numpy.array([[55.95615851, -2.96251228],
        ...                    [55.95705685, -2.96253458],
        ...                    [55.95706935, -2.96093324],
        ...                    [55.956171  , -2.96091098]])

        >>> new_arr = swap_cols(arr, c1=0, c2=1)
        >>> new_arr
        array([[-2.96251228, 55.95615851],
               [-2.96253458, 55.95705685],
               [-2.96093324, 55.95706935],
               [-2.96091098, 55.956171  ]])
    """

    array_ = array.copy()
    array_[:, c1], array_[:, c2] = array[:, c2], array[:, c1]

    if as_list:
        array_ = list(array_)

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
    :rtype: numpy.ndarray or list

    **Examples**::

        >>> from pyhelpers.ops import swap_rows
        >>> import numpy

        >>> arr = numpy.array([[55.95615851, -2.96251228],
        ...                    [55.95705685, -2.96253458],
        ...                    [55.95706935, -2.96093324],
        ...                    [55.956171  , -2.96091098]])

        >>> new_arr = swap_rows(arr, r1=0, r2=1)
        >>> new_arr
        array([[55.95705685, -2.96253458],
               [55.95615851, -2.96251228],
               [55.95706935, -2.96093324],
               [55.956171  , -2.96091098]])
    """

    array_ = array.copy()
    array_[r1, :], array_[r2, :] = array[r2, :], array[r1, :]

    if as_list:
        array_ = list(array_)

    return array_


""" == Basic computation ===================================================================== """


def get_extreme_outlier_bounds(num_dat, k=1.5):
    """
    Get upper and lower bounds for extreme outliers.

    :param num_dat: an array of numbers
    :type num_dat: array-like
    :param k: a scale coefficient associated with interquartile range, defaults to ``1.5``
    :type k: float, int
    :return: lower and upper bound
    :rtype: tuple

    **Example**::

        >>> from pyhelpers.ops import get_extreme_outlier_bounds
        >>> import pandas

        >>> data = pandas.DataFrame(range(100), columns=['col'])
        >>> data.describe()
                      col
        count  100.000000
        mean    49.500000
        std     29.011492
        min      0.000000
        25%     24.750000
        50%     49.500000
        75%     74.250000
        max     99.000000

        >>> lo_bound, up_bound = get_extreme_outlier_bounds(data, k=1.5)
        >>> lo_bound, up_bound
        (0.0, 148.5)
    """

    q1, q3 = np.percentile(num_dat, 25), np.percentile(num_dat, 75)
    iqr = q3 - q1

    lower_bound = np.max([0, q1 - k * iqr])
    upper_bound = q3 + k * iqr

    return lower_bound, upper_bound


def interquartile_range(num_dat):
    """
    Calculate interquartile range.

    This function may be an alternative to
    `scipy.stats.iqr <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.iqr.html>`_.

    :param num_dat: an array of numbers
    :type num_dat: numpy.ndarry or list or tuple
    :return: interquartile range of ``num_dat``
    :rtype: float

    **Example**::

        >>> from pyhelpers.ops import interquartile_range
        >>> import pandas

        >>> data = pandas.DataFrame(range(100), columns=['col'])
        >>> data.describe()
                      col
        count  100.000000
        mean    49.500000
        std     29.011492
        min      0.000000
        25%     24.750000
        50%     49.500000
        75%     74.250000
        max     99.000000

        >>> iqr_ = interquartile_range(data)
        >>> iqr_
        49.5
    """

    iqr = np.subtract(*np.percentile(num_dat, [75, 25]))

    return iqr


def find_closest_date(date, lookup_dates, as_datetime=False, fmt='%Y-%m-%d %H:%M:%S.%f'):
    """
    Find the closest date of a given one from a list of dates.

    :param date: a date
    :type date: str or datetime.datetime
    :param lookup_dates: an array of dates
    :type lookup_dates: typing.Iterable
    :param as_datetime: whether to return a datetime.datetime-formatted date, defaults to ``False``
    :type as_datetime: bool
    :param fmt: datetime format, defaults to ``'%Y-%m-%d %H:%M:%S.%f'``
    :type fmt: str
    :return: the date that is closest to the given ``date``
    :rtype: str or datetime.datetime

    **Examples**::

        >>> from pyhelpers.ops import find_closest_date
        >>> import pandas

        >>> date_list = pandas.date_range('2019-01-02', '2019-12-31')
        >>> date_list
        DatetimeIndex(['2019-01-02', '2019-01-03', '2019-01-04', '2019-01-05',
                       '2019-01-06', '2019-01-07', '2019-01-08', '2019-01-09',
                       '2019-01-10', '2019-01-11',
                       ...
                       '2019-12-22', '2019-12-23', '2019-12-24', '2019-12-25',
                       '2019-12-26', '2019-12-27', '2019-12-28', '2019-12-29',
                       '2019-12-30', '2019-12-31'],
                      dtype='datetime64[ns]', length=364, freq='D')

        >>> date_ = '2019-01-01'
        >>> closest_date_ = find_closest_date(date_, date_list, as_datetime=True)
        >>> closest_date_
        Timestamp('2019-01-02 00:00:00', freq='D')

        >>> date_ = pandas.to_datetime('2019-01-01')
        >>> closest_date_ = find_closest_date(date_, date_list, as_datetime=False)
        >>> closest_date_
        '2019-01-02 00:00:00.000000'
    """

    closest_date = min(lookup_dates, key=lambda x: abs(pd.to_datetime(x) - pd.to_datetime(date)))

    if as_datetime:
        if isinstance(closest_date, str):
            closest_date = pd.to_datetime(closest_date)

    else:
        if isinstance(closest_date, datetime.datetime):
            closest_date = closest_date.strftime(fmt)

    return closest_date


""" == Graph plotting ======================================================================== """


def cmap_discretisation(cmap, n_colours):
    """
    Create a discrete colour ramp.

    See also [`OPS-CD-1
    <https://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: a colormap instance,
        e.g. built-in `colormaps`_ that is accessible via `matplotlib.cm.get_cmap`_
    :type cmap: matplotlib.colors.ListedColormap
    :param n_colours: number of colours
    :type n_colours: int
    :return: a discrete colormap from (the continuous) ``cmap``
    :rtype: matplotlib.colors.LinearSegmentedColormap

    .. _`colormaps`: https://matplotlib.org/tutorials/colors/colormaps.html
    .. _`matplotlib.cm.get_cmap`: https://matplotlib.org/api/cm_api.html#matplotlib.cm.get_cmap

    **Example**::

        >>> from pyhelpers.ops import cmap_discretisation
        >>> import matplotlib.cm
        >>> import matplotlib.pyplot as plt
        >>> import numpy

        >>> cm_accent = cmap_discretisation(matplotlib.cm.get_cmap('Accent'), n_colours=5)
        >>> cm_accent.name
        'Accent_5'

        >>> fig, ax = plt.subplots(figsize=(10, 2))

        >>> ax.imshow(numpy.resize(range(100), (5, 100)), cmap=cm_accent, interpolation='nearest')

        >>> plt.axis('off')
        >>> plt.tight_layout()
        >>> plt.show()

    The exmaple is illustrated in :numref:`cmap-discretisation`:

    .. figure:: ../_images/cmap-discretisation.*
        :name: cmap-discretisation
        :align: center
        :width: 60%

        An example of discrete colour ramp, created by
        :py:func:`cmap_discretisation()<pyhelpers.ops.cmap_discretisation>`.
    """

    import matplotlib.cm
    import matplotlib.colors

    if isinstance(cmap, str):
        cmap = matplotlib.cm.get_cmap(cmap)

    colours_i = np.concatenate((np.linspace(0, 1., n_colours), (0., 0., 0., 0.)))
    colours_rgba = cmap(colours_i)
    indices = np.linspace(0, 1., n_colours + 1)
    c_dict = {}

    for ki, key in enumerate(('red', 'green', 'blue')):
        c_dict[key] = [
            (indices[x], colours_rgba[x - 1, ki], colours_rgba[x, ki]) for x in range(n_colours + 1)
        ]

    colour_map = matplotlib.colors.LinearSegmentedColormap(cmap.name + '_%d' % n_colours, c_dict, 1024)

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
    :type labels: list or None
    :param kwargs: [optional] parameters of `matplotlib.pyplot.colorbar`_
    :return: a colour bar object
    :rtype: matplotlib.colorbar.Colorbar

    .. _`colormaps`: https://matplotlib.org/tutorials/colors/colormaps.html
    .. _`matplotlib.cm.get_cmap`: https://matplotlib.org/api/cm_api.html#matplotlib.cm.get_cmap
    .. _`matplotlib.pyplot.colorbar`: https://matplotlib.org/api/_as_gen/matplotlib.pyplot.colorbar.html

    **Examples**::

        >>> from pyhelpers.ops import colour_bar_index
        >>> import matplotlib.pyplot as plt
        >>> import matplotlib.cm

        >>> plt.figure(figsize=(2, 6))

        >>> cbar = colour_bar_index(cmap=matplotlib.cm.get_cmap('Accent'), n_colours=5)

        >>> plt.xticks(fontsize=12)
        >>> plt.yticks(fontsize=12)
        >>> cbar.ax.tick_params(labelsize=14)

        >>> # plt.axis('off')
        >>> plt.tight_layout()
        >>> plt.show()

    The above example is illustrated in :numref:`colour-bar-index-1`:

    .. figure:: ../_images/colour-bar-index-1.*
        :name: colour-bar-index-1
        :align: center
        :width: 23%

        An example of colour bar with numerical index,
        created by :py:func:`colour_bar_index()<pyhelpers.ops.colour_bar_index>`.

    .. code-block:: python

        >>> plt.figure(figsize=(2, 6))

        >>> labels_ = list('abcde')
        >>> cbar = colour_bar_index(matplotlib.cm.get_cmap('Accent'), n_colours=5, labels=labels_)

        >>> plt.xticks(fontsize=12)
        >>> plt.yticks(fontsize=12)
        >>> cbar.ax.tick_params(labelsize=14)

        >>> # plt.axis('off')
        >>> plt.tight_layout()
        >>> plt.show()

    This second example is illustrated in :numref:`colour-bar-index-2`:

    .. figure:: ../_images/colour-bar-index-2.*
        :name: colour-bar-index-2
        :align: center
        :width: 23%

        An example of colour bar with textual index,
        created by :py:func:`colour_bar_index()<pyhelpers.ops.colour_bar_index>`.
    """

    import matplotlib.cm
    import matplotlib.pyplot

    cmap = cmap_discretisation(cmap, n_colours)

    mappable = matplotlib.cm.ScalarMappable(cmap=cmap)
    mappable.set_array(np.array([]))
    mappable.set_clim(-0.5, n_colours + 0.5)

    colour_bar = matplotlib.pyplot.colorbar(mappable, **kwargs)
    colour_bar.set_ticks(np.linspace(0, n_colours, n_colours))
    colour_bar.set_ticklabels(range(n_colours))

    if labels:
        colour_bar.set_ticklabels(labels)

    return colour_bar


""" == Web scraping ========================================================================== """


def is_network_connected():
    """
    Check whether the current machine can connect to the Internet.

    :return: whether the Internet connection is currently working
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.ops import is_network_connected

        >>> is_network_connected()  # assuming the machine is currently connected to the Internet
        True
    """

    host_name = socket.gethostname()
    ip_address = socket.gethostbyname(host_name)

    return False if ip_address == "127.0.0.1" else True


def is_url(url, partially=False):
    """
    Check whether ``url`` is a valid URL.

    See also [`OPS-IU-1 <https://stackoverflow.com/questions/7160737/>`_]

    :param url: a string-type variable
    :type url: str
    :param partially: whether to consider the input as partially valid, defaults to ``False``
    :type partially: bool
    :return: whether ``url`` is a valid URL
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.ops import is_url

        >>> is_url(url='https://github.com/mikeqfu/pyhelpers')
        True

        >>> is_url(url='github.com/mikeqfu/pyhelpers')
        False

        >>> is_url(url='github.com/mikeqfu/pyhelpers', partially=True)
        True

        >>> is_url(url='github.com')
        False

        >>> is_url(url='github.com', partially=True)
        True

        >>> is_url(url='github', partially=True)
        False
    """

    try:
        parsed_url = urllib.parse.urlparse(url)
        schema_netloc = [parsed_url.scheme, parsed_url.netloc]

        rslt = all(schema_netloc)

        if rslt is False and not any(schema_netloc):
            assert re.match(r'(/\w+)+|(\w+\.\w+)', parsed_url.path.lower())
            if partially:
                rslt = True
        else:
            assert re.match(r'(ht|f)tp(s)?', parsed_url.scheme.lower())

    except AssertionError:
        rslt = False

    return rslt


def is_url_connectable(url):
    """
    Check whether the current machine can connect to a given URL.

    :param url: a (valid) URL
    :type url: str
    :return: whether the machine can currently connect to the given URL
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.ops import is_url_connectable

        >>> url_0 = 'https://www.python.org/'
        >>> is_url_connectable(url_0)
        True

        >>> url_1 = 'https://www.python.org1/'
        >>> is_url_connectable(url_1)
        False
    """

    try:
        netloc = urllib.parse.urlparse(url).netloc
        host = socket.gethostbyname(netloc)
        s = socket.create_connection((host, 80))
        s.close()

        return True

    except (socket.gaierror, OSError):
        return False


def is_downloadable(url, request_field='content-type', **kwargs):
    """
    Check whether a URL leads to a web page where there is downloadable contents.

    :param url: a valid URL
    :type url: str
    :param request_field: name of the field/header indicating the original media type of the resource,
        defaults to ``'content-type'``
    :type request_field: str
    :param kwargs: [optional] parameters of `requests.head`_
    :return: whether the ``url`` leads to downloadable contents
    :rtype: bool

    .. _`requests.head`: https://2.python-requests.org/en/master/api/#requests.head

    **Example**::

        >>> from pyhelpers.ops import is_downloadable

        >>> logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> is_downloadable(logo_url)
        True

        >>> google_url = 'https://www.google.co.uk/'
        >>> is_downloadable(google_url)
        False
    """

    kwargs.update({'allow_redirects': True})
    h = requests.head(url=url, **kwargs)

    content_type = h.headers.get(request_field).lower()

    if content_type.startswith('text/html'):
        downloadable = False
    else:
        downloadable = True

    return downloadable


def init_requests_session(url, max_retries=5, backoff_factor=0.1, retry_status='default', **kwargs):
    """
    Instantiate a `requests <https://docs.python-requests.org/en/latest/>`_ session.

    :param url: a valid URL
    :type url: str
    :param max_retries: maximum number of retries, defaults to ``5``
    :type max_retries: int
    :param backoff_factor: ``backoff_factor`` of `urllib3.util.retry.Retry`_, defaults to ``0.1``
    :type backoff_factor: float
    :param retry_status: a list of HTTP status codes that force to retry downloading,
        inherited from ``status_forcelist`` of `urllib3.util.retry.Retry`_;
        when ``retry_status='default'``, the list defaults to ``[429, 500, 502, 503, 504]``
    :param kwargs: [optional] parameters of `urllib3.util.retry.Retry`_
    :return: a `requests`_ session
    :rtype: `requests.Session`_

    .. _`requests`: https://docs.python-requests.org/en/latest/
    .. _`urllib3.util.retry.Retry`:
        https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#urllib3.util.Retry
    .. _`requests.Session`:
        https://2.python-requests.org/en/master/api/#request-sessions

    **Example**::

        >>> from pyhelpers.ops import init_requests_session

        >>> logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'

        >>> s = init_requests_session(logo_url)

        >>> type(s)
        requests.sessions.Session
    """

    if retry_status == 'default':
        codes_for_retries = [429, 500, 502, 503, 504]
    else:
        codes_for_retries = copy.copy(retry_status)

    kwargs.update({'backoff_factor': backoff_factor, 'status_forcelist': codes_for_retries})
    retries = urllib3.util.retry.Retry(total=max_retries, **kwargs)

    session = requests.Session()

    session.mount(
        prefix='https://' if url.startswith('https:') else 'http://',
        adapter=requests.adapters.HTTPAdapter(max_retries=retries))

    return session


def _user_agent_strings(browser_names=None, dump_dat=True):
    """
    Get a dictionary of user-agent strings for popular browsers.

    :param browser_names: names of a list of popular browsers
    :type browser_names: list
    :return: a dictionary of user-agent strings for popular browsers
    :rtype: dict

    **Example**::

        >>> # noinspection PyProtectedMember
        >>> from pyhelpers.ops import _user_agent_strings

        >>> uas = _user_agent_strings()
        >>> list(uas.keys())
        ['Chrome', 'Firefox', 'Safari', 'Edge', 'Internet Explorer', 'Opera']
    """

    class _FakeUserAgentParser(html.parser.HTMLParser):
        def __init__(self):
            super().__init__()
            self.reset()
            self.recording = 0
            self.data = []

        def error(self, message):
            pass

        def handle_starttag(self, tag, attrs):
            if tag != 'a':
                return

            if self.recording:
                self.recording += 1
                return

            if tag == 'a':
                for name, link in attrs:
                    if name == 'href' and link.startswith('/index.php?id='):
                        break
                    else:
                        return
                self.recording = 1

        def handle_endtag(self, tag):
            if tag == 'a' and self.recording:
                self.recording -= 1

        def handle_data(self, data):
            if self.recording:
                self.data.append(data.strip())

    resource_url = 'http://useragentstring.com/pages/useragentstring.php'

    if browser_names is None:
        browser_names_ = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Internet Explorer', 'Opera']
    else:
        browser_names_ = browser_names.copy()

    user_agent_strings = {}
    for browser_name in browser_names_:
        url = resource_url + f'?name={browser_name.replace(" ", "+")}'
        response = urllib.request.urlopen(url=url)
        text = response.read().decode('utf-8')

        fua_parser = _FakeUserAgentParser()
        fua_parser.feed(text)

        user_agent_strings[browser_name] = list(set(fua_parser.data))

    if dump_dat:
        path_to_json = pkg_resources.resource_filename(__name__, "dat\\user-agent-strings.json")

        json_out = open(path_to_json, mode='w')
        json_out.write(json.dumps(user_agent_strings))
        json_out.close()

    return user_agent_strings


def get_user_agent_strings(shuffled=False, flattened=False, update=False, verbose=False):
    """
    Get user-agent strings for some popular browsers.

    The current version collects a partially comprehensive list of user-agent strings for
    `Chrome`_, `Firefox`_, `Safari`_, `Edge`_, `Internet Explorer`_ and `Opera`_.

    :param shuffled: whether to randomly shuffle the user-agent strings, defaults to ``False``
    :type shuffled: bool
    :param flattened: whether to make a list of all available user-agent strings, defaults to ``False``
    :type flattened: bool
    :param update: whether to update the backup data of user-agent strings, defaults to ``False``
    :type update: bool
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :return: a dictionary of user agent strings for popular browsers
    :rtype: dict or list

    .. _`Chrome`: http://useragentstring.com/pages/useragentstring.php?name=Chrome
    .. _`Firefox`: http://useragentstring.com/pages/useragentstring.php?name=Firefox
    .. _`Safari`: http://useragentstring.com/pages/useragentstring.php?name=Safari
    .. _`Edge`: http://useragentstring.com/pages/useragentstring.php?name=Edge
    .. _`Internet Explorer`: http://useragentstring.com/pages/useragentstring.php?name=Internet+Explorer
    .. _`Opera`: http://useragentstring.com/pages/useragentstring.php?name=Opera

    **Examples**::

        >>> from pyhelpers.ops import get_user_agent_strings

        >>> uas = get_user_agent_strings()

        >>> list(uas.keys())
        ['Chrome', 'Firefox', 'Safari', 'Edge', 'Internet Explorer', 'Opera']
        >>> type(uas['Chrome'])
        list
        >>> uas['Chrome'][0]
        'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Ubuntu/10.04 Chromiu...

        >>> uas_list = get_user_agent_strings(flattened=True, shuffled=True)
        >>> type(uas_list)
        list
        >>> uas_list[0]
        'Mozilla/5.0 (Windows NT) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari...

    .. note::

        The order of the elements in ``uas_list`` may be different every time we run the example
        as ``shuffled=True``.
    """

    if not update:
        path_to_json = pkg_resources.resource_filename(__name__, "dat\\user-agent-strings.json")

        json_in = open(path_to_json, mode='r')
        user_agent_strings = json.loads(json_in.read())

    else:
        if verbose:
            print("Updating the backup data of user-agent strings", end=" ... ")

        try:
            user_agent_strings = _user_agent_strings(dump_dat=True)
            if verbose:
                print("Done.")

        except Exception as e:
            if verbose:
                print("Failed. {}".format(e))
            user_agent_strings = get_user_agent_strings(update=False, verbose=False)

    if shuffled:
        for browser_name, ua_str in user_agent_strings.items():
            random.shuffle(ua_str)
            user_agent_strings.update({browser_name: ua_str})

    if flattened:
        user_agent_strings = [x for v in user_agent_strings.values() for x in v]

    return user_agent_strings


def get_user_agent_string(fancy=None, **kwargs):
    """
    Get a random user-agent string of a certain browser.

    :param fancy: name of a preferred browser, defaults to ``None``;
        options include ``'Chrome'``, ``'Firefox'``, ``'Safari'``, ``'Edge'``,
        ``'Internet Explorer'`` and ``'Opera'``;
        if ``fancy=None``, the function returns a user-agent string of a randomly-selected browser
        among all the available options
    :type: fancy: None or str
    :param kwargs: [optional] parameters of the function :py:func:`pyhelpers.ops.get_user_agent_strings`
    :return: a user-agent string of a certain browser
    :rtype: str

    **Examples**::

        >>> from pyhelpers.ops import get_user_agent_string

        >>> # Get a random user-agent string
        >>> uas_0 = get_user_agent_string()
        >>> uas_0
        'Mozilla/5.0 (Windows; U; Win98; de-DE; rv:1.7.7) Gecko/20050414 Firefox/1.0.3'

        >>> # Get a random Chrome user-agent string
        >>> uas_1 = get_user_agent_string(fancy='Chrome')
        >>> uas_1
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:22.0) Gecko/20130328 Firefox/22.0'

    .. note::

        In the above examples, the returned user-agent string is random and may be different
        every time of running the function.
    """

    if fancy is not None:
        browser_names = {'Chrome', 'Firefox', 'Safari', 'Edge', 'Internet Explorer', 'Opera'}
        assert fancy in browser_names, f"`fancy` must be one of {browser_names}."

        kwargs.update({'flattened': False})
        user_agent_strings_ = get_user_agent_strings(**kwargs)

        user_agent_strings = user_agent_strings_[fancy]

    else:
        kwargs.update({'flattened': True})
        user_agent_strings = get_user_agent_strings(**kwargs)

    user_agent_string = random.choice(user_agent_strings)

    return user_agent_string


def fake_requests_headers(randomized=True, **kwargs):
    """
    Make a fake HTTP headers for `requests.get
    <https://requests.readthedocs.io/en/master/user/advanced/#request-and-response-objects>`_.

    :param randomized: whether to use a user-agent string randomly selected
        from among all available data of several popular browsers, defaults to ``True``;
        if ``randomized=False``, the function uses a random Chrome user-agent string
    :type randomized: bool
    :param kwargs: [optional] parameters of the function :py:func:`pyhelpers.ops.get_user_agent_string`
    :return: fake HTTP headers
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.ops import fake_requests_headers

        >>> fake_headers_1 = fake_requests_headers()
        >>> fake_headers_1
        {'user-agent': 'Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.7.7) Gecko/20050420 Firefo...

        >>> fake_headers_2 = fake_requests_headers(randomized=False)
        >>> # using a random Chrome user-agent string
        >>> fake_headers_2
        {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_4) AppleWebKit/534.30 (KHTML,...

        >>> fake_headers_2 == fake_headers_1
        False

    .. note::

        - ``fake_headers_1`` may also be different every time we run the example.
          This is because the returned result is randomly chosen from a limited set of candidate
          user-agent strings, even though ``randomized`` is (by default) set to be ``False``.
        - By setting ``randomized=True``, the function returns a random result from among
          all available user-agent strings of several popular browsers.
    """

    if not randomized:
        kwargs.update({'fancy': 'Chrome'})

    user_agent_string = get_user_agent_string(**kwargs)

    fake_headers = {'user-agent': user_agent_string}

    return fake_headers


def _download_file_from_url(response, path_to_file):
    import tqdm

    file_size = int(response.headers.get('content-length'))  # Total size in bytes

    unit_divisor = 1024
    block_size = unit_divisor ** 2
    chunk_size = block_size if file_size >= block_size else unit_divisor

    total_iter = file_size // chunk_size

    progress = tqdm.tqdm(
        desc=f'"{os.path.relpath(path_to_file)}"', total=total_iter, unit='B',
        unit_scale=True, unit_divisor=unit_divisor)

    contents = response.iter_content(chunk_size=chunk_size, decode_unicode=True)
    with open(file=path_to_file, mode='wb') as f:
        written = 0
        for data in contents:
            if data:
                try:
                    f.write(data)
                except TypeError:
                    f.write(data.encode())
                progress.update(len(data))
                written += len(data)

        progress.close()

    f.close()

    if file_size != 0 and written != file_size:
        print("ERROR! Something went wrong!")


def download_file_from_url(url, path_to_file, if_exists='replace', max_retries=5, random_header=True,
                           verbose=False, requests_session_args=None, fake_headers_args=None,
                           **kwargs):
    """
    Download an object available at a valid URL.

    See also [`OPS-DFFU-1`_] and [`OPS-DFFU-2`_].

    .. _OPS-DFFU-1: https://stackoverflow.com/questions/37573483/
    .. _OPS-DFFU-2: https://stackoverflow.com/questions/15431044/

    :param url: valid URL to a web resource
    :type url: str
    :param path_to_file: a path where the downloaded object is saved as, or a filename
    :type path_to_file: str
    :param if_exists: given that the specified file already exists, options include
        ``'replace'`` (default, continuing to download the requested file and replace the existing one
        at the specified path) and ``'pass'`` (cancelling the download)
    :type if_exists: str
    :param max_retries: maximum number of retries, defaults to ``5``
    :type max_retries: int
    :param random_header: whether to go for a random agent, defaults to ``True``
    :type random_header: bool
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param requests_session_args: [optional] parameters of
        :py:func:`init_requests_session<pyhelpers.ops.init_requests_session>`, defaults to ``None``
    :type requests_session_args: dict or None
    :param fake_headers_args: [optional] parameters of
        :py:func:`fake_requests_headers<pyhelpers.ops.fake_requests_headers>`, defaults to ``None``
    :type fake_headers_args: dict or None
    :param kwargs: [optional] parameters of `requests.Session.get`_

    .. _requests.Session.get:
        https://docs.python-requests.org/en/master/_modules/requests/sessions/#Session.get

    **Example**::

        >>> from pyhelpers.ops import download_file_from_url
        >>> from pyhelpers.dir import cd
        >>> import os
        >>> from PIL import Image

        >>> logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> path_to_img = cd("tests", "images", "python-logo.png")

        >>> # Check if "python-logo.png" exists at the specified path
        >>> os.path.exists(path_to_img)
        False

        >>> # Download the .png file
        >>> download_file_from_url(logo_url, path_to_img)

        >>> # If download is successful, check again:
        >>> os.path.exists(path_to_img)
        True

        >>> img = Image.open(path_to_img)
        >>> img.show()  # as illustrated below

    .. figure:: ../_images/python-logo.*
        :name: python-logo
        :align: center
        :width: 65%

        The Python Logo.

    .. only:: html

        |

    .. note::

        - When setting ``verbose`` to be ``True`` (or ``1``), the function relies on `tqdm`_,
          which is not an essential dependency for installing `pyhelpers>=1.2.15`_.
          You may need to install `tqdm`_ before proceeding with ``verbose=True`` (or ``verbose=1``).

        .. _`tqdm`: https://pypi.org/project/tqdm/
        .. _`pyhelpers>=1.2.15`: https://pypi.org/project/pyhelpers/1.2.15/
    """

    path_to_dir = os.path.dirname(path_to_file)
    if path_to_dir == "":
        path_to_file_ = os.path.join(os.getcwd(), path_to_file)
        path_to_dir = os.path.dirname(path_to_file_)
    else:
        path_to_file_ = copy.copy(path_to_file)

    if os.path.exists(path_to_file_) and if_exists != 'replace':
        if verbose:
            print(f"The destination already has a file named \"{os.path.basename(path_to_file_)}\". "
                  f"The download is cancelled.")

    else:
        if requests_session_args is None:
            requests_session_args = {}
        session = init_requests_session(url=url, max_retries=max_retries, **requests_session_args)

        if fake_headers_args is None:
            fake_headers_args = {}
        fake_headers = fake_requests_headers(randomized=random_header, **fake_headers_args)

        # Streaming, so we can iterate over the response
        response = session.get(url=url, stream=True, headers=fake_headers, **kwargs)

        if not os.path.exists(path_to_dir):
            os.makedirs(path_to_dir)

        if verbose:
            _download_file_from_url(response=response, path_to_file=path_to_file_)

        else:
            with open(file=path_to_file_, mode='wb') as f:
                shutil.copyfileobj(fsrc=response.raw, fdst=f)

            f.close()

            if os.stat(path=path_to_file_).st_size == 0:
                print("ERROR! Something went wrong! Check if the URL is downloadable.")

        response.close()
