""" Miscellaneous helper functions """

import collections
import inspect
import numbers
import re
import types

import numpy as np


# Type to confirm whether to proceed or not
def confirmed(prompt=None, resp=False, confirmation_required=True):
    """
    :param prompt: [str; None (default)]
    :param resp: [bool] (default: False)
    :param confirmation_required: [bool] (default: True)
    :return: [bool]

    Example:
        prompt = "Create Directory?"
        confirm(prompt, resp=True)
        >> Create Directory? [No]|Yes: yes
        >> True

    Reference: http://code.activestate.com/recipes/541096-prompt-the-user-for-confirmation/
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


# Get a variable's name as a string
def get_variable_name(variable) -> str:
    """
    Example:
        x = 1
        print(get_variable_name(x))  # 'x'
    """
    local_variables = inspect.currentframe().f_back.f_locals.items()
    var_str = [var_name for var_name, var_val in local_variables if var_val is variable]
    if len(var_str) > 1:
        var_str = [x for x in var_str if '_' not in x][0]
    else:
        var_str = var_str[0]
    return var_str


# Get the given variable's name
def get_variable_names(*variable) -> list:
    """
    Examples:
        x = 1
        print(get_variable_names(x))  # ['x']
        y = 2
        get_variable_names(x, y)  # ['x', 'y']
    """
    local_variables = inspect.currentframe().f_back.f_locals.items()
    variable_list = []
    for v in variable:
        var_str = [var_name for var_name, var_val in local_variables if var_val is v]
        if len(var_str) > 1:
            var_str = [x for x in var_str if '_' not in x][0]
        else:
            var_str = var_str[0]
        variable_list.append(var_str)
    return variable_list


# Split a list into (evenly sized) chunks
def divide_list_into_chunks(lst, chunk_size) -> types.GeneratorType:
    """
    :param lst: [list]
    :param chunk_size: [int]
    :return: [types.GeneratorType] successive n-sized chunks from a list

    Example:
        lst = list(range(0, 10))
        chunk_size = 3
        list(divide_list_into_chunks(lst, chunk_size))  # [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    Reference: https://stackoverflow.com/questions/312443/
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


# Update a nested dictionary or similar mapping
def update_nested_dict(source_dict, updates) -> dict:
    """
    :param source_dict: [dict]
    :param updates: [dict]
    :return: [dict]

    Examples:
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
        update_nested_dict(source_dict, updates)  # {'key': {'k1': 'v1', 'k2': 'v2'}}  # It does not update with {}

    Reference: https://stackoverflow.com/questions/3232943/
    """
    for key, val in updates.items():
        if isinstance(val, collections.Mapping):
            source_dict[key] = update_nested_dict(source_dict.get(key, {}), val)
        elif isinstance(val, list):
            source_dict[key] = (source_dict.get(key, []) + val)
        else:
            source_dict[key] = updates[key]
    return source_dict


# Get all values in a nested dictionary
def get_all_values_from_nested_dict(key, target_dict) -> types.GeneratorType:
    """
    :param key: any object that can be the 'key' of a [dict]
    :param target_dict: [types.GeneratorType]

    Examples:
        key = 'k1'
        target_dict = {'key': {'k1': 'v1', 'k2': 'v2'}}
        list(get_all_values_from_nested_dict(key, target_dict))  # [['v1']]

        key = 'key'
        target_dict = {'key': 'val'}
        list(get_all_values_from_nested_dict(key, target_dict))  # [['val']]

        key = 'k1'
        target_dict = {'key': {'k1': ['v1', 'v1_1']}}
        list(get_all_values_from_nested_dict(key, target_dict))  # [['v1', 'v1_1']]

        key = 'k2'
        target_dict = {'key': {'k1': 'v1', 'k2': ['v2', 'v2_1']}}
        list(get_all_values_from_nested_dict(key, target_dict))  # [['v2', 'v2_1']]

    Reference:
    https://gist.github.com/douglasmiranda/5127251
    https://stackoverflow.com/questions/9807634/
    """
    for k, v in target_dict.items():
        if key == k:
            yield [v] if isinstance(v, str) else v
        elif isinstance(v, dict):
            for x in get_all_values_from_nested_dict(key, v):
                yield x
        elif isinstance(v, collections.Iterable):
            for d in v:
                if isinstance(d, dict):
                    for y in get_all_values_from_nested_dict(key, d):
                        yield y


# Remove multiple keys from a dictionary
def remove_multiple_keys_from_dict(target_dict, *keys):
    """
    :param target_dict: [dict]
    :param keys:
    
    Example:
        target_dict = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'k4': 'v4', 'k5': 'v5'}
        remove_multiple_keys_from_dict(target_dict, 'k1', 'k3', 'k4')  # {'k2': 'v2', 'k5': 'v5'}
    """
    # assert isinstance(dictionary, dict)
    for k in keys:
        if k in target_dict.keys():
            target_dict.pop(k)


