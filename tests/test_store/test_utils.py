"""
Tests the :mod:`~pyhelpers.store.utils` submodule.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pyhelpers._cache import _add_slashes, example_dataframe
from pyhelpers.store.utils import _check_loading_path, _check_saving_path, _set_index


@pytest.mark.parametrize('print_wrap_limit', [None, 10, 1000])
def test__check_saving_path(print_wrap_limit, tmp_path, capfd):
    path = Path.cwd()
    with pytest.raises(ValueError) as exc_info:
        _check_saving_path(path, verbose=True)
    assert (str(exc_info.value) ==
            f'The input "{str(path)}" appears to be a directory, not a file path.')

    path = "pyhelpers.txt"
    _check_saving_path(path, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{path}" ... ' in out

    filename = "pyhelpers.txt"
    path = tmp_path / filename
    with open(path, 'w'):
        pass

    _check_saving_path(path, verbose=True, msg_wrap_limit=print_wrap_limit)
    out, _ = capfd.readouterr()

    if print_wrap_limit in {None, 1000}:
        assert "Updating " in out and "\n" not in out
    else:
        assert "Updating " in out and "\n" in out


def test__check_loading_path(tmp_path, capfd):
    path = tmp_path / "pyhelpers.txt"
    _check_loading_path(path, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Loading {_add_slashes(path)}' in out


def test__set_index():
    example_df = example_dataframe()

    # Basic Identity: index_col=None on a df with a named index should do nothing
    assert example_df.equals(_set_index(example_df))

    # Positional Indexing: Set first column (Longitude) as index
    example_df_pos = _set_index(example_df, index_col=0)
    assert example_df_pos.index.name == 'Longitude'
    assert 'Longitude' not in example_df_pos.columns

    # Label-based Indexing: Reset and set back by name
    example_df_res = example_df.reset_index()
    example_df_lab = _set_index(example_df_res, index_col='City')
    assert example_df_lab.equals(example_df)

    # Unnamed/None Logic: Handle empty string index name
    example_df_unnamed = example_df.copy()
    example_df_unnamed.index.name = ''
    # reset_index() makes the first column name ''
    example_df_unnamed = _set_index(example_df_unnamed.reset_index(), index_col=None)
    assert np.array_equal(example_df_unnamed.values, example_df.values)
    assert example_df_unnamed.index.name is None

    # MultiIndex & De-duplication: [0, 'City'] where 0 is 'City'
    example_df_res = example_df.reset_index()  # Cols: ['City', 'Longitude', 'Latitude']
    example_df_multi = _set_index(example_df_res, index_col=[0, 'City'])
    # Should NOT be a MultiIndex because 0 and 'City' are the same column
    assert not isinstance(example_df_multi.index, pd.MultiIndex)
    assert example_df_multi.index.name == 'City'

    # Actual MultiIndex: Mixed types
    example_df_multi_real = _set_index(example_df_res, index_col=['City', 1])
    assert isinstance(example_df_multi_real.index, pd.MultiIndex)
    # noinspection PyUnresolvedReferences
    assert list(example_df_multi_real.index.names) == ['City', 'Longitude']

    # Error Handling: Missing column
    with pytest.raises(KeyError):
        _set_index(example_df, index_col='NonExistentColumn')

    # Error Handling: Out of bounds
    with pytest.raises(IndexError):
        _set_index(example_df, index_col=99)


if __name__ == '__main__':
    pytest.main()
