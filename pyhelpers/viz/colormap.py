"""
Colormap utilities for Folium map visualization.
"""

from .._cache import _check_dependencies

branca, jinja2 = _check_dependencies('branca', 'jinja2')


class BindColormap(branca.element.MacroElement):
    """
    Binds a colormap to a Folium layer with visibility synchronization.

    This class creates a connection between a Folium map layer and a color scale,
    showing/hiding the colormap legend when the layer visibility changes.
    """

    def __init__(self, layer, colormap, display=True):
        """
        :param layer: Folium layer object (FeatureGroup, GeoJson, etc.) to bind with.
        :type layer: folium.FeatureGroup | folium.GeoJson | folium.vector_layers.Path
        :param colormap: Color scale to display and synchronize with layer visibility.
        :type colormap: branca.colormap.ColorMap
        :param display: Initial visibility state of the colormap legend. When ``True`` (default),
            the legend will be visible by default;
            valid options are ``'block'`` (visible) or ``'none'`` (hidden).
        :type display: bool

        .. note::

            Requires Folium's ``LayerControl`` to be enabled for automatic visibility toggling.

        .. seealso::

            - Example usages:
              - `Exploration of UK's Food Hygiene Rating data
                <https://github.com/mikeqfu/uk-fsa-fhr-exploration/blob/
                master/src/geographic_disparities.py>`_
            - Reference: [`VIZ-BC-1
              <https://nbviewer.org/gist/BibMartin/f153aa957ddc5fadc64929abdee9ff2e>`_].
        """

        super().__init__()

        self.layer = layer
        self.colormap = colormap

        display_first = "'block'" if display else "'none'"

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

        self._template = jinja2.Template(template_str.replace('{display_first}', display_first))
