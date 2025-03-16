"""
Test the module ``_cache.py``
"""

import os
import sys

import pytest


@pytest.mark.parametrize('osgb36', [False, True])
def test_example_dataframe(osgb36):
    from pyhelpers._cache import example_dataframe

    data = example_dataframe(osgb36=osgb36)
    assert data.shape == (4, 2)
    assert data.index.tolist() == ['London', 'Birmingham', 'Manchester', 'Leeds']

    if osgb36:
        assert data.columns.tolist() == ['Easting', 'Northing']
    else:
        assert data.columns.tolist() == ['Longitude', 'Latitude']


def test__check_dependency():
    from pyhelpers._cache import _check_dependency

    psycopg2 = _check_dependency(name='psycopg2')
    assert psycopg2.__name__ == 'psycopg2'

    sqlalchemy_dialects = _check_dependency(name='dialects', package='sqlalchemy')
    assert sqlalchemy_dialects.__name__ == 'sqlalchemy.dialects'

    gdal = _check_dependency(name='gdal', package='osgeo')
    assert gdal.__name__ == 'osgeo.gdal'

    test_name = 'unknown_package'
    err_msg = (f"Missing optional dependency '{test_name}'. "
               f"Use `pip` or `conda` to install it, e.g. `pip install unknown_package`.")
    with pytest.raises(ModuleNotFoundError, match=err_msg):
        _ = _check_dependency(name=test_name)


def test__confirmed(monkeypatch, capfd):
    from pyhelpers._cache import _confirmed

    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    if _confirmed(prompt="Testing if the function works?", resp=True):
        print("Passed.")

    out, _ = capfd.readouterr()
    assert "Passed." in out


def test__check_relative_pathname():
    from pyhelpers._cache import _check_relative_pathname

    pathname = ""
    rel_path = _check_relative_pathname(pathname=pathname)
    assert rel_path == pathname

    pathname = os.path.curdir
    rel_path = _check_relative_pathname(os.path.curdir)
    assert rel_path == pathname

    if os.name == 'nt':
        pathname = "C:/Windows"
        rel_path = _check_relative_pathname(pathname)
        assert os.path.splitdrive(rel_path)[0] == os.path.splitdrive(pathname)[0]

    # Test an absolute path outside the working directory
    home_dir = os.path.expanduser("~")  # Cross-platform home directory
    rel_path = _check_relative_pathname(home_dir)
    assert rel_path == home_dir  # Should return unchanged

    # Test a relative path within the current working directory
    subdir = os.path.join(os.getcwd(), "test_dir")
    rel_path = _check_relative_pathname(subdir)
    assert rel_path == "test_dir"


def test__normalize_pathname():
    from pyhelpers._cache import _normalize_pathname
    import pathlib

    pathname = _normalize_pathname("tests\\data\\dat.csv")
    assert pathname == 'tests/data/dat.csv'

    pathname = _normalize_pathname("tests\\data\\dat.csv", add_slash=True)
    assert pathname == './tests/data/dat.csv'

    pathname = _normalize_pathname("tests//data/dat.csv".encode('utf-8'))
    assert pathname == 'tests/data/dat.csv'

    pathname = pathlib.Path("tests\\data/dat.csv")
    pathname_1 = _normalize_pathname(pathname, sep=os.path.sep)
    pathname_2 = _normalize_pathname(pathname, sep=os.path.sep, add_slash=True)
    if os.name == 'nt':
        assert pathname_1 == 'tests\\data\\dat.csv'
        assert pathname_2 == '.\\tests\\data\\dat.csv'
    else:
        assert pathname_1 == 'tests/data/dat.csv'
        assert pathname_2 == './tests/data/dat.csv'


def test__add_slashes():
    from pyhelpers._cache import _add_slashes

    path = _add_slashes("pyhelpers\\data")
    assert path == '"./pyhelpers/data/"'

    path = _add_slashes("pyhelpers\\data", normalized=False)
    if os.name == 'nt':
        assert path == '".\\pyhelpers\\data\\"'
    else:
        assert path == '"./pyhelpers/data/"'

    path = _add_slashes("pyhelpers\\data\\pyhelpers.dat", surrounded_by='')
    assert path == './pyhelpers/data/pyhelpers.dat'


