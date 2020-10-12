"""
A module for miscellaneous operations.
"""

import collections.abc
import datetime
import itertools
import math
import os
import re
import time
import types

import numpy as np
import pandas as pd
import tqdm


# For general use ----------------------------------------------------------------------

def confirmed(prompt=None, resp=False, confirmation_required=True):
    """
    Type to confirm whether to proceed or not.

    See also
    [`C-1 <http://sensitivecities.com/
    so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param prompt: a message that prompts an response (Yes/No), defaults to ``None``
    :type prompt: str or None
    :param resp: default response, defaults to ``False``
    :type resp: bool
    :param confirmation_required: whether to require users to confirm and proceed,
        defaults to ``True``
    :type confirmation_required: bool
    :return: a response
    :rtype: bool

    **Example**::

        >>> from pyhelpers.ops import confirmed

        >>> if confirmed(prompt="Create Directory?", resp=True):
        ...     print(True)
        Create Directory? [No]|Yes: yes
        True
    """

    if confirmation_required:
        if prompt is None:
            prompt = "Confirmed? "

        if resp is True:  # meaning that default response is True
            prompt = "{} [{}]|{}: ".format(prompt, "Yes", "No")
        else:
            prompt = "{} [{}]|{}: ".format(prompt, "No", "Yes")

        ans = input(prompt)
        if not ans:
            return resp

        if re.match('[Yy](es)?', ans):
            return True
        if re.match('[Nn](o)?', ans):
            return False

    else:
        return True


# For iterable manipulation ------------------------------------------------------------

def split_list_by_size(lst, sub_len):
    """
    Split a list into (evenly sized) sub-lists.

    See also [`SLBS-1 <https://stackoverflow.com/questions/312443/>`_].

    :param lst: a list of any
    :type lst: list
    :param sub_len: length of a sub-list
    :type sub_len: int
    :return: a sequence of ``sub_len``-sized sub-lists from ``lst``
    :rtype: types.GeneratorType

    **Example**::

        >>> from pyhelpers.ops import split_list_by_size

        >>> lst_ = list(range(0, 10))
        >>> sub_lst_len = 3

        >>> lists = split_list_by_size(lst_, sub_lst_len)
        >>> print(list(lists))
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    """

    for i in range(0, len(lst), sub_len):
        yield lst[i:i + sub_len]


def split_list(lst, num_of_sub):
    """
    Split a list into a number of equally-sized sub-lists.

    See also [`SL-1 <https://stackoverflow.com/questions/312443/>`_].

    :param lst: a list of any
    :type lst: list
    :param num_of_sub: number of sub-lists
    :type num_of_sub: int
    :return: a total of ``num_of_sub`` sub-lists from ``lst``
    :rtype: types.GeneratorType

    **Example**::

        >>> from pyhelpers.ops import split_list

        >>> lst_ = list(range(0, 10))
        >>> num_of_sub_lists = 3

        >>> lists = list(split_list(lst_, num_of_sub_lists))
        >>> print(list(lists))
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]
    """

    chunk_size = math.ceil(len(lst) / num_of_sub)
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def split_iterable(iterable, chunk_size):
    """
    Split a list into (evenly sized) chunks.

    See also [`SI-1 <https://stackoverflow.com/questions/24527006/>`_].

    :param iterable: iterable object
    :type iterable: list or tuple or collections.abc.Iterable
    :param chunk_size: length of a chunk
    :type chunk_size: int
    :return: a sequence of equally-sized chunks from ``iterable``
    :rtype: types.GeneratorType

    **Examples**::

        >>> import pandas as pd_
        >>> from pyhelpers.ops import split_iterable

        >>> lst = list(range(0, 10))
        >>> size_of_chunk = 3

        >>> for lst_ in split_iterable(lst, size_of_chunk):
        ...     print(list(lst_))
        [0, 1, 2]
        [3, 4, 5]
        [6, 7, 8]
        [9]

        >>> lst = pd_.Series(range(0, 20))
        >>> size_of_chunk = 5
        >>> for lst_ in split_iterable(lst, size_of_chunk):
        ...     print(list(lst_))
        [0, 1, 2, 3, 4]
        [5, 6, 7, 8, 9]
        [10, 11, 12, 13, 14]
        [15, 16, 17, 18, 19]
    """

    iterator = iter(iterable)
    for x in iterator:
        yield itertools.chain([x], itertools.islice(iterator, chunk_size - 1))


