"""
Test the module ``_cache.py``
"""

import os
import sys
from pathlib import Path

import numpy as np
import pytest
import requests
import shapely.geometry

from pyhelpers._cache import _check_dependencies, _check_url_scheme, _confirmed, _find_file_path, \
    _format_display_path, _format_exception_message, _get_ansi_color_code, _get_relative_path, \
    _init_requests_session, _lazy_check_dependencies, _load_ansi_escape_codes, _normalize_path, \
    _normalize_token, _print_failure_message, _transform_point_type, example_dataframe


@pytest.mark.parametrize('osgb36', [False, True])
def test_example_dataframe(osgb36):
    data = example_dataframe(osgb36=osgb36)
    assert data.shape == (4, 2)
    assert data.index.tolist() == ['London', 'Birmingham', 'Manchester', 'Leeds']

    if osgb36:
        assert data.columns.tolist() == ['Easting', 'Northing']
    else:
        assert data.columns.tolist() == ['Longitude', 'Latitude']


def test__check_dependency(mocker):
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
    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    if _confirmed(prompt="Testing if the function works?", resp=True):
        print("Passed.")

    out, _ = capfd.readouterr()
    assert "Passed." in out


def test__normalize_token():
    """Test :func:`~pyhelpers._cache._normalize_token`."""

    # Empty input returns empty string
    assert _normalize_token('') == ''

    # camelCase and PascalCase are split on case transitions and lowercased
    assert _normalize_token('camelCase') == 'camel_case'
    assert _normalize_token('PascalCase') == 'pascal_case'

    # Consecutive uppercase letters (acronyms) are split before the trailing word
    assert _normalize_token('myHTTPServer') == 'my_http_server'
    assert _normalize_token('HTTPServer') == 'http_server'

    # Spaces, hyphens and slashes are converted to underscores
    assert _normalize_token('my token name') == 'my_token_name'
    assert _normalize_token('my-token-name') == 'my_token_name'
    assert _normalize_token('my/token\\name') == 'my_token_name'

    # Punctuation is stripped by default
    assert _normalize_token('token!@#name') == 'tokenname'  # noqa

    # Consecutive underscores (from collapsing or stripped punctuation) are condensed
    assert _normalize_token('token   name') == 'token_name'
    assert _normalize_token('token___name') == 'token_name'

    # `preserve_dot=False` (default) strips dots along with other punctuation
    assert _normalize_token('data.csv') == 'datacsv'

    # `preserve_dot=True` keeps a single dot and condenses repeated dots
    assert _normalize_token('data.csv', preserve_dot=True) == 'data.csv'
    assert _normalize_token('data..csv', preserve_dot=True) == 'data.csv'

    # Leading/trailing boundary characters (space, hyphen, underscore) are collapsed
    # to a single flag underscore rather than preserved verbatim
    assert _normalize_token('  token') == '_token'
    assert _normalize_token('token  ') == 'token_'
    assert _normalize_token('--token--') == '_token_'

    # A trailing flag underscore is not appended past a preserved file extension
    assert _normalize_token('data.csv  ', preserve_dot=True) == 'data.csv'

    # A token consisting solely of boundary characters collapses to a single underscore,
    # rather than doubling up from both the leading- and trailing-flag logic
    assert _normalize_token('_') == '_'
    assert _normalize_token('   ') == '_'

    # Mixed case, spacing and punctuation combined
    assert _normalize_token('  My Data-File!!') == '_my_data_file'


