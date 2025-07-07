"""
Tests the :mod:`~pyhelpers.text.similarity` submodule.
"""

import pytest

from pyhelpers.text.similarity import *


def test_euclidean_distance_between_texts():
    txt_1, txt_2 = 'This is an apple.', 'That is a pear.'

    euclidean_distance = euclidean_distance_between_texts(txt_1, txt_2)
    assert euclidean_distance == 2.449489742783178


def test_cosine_similarity_between_texts():
    txt1, txt2 = 'This is an apple.', 'That is a pear.'
    cos_sim = cosine_similarity_between_texts(txt1, txt2)
    assert cos_sim == 0.25
    cos_dist = cosine_similarity_between_texts(txt1, txt2, cosine_distance=True)  # 1 - cos_sim
    assert cos_dist == 0.75

    txt1, txt2 = 'up-to-date', 'Up to date'
    cos_sim = cosine_similarity_between_texts(txt1, txt2)
    assert int(cos_sim) == 1
    cos_dist = cosine_similarity_between_texts(txt1, txt2, cosine_distance=True)  # 1 - cos_sim
    assert int(cos_dist) == 0


def test_find_matched_str():
    lookup_lst = ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel']
    res = find_matched_str('apple', lookup_lst)
    assert list(res) == []

    lookup_lst += ['apple']
    assert lookup_lst == ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel', 'apple']

    res = find_matched_str('apple', lookup_lst)
    assert list(res) == ['apple']

    res = find_matched_str(r'app(le)?', lookup_lst)
    assert list(res) == ['app', 'apple']


def test_find_similar_str():
    from pyhelpers.text.similarity import _find_str_by_rapidfuzz

    lookup_lst = [
        'Anglia',
        'East Coast',
        'East Midlands',
        'North and East',
        'London North Western',
        'Scotland',
        'South East',
        'Wales',
        'Wessex',
        'Western']

    y = find_similar_str('angle', lookup_list=lookup_lst)
    assert y == 'Anglia'
    y = find_similar_str('angle', lookup_list=lookup_lst, n=2)
    assert y == ['Anglia', 'Wales']

    y = find_similar_str('angle', lookup_list=lookup_lst, engine='rapidfuzz')
    assert y == 'Anglia'
    y = find_similar_str('angle', lookup_lst, n=2, engine='rapidfuzz')
    assert y == ['Anglia', 'Wales']

    y = find_similar_str('x', lookup_list=lookup_lst)
    assert y is None
    y = find_similar_str('x', lookup_list=lookup_lst, cutoff=0.25)
    assert y == 'Wessex'
    y = find_similar_str('x', lookup_list=lookup_lst, n=2, cutoff=0.25)
    assert y == 'Wessex'

    y = find_similar_str('x', lookup_list=lookup_lst, engine='fuzz')
    assert y == 'Wessex'
    y = find_similar_str('x', lookup_list=lookup_lst, n=2, engine='fuzz')
    assert y == ['Wessex', 'Western']

    y = find_similar_str('123', lookup_list=lookup_lst, n=1, engine='fuzz')
    assert y is None

    y = find_similar_str('anglia', lookup_list=lookup_lst, n=1, engine=_find_str_by_rapidfuzz)
    assert y == 'Anglia'

    y = find_similar_str('123', lookup_list=lookup_lst, n=1, engine=_find_str_by_rapidfuzz)
    assert y is None

    with pytest.raises(Exception):
        find_similar_str('anglia', lookup_list=lookup_lst, n=1, engine=str)


if __name__ == '__main__':
    pytest.main()
