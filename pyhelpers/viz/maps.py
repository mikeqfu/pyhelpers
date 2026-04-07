"""
Mapping and geographic data plotting.

This submodule provides high-level wrappers for creating interactive maps using
`Folium <https://python-visualization.github.io/folium/>`_. It includes functions
for calculating optimal map centers and initializing base maps directly from
`GeoPandas <https://geopandas.org/>`_ GeoDataFrames.
"""

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
    :rtype: tuple[list[float], list[float], list[float], geopandas.GeoDataFrame]

    **Examples**::

        >>> from pyhelpers.viz import get_base_map_center
        >>> import geopandas as gpd
        >>> from shapely.geometry import Point
        >>> gdf = gpd.GeoDataFrame({'col': [1, 2]}, geometry=[Point(0, 0), Point(2, 2)], crs=4326)
        >>> center_lat_lon, ll_lat_lon, ur_lat_lon, gdf_proj = get_base_map_center(gdf)
        >>> center_lat_lon
        [1.0, 1.0]
        >>> center_lat_lon, ll_lat_lon, ur_lat_lon, gdf_proj = get_base_map_center(
        ...     gdf, center_method='centroid')
        >>> center_lat_lon
        [1.0001523435165862, 0.9999999999999998]
    """

    if gdf.empty:
        raise ValueError("The input GeoDataFrame is empty.")

    # Standardize CRS to WGS84 (EPSG:4326) for Folium compatibility
    target_crs = 'EPSG:4326'
    if gdf.crs is None or not gdf.crs.equals(target_crs):  # noqa
        gdf_proj = gdf.to_crs(target_crs)
    else:
        gdf_proj = gdf.copy()

    # Get the global WGS84 bounds (used for ll and ur in most methods)
    bounds = gdf_proj.total_bounds  # [min_x, min_y, max_x, max_y]
    ll_lat_lon = [bounds[1], bounds[0]]
    ur_lat_lon = [bounds[3], bounds[2]]

    # Calculate center based on selected method
    if center_method == 'bounds':  # Bounds center
        center_lat_lon = [float((bounds[1] + bounds[3]) / 2), float((bounds[0] + bounds[2]) / 2)]

    elif center_method == 'centroid':  # Proper centroid calculation
        # Project to a metric CRS (Web Mercator) for accurate centroid calculation
        gdf_proj_ = gdf_proj.geometry.union_all()
        temp_crs = 'EPSG:3857'
        # Create a temporary Series to project just the union geometry
        temp_gs = gpd.GeoSeries([gdf_proj_], crs=target_crs).to_crs(temp_crs)  # noqa

        centroid_wgs84 = temp_gs.centroid.to_crs(target_crs).iloc[0]
        center_lat_lon = [float(centroid_wgs84.y), float(centroid_wgs84.x)]

    elif center_method == 'convex_hull':
        convex_hull = gdf_proj.geometry.union_all().convex_hull
        center_lat_lon = [float(convex_hull.centroid.y), float(convex_hull.centroid.x)]

    else:
        valid_methods = ('bounds', 'centroid', 'convex_hull')
        raise ValueError(
            f"Invalid `center_method`: '{center_method}'.\n"
            f"  Expected: {valid_methods}")

    return center_lat_lon, ll_lat_lon, ur_lat_lon, gdf_proj


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
    :type tiles: str | list[str] | None
    :param initial_tile_name: Optional custom name to display for the first (default) tile layer
        in the map's Layer Control. If None, the default tile name is used.
    :type initial_tile_name: str | None
    :param add_mini_map: If ``True``, a small inset map is added to the bottom-right corner
        using ``folium.plugins.MiniMap``.
    :type add_mini_map: bool
    :param kwargs: Additional arguments passed to the ``folium.Map`` constructor.
    :type kwargs: dict
    :return: Tuple of (re-projected GeoDataFrame, Folium Map object).
    :rtype: tuple[folium.Map, geopandas.GeoDataFrame]

    **Examples**::

        >>> from pyhelpers.viz import create_base_folium_map
        >>> from pyhelpers._cache import example_dataframe
        >>> from shapely.geometry import Point
        >>> import geopandas as gpd
        >>> df = example_dataframe()
        >>> df['geometry'] = df.apply(lambda x: Point([x.Longitude, x.Latitude]), axis=1)
        >>> gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=4326)
        >>> m, gdf_proj = create_base_folium_map(gdf, fit_bounds=False, zoom_start=7)
        >>> m.show_in_browser()
    """

    center_lat_lon, ll_lat_lon, ur_lat_lon, gdf_proj = get_base_map_center(
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

    return m, gdf_proj
