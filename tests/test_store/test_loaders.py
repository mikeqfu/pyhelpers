"""Test the module :mod:`~pyhelpers.store`."""

import importlib.resources

import pytest
import sklearn.linear_model

from pyhelpers._cache import _add_slashes, _check_relative_pathname, example_dataframe
from pyhelpers.store.loaders import *


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
        import geopandas as gpd

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
        ".csv", ".xlsx", ".ods", ".json", ".feather", ".joblib", ".parquet"])
@pytest.mark.parametrize('engine', ['ujson', 'orjson', 'rapidjson', None])
def test_load_data(file_ext, engine, capfd, caplog):
    original_data = example_dataframe()

    path_to_file_ = importlib.resources.files("tests").joinpath("data", f"dat{file_ext}")

    with importlib.resources.as_file(path_to_file_) as path_to_file:
        args = {'path_to_file': path_to_file, 'verbose': True}
        if file_ext in {".csv", ".xlsx", ".ods", ".feather"}:
            args.update({'index_col': 0})  # noqa
        elif file_ext in {".json", ".parquet"}:
            args.update({'engine': engine})  # noqa

        if file_ext == ".parquet" and engine is not None:
            with pytest.warns(UserWarning):
                retrieved_data = load_data(**args)
        else:
            retrieved_data = load_data(**args)

        out, _ = capfd.readouterr()

        assert f"Loading {_add_slashes(_check_relative_pathname(path_to_file))} ... " in out
        assert "Done." in out

    if file_ext in {".xlsx", ".ods"}:
        assert isinstance(retrieved_data, dict)
        assert retrieved_data['TestSheet1'].equals(original_data)
    elif file_ext == ".json":
        assert list(retrieved_data.keys()) == original_data.index.to_list()
    elif file_ext == ".joblib":
        assert isinstance(retrieved_data, sklearn.linear_model.LinearRegression)
    else:  # file_ext in {".pickle", ".pickle.gz", ".pickle.xz", ".pickle.bz2", ".csv", ".feather"}
        assert retrieved_data.astype(float).equals(original_data)

    with importlib.resources.as_file(path_to_file_) as path_to_file:
        _ = load_data(path_to_file=path_to_file, verbose=True, test_arg=True)

        out, _ = capfd.readouterr()
        assert "'test_arg'" in out
        assert "invalid keyword argument" in out or "unexpected keyword argument" in out

    # with pytest.warns(UserWarning):
    with caplog.at_level(logging.WARNING):
        retrieved_data = load_data(path_to_file='none.test', verbose=True)
        assert retrieved_data is None


if __name__ == '__main__':
    pytest.main()
