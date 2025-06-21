"""
Colourmap utilities for Folium map visualisation.
"""

from .._cache import _check_dependencies

branca, jinja2 = _check_dependencies('branca', 'jinja2')


class BindColourmap(branca.element.MacroElement):
    """
    Binds a colourmap to a Folium layer with visibility synchronisation.

    This class creates a connection between a Folium map layer and a colour scale,
    showing/hiding the colourmap legend when the layer visibility changes.
    """

    def __init__(self, layer, colour_map, display=True):
        """
        :param layer: Folium layer object (FeatureGroup, GeoJson, etc.) to bind with.
        :type layer: folium.FeatureGroup or folium.GeoJson or folium.vector_layers.Path
        :param colour_map: Color scale to display and synchronise with layer visibility.
        :type colour_map: branca.colormap.ColorMap
        :param display: Whether to display the colour map when opening maps
            (i.e. initial visibility state of the colormap legend), with valid options including
            ``{'block', 'none'}``; defaults to ``'block'``.
        :type display: bool

        .. note::

            Requires Folium's ``LayerControl`` to be enabled for automatic visibility toggling.

        .. seealso::

            Reference: https://nbviewer.org/gist/BibMartin/f153aa957ddc5fadc64929abdee9ff2e

        **Examples**::

            >>> from pyhelpers.viz import BindColourmap
        """

        super(BindColourmap, self).__init__()

        self.layer = layer
        self.colormap = colour_map

        display_first = "'block'" if display else "'none'"

        # noinspection SpellCheckingInspection
        template_str = u"""
            {% macro script(this, kwargs) %}
                {{this.colormap.get_name()}}.svg[0][0].style.display = {display_first};
                {{this._parent.get_name()}}.on('overlayadd', function (eventLayer) {
                    if (eventLayer.layer == {{this.layer.get_name()}}) {
                        {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
                    }});
                {{this._parent.get_name()}}.on('overlayremove', function (eventLayer) {
                    if (eventLayer.layer == {{this.layer.get_name()}}) {
                        {{this.colormap.get_name()}}.svg[0][0].style.display = 'none';
                    }});
            {% endmacro %}
            """

        self._template = jinja2.Template(template_str.replace('{display_first}', display_first))
