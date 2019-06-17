""" Text-related """

import re

import fuzzywuzzy.process
import nltk.metrics


# Find similar string from a list of strings
def find_similar_str(x, lookup_list, processor='fuzzywuzzy', score_cutoff=10, substitution_cost=100):
    """
    :param x: [str]
    :param lookup_list: [iterable]
    :param processor: [bool]
    :param score_cutoff: [bool]
    :param substitution_cost: [bool]
    :return: [str]
    """
    if processor == 'fuzzywuzzy':
        the_one = fuzzywuzzy.process.extractOne(x, lookup_list, score_cutoff=score_cutoff)
    elif processor == 'nltk':
        l_distances = [nltk.metrics.edit_distance(x, a, substitution_cost=substitution_cost) for a in lookup_list]
        the_one = lookup_list[l_distances.index(min(l_distances))]
    else:
        the_one = None
    return the_one


# Find from a list the closest, case-insensitive, str to the given one
def find_matched_str(x, lookup_list):
    """
    :param x: [str] If x is None, return None
    :param lookup_list: [iterable] or any other iterable object
    :return: [str], [list]
    """
    # assert isinstance(x, str), "'x' must be a string."
    # assert isinstance(lookup, list) or isinstance(lookup, tuple), "'lookup' must be a list/tuple"
    if x is '' or x is None:
        return None
    else:
        for y in lookup_list:
            if re.match(x, y, re.IGNORECASE):
                return y
