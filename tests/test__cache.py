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


def test__check_dependency(mocker):
    from pyhelpers._cache import _check_dependencies

    result = _check_dependencies('os')
    assert result.__name__ == 'os'

    # Test alias resolution (beautifulSoup4 -> bs4)
    mock_import = mocker.patch('pyhelpers._cache.importlib.import_module')

    mock_bs4 = mocker.MagicMock()
    mock_bs4.__name__ = 'bs4'
    mock_import.return_value = mock_bs4

    mocker.patch.dict(sys.modules, values={}, clear=False)
    sys.modules.pop('bs4', None)

    result = _check_dependencies('beautifulsoup4')

    mock_import.assert_called_once_with('bs4')
    assert result.__name__ == 'bs4'

    # Test GDAL fallback (osgeo.gdal -> gdal -> Error)
    mock_import.reset_mock(return_value=True, side_effect=True)
    # Simulate osgeo.gdal missing, but legacy gdal existing
    def side_effect(name, *args, **kwargs):  # noqa
        if name == 'osgeo.gdal':
            raise ModuleNotFoundError("No osgeo")
        if name == 'gdal':
            m = mocker.MagicMock()
            # MANUALLY assign __name__ (constructor assignment fails for magic attributes)
            m.__name__ = 'gdal'
            return m
        raise ModuleNotFoundError()

    mock_import.side_effect = side_effect
    result = _check_dependencies('gdal')
    # Check that it called both osgeo.gdal (failed) and gdal (success)
    assert mock_import.call_count == 2
    assert result.__name__ == 'gdal'

    # Test missing dependency error message
    mock_import.reset_mock(side_effect=True)
    mock_import.side_effect = ModuleNotFoundError("Not found")
    with pytest.raises(ModuleNotFoundError, match="pip install unknown"):
        _check_dependencies('unknown')


def test__lazy_check_dependencies(monkeypatch):
    """
    Test the decorator's ability to inject proxies and load modules on demand.
    """
    from pyhelpers._cache import _lazy_check_dependencies

    @_lazy_check_dependencies('numpy', 'pandas')  # No aliases
    def _test_import_numpy_pandas():
        return numpy.__name__ == 'numpy' and pandas.__name__ == 'pandas'  # noqa

    assert _test_import_numpy_pandas()

    @_lazy_check_dependencies(np='numpy', pd='pandas')  # Aliases
    def _test_import_np_pd():
        return np.__name__ == 'numpy' and pd.__name__ == 'pandas'  # noqa

    assert _test_import_np_pd()

    @_lazy_check_dependencies('geopandas', plt='matplotlib.pyplot')  # Mixed
    def _test_import_geopandas_plt():
        return geopandas.__name__ == 'geopandas' and plt.__name__ == 'matplotlib.pyplot'  # noqa

    assert _test_import_geopandas_plt()

    @_lazy_check_dependencies('scipy')
    def _test_import_scipy():
        return (scipy.__name__ == 'scipy') & (scipy.sparse.__name__ == 'scipy.sparse')  # noqa

    assert _test_import_scipy()

    @_lazy_check_dependencies(**{'sp': 'scipy.sparse'})  # (Alternative)
    def _test_import_sp():
        return sp.__name__ == 'scipy.sparse'  # noqa

    assert _test_import_sp()

    # Test actual laziness (Verification that it's not preloading)
    target_mod = 'pandas'  # or any optional dependency you have
    # Temporarily remove it from sys.modules for this test only
    monkeypatch.delitem(sys.modules, target_mod, raising=False)

    @_lazy_check_dependencies(target_mod)
    def _test_laziness():
        # Before accessing, it shouldn't be in sys.modules
        assert target_mod not in sys.modules
        # Trigger the lazy load
        name = pandas.__name__  # noqa
        assert target_mod in sys.modules
        return name

    assert _test_laziness() == target_mod

    # 7. Test failure mode (AttributeError)
    @_lazy_check_dependencies('numpy')
    def _test_invalid_attribute():
        try:
            return numpy.this_attribute_does_not_exist  # noqa
        except AttributeError as e:
            return str(e)

    assert "has no attribute 'this_attribute_does_not_exist'" in _test_invalid_attribute()


