"""
Tests the :mod:`~pyhelpers.dirs.validation` submodule.
"""

import importlib.resources
import tempfile

import pytest

from pyhelpers.dirs.validation import *


def test_normalize_pathname():
    pathname = normalize_pathname("tests\\data\\dat.csv")
    assert pathname == 'tests/data/dat.csv'

    pathname = normalize_pathname("tests\\data\\dat.csv", add_slash=True)
    if os.name == 'nt':
        assert pathname == '.\\tests\\data\\dat.csv'
    else:
        assert pathname == './tests/data/dat.csv'

    pathname = normalize_pathname("tests//data/dat.csv".encode('utf-8'))
    assert pathname == 'tests/data/dat.csv'

    pathname = pathlib.Path("tests\\data/dat.csv")
    pathname_1 = normalize_pathname(pathname, sep=os.path.sep)
    pathname_2 = normalize_pathname(pathname, sep=os.path.sep, add_slash=True)
    if os.name == 'nt':
        assert pathname_1 == 'tests\\data\\dat.csv'
        assert pathname_2 == '.\\tests\\data\\dat.csv'
    else:
        assert pathname_1 == 'tests/data/dat.csv'
        assert pathname_2 == './tests/data/dat.csv'


def test_is_dir():
    # noinspection PyTypeChecker
    assert not is_dir(1)
    assert not is_dir("tests")
    assert is_dir("/tests")

    if os.name == 'nt':
        assert is_dir("\\tests")


def test_validate_dir():
    dat_dir = validate_dir()
    assert os.path.relpath(dat_dir) == '.'
    dat_dir = validate_dir(os.getcwd())
    assert os.path.relpath(dat_dir) == '.'

    dat_dir = validate_dir("tests")
    assert os.path.relpath(dat_dir) == 'tests'
    dat_dir = validate_dir(b"tests")
    assert os.path.relpath(dat_dir) == 'tests'
    dat_dir = validate_dir(pathlib.Path("tests"))
    assert os.path.relpath(dat_dir) == 'tests'

    dat_dir = validate_dir(subdir="data")
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


def test_get_file_pathnames():
    test_dir_name_ = importlib.resources.files(__package__).joinpath("..", "data")

    dat_filenames = [
        'csr_mat.npz',
        'dat.csv',
        'dat.feather',
        'dat.joblib',
        'dat.json',
        'dat.ods',
        'dat.pickle',
        'dat.pickle.bz2',
        'dat.pickle.gz',
        'dat.pickle.xz',
        'dat.txt',
        'dat.xlsx',
        'zipped',
        'zipped.7z',
        'zipped.txt',
        'zipped.zip',
    ]

    with importlib.resources.as_file(test_dir_name_) as test_dir_name:
        result_1 = get_file_pathnames(test_dir_name)
        assert isinstance(result_1, list)
        assert all(os.path.basename(x) in dat_filenames for x in result_1)

        result_2 = get_file_pathnames(test_dir_name, incl_subdir=True)
        assert all(os.path.basename(x) in dat_filenames for x in result_2)

        result_3 = get_file_pathnames(test_dir_name, file_ext=".txt")
        assert all(os.path.basename(x) in ['dat.txt', 'zipped.txt'] for x in result_3)

        result_4 = get_file_pathnames(test_dir_name, file_ext=".txt", incl_subdir=True)
        assert all(os.path.basename(x) in ['dat.txt', 'zipped.txt'] for x in result_4)


def test_check_files_exist(capfd):
    test_dir_name_ = importlib.resources.files(__package__).joinpath("..", "data")
    with importlib.resources.as_file(test_dir_name_) as test_dir_name:
        assert check_files_exist(["dat.csv", "dat.txt"], test_dir_name)
        rslt = check_files_exist(["dat.csv", "dat.txt", "dat_0.txt"], test_dir_name, verbose=True)
        out, _ = capfd.readouterr()
        assert rslt is False
        assert "Error: Required files are not satisfied, missing files are: ['dat_0.txt']" in out


if __name__ == '__main__':
    pytest.main()
