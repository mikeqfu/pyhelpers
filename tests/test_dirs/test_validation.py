"""
Tests the :mod:`~pyhelpers.dirs.validation` submodule.
"""

import os
import tempfile
from pathlib import Path

import pytest

from pyhelpers.dirs.validation import check_files_exist, is_dir_path, validate_filename


@pytest.fixture(scope='module')
def test_dirname():
    return Path(__file__).resolve().parents[1] / "data"


def test_is_dir_path():
    # noinspection PyTypeChecker
    assert not is_dir_path(1)
    assert not is_dir_path("tests")
    assert is_dir_path("/tests")

    if os.name == 'nt':
        assert is_dir_path("\\tests")


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


def test_check_files_exist(test_dirname, capfd):
    assert check_files_exist(["dat.csv", "dat.txt"], test_dirname)
    rslt = check_files_exist(["dat.csv", "dat.txt", "dat_0.txt"], test_dirname, verbose=True)
    out, _ = capfd.readouterr()
    assert rslt is False
    assert "Error: Required files are not satisfied, missing files are: ['dat_0.txt']" in out


if __name__ == '__main__':
    pytest.main()
