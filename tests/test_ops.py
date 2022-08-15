"""Test ops.py"""

import datetime

import pytest


def test_eval_dtype(capfd):
    from pyhelpers.ops import eval_dtype

    val_1 = '1'
    origin_val = eval_dtype(val_1)
    assert origin_val == 1

    val_2 = '1.1.1'
    origin_val = eval_dtype(val_2)
    assert origin_val == '1.1.1'


def test_gps_to_utc():
    from pyhelpers.ops import gps_to_utc

    utc_dt = gps_to_utc(gps_time=1271398985.7822514)

    assert utc_dt == datetime.datetime(2020, 4, 20, 6, 23, 5, 782251)


def test_parse_size():
    from pyhelpers.ops import parse_size

    assert parse_size(size='123.45 MB') == 129446707
    assert parse_size(size='123.45 MB', binary=False) == 123450000
    assert parse_size(size='123.45 MiB', binary=True) == 129446707
    assert parse_size(size='123.45 MiB', binary=False) == 129446707
    assert parse_size(size=129446707, precision=2) == '123.45 MiB'
    assert parse_size(size=129446707, binary=False, precision=2) == '129.45 MB'


def test_update_dict_keys():
    from pyhelpers.ops import update_dict_keys

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


def test_merge_dicts():
    from pyhelpers.ops import merge_dicts

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


if __name__ == '__main__':
    pytest.main()
