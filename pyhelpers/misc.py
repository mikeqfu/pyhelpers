""" Misc helper functions """

import collections
import inspect
import re

import numpy as np


# Type to confirm whether to proceed or not
def confirmed(prompt=None, resp=False, confirmation_required=True):
    """
    Reference: http://code.activestate.com/recipes/541096-prompt-the-user-for-confirmation/

    :param prompt: [str] or None
    :param resp: [bool]
    :param confirmation_required: [bool]
    :return:

    Example: confirm(prompt="Create Directory?", resp=True)
             Create Directory? Yes|No:
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


# ====================================================================================================================
""" Misc """


# Update a nested dictionary or similar mapping
def update_nested_dict(source_dict, overrides):
    """
    Reference: https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    :param source_dict: [dict]
    :param overrides: [dict]
    :return:
    """
    for key, val in overrides.items():
        if isinstance(val, collections.Mapping):
            source_dict[key] = update_nested_dict(source_dict.get(key, {}), val)
        elif isinstance(val, list):
            source_dict[key] = (source_dict.get(key, []) + val)
        else:
            source_dict[key] = overrides[key]
    return source_dict


# Get a variable's name as a string
def get_variable_name(variable):
    var_name = [k for k, v in locals().items() if v == variable][0]
    return var_name


# Get the given variable's name
def get_variable_names(*variable):
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
def divide_list_into_chunks(lst, chunk_size):
    """
    Yield successive n-sized chunks from a list
    Reference: https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


# Divide a list into sub-lists of equal length
def divide_list_equally(lst, chunk_size):
    """
    Yield successive n-sized chunks from l.
    Reference: https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


# Get all values in a nested dictionary
def get_all_values_from_nested_dict(key, target_dict):
    """
    Reference:
    https://gist.github.com/douglasmiranda/5127251
    https://stackoverflow.com/questions/9807634/find-all-occurrences-of-a-key-in-nested-python-dictionaries-and-lists

    :param key:
    :param target_dict: [dict]
    :return:
    """
    for k, v in target_dict.items():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for x in get_all_values_from_nested_dict(k, v):
                yield x
        elif isinstance(v, list):
            for d in v:
                for y in get_all_values_from_nested_dict(k, d):
                    yield y


# Remove multiple keys from a dictionary
def remove_multiple_keys(dictionary, *keys):
    assert isinstance(dictionary, dict)
    for k in keys:
        if k in dictionary.keys():
            dictionary.pop(k)


# Get upper and lower bounds for removing extreme outliers
def get_extreme_outlier_bounds(data_set, k=1.5):
    q1, q3 = np.percentile(data_set, 25), np.percentile(data_set, 75)
    iqr = q3 - q1
    lower_bound = np.max([0, q1 - k * iqr])
    upper_bound = q3 + k * iqr
    return lower_bound, upper_bound


# Convert compressed sparse matrix to dictionary
def csr_matrix_to_dict(csr_matrix, vectorizer):
    import pandas as pd

    features = vectorizer.get_feature_names()
    dict_data = []
    for i in range(len(csr_matrix.indptr) - 1):
        sid, eid = csr_matrix.indptr[i: i + 2]
        row_feat = [features[x] for x in csr_matrix.indices[sid:eid]]
        row_data = csr_matrix.data[sid:eid]
        dict_data.append(dict(zip(row_feat, row_data)))
    return pd.Series(dict_data).to_frame('word_count')


# Calculate interquartile range
def interquartile_range(x):
    """
    Alternative way: using scipy.stats.iqr(x)
    """
    return np.subtract(*np.percentile(x, [75, 25]))


# Find the closest date of the given 'data' from a list of dates
def find_closest_date(date, dates_list):
    return min(dates_list, key=lambda x: abs(x - date))


# A function for working with colour ramps
def cmap_discretisation(cmap_param, no_of_colours):
    """
    :param cmap_param: colormap instance, e.g. cm.jet
    :param no_of_colours: number of colours
    :return: a discrete colormap from the continuous colormap cmap.

    Reference: http://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB

    Example:
        x = np.resize(np.arange(100), (5, 100))
        d_jet = cmap_discretize(cm.jet, 5)
        plt.imshow(x, cmap=d_jet)
    """

    import matplotlib.cm
    import matplotlib.colors
    if isinstance(cmap_param, str):
        cmap_param = matplotlib.cm.get_cmap(cmap_param)
    colors_i = np.concatenate((np.linspace(0, 1., no_of_colours), (0., 0., 0., 0.)))
    colors_rgba = cmap_param(colors_i)
    indices = np.linspace(0, 1., no_of_colours + 1)
    c_dict = {}
    for ki, key in enumerate(('red', 'green', 'blue')):
        c_dict[key] = [(indices[x], colors_rgba[x - 1, ki], colors_rgba[x, ki]) for x in range(no_of_colours + 1)]
    return matplotlib.colors.LinearSegmentedColormap(cmap_param.name + '_%d' % no_of_colours, c_dict, 1024)


# A function for working with colour color bars
def colour_bar_index(no_of_colours, cmap_param, labels=None, **kwargs):
    """
    :param no_of_colours: number of colors
    :param cmap_param: colormap instance, eg. cm.jet
    :param labels:
    :param kwargs:
    :return:

    Reference: http://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB

    This is a convenience function to stop making off-by-one errors
    Takes a standard colour ramp, and discretizes it, then draws a colour bar with correctly aligned labels
    """

    import matplotlib.cm
    import matplotlib.pyplot
    cmap_param = cmap_discretisation(cmap_param, no_of_colours)
    mappable = matplotlib.cm.ScalarMappable(cmap=cmap_param)
    mappable.set_array(np.array([]))
    mappable.set_clim(-0.5, no_of_colours + 0.5)
    color_bar = matplotlib.pyplot.colorbar(mappable, **kwargs)
    color_bar.set_ticks(np.linspace(0, no_of_colours, no_of_colours))
    color_bar.set_ticklabels(range(no_of_colours))
    if labels:
        color_bar.set_ticklabels(labels)
    return color_bar
