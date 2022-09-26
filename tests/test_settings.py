"""Test the module :mod:`~pyhelpers.settings`."""

import pytest


def test_gdal_configurations():
    from pyhelpers.settings import gdal_configurations

    gdal_configurations()

    gdal_configurations(reset=True)


def test_mpl_preferences():
    from pyhelpers.settings import mpl_preferences

    mpl_preferences(backend='TkAgg')

    mpl_preferences(fig_style='ggplot')

    mpl_preferences(reset=True)


def test_np_preferences():
    from pyhelpers.settings import np_preferences

    np_preferences()

    np_preferences(reset=True)


def test_pd_preferences():
    from pyhelpers.settings import pd_preferences

    pd_preferences()

    pd_preferences(reset=True)


if __name__ == '__main__':
    pytest.main()