def test__normalize_path():
    """Test :func:`~pyhelpers._cache._normalize_path`."""

    test_path_1 = "tests\\data\\dat.csv"
    expected_output_1 = "tests/data/dat.csv"

    # Default behavior: mixed/backslash separators normalized to forward slashes
    assert _normalize_path(test_path_1) == expected_output_1
    # `prepend_dot=True` prepends "./" to a bare relative path
    assert _normalize_path(test_path_1, prepend_dot=True) == "./tests/data/dat.csv"

    # Repeated separators are collapsed; bytes input is decoded correctly
    test_path_2 = b"tests//data/dat.csv"
    assert _normalize_path(test_path_2) == expected_output_1

    # `prepend_dot=True` is a no-op when the path already has a relative/absolute prefix
    assert _normalize_path("./tests/data", prepend_dot=True) == "./tests/data"
    assert _normalize_path("/tests/data", prepend_dot=True) == "./tests/data"
    assert _normalize_path("C:\\tests\\data", prepend_dot=True) == "C:/tests/data"

    # Verify isolated dot and double-dot paths are correctly resolved under prepend instructions
    assert _normalize_path(".", prepend_dot=True) == "."
    assert _normalize_path("..", prepend_dot=True) == ".."

    # `sep` controls the separator used in the string output, and is platform-dependent
    test_path_3 = Path("tests\\data/dat.csv")
    path_1 = _normalize_path(test_path_3, sep=os.sep)
    path_2 = _normalize_path(test_path_3, sep=os.sep, prepend_dot=True)
    if os.name == "nt":
        assert path_1 == test_path_1
        assert path_2 == ".\\tests\\data\\dat.csv"
    else:
        assert path_1 == expected_output_1
        assert path_2 == "./tests/data/dat.csv"

    # `as_str=False` returns a `pathlib.Path` and ignores string parameters completely
    path_obj = _normalize_path(test_path_1, as_str=False)
    assert isinstance(path_obj, Path)
    assert path_obj == Path(expected_output_1)
    assert _normalize_path(test_path_1, sep="\\", as_str=False, prepend_dot=True) == path_obj


def test__format_display_path():
    """Test :func:`~pyhelpers._cache._format_display_path`."""

    # Default: forward-slash normalized, no leading "./" (prepend_dot=False by default);
    # trailing slash added because "pyhelpers\data" has no extension (heuristically a dir)
    path = _format_display_path("pyhelpers\\data")
    assert path == '"pyhelpers/data/"'

    # `normalized=False` preserves the raw separators; only the OS-native trailing slash is added
    path = _format_display_path("pyhelpers\\data", normalized=False)
    if os.name == 'nt':
        assert path == '"pyhelpers\\data\\"'
    else:
        assert path == '"pyhelpers\\data/"'

    # A path with an extension is not treated as a directory: no trailing slash
    path = _format_display_path("pyhelpers\\data\\pyhelpers.dat", surrounded_by='')
    assert path == 'pyhelpers/data/pyhelpers.dat'

    # `prepend_dot=True` adds "./" to a bare relative path
    path = _format_display_path("pyhelpers\\data\\pyhelpers.dat", prepend_dot=True, surrounded_by='')
    assert path == './pyhelpers/data/pyhelpers.dat'

    # `prepend_dot=True` is a no-op when the path is already relative-prefixed or absolute
    path = _format_display_path("./pyhelpers/data", prepend_dot=True, surrounded_by='')
    assert path == './pyhelpers/data/'
    path = _format_display_path("/pyhelpers/data", prepend_dot=True, surrounded_by='')
    assert path == './pyhelpers/data/'

    # `is_dir` overrides both the filesystem check and the extension heuristic
    path = _format_display_path("pyhelpers.dat", is_dir=True, surrounded_by='')
    assert path == 'pyhelpers.dat/'
    path = _format_display_path("pyhelpers_data", is_dir=False, surrounded_by='')
    assert path == 'pyhelpers_data'

    # `surrounded_by` can wrap the output in any string, not just quotes
    path = _format_display_path("pyhelpers.dat", is_dir=False, surrounded_by='**')
    assert path == '**pyhelpers.dat**'


def test__get_relative_path():
    """Test :func:`~pyhelpers._cache._get_relative_path`."""

    # `pathlib.Path("")` resolves to the current working directory itself
    assert _get_relative_path(path="") == Path(".")
    assert _get_relative_path(path=Path.cwd()) == Path(".")

    if os.name == "nt":
        path = "C:\\Windows"
        rel_path = _get_relative_path(path)
        assert os.path.splitdrive(rel_path)[0] == os.path.splitdrive(path)[0]

    # An absolute path outside the working directory is returned unchanged as an absolute Path
    home_dir = os.path.expanduser("~")
    rel_path = _get_relative_path(home_dir, normalized=False)
    assert isinstance(rel_path, Path)
    assert rel_path == Path(home_dir).resolve()

    # A relative path within the current working directory transformed to string representation
    subdir = os.path.join(os.getcwd(), "test_dir")
    rel_path = _get_relative_path(subdir, as_str=True)
    assert rel_path == "test_dir"

    # Verify that string-formatting pipelines forward arguments from the tracking layer correctly
    assert _get_relative_path(subdir, as_str=True, quoted=True) == '"test_dir/"'
    assert _get_relative_path(subdir, as_str=True, prepend_dot=True) == "./test_dir"

    # `normalized=False` on a path within the CWD also returns a Path object, not a string
    rel_path_obj = _get_relative_path(subdir, normalized=False)
    assert isinstance(rel_path_obj, Path)
    assert rel_path_obj == Path("test_dir")


