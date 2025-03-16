"""
Tests the :mod:`~pyhelpers.ops.general` submodule.
"""

import time

import pytest

from pyhelpers._cache import _ANSI_ESCAPE_CODES
from pyhelpers.dbms import PostgreSQL
from pyhelpers.ops.general import *


def test_confirmed(monkeypatch):
    assert confirmed(confirmation_required=False)

    monkeypatch.setattr('builtins.input', lambda _: "Yes")
    assert confirmed()

    monkeypatch.setattr('builtins.input', lambda _: "")
    assert not confirmed()

    monkeypatch.setattr('builtins.input', lambda _: "no")
    assert not confirmed(resp=True)

    prompt = "Testing if the function works?"
    monkeypatch.setattr('builtins.input', lambda _: "Yes")
    assert confirmed(prompt=prompt, resp=False)


def test_get_obj_attr():
    res = get_obj_attr(PostgreSQL)
    assert isinstance(res, list)

    res = get_obj_attr(PostgreSQL, as_dataframe=True)
    assert isinstance(res, pd.DataFrame)
    assert res.columns.tolist() == ['attribute', 'value']
    res = get_obj_attr(PostgreSQL, col_names=['a', 'b'], as_dataframe=True)
    assert isinstance(res, pd.DataFrame)
    assert res.columns.tolist() == ['a', 'b']


def test_eval_dtype():
    from pyhelpers.ops import eval_dtype

    val_1 = '1'
    origin_val = eval_dtype(val_1)
    assert origin_val == 1

    val_2 = '1.1.1'
    origin_val = eval_dtype(val_2)
    assert origin_val == '1.1.1'


def test_hash_password():
    test_pwd = 'test%123'
    salt_size_ = 16
    sk = hash_password(password=test_pwd, salt_size=salt_size_)  # salt and key
    salt_data, key_data = sk[:salt_size_].hex(), sk[salt_size_:].hex()
    assert verify_password(password=test_pwd, salt=salt_data, key=key_data)

    test_pwd = b'test%123'
    sk = hash_password(password=test_pwd)
    salt_data, key_data = sk[:128].hex(), sk[128:].hex()
    assert verify_password(password=test_pwd, salt=salt_data, key=key_data)


def test_func_running_time(capfd):
    @func_running_time
    def test_func():
        print("Testing if the function works.")
        time.sleep(3)

    test_func()
    out, _ = capfd.readouterr()
    assert "INFO Finished running function: test_func, total: 3s" in out


def test_get_git_branch(capfd):
    branch_name = get_git_branch(verbose=True)
    out, _ = capfd.readouterr()
    if out:
        assert branch_name is None
    else:
        assert isinstance(branch_name, str)


def test_get_ansi_colour_code():
    color_codes = get_ansi_colour_code('red')
    assert color_codes == '\033[31m'

    color_codes = get_ansi_colour_code(['red', 'blue'])
    assert color_codes == ['\033[31m', '\033[34m']

    with pytest.raises(ValueError, match="'invalid_colour' is not a valid colour name."):
        _ = get_ansi_colour_code('invalid_colour')

    color_codes = get_ansi_colour_code('red', show_valid_colours=True)
    assert isinstance(color_codes, tuple)
    assert color_codes[0] == '\033[31m'
    assert color_codes[1] == set(_ANSI_ESCAPE_CODES)


if __name__ == '__main__':
    pytest.main()
