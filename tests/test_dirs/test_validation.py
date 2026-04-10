"""
Tests the :mod:`~pyhelpers.dirs.validation` submodule.
"""

import os
import tempfile
from pathlib import Path

import pytest

from pyhelpers.dirs.validation import check_files_exist, check_relative_pathname, \
    get_file_pathnames, is_path_to_dir, normalize_pathname, resolve_dir, validate_filename


@pytest.fixture(scope='module')
def test_dir_name():
    return Path(__file__).resolve().parents[1] / "data"


def test_normalize_pathname():
    pathname = normalize_pathname("tests\\data\\dat.csv")
    assert pathname == 'tests/data/dat.csv'

    pathname = normalize_pathname("tests\\data\\dat.csv", add_slash=True)
    assert pathname == './tests/data/dat.csv'

    pathname = normalize_pathname("tests//data/dat.csv".encode('utf-8'))
    assert pathname == 'tests/data/dat.csv'

    pathname = Path("tests\\data/dat.csv")
    pathname_1 = normalize_pathname(pathname, sep=os.path.sep)
    pathname_2 = normalize_pathname(pathname, sep=os.path.sep, add_slash=True)
    if os.name == 'nt':
        assert pathname_1 == 'tests\\data\\dat.csv'
        assert pathname_2 == '.\\tests\\data\\dat.csv'
    else:
        assert pathname_1 == 'tests/data/dat.csv'
        assert pathname_2 == './tests/data/dat.csv'


def test_is_path_to_dir():
    # noinspection PyTypeChecker
    assert not is_path_to_dir(1)
    assert not is_path_to_dir("tests")
    assert is_path_to_dir("/tests")

    if os.name == 'nt':
        assert is_path_to_dir("\\tests")


def test_resolve_dir():
    dat_dir = resolve_dir()
    assert os.path.relpath(dat_dir) == '.'
    dat_dir = resolve_dir(os.getcwd())
    assert os.path.relpath(dat_dir) == '.'

    dat_dir = resolve_dir("tests")
    assert os.path.relpath(dat_dir) == 'tests'
    dat_dir = resolve_dir(b"tests")
    assert os.path.relpath(dat_dir) == 'tests'
    dat_dir = resolve_dir(Path("tests"))
    assert os.path.relpath(dat_dir) == 'tests'

    dat_dir = resolve_dir(subdir="data")
    assert os.path.relpath(dat_dir) == 'data'


def test_validate_filename():
    temp_pathname_ = tempfile.NamedTemporaryFile()
    temp_pathname_0 = temp_pathname_.name + '.txt'

    open(temp_pathname_0, 'w').close()
    assert os.path.isfile(temp_pathname_0)

    temp_pathname_1 = validate_filename(temp_pathname_0)
    assert os.path.splitext(temp_pathname_1)[0].endswith('(1)')

    open(temp_pathname_1, 'w').close()
    temp_pathname_2 = validate_filename(temp_pathname_1)
    assert os.path.splitext(temp_pathname_2)[0].endswith('(2)')

    os.remove(temp_pathname_0)
    os.remove(temp_pathname_1)


def test_get_file_pathnames(test_dir_name):
    dat_filenames = os.listdir(test_dir_name)

    result_1 = get_file_pathnames(test_dir_name)
    assert isinstance(result_1, list)
    assert all(os.path.basename(x) in dat_filenames for x in result_1)

    result_2 = get_file_pathnames(test_dir_name, incl_subdir=True)
    assert all(os.path.basename(x) in dat_filenames for x in result_2)

    result_3 = get_file_pathnames(test_dir_name, file_ext=".txt")
    assert all(os.path.basename(x) in ['dat.txt', 'zipped.txt'] for x in result_3)

    result_4 = get_file_pathnames(test_dir_name, file_ext=".txt", incl_subdir=True)
    assert all(os.path.basename(x) in ['dat.txt', 'zipped.txt'] for x in result_4)


def test_check_files_exist(test_dir_name, capfd):
    assert check_files_exist(["dat.csv", "dat.txt"], test_dir_name)
    rslt = check_files_exist(["dat.csv", "dat.txt", "dat_0.txt"], test_dir_name, verbose=True)
    out, _ = capfd.readouterr()
    assert rslt is False
    assert "Error: Required files are not satisfied, missing files are: ['dat_0.txt']" in out


def test_check_relative_pathname():
    pathname = ""
    rel_path = check_relative_pathname(pathname=pathname)
    assert rel_path == pathname

    pathname = os.path.curdir
    rel_path = check_relative_pathname(os.path.curdir)
    assert rel_path == pathname

    if os.name == 'nt':
        pathname = "C:/Windows"
        rel_path = check_relative_pathname(pathname)
        assert os.path.splitdrive(rel_path)[0] == os.path.splitdrive(pathname)[0]

    # Test an absolute path outside the working directory
    home_dir = os.path.expanduser("~")  # Cross-platform home directory
    rel_path = check_relative_pathname(home_dir, normalized=False)
    assert rel_path == home_dir  # Should return unchanged

    # Test a relative path within the current working directory
    subdir = os.path.join(os.getcwd(), "test_dir")
    rel_path = check_relative_pathname(subdir)
    assert rel_path == "test_dir"


if __name__ == '__main__':
    pytest.main()
