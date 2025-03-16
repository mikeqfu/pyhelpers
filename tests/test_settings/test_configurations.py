"""
Tests the :mod:`~pyhelpers.settings.configurations` submodule.
"""

import pytest

from pyhelpers.settings.configurations import *


@pytest.mark.parametrize('reset', [False, True])
def test_gdal_configurations(reset):
    gdal_configurations(reset=reset)


if __name__ == '__main__':
    pytest.main()
