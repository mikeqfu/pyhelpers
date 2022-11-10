"""Test the module :mod:`~pyhelpers.settings`."""

import pytest


@pytest.mark.parametrize('reset', [False, True])
def test_gdal_configurations(reset):
    from pyhelpers.settings import gdal_configurations

    gdal_configurations(reset=reset)


@pytest.mark.parametrize('reset', [False, True, 'all'])
@pytest.mark.parametrize('backend', [None, 'TkAgg'])
@pytest.mark.parametrize('font_name', [None, 'Cambria'])
@pytest.mark.parametrize('fig_style', [None, 'ggplot'])
def test_mpl_preferences(reset, backend, font_name, fig_style):
    from pyhelpers.settings import mpl_preferences

    mpl_preferences(reset=reset, backend='TkAgg', font_name=font_name, fig_style=fig_style)


@pytest.mark.parametrize('reset', [False, True])
def test_np_preferences(reset):
    from pyhelpers.settings import np_preferences

    np_preferences(reset=reset)


@pytest.mark.parametrize('reset', [False, True, 'all'])
@pytest.mark.parametrize('east_asian_text', [False, True])
@pytest.mark.parametrize('ignore_future_warning', [False, True])
@pytest.mark.filterwarnings("ignore::FutureWarning")
def test_pd_preferences(reset, east_asian_text, ignore_future_warning):
    from pyhelpers.settings import pd_preferences

    pd_preferences(
        reset=reset, east_asian_text=east_asian_text, ignore_future_warning=ignore_future_warning)


if __name__ == '__main__':
    pytest.main()