def update_nested_dict(source_dict, updates):
    """
    Update a nested dictionary or similar mapping.

    See also [`UND-1 <https://stackoverflow.com/questions/3232943/>`_].

    :param source_dict: a dictionary that needs to be updated
    :type source_dict: dict
    :param updates: a dictionary with new data
    :type updates: dict
    :return: an updated dictionary
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.ops import update_nested_dict

        >>> source_dict_ = {'key_1': 1}
        >>> updates_ = {'key_2': 2}
        >>> source_dict_ = update_nested_dict(source_dict_, updates_)
        >>> print(source_dict_)
        {'key_1': 1, 'key_2': 2}

        >>> source_dict_ = {'key': 'val_old'}
        >>> updates_ = {'key': 'val_new'}
        >>> source_dict_ = update_nested_dict(source_dict_, updates_)
        >>> print(source_dict_)
        {'key': 'val_new'}

        >>> source_dict_ = {'key': {'k1': 'v1_old', 'k2': 'v2'}}
        >>> updates_ = {'key': {'k1': 'v1_new'}}
        >>> source_dict_ = update_nested_dict(source_dict_, updates_)
        >>> print(source_dict_)
        {'key': {'k1': 'v1_new', 'k2': 'v2'}}

        >>> source_dict_ = {'key': {'k1': {}, 'k2': 'v2'}}
        >>> updates_ = {'key': {'k1': 'v1'}}
        >>> source_dict_ = update_nested_dict(source_dict_, updates_)
        >>> print(source_dict_)
        {'key': {'k1': 'v1', 'k2': 'v2'}}

        >>> source_dict_ = {'key': {'k1': 'v1', 'k2': 'v2'}}
        >>> updates_ = {'key': {'k1': {}}}
        >>> source_dict_ = update_nested_dict(source_dict_, updates_)
        >>> print(source_dict_)
        {'key': {'k1': 'v1', 'k2': 'v2'}}
    """

    for key, val in updates.items():
        if isinstance(val, collections.abc.Mapping) or isinstance(val, dict):
            source_dict[key] = update_nested_dict(source_dict.get(key, {}), val)

        elif isinstance(val, list):
            source_dict[key] = (source_dict.get(key, []) + val)

        else:
            source_dict[key] = updates[key]

    return source_dict


def get_all_values_from_nested_dict(key, target_dict):
    """
    Get all values in a nested dictionary.

    See also
    [`GAVFND-1 <https://gist.github.com/douglasmiranda/5127251>`_] and
    [`GAVFND-2 <https://stackoverflow.com/questions/9807634/>`_].

    :param key: any that can be the key of a dictionary
    :type key: any
    :param target_dict: a (nested) dictionary
    :type target_dict: dict
    :return: all values of the ``key`` within the given ``target_dict``
    :rtype: types.GeneratorType

    **Examples**::

        >>> from pyhelpers.ops import get_all_values_from_nested_dict

        >>> key_ = 'key'
        >>> target_dict_ = {'key': 'val'}
        >>> val = get_all_values_from_nested_dict(key_, target_dict_)
        >>> print(list(val))
        [['val']]

        >>> key_ = 'k1'
        >>> target_dict_ = {'key': {'k1': 'v1', 'k2': 'v2'}}
        >>> val = get_all_values_from_nested_dict(key_, target_dict_)
        >>> print(list(val))
        [['v1']]

        >>> key_ = 'k1'
        >>> target_dict_ = {'key': {'k1': ['v1', 'v1_1']}}
        >>> val = get_all_values_from_nested_dict(key_, target_dict_)
        >>> print(list(val))
        [['v1', 'v1_1']]

        >>> key_ = 'k2'
        >>> target_dict_ = {'key': {'k1': 'v1', 'k2': ['v2', 'v2_1']}}
        >>> val = get_all_values_from_nested_dict(key_, target_dict_)
        >>> print(list(val))
        [['v2', 'v2_1']]
    """

    for k, v in target_dict.items():
        if key == k:
            yield [v] if isinstance(v, str) else v
        elif isinstance(v, dict):
            for x in get_all_values_from_nested_dict(key, v):
                yield x
        elif isinstance(v, collections.abc.Iterable):
            for d in v:
                if isinstance(d, dict):
                    for y in get_all_values_from_nested_dict(key, d):
                        yield y


