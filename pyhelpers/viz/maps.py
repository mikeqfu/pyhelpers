"""
Mapping and geographic data plotting.

This submodule provides high-level wrappers for creating interactive maps using
`Folium <https://python-visualization.github.io/folium/>`_. It includes functions
for calculating optimal map centers and initializing base maps directly from
`GeoPandas <https://geopandas.org/>`_ GeoDataFrames.
"""

import shapely

from .._cache import _lazy_check_dependencies


@_lazy_check_dependencies(gpd='geopandas')
def get_base_map_center(gdf, center_method='bounds'):
    # noinspection PyShadowingNames
    """
    Calculates geographical center and bounding box for a GeoDataFrame.

    This function prepares data for web mapping by re-projecting to EPSG:4326 and calculating
    coordinates based on the chosen geometric method.
    It is primarily used to determine the initial central point for creating a base map using
    libraries such as Folium or Leaflet.

    :param gdf: Input GeoDataFrame containing geographical features.
    :type gdf: geopandas.GeoDataFrame
    :param center_method: Method to calculate the center:

        - ``'bounds'``: Calculates the center based on the arithmetic mean of the bounding box
          corners (quickest method).
        - ``'centroid'``: Calculates the true geometric centroid of the merged (union) geometry
          (most accurate, requires projection).
        - ``'convex_hull'``: Calculates the centroid of the convex hull of all geometries
          (quicker than 'centroid' for complex data).

    :type center_method: str
    :return: A tuple containing the re-projected GeoDataFrame and the center coordinates.
        The center coordinates are returned as a list `[latitude, longitude]`.
    :rtype: tuple[geopandas.GeoDataFrame, list[float], list[float], list[float]]

    **Examples**::

        >>> from pyhelpers.viz import get_base_map_center
        >>> # gdf_proj, center, ll, ur = get_base_map_center(my_gdf)
    """

    # Converted CRS to EPSG:4326 for Folium compatibility
    gdf_proj = gdf.to_crs(epsg=4326) if not gdf.crs.equals(4326) else gdf.copy()

    if gdf_proj.empty:
        raise ValueError("The input GeoDataFrame is empty.")

    # Calculate center based on selected method
    if center_method == 'bounds':  # Bounds center
        bounds = gdf_proj.total_bounds
        center_lat_lon = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        ll_lat_lon = [bounds[1], bounds[0]]
        ur_lat_lon = [bounds[3], bounds[2]]

    elif center_method == 'centroid':  # Proper centroid calculation
        # Project to a metric CRS (Web Mercator) for accurate centroid calculation
        gdf_proj_ = gdf_proj.geometry.union_all()
        # Create a temporary Series to project just the union geometry
        temp_gs = gpd.GeoSeries([gdf_proj_], crs='EPSG:4326').to_crs(epsg=3857)  # noqa
        centroid_3857 = temp_gs.centroid.iloc[0]

        # Convert centroid and bounds back to 4326
        dat = gpd.GeoSeries([  # noqa
            centroid_3857,
            shapely.Point(temp_gs.total_bounds[[0, 1]]),
            shapely.Point(temp_gs.total_bounds[[2, 3]])
        ], crs='EPSG:3857').to_crs(epsg=4326)

        center_lat_lon = [dat.iloc[0].y, dat.iloc[0].x]
        ll_lat_lon = [dat.iloc[1].y, dat.iloc[1].x]
        ur_lat_lon = [dat.iloc[2].y, dat.iloc[2].x]

    elif center_method == 'convex_hull':
        convex_hull = gdf_proj.geometry.union_all().convex_hull
        center_lat_lon = [convex_hull.centroid.y, convex_hull.centroid.x]
        ll_lat_lon = [convex_hull.bounds[1], convex_hull.bounds[0]]
        ur_lat_lon = [convex_hull.bounds[3], convex_hull.bounds[2]]

    else:
        valid_methods = ('bounds', 'centroid', 'convex_hull')
        raise ValueError(f"Invalid `center_method`: '{center_method}'.\n"
                         f"  Expected: {valid_methods}")

    return gdf_proj, center_lat_lon, ll_lat_lon, ur_lat_lon


