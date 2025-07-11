"""
Colormap utilities for Folium map visualization.
"""

from .._cache import _check_dependencies


class BindColormap:
    """
    Binds a colormap to a Folium layer with visibility synchronization.

    This class creates a connection between a Folium map layer and a color scale,
    showing/hiding the colormap legend when the layer visibility changes.
    """

    def __new__(cls, layer, colormap, display=True):
        """
        :param layer: Folium layer object (``FeatureGroup``, ``GeoJson``, etc.) to bind with.
        :type layer: folium.FeatureGroup | folium.GeoJson
        :param colormap: Color scale to display and synchronize with layer visibility.
        :type colormap: branca.colormap.ColorMap
        :param display: Initial visibility state of the colormap legend;
            when ``display=True`` (default), the legend will be visible by default;
            valid options are ``'block'`` (visible) or ``'none'`` (hidden).
        :type display: bool

        .. note::

            Requires Folium's ``LayerControl`` to be enabled for automatic visibility toggling.

        **Examples**::

            >>> from pyhelpers.viz import BindColormap
            >>> import folium
            >>> import branca
            >>> m = folium.Map()
            >>> test_feature_group = folium.FeatureGroup(name='Test')
            >>> test_feature_cm = branca.colormap.LinearColormap(
            ...     colors=branca.colormap.linear.RdYlGn_06.colors[::-1],
            ...     vmin=0.0,
            ...     vmax=1.0,
            ...     caption="Test",
            ... )
            >>> m.add_child(BindColormap(test_feature_group, test_feature_cm))
            >>> m

        .. seealso::

            - Example usages: `Exploration of UK's Food Hygiene Rating data
              <https://github.com/mikeqfu/uk-fsa-fhr-exploration/blob/master/src/
              geographic_disparities.py>`_
            - Reference: [`VIZ-BC-1
              <https://nbviewer.org/gist/BibMartin/f153aa957ddc5fadc64929abdee9ff2e>`_].
        """

        branca, jinja2 = _check_dependencies('branca', 'jinja2')

        class _BindColormap(branca.element.MacroElement):

            def __init__(self, _layer, _colormap, _display):
                super().__init__()

                self.layer = _layer
                self.colormap = _colormap

                display_first = "'block'" if _display else "'none'"

                # noinspection SpellCheckingInspection
                template_str = u"""
                    {% macro script(this, kwargs) %}
                        {{this.colormap.get_name()}}.svg[0][0].style.display = {display_first};
                        {{this._parent.get_name()}}.on('overlayadd', function(eventLayer) {
                            if (eventLayer.layer == {{this.layer.get_name()}}) {
                                {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
                            }});
                        {{this._parent.get_name()}}.on('overlayremove', function(eventLayer) {
                            if (eventLayer.layer == {{this.layer.get_name()}}) {
                                {{this.colormap.get_name()}}.svg[0][0].style.display = 'none';
                            }});
                    {% endmacro %}
                    """

                self._template = jinja2.Template(
                    template_str.replace('{display_first}', display_first))

        # Instantiate the dynamic subclass and return it directly
        return _BindColormap(layer, colormap, display)
