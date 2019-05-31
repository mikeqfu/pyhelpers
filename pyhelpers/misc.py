""" Misc helper functions """

import collections
import re


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
def get_var_name(var):
    var_name = [k for k, v in locals().items() if v == var][0]
    return var_name


# Split a list into (evenly sized) chunks
def split_list(lst, chunk_size):
    """Yield successive n-sized chunks from a list
    Reference: https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks

    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


# Get all values in a nested dictionary
def get_all_values(key, target_dict):
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
            for x in get_all_values(k, v):
                yield x
        elif isinstance(v, list):
            for d in v:
                for y in get_all_values(k, d):
                    yield y
        else:
            pass


#
def remove_multi_keys(dictionary, *keys):
    assert isinstance(dictionary, dict)
    for k in keys:
        if k in dictionary.keys():
            dictionary.pop(k)