def remove_multiple_keys_from_dict(target_dict, *keys):
    """
    Remove multiple keys from a dictionary.

    :param target_dict: a dictionary
    :type target_dict: dict
    :param keys: (a sequence of) any that can be the key of a dictionary
    :type keys: any

    **Example**::

        >>> from pyhelpers.ops import remove_multiple_keys_from_dict

        >>> target_dict_ = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'k4': 'v4', 'k5': 'v5'}

        >>> remove_multiple_keys_from_dict(target_dict_, 'k1', 'k3', 'k4')

        >>> print(target_dict_)
        {'k2': 'v2', 'k5': 'v5'}
    """

    # assert isinstance(dictionary, dict)
    for k in keys:
        if k in target_dict.keys():
            target_dict.pop(k)


# Tabular data -------------------------------------------------------------------------

def detect_nan_for_str_column(data_frame, column_names=None):
    """
    Detect if a str type column contains ``NaN`` when reading csv files.

    :param data_frame: a data frame to be examined
    :type data_frame: pandas.DataFrame
    :param column_names: a sequence of column names, if ``None`` (default), all columns
    :type column_names: None or collections.abc.Iterable
    :return: position index of the column that contains ``NaN``
    :rtype: types.GeneratorType

    **Example**::

        >>> import numpy as np_
        >>> import pandas as pd_
        >>> from pyhelpers.ops import detect_nan_for_str_column

        >>> df = pd_.DataFrame(np_.resize(range(10), (10, 2)), columns=['a', 'b'])
        >>> df.iloc[3, 1] = np.nan

        >>> nan_col_pos = detect_nan_for_str_column(df, column_names=None)
        >>> print(list(nan_col_pos))
        [1]
    """

    if column_names is None:
        column_names = data_frame.columns

    for x in column_names:
        temp = [str(v) for v in data_frame[x].unique() if isinstance(v, str)
                or np.isnan(v)]
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

        >>> print(rotation_mat)
        # [[-0.98803162  0.15425145]
        #  [-0.15425145 -0.98803162]]
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

        >>> print(df)
        #   key  value
        # 0   a      1
        # 1   b      2
    """

    dict_keys = list(input_dict.keys())
    dict_vals = list(input_dict.values())

    data_frame = pd.DataFrame({k: dict_keys, v: dict_vals})

    return data_frame


def parse_csr_matrix(path_to_csr, verbose=False, **kwargs):
    """
    Load in a compressed sparse row (CSR) or compressed row storage (CRS).

    :param path_to_csr: path where a CSR (e.g. .npz) file is saved
    :type path_to_csr: str
    :param verbose: whether to print relevant information in console
        as the function runs, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: optional parameters of
        `numpy.load <https://numpy.org/doc/stable/reference/generated/numpy.load>`_
    :return: a compressed sparse row
    :rtype: scipy.sparse.csr.csr_matrix

    **Example**::

        >>> import numpy as np_
        >>> import scipy.sparse
        >>> from pyhelpers.dir import cd
        >>> from pyhelpers.ops import parse_csr_matrix

        >>> data_ = np_.array([1, 2, 3, 4, 5, 6])
        >>> indices_ = np_.array([0, 2, 2, 0, 1, 2])
        >>> indptr_ = np_.array([0, 2, 3, 6])
        >>> csr_m = scipy.sparse.csr_matrix((data_, indices_, indptr_), shape=(3, 3))

        >>> path_to_csr_npz = cd("tests\\data", "csr_mat.npz")
        >>> np_.savez_compressed(path_to_csr_npz, indptr=csr_m.indptr,
        ...                      indices=csr_m.indices, data=csr_m.data,
        ...                      shape=csr_m.shape)

        >>> csr_mat_ = parse_csr_matrix(path_to_csr_npz, verbose=True)
        Loading "\\tests\\data\\csr_mat.npz" ... Done.

        >>> # .nnz gets the count of explicitly-stored values (non-zeros)
        >>> print((csr_mat_ != csr_m).count_nonzero() == 0)
        True

        >>> print((csr_mat_ != csr_m).nnz == 0)
        True
    """

    if verbose:
        print("Loading \"\\{}\"".format(os.path.relpath(path_to_csr)),
              end=" ... ")

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
        print("Failed. {}".format(e)) if verbose else ""


# For simple computation ---------------------------------------------------------------

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

        >>> import pandas as pd_
        >>> from pyhelpers.ops import get_extreme_outlier_bounds

        >>> data = pd_.DataFrame(range(100), columns=['col'])

        >>> lo_bound, up_bound = get_extreme_outlier_bounds(data, k=1.5)

        >>> print((lo_bound, up_bound))
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
    `scipy.stats.iqr
    <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.iqr.html>`_.

    :param num_dat: an array of numbers
    :type num_dat: array-like
    :return: interquartile range of ``num_dat``
    :rtype: float

    **Example**::

        >>> import pandas as pd_
        >>> from pyhelpers.ops import interquartile_range

        >>> data = pd_.DataFrame(range(100), columns=['col'])

        >>> iqr_ = interquartile_range(data)
        >>> print(iqr_)
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
    :type lookup_dates: list or tuple or collections.abc.Iterable
    :param as_datetime: whether to return a datetime.datetime-formatted date,
        defaults to ``False``
    :type as_datetime: bool
    :param fmt: datetime format, defaults to ``'%Y-%m-%d %H:%M:%S.%f'``
    :type fmt: str
    :return: the date that is closest to the given ``date``
    :rtype: str or datetime.datetime

    **Examples**::

        >>> import pandas as pd_
        >>> from pyhelpers.ops import find_closest_date

        >>> date_list = pd_.date_range('2019-01-02', '2019-12-31')

        >>> date_ = '2019-01-01'
        >>> closest_date_ = find_closest_date(date_, date_list, as_datetime=True)
        >>> print(closest_date_)  # Timestamp('2019-01-02 00:00:00', freq='D')
        2019-01-02 00:00:00

        >>> date_ = pd_.to_datetime('2019-01-01')
        >>> closest_date_ = find_closest_date(date_, date_list, as_datetime=False)
        >>> print(closest_date_)  # '2019-01-02 00:00:00.000000'
        2019-01-02 00:00:00.000000
    """

    closest_date = min(lookup_dates,
                       key=lambda x: abs(pd.to_datetime(x) - pd.to_datetime(date)))

    if as_datetime:
        if isinstance(closest_date, str):
            closest_date = pd.to_datetime(closest_date)

    else:
        if isinstance(closest_date, datetime.datetime):
            closest_date = closest_date.strftime(fmt)

    return closest_date


