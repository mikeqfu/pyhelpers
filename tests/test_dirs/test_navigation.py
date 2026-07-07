"""
Tests the :mod:`~pyhelpers.dirs.navigation` submodule.
"""

import os
import shutil
import sys
from pathlib import Path

import pytest

from pyhelpers._cache import _normalize_path
from pyhelpers.dirs.navigation import cd, cd_data, cdd, find_executable, resolve_dir_path
from pyhelpers.dirs.validation import is_dir_path


@pytest.mark.parametrize('cwd', [None, ".", os.path.join(os.sep, "some_directory")])
def test_cd(capfd, cwd, tmp_path):  # import tempfile; tmp_path = Path(tempfile.mkdtemp())
    """Test :func:`~pyhelpers.dirs.cd`."""

    # Ensure back_check resolves down to root or current CWD safely
    current_wd = cd(cwd=cwd, back_check=True, normalized=False)
    if cwd in {None, "."}:
        assert current_wd == Path.cwd()
    else:
        # Resolves non-existent path down to the root directory
        assert current_wd == Path(os.path.abspath(os.sep))

    for subdir in ["tests", b"tests", Path("tests")]:
        path_to_tests_dir = cd(subdir)
        assert isinstance(path_to_tests_dir, Path)
        assert os.path.relpath(path_to_tests_dir).replace(os.sep, "/") == "tests"

    # Test that None values in subdir are ignored completely
    path_with_none = cd(None)
    assert path_with_none == Path.cwd()

    # Pass as_str=True explicitly when comparing against string outputs from _normalize_path
    path_with_none_mixed = cd("test1", None, "test2", as_str=True)
    expected_path = _normalize_path(Path.cwd() / "test1" / "test2")
    assert path_with_none_mixed == expected_path

    path_with_multiple_nones = cd(None, None, "test1", None, as_str=True)
    expected_path = _normalize_path(os.path.join(os.getcwd(), "test1"))
    assert path_with_multiple_nones == expected_path

    # Verify directory generation via tmp_path fixture
    temp_dir: Path = cd(str(tmp_path / 'test_dir'), mkdir=True)
    assert temp_dir.is_dir()

    temp_dir_: Path = cd(temp_dir, 'test.dir', mkdir=True)
    assert not os.path.isfile(temp_dir_)
    assert temp_dir == temp_dir_.parent and temp_dir_.parent.is_dir()

    init_cwd = cd()

    # Isolate context inside a temporary working directory modification block
    new_cwd = str(tmp_path / "new_cwd")
    os.makedirs(new_cwd, exist_ok=True)
    os.chdir(new_cwd)

    try:
        path_to_tests = cd("test1")
        assert os.path.relpath(path_to_tests).replace(os.sep, "/") == "test1"

        path_to_tests = cd("tests")
        assert os.path.relpath(path_to_tests).replace(os.sep, "/") == 'tests'

        # Fixed name error: replaced normalize_pathname with _normalize_path
        path_to_tests_ = cd("test1", "test2", as_str=True)
        assert path_to_tests_ == _normalize_path(os.path.join(os.getcwd(), "test1", "test2"))
    finally:
        os.chdir(init_cwd)  # Guaranteed restoration of the primary workspace CWD


def test_cdd():
    """Test :func:`~pyhelpers.dirs.cdd`."""

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
    """Test :func:`~pyhelpers.dirs.cd_data`."""

    path_to_dat_dir = cd_data(*subdir, mkdir=mkdir)
    if is_dir_path(path_to_dat_dir):
        path_to_dat_dir_ = path_to_dat_dir
    else:
        path_to_dat_dir_ = os.path.relpath(os.path.dirname(path_to_dat_dir))
    assert os.path.relpath(path_to_dat_dir_) == os.path.join("pyhelpers", "data", "test_dir")

    if mkdir:
        shutil.rmtree(path_to_dat_dir_)


def test_resolve_dir_path():
    dat_dir = resolve_dir_path()
    assert os.path.relpath(dat_dir) == '.'
    dat_dir = resolve_dir_path(os.getcwd())
    assert os.path.relpath(dat_dir) == '.'

    dat_dir = resolve_dir_path("tests")
    assert os.path.relpath(dat_dir) == 'tests'
    dat_dir = resolve_dir_path(b"tests")
    assert os.path.relpath(dat_dir) == 'tests'
    dat_dir = resolve_dir_path(Path("tests"))
    assert os.path.relpath(dat_dir) == 'tests'

    dat_dir = resolve_dir_path(subdir="data")
    assert os.path.relpath(dat_dir) == 'data'


def test_find_executable():
    """Test :func:`~pyhelpers.dirs.find_executable`."""

    python_exe = os.path.basename(sys.executable)  # "python.exe" on Windows, "python3" on Linux
    python_dir = os.path.dirname(sys.executable)  # Path to Python installation
    system_paths = os.get_exec_path()  # System paths where executables are searched

    # 1. Test standard string path lookup (as_str=True, normalized=True)
    python_exe_exists, path_to_python_exe = find_executable(
        python_exe, normalized=True, as_str=True)
    assert python_exe_exists
    assert isinstance(path_to_python_exe, str)
    assert os.path.isfile(path_to_python_exe)

    # 2. Test pathlib.Path return structure (as_str=False, normalized=True)
    python_exe_exists_path, path_to_python_obj = find_executable(
        python_exe, normalized=True, as_str=False)
    assert python_exe_exists_path
    assert isinstance(path_to_python_obj, Path)
    assert path_to_python_obj.is_file()

    # 3. Test finding Python executable with a single target option directory passed
    python_exe_exists, path_to_python_exe = find_executable(python_exe, [python_dir])
    assert python_exe_exists
    assert os.path.isfile(path_to_python_exe)

    # 4. Test finding Python executable explicitly within verified system paths array
    python_exe_exists, path_to_python_exe = find_executable(python_exe, options=system_paths)
    assert python_exe_exists
    assert os.path.isfile(path_to_python_exe)

    # 5. Verify non-existent executable search boundaries
    test_exe = "pyhelpers-non-existent-binary"
    if os.name == "nt":  # Append executable extension suffix safely on Windows
        test_exe += ".exe"

    # Case A: Check for non-existent executable inside a valid directory pool
    test_exe_exists, path_to_test_exe = find_executable(test_exe, options=[python_dir])
    assert not test_exe_exists
    assert path_to_test_exe is None

    # Case B: Check for non-existent executable over system path lookups
    test_exe_exists, path_to_test_exe = find_executable(test_exe, system_paths)
    assert not test_exe_exists
    assert path_to_test_exe is None

    # Case C: Isolate target evaluation by using an existing file with mismatched naming
    # This triggers an immediate target mismatch validation
    test_exe_exists, path_to_test_exe = find_executable(test_exe, target=sys.executable)
    assert not test_exe_exists
    assert path_to_test_exe is None


if __name__ == '__main__':
    pytest.main()