def test__confirmed(monkeypatch, capfd):
    from pyhelpers._cache import _confirmed

    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    if _confirmed(prompt="Testing if the function works?", resp=True):
        print("Passed.")

    out, _ = capfd.readouterr()
    assert "Passed." in out


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


def test__check_relative_pathname():
    from pyhelpers._cache import _check_relative_pathname

    pathname = ""
    rel_path = _check_relative_pathname(pathname=pathname)
    assert rel_path == pathname

    pathname = os.path.curdir
    rel_path = _check_relative_pathname(os.path.curdir)
    assert rel_path == pathname

    if os.name == 'nt':
        pathname = "C:\\Windows"
        rel_path = _check_relative_pathname(pathname)
        assert os.path.splitdrive(rel_path)[0] == os.path.splitdrive(pathname)[0]

    # Test an absolute path outside the working directory
    home_dir = os.path.expanduser("~")  # Cross-platform home directory
    rel_path = _check_relative_pathname(home_dir, normalized=False)
    assert rel_path == home_dir  # Should return unchanged

    # Test a relative path within the current working directory
    subdir = os.path.join(os.getcwd(), "test_dir")
    rel_path = _check_relative_pathname(subdir)
    assert rel_path == "test_dir"


def test__check_file_pathname():
    from pyhelpers._cache import _check_file_pathname

    python_exe = os.path.basename(sys.executable)

    python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe)
    assert python_exe_exists
    assert str(path_to_python_exe) == sys.executable

    # Use the directory containing Python
    python_dir = os.path.dirname(sys.executable)
    possible_paths = [python_dir, sys.executable]

    # Check if specifying Python's actual path works
    python_exe_exists, path_to_python_exe = _check_file_pathname(sys.executable)
    assert python_exe_exists
    assert str(path_to_python_exe) == sys.executable
    python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe, target=os.getcwd())
    assert not python_exe_exists
    python_exe_exists, path_to_python_exe = _check_file_pathname(possible_paths[1])
    assert python_exe_exists

    # Check non-existent file
    text_exe = "pyhelpers.exe"
    test_exe_exists, path_to_test_exe = _check_file_pathname(text_exe, options=possible_paths)
    assert not test_exe_exists
    assert path_to_test_exe is None  # Should return input name


def test__format_exception_message():
    from pyhelpers._cache import _format_exception_message

    res = _format_exception_message(None)
    assert res == ''

    res = _format_exception_message("test")
    assert res == 'test.'

    res = _format_exception_message("test", prefix="Failed.")
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


@pytest.mark.parametrize("colors", ['invalid_color', 'red', ['red', 'blue']])
@pytest.mark.parametrize("show_valid_colors", [False, True])
@pytest.mark.parametrize('concatenated', [True, False])
def test__get_ansi_color_code(colors, show_valid_colors, concatenated):
    from pyhelpers._cache import _get_ansi_color_code, _load_ansi_escape_codes

    if colors == 'invalid_color':
        with pytest.raises(ValueError, match=f"'{colors}' is not a valid color name."):
            _ = _get_ansi_color_code(
                colors=colors, show_valid_colors=show_valid_colors, concatenated=concatenated)

    else:
        red_code = '\033[31m'
        blue_code = '\033[34m'
        red_blue_compound = f'{red_code}{blue_code}'
        red_blue_list = [red_code, blue_code]

        is_single_input = colors == 'red'
        expected_set = set(_load_ansi_escape_codes())

        if concatenated:
            expected_code = red_code if is_single_input else red_blue_compound
        else:
            expected_code = red_code if is_single_input else red_blue_list

        color_codes = _get_ansi_color_code(
            colors=colors, show_valid_colors=show_valid_colors, concatenated=concatenated)

        if show_valid_colors:
            assert isinstance(color_codes, tuple)
            assert color_codes[0] == expected_code, \
                f"Code mismatch in tuple (concatenated={concatenated})"
            assert color_codes[1] == expected_set, "Set mismatch in tuple"
        else:
            assert color_codes == expected_code, \
                f"Direct output mismatch (concatenated={concatenated})"


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
