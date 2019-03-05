""" Text-related """

import re

import nltk.metrics


# Find similar string from a list of strings
def find_similar_str(s, str_list):
    l_distances = [nltk.metrics.edit_distance(s, a, substitution_cost=100) for a in str_list]
    the_one = str_list[l_distances.index(min(l_distances))]
    return the_one


# Find from a list the closest, case-insensitive, str to the given one
def find_matched_str(x, lookup):
    """
    :param x: [str] If x is None, return None
    :param lookup: [list], [tuple] or any other iterable object
    :return: [str], [list]
    """
    # assert isinstance(x, str), "'x' must be a string."
    # assert isinstance(lookup, list) or isinstance(lookup, tuple), "'lookup' must be a list/tuple"
    if x is '' or x is None:
        return None
    else:
        for y in lookup:
            if re.match(x, y, re.IGNORECASE):
                return y
