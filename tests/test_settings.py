"""Test the module :mod:`~pyhelpers.settings`."""

import pytest

from pyhelpers.settings import *


# ==================================================================================================
# configs - Configurations.
# ==================================================================================================

@pytest.mark.parametrize('reset', [False, True])
def test_gdal_configurations(reset):
    gdal_configurations(reset=reset)


# ==================================================================================================
# prefs - Preferences.
# ==================================================================================================

@pytest.mark.parametrize('reset', [False, True, 'all'])
@pytest.mark.parametrize('backend', [None, 'TkAgg'])
@pytest.mark.parametrize('font_name', [None, 'Cambria'])
@pytest.mark.parametrize('fig_style', [None, 'ggplot'])
def test_mpl_preferences(reset, backend, font_name, fig_style):
    mpl_preferences(reset=reset, backend='TkAgg', font_name=font_name, fig_style=fig_style)


@pytest.mark.parametrize('reset', [False, True])
def test_np_preferences(reset):
    np_preferences(reset=reset)


@pytest.mark.parametrize('reset', [False, True, 'all'])
@pytest.mark.parametrize('east_asian_text', [False, True])
@pytest.mark.parametrize('ignore_future_warning', [False, True])
@pytest.mark.filterwarnings("ignore::FutureWarning")
def test_pd_preferences(reset, east_asian_text, ignore_future_warning):
    pd_preferences(
        reset=reset, east_asian_text=east_asian_text, ignore_future_warning=ignore_future_warning)


if __name__ == '__main__':
    pytest.main()
