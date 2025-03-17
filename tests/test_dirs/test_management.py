"""
Tests the :mod:`~pyhelpers.dirs.management` submodule.
"""

import tempfile

import pytest

from pyhelpers.dirs import *


def test_add_slashes():
    path = add_slashes("pyhelpers\\data")
    assert path == '"./pyhelpers/data/"'

    path = add_slashes("pyhelpers\\data", normalized=False)
    if os.name == 'nt':
        assert path == '".\\pyhelpers\\data\\"'
    else:
        assert path == '"./pyhelpers/data/"'

    path = add_slashes("pyhelpers\\data\\pyhelpers.dat", surrounded_by='')
    assert path == './pyhelpers/data/pyhelpers.dat'


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
    expected_out = f'Deleting {add_slashes(os.path.normpath(tmp_dir.name))} ... Done.\n'
    assert expected_out == out

    # Test deleting multiple directories
    delete_dir(path_to_dir=test_dirs, confirmation_required=False, verbose=True)
    out, _ = capfd.readouterr()
    expected_output = '\n'.join(
        [f'Deleting {add_slashes(os.path.normpath(tmp_dir.name + str(x)))} ... Done.'
         for x in range(3)])
    expected_output += '\n'
    assert expected_output == out


if __name__ == '__main__':
    pytest.main()
