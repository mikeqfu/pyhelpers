"""Test the module ``_cache.py``"""

import os

import pytest


def test__check_dependency():
    from pyhelpers._cache import _check_dependency

    psycopg2_ = _check_dependency(name='psycopg2')
    assert psycopg2_.__name__ == 'psycopg2'

    sqlalchemy_dialects = _check_dependency(name='dialects', package='sqlalchemy')
    assert sqlalchemy_dialects.__name__ == 'sqlalchemy.dialects'

    gdal_ = _check_dependency(name='gdal', package='osgeo')
    assert gdal_.__name__ == 'osgeo.gdal'

    err_msg = ("Missing optional dependency 'unknown_package'. "
               "Use pip or conda to install it, e.g. 'pip install unknown_package'.")
    with pytest.raises(ModuleNotFoundError, match=err_msg):
        _ = _check_dependency(name='unknown_package')


def test__check_rel_pathname():
    from pyhelpers._cache import _check_rel_pathname

    pathname = ""
    pathname_ = _check_rel_pathname(pathname=pathname)
    assert pathname_ == pathname


def test__get_rel_pathname():
    from pyhelpers._cache import _get_rel_pathname

    res = _get_rel_pathname(os.path.curdir)
    assert res == '.'

    res = _get_rel_pathname("C:\\Windows")
    assert res == "C:\\Windows"


def test__check_file_pathname():
    from pyhelpers._cache import _check_file_pathname

    python_exe = "python.exe"

    python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe)
    assert python_exe_exists

    possible_paths = ["C:\\Program Files\\Python310", "C:\\Program Files\\Python310\\python.exe"]
    python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe, target=possible_paths[0])
    assert not python_exe_exists
    python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe, target=possible_paths[1])
    assert python_exe_exists
    python_exe_exists, path_to_python_exe = _check_file_pathname(possible_paths[1])
    assert python_exe_exists

    text_exe = "pyhelpers.exe"
    test_exe_exists, path_to_test_exe = _check_file_pathname(text_exe, possible_paths)
    assert not test_exe_exists
    assert os.path.relpath(path_to_test_exe) == 'pyhelpers.exe'


def test__format_err_msg():
    from pyhelpers._cache import _format_err_msg

    res = _format_err_msg(None)
    assert res == ''

    res = _format_err_msg("test")
    assert res == 'test.'

    res = _format_err_msg("test", msg="Failed.")
    assert res == 'Failed. test.'


def test__print_failure_msg(capfd):
    from pyhelpers._cache import _print_failure_msg

    _print_failure_msg('test', msg="Failed.")
    out, _ = capfd.readouterr()
    assert out == 'Failed. test.\n'


if __name__ == '__main__':
    pytest.main()
