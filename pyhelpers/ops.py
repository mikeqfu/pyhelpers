""" A module for miscellaneous use. """

import collections.abc
import datetime
import inspect
import itertools
import math
import os
import re
import time
import types

import numpy as np
import pandas as pd
import tqdm


def download_file_from_url(url, path_to_file, wait_to_retry=3600, **kwargs):
    """
    Download an object available at the given ``url``.

    See also [`DFFU-1 <https://stackoverflow.com/questions/37573483/>`_].

    :param url: URL
    :type url: str
    :param path_to_file: a full path to which the downloaded object is saved as
    :type path_to_file: str
    :param wait_to_retry: a wait time to retry downloading, defaults to ``3600`` (in second)
    :type wait_to_retry: int, float
    :param kwargs: optional parameters of `open <https://docs.python.org/3/library/functions.html#open>`_

    **Example**::

        from pyhelpers.dir import cd
        from pyhelpers.ops import download_file_from_url

        wait_to_retry = 3600

        url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        path_to_file = cd("tests/images", "python-logo.png")

        download_file_from_url(url, path_to_file, wait_to_retry)
    """

    import requests
    import fake_useragent

    headers = {'User-Agent': fake_useragent.UserAgent().random}
    resp = requests.get(url, stream=True, headers=headers)  # Streaming, so we can iterate over the response

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
            f.write(data)
    f.close()

    resp.close()

    if total_size != 0 and wrote != total_size:
        print("ERROR, something went wrong!")


def confirmed(prompt=None, resp=False, confirmation_required=True):
    """
    Type to confirm whether to proceed or not.

    See also [`C-1 <http://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param prompt: a message that prompts an response (Yes/No), defaults to ``None``
    :type prompt: str, None
    :param resp: default response, defaults to ``False``
    :type resp: bool
    :param confirmation_required: whether to require users to confirm and proceed, defaults to ``True``
    :type confirmation_required: bool
    :return: a response
    :rtype: bool

    **Example**::

        from pyhelpers.ops import confirmed

        prompt = "Create Directory?"
        confirmed(prompt, resp=True)
        # Create Directory? [No]|Yes:
        # >? yes
        # True
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


def get_variable_name(variable):
    """
    Get a variable's name as a string.

    :param variable: any
    :type variable: any
    :return: name of the given parameter
    :rtype: str

    **Examples**::

        from pyhelpers.ops import get_variable_name

        x = 1
        get_variable_name(x)  # 'x'

        y = 2
        get_variable_name(y)  # 'y'

        y = x
        get_variable_name(y)  # 'x'
    """

    local_variables = inspect.currentframe().f_back.f_locals.items()
    var_str = [var_name for var_name, var_val in local_variables if var_val is variable]
    if len(var_str) > 1:
        var_str = [x for x in var_str if '_' not in x][0]
    else:
        var_str = var_str[0]
    return var_str


def get_variable_names(*variable):
    """
    Get names of a sequence of variables.

    :param variable: (a sequence of) any variable(s)
    :type variable: any
    :return: (a sequence of) variable name(s)
    :rtype: generator

    **Examples**::

        from pyhelpers.ops import get_variable_names

        x = 1
        var_name = get_variable_names(x)
        print(list(var_name))  # ['x']

        y = 2
        var_names = get_variable_names(x, y)
        print(list(var_names))  # ['x', 'y']

        y = 1
        var_names = get_variable_names(x, y)
        print(list(var_names))  # ['x', 'x']
    """

    local_variables = inspect.currentframe().f_back.f_locals.items()
    for v in variable:
        var_str = [var_name for var_name, var_val in local_variables if var_val is v]
        if len(var_str) > 1:
            var_str = [x for x in var_str if '_' not in x][0]
        else:
            var_str = var_str[0]
        yield var_str


def split_list_by_size(lst, sub_len):
    """
    Split a list into (evenly sized) sub-lists.

    See also [`SLBS-1 <https://stackoverflow.com/questions/312443/>`_].

    :param lst: a list of any
    :type lst: list
    :param sub_len: length of a sub-list
    :type sub_len: int
    :return: a sequence of ``sub_len``-sized sub-lists from ``lst``
    :rtype: generator

    **Example**::

        from pyhelpers.ops import split_list_by_size

        lst = list(range(0, 10))
        sub_len = 3

        lists = split_list_by_size(lst, sub_len)
        print(list(lists))  # [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    """

    for i in range(0, len(lst), sub_len):
        yield lst[i:i + sub_len]


