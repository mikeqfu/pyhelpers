"""
Tests the :mod:`~pyhelpers.ops.manipulation` submodule.
"""

import typing

import matplotlib.cm
import matplotlib.pyplot as plt
import pytest

from pyhelpers._cache import example_dataframe
from pyhelpers.ops.manipulation import *


def test_loop_in_pairs():
    res = loop_in_pairs(iterable=[1])
    assert list(res) == []

    res = loop_in_pairs(iterable=range(0, 10))
    assert list(res) == [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)]


def test_split_list_by_size():
    lst_ = list(range(0, 10))
    assert lst_ == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    lists = split_list_by_size(lst_, sub_len=3)
    assert list(lists) == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


def test_split_list():
    lst_ = list(range(0, 10))
    assert lst_ == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    lists = split_list(lst_, num_of_sub=3)
    assert list(lists) == [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]


def test_split_iterable():
    iterable_1 = list(range(0, 10))
    iterable_1_ = split_iterable(iterable_1, chunk_size=3)
    assert isinstance(iterable_1_, typing.Generator)
    assert [list(dat) for dat in iterable_1_] == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    iterable_2 = pd.Series(range(0, 20))
    iterable_2_ = split_iterable(iterable_2, chunk_size=5)

    assert [list(dat) for dat in iterable_2_] == [
        [0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11, 12, 13, 14], [15, 16, 17, 18, 19]]


def test_update_dict():
    source_dict = {'key_1': 1}
    update_data = {'key_2': 2}
    upd_dict = update_dict(source_dict, updates=update_data)
    assert upd_dict == {'key_1': 1, 'key_2': 2}
    assert source_dict == {'key_1': 1}
    update_dict(source_dict, updates=update_data, inplace=True)
    assert source_dict == {'key_1': 1, 'key_2': 2}

    source_dict = {'key': 'val_old'}
    update_data = {'key': 'val_new'}
    upd_dict = update_dict(source_dict, updates=update_data)
    assert upd_dict == {'key': 'val_new'}

    source_dict = {'key': {'k1': 'v1_old', 'k2': 'v2'}}
    update_data = {'key': {'k1': 'v1_new'}}
    upd_dict = update_dict(source_dict, updates=update_data)
    assert upd_dict == {'key': {'k1': 'v1_new', 'k2': 'v2'}}

    source_dict = {'key': {'k1': {}, 'k2': 'v2'}}
    update_data = {'key': {'k1': 'v1'}}
    upd_dict = update_dict(source_dict, updates=update_data)
    assert upd_dict == {'key': {'k1': 'v1', 'k2': 'v2'}}

    source_dict = {'key': {'k1': 'v1', 'k2': 'v2'}}
    update_data = {'key': {'k1': {}}}
    upd_dict = update_dict(source_dict, updates=update_data)
    assert upd_dict == {'key': {'k1': 'v1', 'k2': 'v2'}}


def test_update_dict_keys():
    source_dict = {'a': 1, 'b': 2, 'c': 3}

    upd_dict = update_dict_keys(source_dict, replacements=None)
    assert upd_dict == {'a': 1, 'b': 2, 'c': 3}

    repl_keys = {'a': 'd', 'c': 'e'}
    upd_dict = update_dict_keys(source_dict, replacements=repl_keys)
    assert upd_dict == {'d': 1, 'b': 2, 'e': 3}

    source_dict = {'a': 1, 'b': 2, 'c': {'d': 3, 'e': {'f': 4, 'g': 5}}}

    repl_keys = {'d': 3, 'f': 4}
    upd_dict = update_dict_keys(source_dict, replacements=repl_keys)
    assert upd_dict == {'a': 1, 'b': 2, 'c': {3: 3, 'e': {4: 4, 'g': 5}}}


def test_get_dict_values():
    key_ = 'key'
    target_dict_ = {'key': 'val'}
    val = get_dict_values(key_, target_dict_)
    assert list(val) == [['val']]

    key_ = 'k1'
    target_dict_ = {'key': {'k1': 'v1', 'k2': 'v2'}}
    val = get_dict_values(key_, target_dict_)
    assert list(val) == [['v1']]

    key_ = 'k1'
    target_dict_ = {'key': {'k1': ['v1', 'v1_1']}}
    val = get_dict_values(key_, target_dict_)
    assert list(val) == [['v1', 'v1_1']]

    key_ = 'k2'
    target_dict_ = {'key': {'k1': 'v1', 'k2': ['v2', 'v2_1']}}
    val = get_dict_values(key_, target_dict_)
    assert list(val) == [['v2', 'v2_1']]


