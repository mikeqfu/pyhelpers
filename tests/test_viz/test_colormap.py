import pytest

from pyhelpers.viz.colormap import *


def test_cmap_discretisation():
    import folium
    import branca

    m = folium.Map()

    test_feature_group = folium.FeatureGroup(name='Test')
    test_feature_cm = branca.colormap.LinearColormap(
        colors=branca.colormap.linear.RdYlGn_06.colors[::-1],
        vmin=0.0,
        vmax=1.0,
        caption="Test",
    )

    m.add_child(BindColormap(test_feature_group, test_feature_cm))

    assert isinstance(m, folium.folium.Map)


if __name__ == '__main__':
    pytest.main()
