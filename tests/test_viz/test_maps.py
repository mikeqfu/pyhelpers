"""
Tests the :mod:`~pyhelpers.viz.maps` submodule.
"""

from pathlib import Path

import folium
import pytest

from pyhelpers.store import load_geopackage
from pyhelpers.viz import create_base_folium_map


@pytest.mark.parametrize('fit_bounds', [True, False])
@pytest.mark.parametrize('tiles', [None, ['CartoDB Positron', 'OpenStreetMap']])
def test_create_base_folium_map(fit_bounds, tiles):
    test_data_path = Path(__file__).resolve().parents[1] / "data" / "dat.gpkg"
    gdf = load_geopackage(test_data_path)

    # noinspection PyTypeChecker
    m1, gdf_4326_1 = create_base_folium_map(gdf, fit_bounds=fit_bounds, tiles=tiles)
    assert gdf_4326_1.crs.to_epsg() == 4326
    assert isinstance(m1, folium.Map)

    # noinspection PyTypeChecker
    m2, gdf_4326_2 = create_base_folium_map(
        gdf, fit_bounds=fit_bounds, tiles=tiles, initial_tile_name="Test tile")
    assert gdf_4326_2.crs.to_epsg() == 4326
    assert isinstance(m2, folium.Map)


if __name__ == '__main__':
    pytest.main()