def test__find_file_path():
    """Test :func:`~pyhelpers._cache._find_file_path`."""

    python_exe = Path(sys.executable).name
    python_dir = Path(sys.executable).parent

    # Bare basename resolved via PATH; only check that *a* match was found with the expected
    # basename -- `shutil.which()` isn't guaranteed to resolve to the exact same binary as
    # `sys.executable` in shimmed/managed environments (pyenv, conda, venvs)
    python_exe_exists, path_to_python_exe = _find_file_path(python_exe)
    assert python_exe_exists
    assert isinstance(path_to_python_exe, Path)
    assert path_to_python_exe.name == python_exe

    # Passing the full path directly is deterministic (hits the direct-path-lookup branch)
    python_exe_exists, path_to_python_exe = _find_file_path(sys.executable)
    assert python_exe_exists
    assert str(path_to_python_exe) == sys.executable

    # `as_str=True` returns an actual `str`, not just something convertible to one
    python_exe_exists, path_to_python_exe = _find_file_path(sys.executable, as_str=True)
    assert python_exe_exists
    assert isinstance(path_to_python_exe, str)
    assert path_to_python_exe == sys.executable

    # An invalid `target` (a directory, not a file) now falls through to the rest of the
    # search rather than giving up immediately, so this still finds it via PATH
    python_exe_exists, path_to_python_exe = _find_file_path(python_exe, target=os.getcwd())
    assert not python_exe_exists
    assert path_to_python_exe is None

    # Searching within a directory passed via `options` (the option-is-a-directory branch)
    python_exe_exists, path_to_python_exe = _find_file_path(python_exe, options=[python_dir])
    assert python_exe_exists
    assert path_to_python_exe.name == python_exe

    # `None` entries in `options` are skipped rather than raising
    python_exe_exists, path_to_python_exe = _find_file_path(python_exe, options=[None, python_dir])
    assert python_exe_exists

    # A genuinely non-existent name, with no `options`/`target` able to resolve it, returns False
    text_exe = "pyhelpers.exe"
    test_exe_exists, path_to_test_exe = _find_file_path(
        text_exe, options=[python_dir, sys.executable])
    assert not test_exe_exists
    assert path_to_test_exe is None  # Should return None when nothing matches


def test__format_exception_message():
    res = _format_exception_message(None)
    assert res == ''

    res = _format_exception_message("test")
    assert res == 'test.'

    res = _format_exception_message("test", prefix="Failed.")
    assert res == 'Failed. test.'


def test__print_failure_message(capfd):
    _print_failure_message('test', prefix="Failed.")
    out, _ = capfd.readouterr()
    assert out == 'Failed. test.\n'


@pytest.mark.parametrize('allowed_schemes', [None, {'https'}])
def test__check_url_scheme(allowed_schemes):
    url = 'https://github.com/mikeqfu/pyhelpers'
    parsed_url = _check_url_scheme(url, allowed_schemes=allowed_schemes)
    assert parsed_url.netloc == 'github.com'

    with pytest.raises(ValueError) as exc_info:
        _ = _check_url_scheme('httpx://github.com/mikeqfu/pyhelpers')
    assert str(exc_info.value) == "Unknown/unsafe URL scheme: 'httpx'."


@pytest.mark.parametrize('retry_status', ['default', 123])
def test__init_requests_session(retry_status):
    logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
    s = _init_requests_session(logo_url, retry_status=retry_status)
    assert isinstance(s, requests.sessions.Session)


@pytest.mark.parametrize("colors", ['invalid_color', 'red', ['red', 'blue']])
@pytest.mark.parametrize("show_valid_colors", [False, True])
@pytest.mark.parametrize('concatenated', [True, False])
def test__get_ansi_color_code(colors, show_valid_colors, concatenated):
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