# Get upper and lower bounds for removing extreme outliers
def get_extreme_outlier_bounds(data_set, k=1.5) -> tuple:
    """
    :param data_set: [array-like]
    :param k: [numbers.Number]
    :return: [tuple]
    """
    q1, q3 = np.percentile(data_set, 25), np.percentile(data_set, 75)
    iqr = q3 - q1
    lower_bound = np.max([0, q1 - k * iqr])
    upper_bound = q3 + k * iqr
    return lower_bound, upper_bound


# Calculate interquartile range
def interquartile_range(x) -> numbers.Number:
    """
    :param x: [array-like]
    :return: [numbers.Number]

    An alternative way to scipy.stats.iqr(x)
    """
    iqr = np.subtract(*np.percentile(x, [75, 25]))
    return iqr


# Find the closest date of the given 'date' from a list of dates
def find_closest_date(date, date_list, as_datetime=None, fmt="%Y-%m-%d %H:%M:%S.%f"):
    """
    :param date: [str; datetime.datetime]
    :param date_list: [array-like]
    :param as_datetime: [bool; None (default)]
    :param fmt: [str] (default: "%Y-%m-%d %H:%M:%S.%f")
    :return: [str; datetime.datetime]

    Examples:
        date = pd.to_datetime('2019-01-01')
        date_list = [date + pd.Timedelta(days=d) for d in range(1, 11)]
        find_closest_date(date, date_list)
        find_closest_date(date, date_list, as_datetime=False)

        date = '2019-01-01'
        date_list = ['2019-01-02', '2019-01-03', '2019-01-04', '2019-01-05', '2019-01-06']
        find_closest_date(date, date_list, as_datetime=True)
    """
    import pandas as pd
    closest_date = min(date_list, key=lambda x: abs(pd.to_datetime(x) - pd.to_datetime(date)))
    if as_datetime:
        if isinstance(closest_date, str):
            closest_date = pd.to_datetime(closest_date)
    else:
        if isinstance(closest_date, pd.datetime):
            closest_date = closest_date.strftime(fmt)
    return closest_date


# Colour ramps
def cmap_discretisation(cmap_param, no_of_colours):
    """
    :param cmap_param: colormap instance, e.g. cm.jet
    :param no_of_colours: number of colours
    :return: a discrete colormap from the continuous colormap cmap.

    Example:
        x = np.resize(np.arange(100), (5, 100))
        d_jet = cmap_discretize(cm.jet, 5)
        plt.imshow(x, cmap=d_jet)

    Reference: http://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB
    """
    if isinstance(cmap_param, str):
        import matplotlib.cm
        cmap_param = matplotlib.cm.get_cmap(cmap_param)

    colours_i = np.concatenate((np.linspace(0, 1., no_of_colours), (0., 0., 0., 0.)))
    colours_rgba = cmap_param(colours_i)
    indices = np.linspace(0, 1., no_of_colours + 1)
    c_dict = {}

    for ki, key in enumerate(('red', 'green', 'blue')):
        c_dict[key] = [(indices[x], colours_rgba[x - 1, ki], colours_rgba[x, ki]) for x in range(no_of_colours + 1)]

    import matplotlib.colors
    colour_map = matplotlib.colors.LinearSegmentedColormap(cmap_param.name + '_%d' % no_of_colours, c_dict, 1024)

    return colour_map


# Colour bars
def colour_bar_index(no_of_colours, cmap_param, labels=None, **kwargs):
    """
    :param no_of_colours: [int] number of colors
    :param cmap_param: colormap instance, eg. cm.jet
    :param labels: [list; None (default)]
    :param kwargs:

    To stop making off-by-one errors
    Takes a standard colour ramp, and discretizes it, then draws a colour bar with correctly aligned labels

    Reference: http://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB
    """
    cmap_param = cmap_discretisation(cmap_param, no_of_colours)

    import matplotlib.cm
    mappable = matplotlib.cm.ScalarMappable(cmap=cmap_param)
    mappable.set_array(np.array([]))
    mappable.set_clim(-0.5, no_of_colours + 0.5)

    import matplotlib.pyplot
    colour_bar = matplotlib.pyplot.colorbar(mappable, **kwargs)
    colour_bar.set_ticks(np.linspace(0, no_of_colours, no_of_colours))
    colour_bar.set_ticklabels(range(no_of_colours))

    if labels:
        colour_bar.set_ticklabels(labels)

    return colour_bar


# Detect if a str type column contains 'nan' when reading csv files
def detect_nan_for_str_column(pd_dataframe, column_names=None):
    if column_names:
        col_names = column_names
    else:
        col_names = pd_dataframe.columns
    for x in col_names:
        if 'nan' in [str(v) for v in pd_dataframe[x].unique() if isinstance(v, str) or np.isnan(v)]:
            yield pd_dataframe.columns.get_loc(x)
