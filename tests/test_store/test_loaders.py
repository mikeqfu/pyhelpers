"""Test the module :mod:`~pyhelpers.store`."""

import importlib.resources
import os

import pytest
from scipy.sparse import csr_matrix

from pyhelpers._cache import _add_slashes, _check_relative_pathname, example_dataframe
from pyhelpers.store.loaders import *


def test_load_spreadsheets(capfd):
    path_to_xlsx_ = importlib.resources.files("tests").joinpath("data", "dat.xlsx")

    with importlib.resources.as_file(path_to_xlsx_) as path_to_xlsx:
        wb_data = load_spreadsheets(path_to_xlsx, verbose=True, index_col=0)
        out, _ = capfd.readouterr()
        assert f'Loading {_add_slashes(_check_relative_pathname(path_to_xlsx_.__str__()))} ... \n' \
               '\t\'TestSheet1\'. ... Done.\n' \
               '\t\'TestSheet2\'. ... Done.\n' \
               '\t\'TestSheet11\'. ... Done.\n' \
               '\t\'TestSheet21\'. ... Done.\n' \
               '\t\'TestSheet12\'. ... Done.\n' \
               '\t\'TestSheet22\'. ... Done.\n' in out
        assert isinstance(wb_data, dict)

        wb_data = load_spreadsheets(path_to_xlsx, as_dict=False, index_col=0)
        assert isinstance(wb_data, list)
        assert all(isinstance(x, pd.DataFrame) for x in wb_data)


def test_parse_csr_matrix(capfd):
    data_ = [1, 2, 3, 4, 5, 6]
    indices_ = [0, 2, 2, 0, 1, 2]
    indptr_ = [0, 2, 3, 6]

    csr_mat = csr_matrix((data_, indices_, indptr_), shape=(3, 3))

    assert list(csr_mat.data) == data_
    assert list(csr_mat.indices) == indices_
    assert list(csr_mat.indptr) == indptr_

    path_to_csr_npz_ = importlib.resources.files("tests").joinpath("data", "csr_mat.npz")

    with importlib.resources.as_file(path_to_csr_npz_) as path_to_csr_npz:
        csr_mat_ = load_csr_matrix(path_to_csr_npz, verbose=True)
        out, _ = capfd.readouterr()
        assert "Loading " in out and \
               f'{_add_slashes(os.path.relpath(path_to_csr_npz_.__str__()))} ... Done.\n' in out

    rslt = csr_mat != csr_mat_
    assert isinstance(rslt, csr_matrix)
    assert rslt.count_nonzero() == 0
    assert rslt.nnz == 0

    _ = load_csr_matrix("", verbose=True)
    out, _ = capfd.readouterr()
    assert "No such file or directory" in out


@pytest.mark.parametrize(
    'ext', [
        ".pickle", ".pickle.gz", ".pickle.xz", ".pickle.bz2",
        ".csv", ".xlsx", ".json", ".feather", ".joblib"])
@pytest.mark.parametrize('engine', ['ujson', 'orjson', 'rapidjson', None])
def test_load_data(ext, engine, capfd, caplog):
    path_to_file = importlib.resources.files("tests").joinpath(f"data{os.path.sep}dat{ext}")

    with importlib.resources.as_file(path_to_file) as f:
        if ext in {".csv", ".xlsx", ".feather"}:
            idx_arg = {'path_to_file': f, 'verbose': True, 'index': 0}
        elif ext == ".json":
            idx_arg = {'path_to_file': f, 'verbose': True, 'engine': engine}
        else:
            idx_arg = {'path_to_file': f, 'verbose': True}

        dat = load_data(**idx_arg)
        out, _ = capfd.readouterr()
        assert "Loading " in out and "Done." in out and \
               f"{_add_slashes(os.path.relpath(path_to_file.__str__()))} ... " in out

    if ext == ".xlsx":
        assert isinstance(dat, dict)
        assert dat['TestSheet1'].set_index('City').equals(example_dataframe())
    elif ext == ".json":
        assert list(dat.keys()) == example_dataframe().index.to_list()
    elif ext == ".joblib":
        np.random.seed(0)
        assert np.array_equal(dat, np.random.rand(100, 100))
    else:  # ext in {".pickle", ".pickle.gz", ".pickle.xz", ".pickle.bz2", ".csv", ".feather"}
        assert dat.astype(float).equals(example_dataframe())

    with importlib.resources.as_file(path_to_file) as f:
        _ = load_data(path_to_file=f, verbose=True, test_arg=True)
        out, _ = capfd.readouterr()
        assert "'test_arg'" in out
        assert "invalid keyword argument" in out or "unexpected keyword argument" in out

    # with pytest.warns(UserWarning):
    with caplog.at_level(logging.WARNING):
        dat = load_data(path_to_file='none.test', verbose=True)
        assert dat is None


if __name__ == '__main__':
    pytest.main()
