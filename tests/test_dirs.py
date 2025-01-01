"""
Test the module :mod:`~pyhelpers.dirs`.
"""

import importlib.resources
import os.path
import tempfile

import pytest

from pyhelpers.dirs import *


# ==================================================================================================
# nav - Directory/file navigation.
# ==================================================================================================

@pytest.mark.parametrize('cwd', [None, ".", "C:\\Programme"])
def test_cd(capfd, cwd):
    current_wd = cd(cwd=cwd, back_check=True)
    if cwd in {None, "."}:
        assert os.path.relpath(current_wd) == "."
    else:
        assert current_wd == "C:\\"

    for subdir in ["tests", b"tests", pathlib.Path("tests")]:
        path_to_tests_dir = cd(subdir)
        assert os.path.relpath(path_to_tests_dir) == "tests"

    tmp = tempfile.TemporaryFile()
    tmp_dir = cd(tmp.name + '0', mkdir=True)
    assert os.path.isdir(tmp_dir)

    tmp_dir_ = cd(tmp.name + '0', 'test.dir', mkdir=True)
    assert not os.path.isdir(tmp_dir_)
    assert tmp_dir == os.path.dirname(tmp_dir_)

    os.rmdir(tmp_dir)

    init_cwd = cd()

    # Change the current working directory
    new_cwd = ".\\tests\\new_cwd\\"
    os.makedirs(new_cwd, exist_ok=True)
    os.chdir(new_cwd)

    path_to_tests = cd("test1")
    assert os.path.relpath(path_to_tests) == "test1"

    # Change again the current working directory
    new_cwd_ = tempfile.TemporaryDirectory()
    os.chdir(new_cwd_.name)

    shutil.rmtree(os.path.dirname(path_to_tests))

    # Get the full path to a folder named "tests"
    path_to_tests = cd("tests")
    assert os.path.relpath(path_to_tests) == 'tests'

    path_to_tests_ = cd("test1", "test2")
    assert path_to_tests_ == os.path.join(os.getcwd(), "test1", "test2")

    os.chdir(init_cwd)
    shutil.rmtree(new_cwd_.name)


def test_cdd():
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


@pytest.mark.parametrize('subdir', [['test_dir'], ['test_dir', 'test.dat']])
@pytest.mark.parametrize('mkdir', [False, True])
def test_cd_data(subdir, mkdir):
    path_to_dat_dir = cd_data(*subdir, mkdir=mkdir)
    if is_dir(path_to_dat_dir):
        path_to_dat_dir_ = path_to_dat_dir
    else:
        path_to_dat_dir_ = os.path.relpath(os.path.dirname(path_to_dat_dir))
    assert os.path.relpath(path_to_dat_dir_) == "pyhelpers\\data\\test_dir"

    if mkdir:
        shutil.rmtree(path_to_dat_dir_)


def test_find_executable():
    python_exe = "python.exe"
    possible_paths = ["C:/Program Files/Python310", "C:/Python310/python.exe"]

    python_exe_exists, path_to_python_exe = find_executable(python_exe, possible_paths)
    assert python_exe_exists
    assert os.path.isfile(path_to_python_exe)

    test_exe = "pyhelpers.exe"
    test_exe_exists, path_to_test_exe = find_executable(test_exe, possible_paths)
    assert not test_exe_exists
    assert path_to_test_exe == test_exe


# ==================================================================================================
# val - Directory/file navigation.
# ==================================================================================================

def test_path2linux():
    test_pathname = "tests\\data\\dat.csv"

    rslt = path2linux(test_pathname)
    assert rslt == 'tests/data/dat.csv'

    rslt = path2linux(pathlib.Path(test_pathname))
    assert rslt == 'tests/data/dat.csv'


def test_uniform_pathname():
    test_pathname = "tests\\data\\dat.csv"

    rslt = uniform_pathname(test_pathname)
    assert rslt == 'tests/data/dat.csv'

    rslt = uniform_pathname(pathlib.Path(test_pathname))
    assert rslt == 'tests/data/dat.csv'


def test_is_dir():
    # noinspection PyTypeChecker
    assert not is_dir(1)
    assert not is_dir("tests")
    assert is_dir("/tests")
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
    test_dir_name_ = importlib.resources.files(__package__).joinpath("data")

    with importlib.resources.as_file(test_dir_name_) as test_dir_name:
        rslt_ = get_file_pathnames(test_dir_name)
        assert isinstance(rslt_, list)
        rslt = [os.path.basename(x) for x in rslt_]
        assert "dat.csv" in rslt

        rslt_ = get_file_pathnames(test_dir_name, incl_subdir=True)
        assert any("zipped/zipped.txt" in x for x in rslt_)

        rslt_ = get_file_pathnames(test_dir_name, file_ext=".txt")
        rslt = [os.path.basename(x) for x in rslt_]
        assert rslt == ['dat.txt', 'zipped.txt']

        rslt_ = get_file_pathnames(test_dir_name, file_ext=".txt", incl_subdir=True)
        rslt = [os.path.basename(x) for x in rslt_]
        assert rslt == ['dat.txt', 'zipped.txt', 'zipped.txt']


def test_check_files_exist(capfd):
    test_dir_name_ = importlib.resources.files(__package__).joinpath("data")
    with importlib.resources.as_file(test_dir_name_) as test_dir_name:
        assert check_files_exist(["dat.csv", "dat.txt"], test_dir_name)
        rslt = check_files_exist(["dat.csv", "dat.txt", "dat_0.txt"], test_dir_name, verbose=True)
        out, _ = capfd.readouterr()
        assert rslt is False
        assert "Error: Required files are not satisfied, missing files are: ['dat_0.txt']" in out


# ==================================================================================================
# mgmt - Directory/file management.
# ==================================================================================================

def test_delete_dir(capfd):
    tmp_dir = tempfile.TemporaryDirectory()

    test_dirs = []
    for x in range(3):
        tmp_dir_pathname = f"{tmp_dir.name}{x}"
        test_dirs.append(cd(tmp_dir_pathname, mkdir=True))
        if x == 0:
            cd(tmp_dir_pathname, "a_folder", mkdir=True)
        elif x == 1:
            open(cd(tmp_dir_pathname, "file"), 'w').close()

    delete_dir(tmp_dir.name, confirmation_required=False, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Deleting "{tmp_dir.name}\\" ... Done.\n' == out

    delete_dir(path_to_dir=test_dirs, confirmation_required=False, verbose=True)
    out, _ = capfd.readouterr()
    out_ = '\n'.join([f'Deleting "{tmp_dir.name}0\\" ... Done.',
                      f'Deleting "{tmp_dir.name}1\\" ... Done.',
                      f'Deleting "{tmp_dir.name}2\\" ... Done.\n'])
    assert out_ == out


if __name__ == '__main__':
    pytest.main()
