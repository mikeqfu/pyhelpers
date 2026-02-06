"""
Tests the :mod:`~pyhelpers.store.utils` submodule.
"""

import numpy as np
import pytest

from pyhelpers._cache import _add_slashes, example_dataframe
from pyhelpers.store.utils import *


@pytest.mark.parametrize('print_wrap_limit', [None, 10, 1000])
def test__check_saving_path(print_wrap_limit, tmp_path, capfd):
    from pyhelpers.store import _check_saving_path

    path_to_file = os.getcwd()
    with pytest.raises(ValueError) as exc_info:
        _check_saving_path(path_to_file, verbose=True)
    assert str(exc_info.value) == f"The input for '{path_to_file}' may not be a file path."

    file_path = "pyhelpers.txt"
    _check_saving_path(file_path, verbose=True)
    out, _ = capfd.readouterr()
    assert f"Saving \"{file_path}\" ... " in out

    filename = "pyhelpers.txt"
    path_to_file = tmp_path / filename
    with open(path_to_file, 'w'):
        pass

    _check_saving_path(path_to_file, verbose=True, print_wrap_limit=print_wrap_limit)
    out, _ = capfd.readouterr()

    if print_wrap_limit in {None, 1000}:
        assert "Updating " in out and "\n" not in out
    else:
        assert "Updating " in out and "\n" in out


def test__check_loading_path(tmp_path, capfd):
    from pyhelpers.store import _check_loading_path

    path_to_file = tmp_path / "pyhelpers.txt"
    _check_loading_path(path_to_file, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Loading {_add_slashes(path_to_file)}' in out


def test__set_index():
    from pyhelpers.store import _set_index

    example_df = example_dataframe()
    assert example_df.equals(_set_index(example_df))

    example_df_ = _set_index(example_df, index_col=0)
    assert example_df.iloc[:, 0].to_list() == example_df_.index.to_list()

    example_df_ = example_df.copy()
    example_df_.index.name = ''
    example_df_ = _set_index(example_df_.reset_index(), index_col=None)
    assert np.array_equal(example_df_.values, example_df.values)


if __name__ == '__main__':
    pytest.main()
