"""Test the module :mod:`~pyhelpers.dirs`."""

import importlib.resources
import os
import pathlib
import shutil

import pytest


def test_cd(capfd):
    from pyhelpers.dirs import cd

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

    assert "pyhelpers\\data\\tests" in os.path.relpath(path_to_dat_dir)


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


def test_is_dir():
    from pyhelpers.dirs import is_dir

    assert not is_dir("tests")
    assert is_dir("/tests")
    assert is_dir("\\tests")


def test_validate_dir():
    from pyhelpers.dirs import validate_dir

    dat_dir = validate_dir()
    assert os.path.relpath(dat_dir) == '.'

    dat_dir = validate_dir("tests")
    assert os.path.relpath(dat_dir) == 'tests'

    dat_dir = validate_dir(subdir="data")
    assert os.path.relpath(dat_dir) == 'data'


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


def test_get_file_pathnames():
    from pyhelpers.dirs import get_file_pathnames

    test_dir_name_ = importlib.resources.files(__package__).joinpath("data")

    with importlib.resources.as_file(test_dir_name_) as test_dir_name:
        rslt_ = get_file_pathnames(test_dir_name)
        assert isinstance(rslt_, list)
        rslt = [os.path.basename(x) for x in rslt_]
        assert "dat.csv" in rslt

        rslt = [os.path.basename(x) for x in get_file_pathnames(test_dir_name, file_ext=".txt")]
        assert rslt == ['dat.txt', 'zipped.txt']

        rslt = [
            os.path.basename(x)
            for x in get_file_pathnames(test_dir_name, file_ext=".txt", incl_subdir=True)]
        assert rslt == ['dat.txt', 'zipped.txt', 'zipped.txt']


def test_check_files_exist(capfd):
    from pyhelpers.dirs import check_files_exist

    test_dir_name_ = importlib.resources.files(__package__).joinpath("data")
    with importlib.resources.as_file(test_dir_name_) as test_dir_name:
        assert check_files_exist(["dat.csv", "dat.txt"], test_dir_name)
        rslt = check_files_exist(["dat.csv", "dat.txt", "dat_0.txt"], test_dir_name)
        out, err = capfd.readouterr()
        assert rslt is False
        assert "Error: Required files are not satisfied, missing files are: ['dat_0.txt']" in out


def test_delete_dir(capfd):
    from pyhelpers.dirs import delete_dir, cd

    test_dirs = []
    for x in range(3):
        test_dirs.append(cd(f"test_dir{x}", mkdir=True))
        if x == 0:
            cd(f"test_dir{x}", "a_folder", mkdir=True)
        elif x == 1:
            open(cd(f"test_dir{x}", "file"), 'w').close()

    delete_dir(path_to_dir=test_dirs, confirmation_required=False, verbose=True)
    out, err = capfd.readouterr()
    out_ = '\n'.join(['Deleting "test_dir0\\" ... Done.',
                      'Deleting "test_dir1\\" ... Done.',
                      'Deleting "test_dir2\\" ... Done.\n'])
    assert out == out_


if __name__ == '__main__':
    pytest.main()
