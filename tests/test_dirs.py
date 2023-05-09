"""Test the module :mod:`~pyhelpers.dirs`."""

import os
import pathlib
import shutil

import pytest

from pyhelpers.dirs import cd


def test_cd(capfd):
    current_wd = cd()
    assert os.path.relpath(current_wd) == "."

    path_to_tests_dir = cd("tests")
    assert os.path.relpath(path_to_tests_dir) == "tests"

    path_to_tests_dir = cd(pathlib.Path("tests"))
    assert os.path.relpath(path_to_tests_dir) == "tests"


def test_go_from_altered_cwd():
    from pyhelpers.dirs import go_from_altered_cwd

    init_cwd = os.getcwd()

    new_cwd = "\\new_cwd"
    new_cwd_pathname = os.path.join(init_cwd, new_cwd)

    os.mkdir(new_cwd_pathname)
    os.chdir(new_cwd_pathname)

    assert os.getcwd() == new_cwd_pathname

    cwd_ = go_from_altered_cwd(dir_name="tests")
    assert cwd_ == os.path.join(new_cwd_pathname, "tests")

    os.chdir(init_cwd)
    shutil.rmtree(new_cwd_pathname)


def test_cdd():
    from pyhelpers.dirs import cdd

    path_to_dat_dir = cdd()
    # As `mkdir=False`, `path_to_dat_dir` will NOT be created if it doesn't exist
    assert os.path.relpath(path_to_dat_dir) == 'data'

    path_to_dat_dir = cdd(data_dir="test_cdd", mkdir=True)
    assert os.path.relpath(path_to_dat_dir) == 'test_cdd'

    os.rmdir(path_to_dat_dir)

    # Set `data_dir` to be `"tests"`
    path_to_dat_dir = cdd("data", data_dir="test_cdd", mkdir=True)
    assert os.path.relpath(path_to_dat_dir) == 'test_cdd\\data'

    # Delete the "test_cdd" folder and the sub-folder "data"
    shutil.rmtree(os.path.dirname(path_to_dat_dir))


def test_cd_data():
    from pyhelpers.dirs import cd_data

    path_to_dat_dir = cd_data("tests", mkdir=False)

    assert os.path.relpath(path_to_dat_dir) == 'pyhelpers\\data\\tests'


def test_is_dir():
    from pyhelpers.dirs import is_dir

    assert not is_dir("tests")
    assert is_dir("/tests")
    assert is_dir(cd("tests"))


def test_validate_dir():
    from pyhelpers.dirs import validate_dir

    dat_dir = validate_dir()
    assert os.path.relpath(dat_dir) == '.'

    dat_dir = validate_dir("tests")
    assert os.path.relpath(dat_dir) == 'tests'

    dat_dir = validate_dir(subdir="data")
    assert os.path.relpath(dat_dir) == 'data'


def test_delete_dir(capfd):
    from pyhelpers.dirs import delete_dir

    test_dirs = []
    for x in range(3):
        test_dirs.append(cd("tests", f"test_dir{x}", mkdir=True))
        if x == 0:
            cd("tests", f"test_dir{x}", "a_folder", mkdir=True)
        elif x == 1:
            open(cd("tests", f"test_dir{x}", "file"), 'w').close()

    delete_dir(path_to_dir=test_dirs, confirmation_required=False, verbose=True)
    out, err = capfd.readouterr()
    out_ = '\n'.join(['Deleting "tests\\test_dir0\\" ... Done.',
                      'Deleting "tests\\test_dir1\\" ... Done.',
                      'Deleting "tests\\test_dir2\\" ... Done.\n'])
    assert out == out_


def test_path2linux():
    from pyhelpers.dirs import path2linux

    test_pathname = "tests\\data\\dat.csv"

    rslt = path2linux(test_pathname)
    assert rslt == 'tests/data/dat.csv'

    rslt = path2linux(pathlib.Path(test_pathname))
    assert rslt == 'tests/data/dat.csv'


def test_uniform_pathname():
    from pyhelpers.dirs import uniform_pathname

    test_pathname = "tests\\data\\dat.csv"

    rslt = uniform_pathname(test_pathname)
    assert rslt == 'tests/data/dat.csv'

    rslt = uniform_pathname(pathlib.Path(test_pathname))
    assert rslt == 'tests/data/dat.csv'


def test_get_rel_pathnames():
    from pyhelpers.dirs import get_rel_pathnames

    test_dir_name = "tests/data"

    rslt = get_rel_pathnames(test_dir_name)
    assert "tests/data/dat.csv" in rslt and isinstance(rslt, list)
    rslt = get_rel_pathnames(test_dir_name, file_ext=".txt")
    assert rslt == ['tests/data/dat.txt', 'tests/data/zipped.txt']
    rslt = get_rel_pathnames(test_dir_name, file_ext=".txt", incl_subdir=True)
    assert rslt == ['tests/data/dat.txt', 'tests/data/zipped.txt', 'tests/data/zipped/zipped.txt']


def test_check_files_exist(capfd):
    from pyhelpers.dirs import check_files_exist

    test_dir_name = "tests/data"

    assert check_files_exist(["dat.csv", "dat.txt"], test_dir_name)
    rslt = check_files_exist(["dat.csv", "dat.txt", "dat_0.txt"], test_dir_name)
    out, err = capfd.readouterr()
    assert rslt is False
    assert "Error: Required files are not satisfied, missing files are: ['dat_0.txt']" in out


def test_validate_filename():
    from pyhelpers.dirs import validate_filename
    import tempfile

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


if __name__ == '__main__':
    pytest.main()
