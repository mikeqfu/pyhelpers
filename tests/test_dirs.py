"""
Test the module :mod:`~pyhelpers.dirs`.
"""

import importlib.resources
import sys
import tempfile

import pytest

from pyhelpers.dirs import *


# ==================================================================================================
# nav - Directory/file navigation.
# ==================================================================================================

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


# ==================================================================================================
# val - Directory/file navigation.
# ==================================================================================================

def test_normalize_pathname():
    test_pathname = os.path.join("tests", "data", "dat.csv")

    pathname_1 = normalize_pathname(test_pathname)
    pathname_2 = normalize_pathname(test_pathname.encode('utf-8'))
    pathname_3 = normalize_pathname(pathlib.Path(test_pathname))
    assert pathname_1 == pathname_2 == pathname_3 == 'tests/data/dat.csv'


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
    test_dir_name_ = importlib.resources.files(__package__).joinpath("data")

    dat_filenames = [
        'csr_mat.npz', 'dat.csv', 'dat.feather', 'dat.joblib', 'dat.json', 'dat.ods', 'dat.pickle',
        'dat.pickle.bz2', 'dat.pickle.gz', 'dat.pickle.xz', 'dat.txt', 'dat.xlsx', 'zipped',
        'zipped.7z', 'zipped.txt', 'zipped.zip']

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
    out, _ = capfd.readouterr()  # Capture the output
    expected_out = f'Deleting "{os.path.normpath(tmp_dir.name)}{os.path.sep}" ... Done.\n'
    assert expected_out == out

    # Test deleting multiple directories
    delete_dir(path_to_dir=test_dirs, confirmation_required=False, verbose=True)
    out, _ = capfd.readouterr()
    expected_output = '\n'.join(
        [f'Deleting "{os.path.normpath(tmp_dir.name)}{x}{os.path.sep}" ... Done.'
         for x in range(3)])
    expected_output += '\n'
    assert expected_output == out


if __name__ == '__main__':
    pytest.main()