# For graph plotting -------------------------------------------------------------------

def cmap_discretisation(cmap, n_colours):
    """
    Create a discrete colour ramp.

    See also [`CD-1 <http://sensitivecities.com/
    so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: a colormap instance, e.g. `matplotlib.cm.Accent`_
    :type cmap: matplotlib.colors.ListedColormap
    :param n_colours: number of colours
    :type n_colours: int
    :return: a discrete colormap from (the continuous) ``cmap``
    :rtype: matplotlib.colors.LinearSegmentedColormap

    .. _`matplotlib.cm.Accent`:
        https://matplotlib.org/3.2.1/gallery/color/colormap_reference.html

    **Example**::

        >>> import matplotlib.cm
        >>> import matplotlib.pyplot as plt_
        >>> import numpy as np_
        >>> from pyhelpers.ops import cmap_discretisation

        >>> cm_accent = cmap_discretisation(cmap=matplotlib.cm.Accent, n_colours=5)

        >>> fig, ax = plt_.subplots(figsize=(10, 2))
        >>> ax.imshow(np.resize(range(100), (5, 100)), cmap=cm_accent,
        ...           interpolation='nearest')
        >>> plt_.axis('off')
        >>> plt_.tight_layout()
        >>> plt_.show()

    .. image:: ../_images/cmap-discretisation.*
       :width: 400pt
    """

    if isinstance(cmap, str):
        import matplotlib.cm
        cmap = matplotlib.cm.get_cmap(cmap)

    colours_i = np.concatenate((np.linspace(0, 1., n_colours), (0., 0., 0., 0.)))
    colours_rgba = cmap(colours_i)
    indices = np.linspace(0, 1., n_colours + 1)
    c_dict = {}

    for ki, key in enumerate(('red', 'green', 'blue')):
        c_dict[key] = [(indices[x], colours_rgba[x - 1, ki], colours_rgba[x, ki])
                       for x in range(n_colours + 1)]

    import matplotlib.colors
    colour_map = matplotlib.colors.LinearSegmentedColormap(
        cmap.name + '_%d' % n_colours, c_dict, 1024)

    return colour_map


