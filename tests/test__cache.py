"""
Test the module ``_cache.py``
"""

import os
import sys

import pytest


def test__confirmed(monkeypatch, capfd):
    from pyhelpers._cache import _confirmed

    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    if _confirmed(prompt="Testing if the function works?", resp=True):
        print("Passed.")

    out, _ = capfd.readouterr()
    assert "Passed." in out


def test__check_dependency():
    from pyhelpers._cache import _check_dependency

    psycopg2 = _check_dependency(name='psycopg2')
    assert psycopg2.__name__ == 'psycopg2'

    sqlalchemy_dialects = _check_dependency(name='dialects', package='sqlalchemy')
    assert sqlalchemy_dialects.__name__ == 'sqlalchemy.dialects'

    gdal = _check_dependency(name='gdal', package='osgeo')
    assert gdal.__name__ == 'osgeo.gdal'

    err_msg = ("Missing optional dependency 'unknown_package'. "
               "Use `pip` or `conda` to install it, e.g. `pip install unknown_package`.")
    with pytest.raises(ModuleNotFoundError, match=err_msg):
        _ = _check_dependency(name='unknown_package')


def test__check_relative_pathname():
    from pyhelpers._cache import _check_relative_pathname

    pathname = ""
    rel_path = _check_relative_pathname(pathname=pathname)
    assert rel_path == pathname

    pathname = os.path.curdir
    rel_path = _check_relative_pathname(os.path.curdir)
    assert rel_path == pathname

    if os.name == 'nt':
        pathname = "C:/Windows"
        rel_path = _check_relative_pathname(pathname)
        assert rel_path == pathname

    # Test an absolute path outside the working directory
    home_dir = os.path.expanduser("~")  # Cross-platform home directory
    rel_path = _check_relative_pathname(home_dir)
    assert rel_path == home_dir  # Should return unchanged

    # Test a relative path within the current working directory
    subdir = os.path.join(os.getcwd(), "test_dir")
    rel_path = _check_relative_pathname(subdir)
    assert rel_path == "test_dir"


def test__check_file_pathname():
    from pyhelpers._cache import _check_file_pathname

    python_exe = os.path.basename(sys.executable)

    python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe)
    assert python_exe_exists
    assert path_to_python_exe == sys.executable

    # Use the directory containing Python
    python_dir = os.path.dirname(sys.executable)
    possible_paths = [python_dir, sys.executable]

    # Check if specifying Python's actual path works
    python_exe_exists, path_to_python_exe = _check_file_pathname(sys.executable)
    assert python_exe_exists
    assert path_to_python_exe == sys.executable
    python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe, target=os.getcwd())
    assert not python_exe_exists
    python_exe_exists, path_to_python_exe = _check_file_pathname(possible_paths[1])
    assert python_exe_exists

    # Check non-existent file
    text_exe = "pyhelpers.exe"
    test_exe_exists, path_to_test_exe = _check_file_pathname(text_exe, options=possible_paths)
    assert not test_exe_exists
    assert path_to_test_exe == text_exe  # Should return input name


def test__format_error_message():
    from pyhelpers._cache import _format_error_message

    res = _format_error_message(None)
    assert res == ''

    res = _format_error_message("test")
    assert res == 'test.'

    res = _format_error_message("test", prefix="Failed.")
    assert res == 'Failed. test.'


def test__print_failure_message(capfd):
    from pyhelpers._cache import _print_failure_message

    _print_failure_message('test', prefix="Failed.")
    out, _ = capfd.readouterr()
    assert out == 'Failed. test.\n'


if __name__ == '__main__':
    pytest.main()