@_lazy_check_dependencies('folium', 'folium.plugins')
def create_base_folium_map(gdf, center_method='bounds', fit_bounds=True, tiles=None,
                           initial_tile_name=None, add_mini_map=True, **kwargs):
    # noinspection PyShadowingNames,PyTypeChecker
    """
    Initializes a Folium map centered on the extent of a GeoDataFrame.

    This function first calls :func:`~pyhelpers.viz.maps.get_base_map_center`
    to calculate the map center coordinates and re-project the data to EPSG:4326 (WGS84),
    which is required by Folium.

    :param gdf: Input GeoDataFrame containing the geographical features.
    :type gdf: geopandas.GeoDataFrame
    :param center_method: The method used to calculate the map center.

        - ``'bounds'``: Calculates the center based on the arithmetic mean of the bounding box
          corners (quickest method).
        - ``'centroid'``: Calculates the true geometric centroid of the merged (union) geometry
          (most accurate, requires projection).
        - ``'convex_hull'``: Calculates the centroid of the convex hull of all geometries
          (quicker than 'centroid' for complex data).

    :type center_method: str
    :param fit_bounds: Whether to automatically adjust the map view to
        fit the full extent of the data bounds. Defaults to ``True``.
    :type fit_bounds: bool
    :param tiles: The tile layer(s) to use. Can be a string (e.g. ``'CartoDB positron'``) or a list
        of strings for multiple tile layers.
    :type tiles: str | list[str]
    :param initial_tile_name: Optional custom name to display for the first (default) tile layer
        in the map's Layer Control. If None, the default tile name is used.
    :type initial_tile_name: str | None
    :param add_mini_map: If ``True``, a small inset map is added to the bottom-right corner
        using ``folium.plugins.MiniMap``.
    :type add_mini_map: bool
    :param kwargs: Additional arguments passed to the ``folium.Map`` constructor.
    :type kwargs: dict
    :return: Tuple of (re-projected GeoDataFrame, Folium Map object).
    :rtype: tuple[geopandas.GeoDataFrame, folium.Map]

    **Examples**::

        >>> from pyhelpers.viz import create_base_folium_map
        >>> from pyhelpers._cache import example_dataframe
        >>> from shapely.geometry import Point
        >>> import geopandas as gpd
        >>> df = example_dataframe()
        >>> df['geometry'] = df.apply(lambda x: Point([x.Longitude, x.Latitude]), axis=1)
        >>> gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=4326)
        >>> gdf_proj, m = create_base_folium_map(gdf, fit_bounds=False, zoom_start=7)
        >>> m.show_in_browser()
    """

    gdf_proj, center_lat_lon, ll_lat_lon, ur_lat_lon = get_base_map_center(
        gdf=gdf, center_method=center_method)

    # Handle tiles logic
    tiles_list = tiles if isinstance(tiles, list) else [tiles or 'CartoDB Positron']
    if not all(isinstance(t, str) for t in tiles_list):
        raise TypeError("`tiles` must be a string or a list of strings.")

    primary_tile = tiles_list[0]
    other_tiles = tiles_list[1:]

    # Map configuration
    map_args = {
        'control_scale': True,
        'location': center_lat_lon,
        'tiles': None,
        'attributionControl': False,
        **kwargs
    }

    # Create map
    m = folium.Map(**map_args)  # noqa

    # Add Tile Layers
    folium.TileLayer(  # noqa
        tiles=primary_tile,
        name=initial_tile_name or primary_tile,
        overlay=False,
        control=True
    ).add_to(m)

    # Add subsequent tile layers
    for tile in other_tiles:
        folium.TileLayer(tiles=tile, name=tile, overlay=False, show=False).add_to(m)  # noqa

    # Add MiniMap
    if add_mini_map:
        folium.plugins.MiniMap(position='bottomright', zoom_level_offset=-5).add_to(m)  # noqa

    # Auto-fit bounds if requested
    if fit_bounds and not gdf_proj.empty:
        m.fit_bounds([ll_lat_lon, ur_lat_lon])

    # Add a control to the map to show or hide layers
    folium.LayerControl(collapsed=True).add_to(m)  # noqa

    return gdf_proj, m
