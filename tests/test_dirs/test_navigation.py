"""
Tests the :mod:`~pyhelpers.dirs.navigation` submodule.
"""

import pathlib
import shutil
import sys
import tempfile

import pytest

from pyhelpers.dirs.navigation import *
from pyhelpers.dirs.validation import is_dir


@pytest.mark.parametrize('cwd', [None, ".", os.path.join(os.sep, "some_directory")])
def test_cd(capfd, cwd):
    current_wd = cd(cwd=cwd, back_check=True)
    if cwd in {None, "."}:
        assert current_wd == os.getcwd()
    else:
        assert current_wd == os.sep  # Ensures compatibility across OS

    for subdir in ["tests", b"tests", pathlib.Path("tests")]:
        path_to_tests_dir = cd(subdir)
        assert os.path.relpath(path_to_tests_dir).replace(os.sep, "/") == "tests"

    temp = tempfile.TemporaryDirectory()
    temp_dir = cd(os.path.join(temp.name, 'test_dir'), mkdir=True)
    assert os.path.isdir(temp_dir)

    temp_dir_ = cd(temp_dir, 'test.dir', mkdir=True)
    assert not os.path.isfile(temp_dir_)
    assert temp_dir == os.path.dirname(temp_dir_) and os.path.isdir(os.path.dirname(temp_dir_))

    init_cwd = cd()

    # Change the current working directory
    new_cwd = os.path.join(".", "tests", "new_cwd")
    os.makedirs(new_cwd, exist_ok=True)
    os.chdir(new_cwd)

    path_to_tests = cd("test1")
    assert os.path.relpath(path_to_tests).replace(os.sep, "/") == "test1"

    # Change again the current working directory
    new_cwd_ = tempfile.TemporaryDirectory()
    os.chdir(new_cwd_.name)

    # Get the full path to a folder named "tests"
    path_to_tests = cd("tests")
    assert os.path.relpath(path_to_tests).replace(os.sep, "/") == 'tests'

    path_to_tests_ = cd("test1", "test2")
    assert path_to_tests_ == os.path.join(os.getcwd(), "test1", "test2")

    os.chdir(init_cwd)  # Restore the initial working directory
    shutil.rmtree(new_cwd)


def test_cdd():
    path_to_dat_dir = cdd()
    # As `mkdir=False`, `path_to_dat_dir` will NOT be created if it doesn't exist
    assert os.path.relpath(path_to_dat_dir) == 'data'

    path_to_dat_dir = cdd(data_dir="test_cdd", mkdir=True)
    assert os.path.relpath(path_to_dat_dir) == 'test_cdd'

    os.rmdir(path_to_dat_dir)

    # Set `data_dir` to be `"tests"`
    path_to_dat_dir = cdd("data", data_dir="test_cdd", mkdir=True)
    assert os.path.relpath(path_to_dat_dir) == os.path.join("test_cdd", "data")  # "test_cdd\\data"

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
    assert os.path.relpath(path_to_dat_dir_) == os.path.join("pyhelpers", "data", "test_dir")

    if mkdir:
        shutil.rmtree(path_to_dat_dir_)


def test_find_executable():
    python_exe = os.path.basename(sys.executable)  # "python.exe" on Windows, "python3" on Linux
    python_dir = os.path.dirname(sys.executable)  # Path to Python installation
    system_paths = os.get_exec_path()  # System paths where executables are searched

    # Test finding Python executable with `options=None` (should check system PATH)
    python_exe_exists, path_to_python_exe = find_executable(python_exe)
    assert python_exe_exists
    assert os.path.isfile(path_to_python_exe)

    # Test finding Python executable with a single directory
    python_exe_exists, path_to_python_exe = find_executable(python_exe, [python_dir])
    assert python_exe_exists
    assert os.path.isfile(path_to_python_exe)

    # Test finding Python executable
    python_exe_exists, path_to_python_exe = find_executable(python_exe, options=system_paths)
    assert python_exe_exists
    assert os.path.isfile(path_to_python_exe)

    # Test a non-existent executable
    test_exe = "pyhelpers"
    if os.name == "nt":  # Append ".exe" on Windows
        test_exe += ".exe"
    # Case 1: Check for non-existent executable in a specific directory
    test_exe_exists, path_to_test_exe = find_executable(test_exe, options=[python_dir])
    assert not test_exe_exists
    assert path_to_test_exe == test_exe
    # Case 2: Check for non-existent executable in system paths
    test_exe_exists, path_to_test_exe = find_executable(test_exe, system_paths)
    assert not test_exe_exists
    assert path_to_test_exe == test_exe  # Should return unchanged
    # Case 3: Check for non-existent executable with `options=None`
    test_exe_exists, path_to_test_exe = find_executable(test_exe, target=sys.executable)
    assert not test_exe_exists
    assert path_to_test_exe is None


if __name__ == '__main__':
    pytest.main()