def colour_bar_index(cmap, n_colours, labels=None, **kwargs):
    """
    Create a colour bar.

    To stop making off-by-one errors. Takes a standard colour ramp, and discretizes it,
    then draws a colour bar with correctly aligned labels.

    See also [`CBI-1 <http://sensitivecities.com/
    so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: a colormap instance, e.g. `matplotlib.cm.Accent`_
    :type cmap: matplotlib.colors.ListedColormap
    :param n_colours: number of colours
    :type n_colours: int
    :param labels: a list of labels for the colour bar, defaults to ``None``
    :type labels: list or None
    :param kwargs: optional parameters of `matplotlib.pyplot.colorbar`_
    :return: a colour bar object
    :rtype: matplotlib.colorbar.Colorbar

    .. _`matplotlib.cm.Accent`:
        https://matplotlib.org/3.2.1/gallery/color/colormap_reference.html
    .. _`matplotlib.pyplot.colorbar`:
        https://matplotlib.org/api/_as_gen/matplotlib.pyplot.colorbar.html

    **Examples**::

        >>> import matplotlib.cm
        >>> import matplotlib.pyplot as plt_
        >>> from pyhelpers.ops import colour_bar_index

        >>> cmap_ = matplotlib.cm.Accent
        >>> n_colours_ = 5

        >>> plt_.figure(figsize=(2, 6))
        >>> cbar = colour_bar_index(cmap_, n_colours_)
        >>> cbar.ax.tick_params(labelsize=18)
        >>> plt_.axis('off')
        >>> plt_.tight_layout()
        >>> plt_.show()

    .. image:: ../_images/colour-bar-index-1.*
        :width: 120pt

    .. code-block:: python

        >>> labels_ = list('abcde')

        >>> plt_.figure(figsize=(2, 6))
        >>> cbar = colour_bar_index(cmap_, n_colours_, labels_)
        >>> cbar.ax.tick_params(labelsize=18)
        >>> plt_.axis('off')
        >>> plt_.tight_layout()
        >>> plt_.show()

    .. image:: ../_images/colour-bar-index-2.*
       :width: 120pt
    """

    cmap = cmap_discretisation(cmap, n_colours)

    import matplotlib.cm
    mappable = matplotlib.cm.ScalarMappable(cmap=cmap)
    mappable.set_array(np.array([]))
    mappable.set_clim(-0.5, n_colours + 0.5)

    import matplotlib.pyplot as plt
    colour_bar = plt.colorbar(mappable, **kwargs)
    colour_bar.set_ticks(np.linspace(0, n_colours, n_colours))
    colour_bar.set_ticklabels(range(n_colours))

    if labels:
        colour_bar.set_ticklabels(labels)

    return colour_bar


