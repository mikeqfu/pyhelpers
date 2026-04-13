"""
Test the module :mod:`~pyhelpers.store.loaders`.
"""

import importlib.resources
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
import sklearn.linear_model
from shapely.geometry import Point

from pyhelpers._cache import _add_slashes, _check_relative_pathname, example_dataframe
from pyhelpers.store.loaders import load_csr_matrix, load_data, load_geopackage, load_parquet, \
    load_spreadsheets


def test_load_spreadsheets(capfd):
    path_to_xlsx_ = importlib.resources.files("tests").joinpath("data", "dat.xlsx")

    with importlib.resources.as_file(path_to_xlsx_) as path_to_xlsx:
        wb_data = load_spreadsheets(path_to_xlsx, verbose=True, index_col=0)
        out, _ = capfd.readouterr()
        assert f'Loading {_add_slashes(_check_relative_pathname(str(path_to_xlsx_)))} ... \n' \
               '  \'TestSheet1\'. ... Done.\n' \
               '  \'TestSheet2\'. ... Done.\n' \
               '  \'TestSheet11\'. ... Done.\n' \
               '  \'TestSheet21\'. ... Done.\n' \
               '  \'TestSheet12\'. ... Done.\n' \
               '  \'TestSheet22\'. ... Done.\n' in out
        assert isinstance(wb_data, dict)

        wb_data = load_spreadsheets(path_to_xlsx, as_dict=False, index_col=0)
        assert isinstance(wb_data, list)
        assert all(isinstance(x, pd.DataFrame) for x in wb_data)


@pytest.mark.parametrize('engine', ['not-an-engine', None, 'pyarrow', 'fastparquet'])
@pytest.mark.parametrize('file_ext', ['.parquet', '.geoparquet'])
@pytest.mark.parametrize('data_type', ['df', 'gdf'])
def test_load_parquet(engine, file_ext, data_type, tmp_path, capfd):
    original_data = example_dataframe()
    path_to_parquet = tmp_path / f"test_data{file_ext}"

    if data_type == 'df':
        original_data.to_parquet(path_to_parquet, index=True)

    elif data_type == 'gdf':
        original_data['geometry'] = gpd.points_from_xy(
            original_data['Longitude'], original_data['Latitude'])
        original_data = gpd.GeoDataFrame(original_data, crs="EPSG:4326")
        original_data.to_parquet(path_to_parquet)

    if engine == 'not-an-engine' and data_type != 'gdf':  # Test invalid engine fallback
        # Should trigger ValueError -> pq.read_table -> to_pandas()
        with pytest.warns(UserWarning, match="Falling back to PyArrow"):
            retrieved_data = load_parquet(path_to_parquet, engine=engine, verbose=True)
    elif engine == 'fastparquet' and data_type == 'df':
        with pytest.warns(UserWarning, match="retried and resolved using `pyarrow`"):
            retrieved_data = load_parquet(path_to_parquet, engine=engine, verbose=True)
    else:
        retrieved_data = load_parquet(path_to_parquet, engine=engine, verbose=True)
        out, _ = capfd.readouterr()
        assert "Loading" in out and "Done." in out

    assert retrieved_data.equals(original_data)


def test_load_geopackage(tmp_path):
    """
    Test loading single and multi-layer GeoPackage files.
    """
    # import tempfile, pathlib; tmp_path = pathlib.Path(tempfile.mkdtemp())
    crs = 4326  # Create mock data
    gdf1 = gpd.GeoDataFrame({'City': ['London'], 'geometry': [Point(-0.1276, 51.5073)]}, crs=crs)
    gdf2 = gpd.GeoDataFrame({'City': ['Paris'], 'geometry': [Point(2.3522, 48.8566)]}, crs=crs)

    gpkg_path = tmp_path / "test_data.gpkg"

    # Test single layer
    gdf1.to_file(gpkg_path, layer='cities', driver='GPKG')

    loaded_df = load_geopackage(gpkg_path)
    assert isinstance(loaded_df, gpd.GeoDataFrame)
    assert loaded_df.iloc[0]['City'] == 'London'
    # noinspection PyUnresolvedReferences
    assert loaded_df.crs.equals(crs)

    # Test Reprojection (target_crs), using EPSG:3857 (Web Mercator)
    test_crs = 3857
    loaded_df_3857 = load_geopackage(gpkg_path, target_crs=test_crs)
    assert isinstance(loaded_df_3857, gpd.GeoDataFrame)
    # noinspection PyUnresolvedReferences
    assert loaded_df_3857.crs.equals(test_crs)

    # Test multi-layer (returns a dict)
    gdf2.to_file(gpkg_path, layer='capitals', driver='GPKG')

    loaded_dict = load_geopackage(gpkg_path)
    assert isinstance(loaded_dict, dict)
    assert 'cities' in loaded_dict
    assert 'capitals' in loaded_dict
    assert loaded_dict['capitals'].iloc[0]['City'] == 'Paris'

    # Test specific layer loading via kwargs
    specific_layer = load_geopackage(gpkg_path, layer='capitals')
    assert isinstance(specific_layer, gpd.GeoDataFrame)
    assert len(specific_layer) == 1
    assert specific_layer.iloc[0]['City'] == 'Paris'

    # Test failure handling
    non_existent_path = tmp_path / "missing.gpkg"
    result = load_geopackage(non_existent_path, raise_error=False, verbose=False)
    assert result is None

    with pytest.raises(Exception):
        load_geopackage(non_existent_path, raise_error=True)


