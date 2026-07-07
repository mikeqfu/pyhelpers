"""
Tests the :mod:`~pyhelpers.dirs.formatting` submodule.
"""

import os
from pathlib import Path

import pytest

from pyhelpers.dirs import format_display_path, get_relative_path, normalize_path, standardize_path


def test_normalize_path():
    pathname = normalize_path("tests\\data\\dat.csv")
    assert pathname == 'tests/data/dat.csv'

    pathname = normalize_path("tests\\data\\dat.csv", prepend_dot=True)
    assert pathname == './tests/data/dat.csv'

    pathname = normalize_path("tests//data/dat.csv".encode('utf-8'))
    assert pathname == 'tests/data/dat.csv'

    pathname = Path("tests\\data/dat.csv")
    pathname_1 = normalize_path(pathname, sep=os.path.sep)
    pathname_2 = normalize_path(pathname, sep=os.path.sep, prepend_dot=True)
    if os.name == 'nt':
        assert pathname_1 == 'tests\\data\\dat.csv'
        assert pathname_2 == '.\\tests\\data\\dat.csv'
    else:
        assert pathname_1 == 'tests/data/dat.csv'
        assert pathname_2 == './tests/data/dat.csv'


def test_standardize_path():
    # Test clean string name transformation to lowercase with separators
    path = standardize_path("Random Evaluation Name")
    assert path == Path("random-evaluation-name")

    # Test preservation of leading punctuation markers on single files
    path = standardize_path("-license.txt")
    assert path == Path("-license.txt")

    # Test relative Windows-style subpath evaluation across directory depths
    path = standardize_path("Users/Username/ProjectData/schema-v2.json")
    assert path.parent.name == "ProjectData"

    # Test custom separator override processing with path objects
    path = standardize_path(Path("/Archive/Old Folders/MyScript.py"), sep="_")
    assert path.name == "my_script.py"

    # Test parent directory preservation when parents parameter is False
    path = standardize_path("/Archive/Old Folders/MyScript.py", parents=False)
    assert path == Path("/Archive/Old Folders/my-script.py")

    # Test deep path standardization across all nodes when parents is True
    path = standardize_path("/Archive/Old Folders/MyScript.py", parents=True)
    assert path == Path("/archive/old-folders/my-script.py")


def test_get_relative_path():
    path = ""
    rel_path = get_relative_path(path)
    assert rel_path == Path(path)

    path = Path.cwd()
    rel_path = get_relative_path(os.path.curdir)
    assert rel_path == path.relative_to(path)

    if os.name == 'nt':
        path = "C:/Windows"
        rel_path = get_relative_path(path)
        assert os.path.splitdrive(rel_path)[0] == os.path.splitdrive(path)[0]

    # Test an absolute path outside the working directory
    home_dir = os.path.expanduser("~")  # Cross-platform home directory
    rel_path = get_relative_path(home_dir, normalized=False, as_str=True)
    assert rel_path == home_dir  # Should return unchanged

    # Test a relative path within the current working directory
    subdir = os.path.join(os.getcwd(), "test_dir")
    rel_path = get_relative_path(subdir, as_str=True)
    assert rel_path == "test_dir"


def test_format_display_path():
    """Test :func:`~pyhelpers.dirs.format_display_path`."""

    # Default: forward-slash normalized, no leading "./" (prepend_dot=False by default);
    # trailing slash added because "pyhelpers\data" has no extension (heuristically a dir)
    path = format_display_path("pyhelpers\\data")
    assert path == '"pyhelpers/data/"'


if __name__ == '__main__':
    pytest.main()