# For web scraping ---------------------------------------------------------------------

def fake_requests_headers(random=False):
    """
    Make a fake HTTP headers for
    `requests.get <https://requests.readthedocs.io/en/master/user/
    advanced/#request-and-response-objects>`_.

    :param random: whether to go for a random agent, defaults to ``False``
    :type random: bool
    :return: fake HTTP headers
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.ops import fake_requests_headers

        >>> fake_headers_ = fake_requests_headers()
        >>> print(fake_headers_)
        {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36'}

        >>> fake_headers_ = fake_requests_headers(random=True)
        >>> print(fake_headers_)
        {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36'
                       ' (KHTML, like Gecko) Chrome/36.0.1944.0 Safari/537.36'}
    """

    import fake_useragent

    fake_user_agent = fake_useragent.UserAgent(verify_ssl=False)

    fake_headers = {'User-Agent': fake_user_agent.random if random else fake_user_agent.chrome}

    return fake_headers


def download_file_from_url(url, path_to_file, wait_to_retry=3600, random_header=False,
                           **kwargs):
    """
    Download an object available at the given ``url``.

    See also [`DFFU-1 <https://stackoverflow.com/questions/37573483/>`_].

    :param url: URL
    :type url: str
    :param path_to_file: a full path to which the downloaded object is saved as
    :type path_to_file: str
    :param wait_to_retry: a wait time to retry downloading,
        defaults to ``3600`` (in second)
    :type wait_to_retry: int or float
    :param random_header: whether to go for a random agent, defaults to ``False``
    :type random_header: bool
    :param kwargs: optional parameters of
        `open <https://docs.python.org/3/library/functions.html#open>`_

    **Example**::

        >>> from pyhelpers.dir import cd
        >>> from pyhelpers.ops import download_file_from_url

        >>> url_to_python_logo = 'https://www.python.org/static/community_logos/' \
        ...                      'python-logo-master-v3-TM.png'

        >>> img_dir = cd("tests\\images")
        >>> path_to_python_logo_png = cd(img_dir, "python-logo.png")

        >>> download_file_from_url(url_to_python_logo, path_to_python_logo_png)
    """

    import requests

    headers = fake_requests_headers(random_header)
    # Streaming, so we can iterate over the response
    resp = requests.get(url, stream=True, headers=headers)

    if resp.status_code == 429:
        time.sleep(wait_to_retry)

    total_size = int(resp.headers.get('content-length'))  # Total size in bytes
    block_size = 1024 * 1024
    wrote = 0

    directory = os.path.dirname(path_to_file)
    if directory == "":
        path_to_file = os.path.join(os.getcwd(), path_to_file)
    else:
        if not os.path.exists(directory):
            os.makedirs(directory)

    with open(path_to_file, mode='wb', **kwargs) as f:
        for data in tqdm.tqdm(resp.iter_content(block_size, decode_unicode=True),
                              total=total_size // block_size, unit='MB'):
            wrote = wrote + len(data)
            try:
                f.write(data)
            except TypeError:
                f.write(data.encode())
        f.close()

    resp.close()

    if total_size != 0 and wrote != total_size:
        print("ERROR, something went wrong!")