def split_list(lst, num_of_sub) -> types.GeneratorType:
    """
    Split a list into a number of equally-sized sub-lists.

    See also [`SL-1 <https://stackoverflow.com/questions/312443/>`_].

    :param lst: a list of any
    :type lst: list
    :param num_of_sub: number of sub-lists
    :type num_of_sub: int
    :return: a total of ``num_of_sub`` sub-lists from ``lst``
    :rtype: generator

    **Example**::

        from pyhelpers.ops import split_list

        lst = list(range(0, 10))
        num_of_sub = 3

        lists = list(split_list(lst, num_of_sub))
        print(list(lists))  # [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]
    """

    chunk_size = math.ceil(len(lst) / num_of_sub)
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def split_iterable(iterable, chunk_size):
    """
    Split a list into (evenly sized) chunks.

    See also [`SI-1 <https://stackoverflow.com/questions/24527006/>`_].

    :param iterable: iterable object
    :type iterable: iterable object
    :param chunk_size: length of a chunk
    :type chunk_size: int
    :return: a sequence of equally-sized chunks from ``iterable``
    :rtype: generator

    **Examples**::

        import pandas as pd
        from pyhelpers.ops import split_iterable

        iterable = list(range(0, 10))
        chunk_size = 3
        res = split_iterable(iterable, chunk_size)
        for x in res:
            print(list(x))
        # [0, 1, 2]
        # [3, 4, 5]
        # [6, 7, 8]
        # [9]

        iterable = pd.Series(range(0, 10))
        for x in split_iterable(iterable, chunk_size):
            print(list(x))
        # [0, 1, 2]
        # [3, 4, 5]
        # [6, 7, 8]
        # [9]
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

        from pyhelpers.ops import update_nested_dict

        source_dict = {'key_1': 1}
        updates = {'key_2': 2}
        update_nested_dict(source_dict, updates)  # {'key_1': 1, 'key_2': 2}

        source_dict = {'key': 'val_old'}
        updates = {'key': 'val_new'}
        update_nested_dict(source_dict, updates)  # {'key': 'val_new'}

        source_dict = {'key': {'k1': 'v1_old', 'k2': 'v2'}}
        updates = {'key': {'k1': 'v1_new'}}
        update_nested_dict(source_dict, updates)  # {'key': {'k1': 'v1_new', 'k2': 'v2'}}

        source_dict = {'key': {'k1': {}, 'k2': 'v2'}}
        updates = {'key': {'k1': 'v1'}}
        update_nested_dict(source_dict, updates)  # {'key': {'k1': 'v1', 'k2': 'v2'}}

        source_dict = {'key': {'k1': 'v1', 'k2': 'v2'}}
        updates = {'key': {'k1': {}}}
        update_nested_dict(source_dict, updates)  # {'key': {'k1': 'v1', 'k2': 'v2'}}
    """

    for key, val in updates.items():
        if isinstance(val, collections.abc.Mapping) or isinstance(val, dict):
            source_dict[key] = update_nested_dict(source_dict.get(key, {}), val)
        elif isinstance(val, list):
            source_dict[key] = (source_dict.get(key, []) + val)
        else:
            source_dict[key] = updates[key]
    return source_dict