def test_load_csr_matrix(capfd):
    import scipy.sparse

    data_ = [1, 2, 3, 4, 5, 6]
    indices_ = [0, 2, 2, 0, 1, 2]
    indptr_ = [0, 2, 3, 6]

    csr_mat = scipy.sparse.csr_matrix((data_, indices_, indptr_), shape=(3, 3))

    assert list(csr_mat.data) == data_
    assert list(csr_mat.indices) == indices_
    assert list(csr_mat.indptr) == indptr_

    path_to_csr_npz_ = importlib.resources.files("tests").joinpath("data", "csr_mat.npz")

    with importlib.resources.as_file(path_to_csr_npz_) as path_to_csr_npz:
        csr_mat_ = load_csr_matrix(path_to_csr_npz, verbose=True)
        out, _ = capfd.readouterr()
        assert f"Loading {_add_slashes(_check_relative_pathname(path_to_csr_npz))}" in out
        assert "Done." in out

    rslt = csr_mat != csr_mat_
    assert isinstance(rslt, scipy.sparse.csr_matrix)
    assert rslt.count_nonzero() == 0
    assert rslt.nnz == 0

    _ = load_csr_matrix("", verbose=True)
    out, _ = capfd.readouterr()
    assert "No such file or directory" in out


@pytest.mark.parametrize(
    'file_ext', [
        ".pickle", ".pickle.gz", ".pickle.xz", ".pickle.bz2",
        ".csv", ".xlsx", ".ods", ".json", ".feather", ".joblib", ".parquet", ".gpkg",
        ".processed.pkl.xz", ".gold.parquet"
    ]
)
@pytest.mark.parametrize('engine', ['ujson', 'orjson', 'rapidjson', None])
def test_load_data(file_ext, engine, capfd, caplog):
    original_data = example_dataframe()

    path_to_file = Path(__file__).resolve().parents[1] / "data" / f"dat{file_ext}"

    args = {'path_to_file': path_to_file, 'verbose': True}
    if file_ext.endswith((".csv", ".xlsx", ".ods", ".feather")):
        args['index_col'] = 0
    elif file_ext.endswith((".json", ".parquet")):
        args['engine'] = engine

    if file_ext.endswith((".parquet", ".geoparquet")) and engine is not None:
        with pytest.warns(UserWarning):
            retrieved_data = load_data(**args)
    else:
        retrieved_data = load_data(**args)

    out, _ = capfd.readouterr()

    assert f"Loading {_add_slashes(_check_relative_pathname(path_to_file))} ... " in out
    assert "Done." in out

    if file_ext.endswith((".xlsx", ".ods")):
        assert isinstance(retrieved_data, dict)
        assert retrieved_data['TestSheet1'].equals(original_data)
    elif file_ext == ".json":
        assert list(retrieved_data.keys()) == original_data.index.to_list()
    elif file_ext == ".joblib":
        assert isinstance(retrieved_data, sklearn.linear_model.LinearRegression)
    elif file_ext == ".gpkg":
        assert retrieved_data.crs is not None
    else:
        # file_ext.endswith(
        #     (".pickle", ".pickle.gz", ".pickle.xz", ".pickle.bz2", ".processed.pkl.xz",
        #      ".csv", ".feather"))
        assert retrieved_data.astype(float).equals(original_data)

    if file_ext == ".gpkg":
        with pytest.warns(RuntimeWarning, match=r"does not support open option TEST_ARG"):
            _ = load_data(path_to_file=path_to_file, suppress_warnings=False, test_arg=True)
    else:
        _ = load_data(path_to_file=path_to_file, verbose=True, test_arg=True)
        out, _ = capfd.readouterr()
        if file_ext != ".gpkg":
            assert "'test_arg'" in out
            assert "invalid keyword argument" in out or "unexpected keyword argument" in out

    # with pytest.warns(UserWarning):
    with caplog.at_level(logging.WARNING):
        retrieved_data = load_data(path_to_file='none.test', verbose=True)
        assert retrieved_data is None


if __name__ == '__main__':
    pytest.main()