def test__check_file_pathname():
    from pyhelpers._cache import _check_file_pathname

    python_exe = os.path.basename(sys.executable)

    python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe)
    assert python_exe_exists
    assert path_to_python_exe == sys.executable

    # Use the directory containing Python
    python_dir = os.path.dirname(sys.executable)
    possible_paths = [python_dir, sys.executable]

    # Check if specifying Python's actual path works
    python_exe_exists, path_to_python_exe = _check_file_pathname(sys.executable)
    assert python_exe_exists
    assert path_to_python_exe == sys.executable
    python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe, target=os.getcwd())
    assert not python_exe_exists
    python_exe_exists, path_to_python_exe = _check_file_pathname(possible_paths[1])
    assert python_exe_exists

    # Check non-existent file
    text_exe = "pyhelpers.exe"
    test_exe_exists, path_to_test_exe = _check_file_pathname(text_exe, options=possible_paths)
    assert not test_exe_exists
    assert path_to_test_exe == text_exe  # Should return input name


def test__format_error_message():
    from pyhelpers._cache import _format_error_message

    res = _format_error_message(None)
    assert res == ''

    res = _format_error_message("test")
    assert res == 'test.'

    res = _format_error_message("test", prefix="Failed.")
    assert res == 'Failed. test.'


def test__print_failure_message(capfd):
    from pyhelpers._cache import _print_failure_message

    _print_failure_message('test', prefix="Failed.")
    out, _ = capfd.readouterr()
    assert out == 'Failed. test.\n'


@pytest.mark.parametrize('allowed_schemes', [None, {'https'}])
def test__check_url_scheme(allowed_schemes):
    from pyhelpers._cache import _check_url_scheme

    url = 'https://github.com/mikeqfu/pyhelpers'
    parsed_url = _check_url_scheme(url, allowed_schemes=allowed_schemes)
    assert parsed_url.netloc == 'github.com'

    with pytest.raises(ValueError) as exc_info:
        _ = _check_url_scheme('httpx://github.com/mikeqfu/pyhelpers')
    assert str(exc_info.value) == "Unknown/unsafe URL scheme: 'httpx'."


@pytest.mark.parametrize('retry_status', ['default', 123])
def test__init_requests_session(retry_status):
    from pyhelpers._cache import _init_requests_session
    import requests

    logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
    s = _init_requests_session(logo_url, retry_status=retry_status)
    assert isinstance(s, requests.sessions.Session)


def test__get_ansi_colour_code():
    from pyhelpers._cache import _get_ansi_colour_code, _ANSI_ESCAPE_CODES

    color_codes = _get_ansi_colour_code('red')
    assert color_codes == '\033[31m'

    color_codes = _get_ansi_colour_code(['red', 'blue'])
    assert color_codes == ['\033[31m', '\033[34m']

    with pytest.raises(ValueError, match="'invalid_colour' is not a valid colour name."):
        _ = _get_ansi_colour_code('invalid_colour')

    color_codes = _get_ansi_colour_code('red', show_valid_colours=True)
    assert isinstance(color_codes, tuple)
    assert color_codes[0] == '\033[31m'
    assert color_codes[1] == set(_ANSI_ESCAPE_CODES)


def test__transform_point_type():
    from pyhelpers._cache import _transform_point_type, example_dataframe
    import numpy as np
    import shapely.geometry

    example_df = example_dataframe()

    pt1 = example_df.loc['London'].values  # array([-0.1276474, 51.5073219])
    pt2 = example_df.loc['Birmingham'].values  # array([-1.9026911, 52.4796992])

    ref_rslt_1 = ['POINT (-0.1276474 51.5073219)', 'POINT (-1.9026911 52.4796992)']
    ref_rslt_2 = [np.array([-0.1276474, 51.5073219]), np.array([-1.9026911, 52.4796992])]

    geom_points = [x.wkt for x in _transform_point_type(pt1, pt2)]
    assert geom_points == ref_rslt_1

    geom_points = list(_transform_point_type(pt1, pt2, as_geom=False))
    assert np.array_equal(geom_points, ref_rslt_2)

    pt1, pt2 = map(lambda x: shapely.geometry.Point(x), (pt1, pt2))

    geom_points = [x.wkt for x in _transform_point_type(pt1, pt2)]
    assert geom_points == ref_rslt_1

    geom_points = list(_transform_point_type(pt1, pt2, as_geom=False))
    assert np.array_equal(geom_points, ref_rslt_2)

    geom_points_ = _transform_point_type(shapely.geometry.Point([1, 2, 3]), as_geom=False)
    assert np.array_equal(list(geom_points_), [(1.0, 2.0, 3.0)])


if __name__ == '__main__':
    pytest.main()