def get_all_values_from_nested_dict(key, target_dict) -> types.GeneratorType:
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
    :rtype: generator

    **Examples**::

        from pyhelpers.ops import get_all_values_from_nested_dict

        key = 'key'
        target_dict = {'key': 'val'}
        val = get_all_values_from_nested_dict(key, target_dict)
        print(list(val))  # [['val']]

        key = 'k1'
        target_dict = {'key': {'k1': 'v1', 'k2': 'v2'}}
        val = get_all_values_from_nested_dict(key, target_dict)
        print(list(val))  #  [['v1']]

        key = 'k1'
        target_dict = {'key': {'k1': ['v1', 'v1_1']}}
        val = get_all_values_from_nested_dict(key, target_dict)
        print(list(val))  #  [['v1', 'v1_1']]

        key = 'k2'
        target_dict = {'key': {'k1': 'v1', 'k2': ['v2', 'v2_1']}}
        val = get_all_values_from_nested_dict(key, target_dict)
        print(list(val))  #  [['v2', 'v2_1']]
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

        from pyhelpers.ops import remove_multiple_keys_from_dict

        target_dict = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'k4': 'v4', 'k5': 'v5'}
        remove_multiple_keys_from_dict(target_dict, 'k1', 'k3', 'k4')
        print(target_dict)  # {'k2': 'v2', 'k5': 'v5'}
    """

    # assert isinstance(dictionary, dict)
    for k in keys:
        if k in target_dict.keys():
            target_dict.pop(k)


def get_extreme_outlier_bounds(num_dat, k=1.5):
    """
    Get upper and lower bounds for removing extreme outliers.

    :param num_dat: an array of numbers
    :type num_dat: array-like
    :param k: a scale coefficient associated with interquartile range, defaults to ``1.5``
    :type k: float, int
    :return: (lower bound, upper bound)
    :rtype: tuple

    **Example**::

        import pandas as pd
        from pyhelpers.ops import get_extreme_outlier_bounds

        num_dat = pd.DataFrame(range(100), columns=['col'])
        k = 1.5
        lower_bound, upper_bound = get_extreme_outlier_bounds(num_dat, k)  # (0.0, 148.5)
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
    :type num_dat: array-like
    :return: interquartile range of ``num_dat``
    :rtype: float

    **Example**::

        from pyhelpers.ops import interquartile_range

        num_dat = pd.DataFrame(range(100), columns=['col'])
        interquartile_range(num_dat)  # 49.5
    """

    iqr = np.subtract(*np.percentile(num_dat, [75, 25]))
    return iqr


def find_closest_date(date, lookup_dates, as_datetime=False, fmt='%Y-%m-%d %H:%M:%S.%f'):
    """
    Find the closest date of the given date from a list of dates.

    :param date: a date
    :type date: str, datetime.datetime
    :param lookup_dates: an array of dates
    :type lookup_dates: array-like
    :param as_datetime: whether to return a datetime.datetime-formatted date, defaults to ``False``
    :type as_datetime: bool
    :param fmt: datetime format, defaults to ``'%Y-%m-%d %H:%M:%S.%f'``
    :type fmt: str
    :return: the date that is closest to the given ``date``
    :rtype: str, datetime.datetime

    **Examples**::

        from pyhelpers.ops import find_closest_date

        date = pd.to_datetime('2019-01-01')
        date_list = []
        for d in range(1, 11): date_list.append(date + pd.Timedelta(days=d))
        find_closest_date(date, date_list, as_datetime=False)  # '2019-01-02 00:00:00.000000'

        date = '2019-01-01'
        date_list = ['2019-01-02', '2019-01-03', '2019-01-04', '2019-01-05', '2019-01-06']
        find_closest_date(date, date_list, as_datetime=True)  # Timestamp('2019-01-02 00:00:00')
    """

    closest_date = min(lookup_dates, key=lambda x: abs(pd.to_datetime(x) - pd.to_datetime(date)))
    if as_datetime:
        if isinstance(closest_date, str):
            closest_date = pd.to_datetime(closest_date)
    else:
        if isinstance(closest_date, datetime.datetime):
            closest_date = closest_date.strftime(fmt)
    return closest_date


def cmap_discretisation(cmap, n_colours):
    """
    Create a discrete colour ramp.

    See also [`CD-1 <http://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: a colormap instance, e.g. `matplotlib.cm.Accent`_
    :type cmap: matplotlib.colors.ListedColormap
    :param n_colours: number of colours
    :type n_colours: int
    :return: a discrete colormap from (the continuous) ``cmap``
    :rtype: matplotlib.colors.LinearSegmentedColormap

    .. _`matplotlib.cm.Accent`: https://matplotlib.org/3.2.1/gallery/color/colormap_reference.html

    **Example**::

        import matplotlib.cm
        import matplotlib.pyplot as plt
        import numpy as np
        from pyhelpers.ops import cmap_discretisation

        cmap = matplotlib.cm.Accent
        n_colours = 5
        cm_accent = cmap_discretisation(cmap, n_colours)

        x = np.resize(range(100), (5, 100))

        fig, ax = plt.subplots(figsize=(10, 2))
        ax.imshow(x, cmap=cm_accent, interpolation='nearest')
        plt.axis('off')
        plt.tight_layout()

    .. image:: _images/cmap-discretisation.*
       :width: 350pt
       :height: 70pt
    """

    if isinstance(cmap, str):
        import matplotlib.cm
        cmap = matplotlib.cm.get_cmap(cmap)

    colours_i = np.concatenate((np.linspace(0, 1., n_colours), (0., 0., 0., 0.)))
    colours_rgba = cmap(colours_i)
    indices = np.linspace(0, 1., n_colours + 1)
    c_dict = {}

    for ki, key in enumerate(('red', 'green', 'blue')):
        c_dict[key] = [(indices[x], colours_rgba[x - 1, ki], colours_rgba[x, ki]) for x in range(n_colours + 1)]

    import matplotlib.colors
    colour_map = matplotlib.colors.LinearSegmentedColormap(cmap.name + '_%d' % n_colours, c_dict, 1024)

    return colour_map


def colour_bar_index(cmap, n_colours, labels=None, **kwargs):
    """
    Create a colour bar.

    To stop making off-by-one errors.
    Takes a standard colour ramp, and discretizes it, then draws a colour bar with correctly aligned labels.

    See also [`CBI-1 <http://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: a colormap instance, e.g. `matplotlib.cm.Accent`_
    :type cmap: matplotlib.colors.ListedColormap
    :param n_colours: number of colours
    :type n_colours: int
    :param labels: a list of labels for the colour bar, defaults to ``None``
    :type labels: list, None
    :param kwargs: optional parameters of `matplotlib.pyplot.colorbar`_
    :return: a colour bar object
    :rtype: matplotlib.colorbar.Colorbar

    .. _`matplotlib.cm.Accent`: https://matplotlib.org/3.2.1/gallery/color/colormap_reference.html
    .. _`matplotlib.pyplot.colorbar`: https://matplotlib.org/api/_as_gen/matplotlib.pyplot.colorbar.html

    **Examples**::

        import matplotlib.cm
        import matplotlib.pyplot as plt
        from pyhelpers.ops import colour_bar_index

        cmap = matplotlib.cm.Accent
        n_colours = 5

        plt.figure(figsize=(2, 6))
        cbar = colour_bar_index(cmap, n_colours)
        cbar.ax.tick_params(labelsize=18)
        plt.axis('off')
        plt.tight_layout()

    .. image:: _images/colour-bar-index-1.*
       :width: 120pt
       :height: 350pt

    .. code-block:: Python

        labels = list('abcde')

        plt.figure(figsize=(2, 6))
        colour_bar = colour_bar_index(cmap, n_colours, labels)
        colour_bar.ax.tick_params(labelsize=18)
        plt.axis('off')
        plt.tight_layout()

    .. image:: _images/colour-bar-index-2.*
       :width: 120pt
       :height: 350pt
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


def detect_nan_for_str_column(data_frame, column_names=None):
    """
    Detect if a str type column contains ``NaN`` when reading csv files.

    :param data_frame: a data frame to be examined
    :type data_frame: pandas.DataFrame
    :param column_names: a sequence of column names, if ``None``, all columns
    :type column_names: iterable, None
    :return: position index of the column that contains ``NaN``
    :rtype: generator

    **Example**::

        import numpy as np
        import pandas as pd
        from pyhelpers.ops import detect_nan_for_str_column

        data_frame = pd.DataFrame(np.resize(range(10), (10, 2)), columns=['a', 'b'])
        data_frame.iloc[3, 1] = np.nan

        nan_col_pos = detect_nan_for_str_column(data_frame, column_names=None)
        print(list(nan_col_pos))  # [1]
    """

    if column_names is None:
        column_names = data_frame.columns

    for x in column_names:
        if 'nan' in [str(v) for v in data_frame[x].unique() if isinstance(v, str) or np.isnan(v)]:
            yield data_frame.columns.get_loc(x)


def create_rotation_matrix(theta):
    """
    Create a rotation matrix (counterclockwise).

    :param theta: rotation angle (in radian)
    :type theta: int, float
    :return: a rotation matrix of shape (2, 2)
    :rtype: numpy.ndarray

    **Example**::

        from pyhelpers.ops import create_rotation_matrix

        theta = 30
        rotation_mat = create_rotation_matrix(theta)
        print(rotation_mat)
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

        from pyhelpers.ops import dict_to_dataframe

        input_dict = {'a': 1, 'b': 2}
        data_frame = dict_to_dataframe(input_dict)
        print(data_frame)
        #   key  value
        # 0   a      1
        # 1   b      2
    """
    dict_keys = list(input_dict.keys())
    dict_vals = list(input_dict.values())
    data_frame = pd.DataFrame({k: dict_keys, v: dict_vals})
    return data_frame
