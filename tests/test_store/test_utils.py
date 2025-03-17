"""
Tests the :mod:`~pyhelpers.store.utils` submodule.
"""

import importlib.resources

import numpy as np
import pytest

from pyhelpers._cache import _add_slashes, example_dataframe
from pyhelpers.store.utils import *


@pytest.mark.parametrize('print_wrap_limit', [None, 10, 100])
def test__check_saving_path(capfd, print_wrap_limit):
    from pyhelpers.store import _check_saving_path

    file_path = os.getcwd()
    with pytest.raises(ValueError) as exc_info:
        _check_saving_path(file_path, verbose=True)
    assert str(exc_info.value) == f"The input for '{file_path}' may not be a file path."

    file_path = "pyhelpers.pdf"
    _check_saving_path(file_path, verbose=True)
    out, _ = capfd.readouterr()
    assert "Saving " in out

    file_path_ = importlib.resources.files("tests").joinpath("documents", "pyhelpers.pdf")
    with importlib.resources.as_file(file_path_) as file_path:
        _check_saving_path(file_path, verbose=True, print_wrap_limit=print_wrap_limit)
        out, _ = capfd.readouterr()

        if print_wrap_limit in {None, 100}:
            assert "Updating " in out and "\t" not in out
        else:
            assert "Updating " in out and "\t" in out


def test__check_loading_path(capfd):
    from pyhelpers.store import _check_loading_path

    file_path = os.path.join("tests", "documents", "pyhelpers.pdf")
    _check_loading_path(file_path, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Loading {_add_slashes(file_path)}' in out


def test__set_index():
    from pyhelpers.store import _set_index

    example_df = example_dataframe()
    assert example_df.equals(_set_index(example_df))

    example_df_ = _set_index(example_df, index=0)
    assert example_df.iloc[:, 0].to_list() == example_df_.index.to_list()

    example_df_ = example_df.copy()
    example_df_.index.name = ''
    example_df_ = _set_index(example_df_.reset_index(), index=None)
    assert np.array_equal(example_df_.values, example_df.values)


if __name__ == '__main__':
    pytest.main()