def test_remove_dict_keys():
    target_dict_ = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'k4': 'v4', 'k5': 'v5'}
    remove_dict_keys(target_dict_, 'k1', 'k3', 'k4')
    assert target_dict_ == {'k2': 'v2', 'k5': 'v5'}


def test_compare_dicts():
    d1 = {'a': 1, 'b': 2, 'c': 3}
    d2 = {'b': 2, 'c': 4, 'd': [5, 6]}

    items_modified, k_shared, k_unchanged, k_new, k_removed = compare_dicts(d1, d2)
    assert items_modified == {'c': [3, 4]}
    assert set(k_shared) == {'b', 'c'}
    assert k_unchanged == ['b']
    assert k_new == ['d']
    assert k_removed == ['a']


def test_merge_dicts():
    dict_a = {'a': 1}
    dict_b = {'b': 2}
    dict_c = {'c': 3}

    merged_dict = merge_dicts(dict_a, dict_b, dict_c)
    assert merged_dict == {'a': 1, 'b': 2, 'c': 3}

    dict_c_ = {'c': 4}
    merged_dict = merge_dicts(merged_dict, dict_c_)
    assert merged_dict == {'a': 1, 'b': 2, 'c': [3, 4]}

    dict_1 = merged_dict
    dict_2 = {'b': 2, 'c': 4, 'd': [5, 6]}
    merged_dict = merge_dicts(dict_1, dict_2)
    assert merged_dict == {'a': 1, 'b': 2, 'c': [[3, 4], 4], 'd': [5, 6]}


def test_detect_nan_for_str_column():
    dat = example_dataframe()
    dat.loc['Leeds', 'Latitude'] = None

    nan_col_pos = detect_nan_for_str_column(data_frame=dat, column_names=None)
    assert list(nan_col_pos) == [1]


def test_create_rotation_matrix():
    rot_mat = create_rotation_matrix(theta=30)
    assert np.array_equal(
        np.round(rot_mat, 8), np.array([[-0.98803162, 0.15425145], [-0.15425145, -0.98803162]]))


def test_dict_to_dataframe():
    test_dict = {'a': 1, 'b': 2}

    dat = dict_to_dataframe(input_dict=test_dict)
    isinstance(dat, pd.DataFrame)


def test_swap_cols():
    example_arr = example_dataframe(osgb36=True).to_numpy(dtype=int)

    # Swap the 0th and 1st columns
    new_arr = swap_cols(example_arr, c1=0, c2=1)
    assert np.array_equal(new_arr, np.array([[180371, 530039],
                                             [286868, 406705],
                                             [398113, 383830],
                                             [433553, 430147]]))

    new_list = swap_cols(example_arr, c1=0, c2=1, as_list=True)
    assert new_list == [[180371, 530039], [286868, 406705], [398113, 383830], [433553, 430147]]


def test_swap_rows():
    example_arr = example_dataframe(osgb36=True).to_numpy(dtype=int)

    # Swap the 0th and 1st rows
    new_arr = swap_rows(example_arr, r1=0, r2=1)
    assert np.array_equal(new_arr, np.array([[406705, 286868],
                                             [530039, 180371],
                                             [383830, 398113],
                                             [430147, 433553]]))

    new_list = swap_rows(example_arr, r1=0, r2=1, as_list=True)
    assert new_list == [[406705, 286868], [530039, 180371], [383830, 398113], [430147, 433553]]


def test_np_shift():
    arr = example_dataframe(osgb36=True).to_numpy()

    rslt1 = np_shift(arr, step=-1)
    assert np.array_equal(rslt1, np.array([[406705.8870136, 286868.1666422],
                                           [383830.0390357, 398113.0558309],
                                           [430147.4473539, 433553.3271173],
                                           [np.nan, np.nan]]),
                          equal_nan=True)

    rslt2 = np_shift(arr, step=1, fill_value=0)
    assert np.array_equal(rslt2, np.array([[0, 0],
                                           [530039, 180371],
                                           [406705, 286868],
                                           [383830, 398113]]))

    rslt3 = np_shift(arr, step=0)
    assert np.array_equal(rslt3, arr)


def test_cmap_discretisation():
    cm_accent = cmap_discretisation(matplotlib.colormaps['Accent'], n_colours=5)
    assert cm_accent.name == 'Accent_5'


def test_colour_bar_index():
    plt.figure(figsize=(2, 6))

    cbar = colour_bar_index(cmap=matplotlib.colormaps['Accent'], n_colours=5, labels=list('abcde'))
    cbar.ax.tick_params(labelsize=14)

    plt.close(fig='all')


if __name__ == '__main__':
    pytest.main()
