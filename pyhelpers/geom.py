"""Manipulation of geometric/geographical data."""

import collections.abc
import copy
import functools
import typing

import numpy as np
import pyproj
import shapely.geometry
import shapely.ops

from ._cache import _check_dependency


# ==================================================================================================
# Geometric data transformation
# ==================================================================================================

# -- Geometric type --------------------------------------------------------------------------------

def transform_geom_point_type(*pts, as_geom=True):
    """
    Transform iterable to
    `shapely.geometry.Point <https://shapely.readthedocs.io/en/latest/manual.html#points>`_ type,
    or the other way round.

    :param pts: data of points (e.g. list of lists/tuples)
    :type pts: list or tuple or shapely.geometry.Point
    :param as_geom: whether to return point(s) as `shapely.geometry.Point`_, defaults to ``True``
    :type as_geom: bool
    :return: a sequence of points (incl. ``None`` if errors occur)
    :rtype: typing.Generator[shapely.geometry.Point, list, tuple, numpy.ndarray]

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import transform_geom_point_type
        >>> from pyhelpers._cache import example_dataframe
        >>> from shapely.geometry import Point

        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> pt1 = example_df.loc['London'].values  # array([-0.1276474, 51.5073219])
        >>> pt2 = example_df.loc['Birmingham'].values  # array([-1.9026911, 52.4796992])

        >>> geom_points = transform_geom_point_type(pt1, pt2)
        >>> for x in geom_points:
        ...     print(x)
        POINT (-0.1276474 51.5073219)
        POINT (-1.9026911 52.4796992)

        >>> geom_points = transform_geom_point_type(pt1, pt2, as_geom=False)
        >>> for x in geom_points:
        ...     print(x)
        [-0.1276474 51.5073219]
        [-1.9026911 52.4796992]

        >>> pt1, pt2 = map(Point, (pt1, pt2))

        >>> geom_points = transform_geom_point_type(pt1, pt2)
        >>> for x in geom_points:
        ...     print(x)
        POINT (-0.1276474 51.5073219)
        POINT (-1.9026911 52.4796992)

        >>> geom_points = transform_geom_point_type(pt1, pt2, as_geom=False)
        >>> for x in geom_points:
        ...     print(x)
        (-0.1276474, 51.5073219)
        (-1.9026911, 52.4796992)

        >>> geom_points_ = transform_geom_point_type(Point([1, 2, 3]), as_geom=False)
        >>> for x in geom_points_:
        ...     print(x)
        (1.0, 2.0, 3.0)
    """

    for pt in pts:
        if isinstance(pt, shapely.geometry.Point):
            if not as_geom:
                if pt.has_z:
                    pt = (pt.x, pt.y, pt.z)
                else:
                    pt = (pt.x, pt.y)

        elif isinstance(pt, collections.abc.Iterable):
            assert len(list(pt)) <= 3
            if as_geom:
                pt = shapely.geometry.Point(pt)

        yield pt


# -- Coordinate system -----------------------------------------------------------------------------

def wgs84_to_osgb36(longitudes, latitudes, as_array=False, **kwargs):
    """
    Convert latitude and longitude (`WGS84 <https://en.wikipedia.org/wiki/World_Geodetic_System>`_)
    to British national grid (`OSGB36 <https://en.wikipedia.org/wiki/Ordnance_Survey_National_Grid>`_).

    :param longitudes: the longitude (abbr: long., λ, or lambda) of a point on Earth's surface
    :type longitudes: int or float or typing.Iterable[int, float]
    :param latitudes: the latitude (abbr: lat., φ, or phi) of a point on Earth's surface
    :type latitudes: int or float or typing.Iterable[int, float]
    :param as_array: whether to return an array, defaults to ``False``
    :type as_array: bool
    :param kwargs: [optional] parameters of `pyproj.Transformer.transform`_
    :return: geographic Cartesian coordinate (Easting, Northing) or (X, Y)
    :rtype: tuple or numpy.ndarry

    .. _`pyproj.Transformer.transform`:
        https://pyproj4.github.io/pyproj/stable/api/transformer.html?
        #pyproj.transformer.Transformer.transform

    .. _geom-wgs84_to_osgb36-example:

    **Examples**::

        >>> from pyhelpers.geom import wgs84_to_osgb36
        >>> from pyhelpers._cache import example_dataframe

        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> lon, lat = example_df.loc['London'].values
        >>> x, y = wgs84_to_osgb36(longitudes=lon, latitudes=lat)
        >>> print(f"London (Easting, Northing): {(x, y)}")
        London (Easting, Northing): (530039.558844505, 180371.68016544735)

        >>> lonlat_array = example_df.to_numpy()
        >>> lonlat_array
        array([[-0.1276474, 51.5073219],
               [-1.9026911, 52.4796992],
               [-2.2451148, 53.4794892],
               [-1.5437941, 53.7974185]])

        >>> lons, lats = lonlat_array.T  # lonlat_array[:, 0], lonlat_array[:, 1]
        >>> xs, ys = wgs84_to_osgb36(longitudes=lons, latitudes=lats)
        >>> xs
        array([530039.5588445 , 406705.8870136 , 383830.03903573, 430147.44735387])
        >>> ys
        array([180371.68016545, 286868.16664219, 398113.05583091, 433553.32711728])

        >>> xy_array = wgs84_to_osgb36(longitudes=lons, latitudes=lats, as_array=True)
        >>> xy_array
        array([[530039.5588445 , 180371.68016545],
               [406705.8870136 , 286868.16664219],
               [383830.03903573, 398113.05583091],
               [430147.44735387, 433553.32711728]])
    """

    wgs84 = 'EPSG:4326'  # LonLat with WGS84 datum used by GPS units and Google Earth
    osgb36 = 'EPSG:27700'  # UK Ordnance Survey, 1936 datum

    transformer = pyproj.Transformer.from_crs(crs_from=wgs84, crs_to=osgb36)
    xy_data = transformer.transform(xx=latitudes, yy=longitudes, **kwargs)  # easting, northing

    # if all(isinstance(coords, pd.Series) for coords in (latitude, longitude)):
    #     xy_data = tuple(map(pd.Series, xy_data))
    if as_array:
        xy_data = np.array(xy_data).T

    return xy_data


def osgb36_to_wgs84(eastings, northings, as_array=False, **kwargs):
    """
    Convert British national grid (`OSGB36`_) to latitude and longitude (`WGS84`_).

    .. _`OSGB36`: https://en.wikipedia.org/wiki/Ordnance_Survey_National_Grid
    .. _`WGS84`: https://en.wikipedia.org/wiki/World_Geodetic_System

    :param eastings: Easting (X), eastward-measured distance (or the x-coordinate)
    :type eastings: int or float or typing.Iterable[int, float]
    :param northings: Northing (Y), northward-measured distance (or the y-coordinate)
    :type northings: int or float or typing.Iterable[int, float]
    :param as_array: whether to return an array, defaults to ``False``
    :type as_array: bool
    :param kwargs: [optional] parameters of `pyproj.Transformer.transform`_
    :return: geographic coordinate (Longitude, Latitude)
    :rtype: tuple or numpy.ndarry

    .. _`pyproj.Transformer.transform`:
        https://pyproj4.github.io/pyproj/stable/api/transformer.html?
        #pyproj.transformer.Transformer.transform

    .. _osgb36_to_wgs84-example:

    **Examples**::

        >>> from pyhelpers.geom import osgb36_to_wgs84
        >>> from pyhelpers._cache import example_dataframe

        >>> example_df = example_dataframe(osgb36=True)
        >>> example_df
                          Easting       Northing
        City
        London      530039.558844  180371.680166
        Birmingham  406705.887014  286868.166642
        Manchester  383830.039036  398113.055831
        Leeds       430147.447354  433553.327117

        >>> x, y = example_df.loc['London'].values
        >>> lon, lat = osgb36_to_wgs84(eastings=x, northings=y)
        >>> print(f"London (Longitude, Latitude): {(lon, lat)}")
        London (Longitude, Latitude): (-0.12764738749567286, 51.50732189539607)

        >>> xy_array = example_df.to_numpy()
        >>> xs, ys = xy_array.T  # xy_array[:, 0], xy_array[:, 1]
        >>> lons, lats = osgb36_to_wgs84(eastings=xs, northings=ys)
        >>> lons
        array([-0.12764739, -1.90269109, -2.24511479, -1.54379409])
        >>> lats
        array([51.5073219, 52.4796992, 53.4794892, 53.7974185])

        >>> lonlat_array = osgb36_to_wgs84(eastings=xs, northings=ys, as_array=True)
        >>> lonlat_array
        array([[-0.12764739, 51.5073219 ],
               [-1.90269109, 52.4796992 ],
               [-2.24511479, 53.4794892 ],
               [-1.54379409, 53.7974185 ]])
    """

    osgb36 = 'EPSG:27700'  # UK Ordnance Survey, 1936 datum
    wgs84 = 'EPSG:4326'  # LonLat with WGS84 datum used by GPS units and Google Earth

    transformer = pyproj.Transformer.from_crs(crs_from=osgb36, crs_to=wgs84)
    latlon_data = transformer.transform(xx=eastings, yy=northings, **kwargs)

    lonlat_data = [latlon_data[1], latlon_data[0]]
    # if all(isinstance(coords, pd.Series) for coords in (eastings, northings)):
    #     lonlat_data = tuple(map(pd.Series, lonlat_data))
    if as_array:
        lonlat_data = np.array(lonlat_data).T

    return lonlat_data


# -- Dimension / Projection ------------------------------------------------------------------------

def _drop_z(x, y, _):
    return x, y


def _drop_y(x, _, z):
    return x, z


def _drop_x(_, y, z):
    return y, z


def drop_axis(geom, axis='z', as_array=False):
    """
    Drop an axis from a given 3D geometry object.

    :param geom: geometry object that has x, y and z coordinates
    :type geom: shapely.geometry object
    :param axis: options include 'x', 'y' and 'z', defaults to ``'z'``
    :type axis: str
    :param as_array: whether to return an array, defaults to ``False``
    :type as_array: bool
    :return: geometry object (or an array) without the specified ``axis``
    :rtype: shapely.geometry object or numpy.ndarray

    **Examples**::

        >>> from pyhelpers.geom import drop_axis
        >>> from shapely.geometry import Point, LineString, Polygon, MultiLineString

        >>> geom_1 = Point([1, 2, 3])
        >>> geom_1.wkt
        'POINT Z (1 2 3)'
        >>> geom_1_ = drop_axis(geom_1, 'x')
        >>> geom_1_.wkt
        'POINT (2 3)'
        >>> geom_1_ = drop_axis(geom_1, 'x', as_array=True)
        >>> geom_1_
        array([2., 3.])

        >>> geom_2 = LineString([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
        >>> geom_2.wkt
        'LINESTRING Z (1 2 3, 2 3 4, 3 4 5)'
        >>> geom_2_ = drop_axis(geom_2, 'y')
        >>> geom_2_.wkt
        'LINESTRING (1 3, 2 4, 3 5)'
        >>> geom_2_ = drop_axis(geom_2, 'y', as_array=True)
        >>> geom_2_
        array([[1., 3.],
               [2., 4.],
               [3., 5.]])

        >>> geom_3 = Polygon([[6, 3, 5], [6, 3, 0], [6, 1, 0], [6, 1, 5], [6, 3, 5]])
        >>> geom_3.wkt
        'POLYGON Z ((6 3 5, 6 3 0, 6 1 0, 6 1 5, 6 3 5))'
        >>> geom_3_ = drop_axis(geom_3, 'z')
        >>> geom_3_.wkt
        'POLYGON ((6 3, 6 3, 6 1, 6 1, 6 3))'
        >>> geom_3_ = drop_axis(geom_3, 'z', as_array=True)
        >>> geom_3_
        array([[6., 3.],
               [6., 3.],
               [6., 1.],
               [6., 1.],
               [6., 3.]])

        >>> ls1 = LineString([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
        >>> ls2 = LineString([[2, 3, 4], [1, 2, 3], [3, 4, 5]])
        >>> geom_4 = MultiLineString([ls1, ls2])
        >>> geom_4.wkt
        'MULTILINESTRING Z ((1 2 3, 2 3 4, 3 4 5), (2 3 4, 1 2 3, 3 4 5))'
        >>> geom_4_ = drop_axis(geom_4, 'z')
        >>> geom_4_.wkt
        'MULTILINESTRING ((1 2, 2 3, 3 4), (2 3, 1 2, 3 4))'
        >>> geom_4_ = drop_axis(geom_4, 'z', as_array=True)
        >>> geom_4_
        array([[[1., 2.],
                [2., 3.],
                [3., 4.]],

               [[2., 3.],
                [1., 2.],
                [3., 4.]]])
    """

    geom_obj = shapely.ops.transform(func=globals()[f'_drop_{axis}'], geom=geom)

    if as_array:
        sim_typ = ('Point', 'LineString')
        if geom_obj.geom_type in sim_typ:
            geom_obj = np.array(geom_obj.coords)
        elif geom_obj.geom_type.startswith('Multi'):
            geom_obj = np.array(
                [np.array(g.coords) if g.geom_type in sim_typ else np.array(g.exterior.coords)
                 for g in geom_obj.geoms])
        else:
            geom_obj = np.array(geom_obj.exterior.coords)

        if geom_obj.shape[0] == 1:
            geom_obj = geom_obj[0]

    return geom_obj


def project_point_to_line(point, line, drop_dimension=None):
    """
    Find the projected point from a known point to a line.

    :param point: geometry object of a point
    :type point: shapely.geometry.Point
    :param line: geometry object of a line
    :type line: shapely.geometry.LineString
    :param drop_dimension: which dimension to drop, defaults to ``None``;
        options include ``'x'``, ``'y'`` and ``'z'``
    :type drop_dimension: str or None
    :return: the original point (with all or partial dimensions, given ``drop``) and the projected one
    :rtype: tuple

    **Examples**::

        >>> from pyhelpers.geom import project_point_to_line
        >>> from shapely.geometry import Point, LineString, MultiPoint

        >>> pt = Point([399297, 655095, 43])
        >>> ls = LineString([[399299, 655091, 42], [399295, 655099, 42]])

        >>> _, pt_proj = project_point_to_line(point=pt, line=ls)
        >>> pt_proj.wkt
        'POINT Z (399297 655095 42)'

    This example is illustrated below (see :numref:`geom-project_point_to_line-demo`)::

        >>> import matplotlib.pyplot as plt
        >>> from pyhelpers.settings import mpl_preferences

        >>> mpl_preferences(font_name='Times New Roman', font_size=12)

        >>> fig = plt.figure()
        >>> ax = fig.add_subplot(projection='3d')

        >>> ls_zs = list(map(lambda c: c[2], ls.coords))
        >>> ax.plot(ls.coords.xy[0], ls.coords.xy[1], ls_zs, label='Line')
        >>> ax.scatter(pt.x, pt.y, pt.z, label='Point')
        >>> ax.scatter(pt_proj.x, pt_proj.y, pt_proj.z, label='Projected point')

        >>> for i in MultiPoint([*ls.coords, pt, pt_proj]).geoms:
        ...     pos = tuple(map(int, i.coords[0]))
        ...     ax.text(pos[0], pos[1], pos[2], str(pos))

        >>> ax.legend(loc=3)
        >>> plt.tight_layout()

        >>> ax.set_xticklabels([])
        >>> ax.set_yticklabels([])
        >>> ax.set_zticklabels([])

        >>> plt.show()

    .. figure:: ../_images/geom-project_point_to_line-demo.*
        :name: geom-project_point_to_line-demo
        :align: center
        :width: 85%

        An example of projecting a point onto a line.
    """

    if line.length == 0:
        point_, line_ = point, shapely.geometry.Point(set(line.coords))

    else:
        if drop_dimension is not None:
            assert drop_dimension in {'x', 'y', 'z'}, "`drop_dimension` must be one of {'x', 'y', 'z'}."
            point_, line_ = map(functools.partial(drop_axis, axis=drop_dimension), [point, line])
        else:
            point_, line_ = map(copy.copy, [point, line])

        x, u, v = map(
            np.array, [point_.coords[0], line_.coords[0], line_.coords[len(line_.coords) - 1]])

        n = v - u
        n /= np.linalg.norm(n, 2)

        line_ = shapely.geometry.Point(u + n * np.dot(x - u, n))

    return point_, line_


# ==================================================================================================
# Geometric data computation
# ==================================================================================================

# -- Distance --------------------------------------------------------------------------------------

def calc_distance_on_unit_sphere(pt1, pt2, verbose=False):
    """
    Calculate distance between two points.

    :param pt1: a point
    :type pt1: shapely.geometry.Point or list or tuple or numpy.ndarray
    :param pt2: another point
    :type pt2: shapely.geometry.Point or list or tuple or numpy.ndarray
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``False``
    :type verbose: bool or int
    :return: distance (in miles) between ``pt1`` and ``pt2`` (relative to the earth's radius)
    :rtype: float

    .. note::

        This function is modified from the original code available at
        [`GEOM-CDOUS-1 <https://www.johndcook.com/blog/python_longitude_latitude/>`_].
        It assumes the earth is perfectly spherical and returns the distance based on each
        point's longitude and latitude.

    **Examples**::

        >>> from pyhelpers.geom import calc_distance_on_unit_sphere
        >>> from pyhelpers._cache import example_dataframe

        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> london, birmingham = example_df.loc[['London', 'Birmingham']].values
        >>> arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham)
        >>> arc_len_in_miles
        101.10431101941569
    """

    # Convert latitude and longitude to spherical coordinates in radians.
    degrees_to_radians = np.pi / 180.0

    if not all(isinstance(x, shapely.geometry.Point) for x in (pt1, pt2)):
        try:
            pt1_, pt2_ = map(shapely.geometry.Point, (pt1, pt2))
        except Exception as e:
            if verbose:
                print(e)
            return None
    else:
        pt1_, pt2_ = map(copy.copy, (pt1, pt2))

    # phi = 90 - latitude
    phi1 = (90.0 - pt1_.y) * degrees_to_radians
    phi2 = (90.0 - pt2_.y) * degrees_to_radians

    # theta = longitude
    theta1 = pt1_.x * degrees_to_radians
    theta2 = pt2_.x * degrees_to_radians

    # Compute spherical distance from spherical coordinates.
    # For two locations in spherical coordinates
    # (1, theta, phi) and (1, theta', phi')
    # cosine( arc length ) = sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length

    cosine = (np.sin(phi1) * np.sin(phi2) * np.cos(theta1 - theta2) + np.cos(phi1) * np.cos(phi2))
    arc_length = np.arccos(cosine) * 3960  # in miles

    # To multiply arc by the radius of the earth in a set of units to get length.
    return arc_length


def calc_hypotenuse_distance(pt1, pt2):
    """
    Calculate hypotenuse given two points (the right-angled triangle, given its side and perpendicular).

    See also [`GEOM-CHD-1 <https://numpy.org/doc/stable/reference/generated/numpy.hypot.html>`_].

    :param pt1: a point
    :type pt1: shapely.geometry.Point or list or tuple or numpy.ndarray
    :param pt2: another point
    :type pt2: shapely.geometry.Point or list or tuple or numpy.ndarray
    :return: hypotenuse
    :rtype: float

    .. note::

        - This is the length of the vector from the ``orig_pt`` to ``dest_pt``.
        - ``numpy.hypot(x, y)`` return the Euclidean norm, ``sqrt(x*x + y*y)``.

    **Examples**::

        >>> from pyhelpers.geom import calc_hypotenuse_distance
        >>> from shapely.geometry import Point

        >>> pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)
        >>> hypot_distance = calc_hypotenuse_distance(pt_1, pt_2)
        >>> hypot_distance
        0.05255244999046248

        >>> pt_1_, pt_2_ = map(Point, (pt_1, pt_2))
        >>> pt_1_.wkt
        'POINT (1.5429 52.6347)'
        >>> pt_2_.wkt
        'POINT (1.4909 52.6271)'
        >>> hypot_distance = calc_hypotenuse_distance(pt_1_, pt_2_)
        >>> hypot_distance
        0.05255244999046248
    """

    pt1_, pt2_ = transform_geom_point_type(pt1, pt2, as_geom=False)

    x_diff, y_diff = pt1_[0] - pt2_[0], pt1_[1] - pt2_[1]

    hypot_dist = np.hypot(x_diff, y_diff)

    return hypot_dist


def get_coordinates_as_array(geom_obj, unique=False):
    """
    Get an array of coordinates of the input geometry object.

    :param geom_obj: geometry object
    :type geom_obj: numpy.ndarray or list or tuple or typing.Iterable or
        shapely.geometry.Point or
        shapely.geometry.MultiPoint or
        shapely.geometry.LineString or
        shapely.geometry.MultiLineString or
        shapely.geometry.Polygon or
        shapely.geometry.MultiPolygon or
        shapely.geometry.GeometryCollection
    :param unique: whether to remove duplicated points, defaults to ``False``
    :type unique: bool
    :return: an array of coordinates
    :rtype: numpy.ndarray

    **Examples**::

        >>> from pyhelpers.geom import get_coordinates_as_array
        >>> from pyhelpers._cache import example_dataframe
        >>> from shapely.geometry import Polygon, MultiPoint, MultiPolygon, GeometryCollection
        >>> from numpy import array_equal

        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> geom_obj_1 = example_df.to_numpy()
        >>> geom_coords_1 = get_coordinates_as_array(geom_obj=geom_obj_1)
        >>> geom_coords_1
        array([[-0.1276474, 51.5073219],
               [-1.9026911, 52.4796992],
               [-2.2451148, 53.4794892],
               [-1.5437941, 53.7974185]])

        >>> geom_obj_2 = Polygon(example_df.to_numpy())
        >>> geom_coords_2 = get_coordinates_as_array(geom_obj=geom_obj_2, unique=True)
        >>> array_equal(geom_coords_2, geom_coords_1)
        True

        >>> geom_obj_3 = MultiPoint(example_df.to_numpy())
        >>> geom_coords_3 = get_coordinates_as_array(geom_obj=geom_obj_3)
        >>> array_equal(geom_coords_3, geom_coords_1)
        True

        >>> geom_obj_4 = MultiPolygon([geom_obj_2, geom_obj_2])
        >>> geom_coords_4 = get_coordinates_as_array(geom_obj=geom_obj_4, unique=True)
        >>> array_equal(geom_coords_4, geom_coords_1)
        True

        >>> geom_obj_5 = GeometryCollection([geom_obj_2, geom_obj_3, geom_obj_4])
        >>> geom_coords_5 = get_coordinates_as_array(geom_obj=geom_obj_5, unique=True)
        >>> array_equal(geom_coords_5, geom_coords_1)
        True
    """

    if isinstance(geom_obj, np.ndarray):
        coords = geom_obj

    elif isinstance(geom_obj, typing.Iterable):  # (list, tuple)
        coords = np.array(geom_obj)

    else:
        assert isinstance(geom_obj, shapely.geometry.base.BaseGeometry)
        geom_type = geom_obj.geom_type

        if 'Collection' in geom_type:
            temp = [get_coordinates_as_array(x) for x in geom_obj.__getattribute__('geoms')]
            coords = np.concatenate(temp)

        elif geom_type.startswith('Multi'):
            if 'Polygon' in geom_type:
                coords = np.vstack([np.array(x.exterior.coords) for x in geom_obj.geoms])
            else:
                coords = np.vstack([np.array(x.coords) for x in geom_obj.geoms])
        else:
            if 'Polygon' in geom_type:
                coords = np.array(geom_obj.exterior.coords)
            else:
                coords = np.array(geom_obj.coords)

    if unique:
        # coords = np.unique(coords)
        _, idx = np.unique(coords, axis=0, return_index=True)
        coords = coords[np.sort(idx)]

    return coords


def find_closest_point(pt, ref_pts, as_geom=True):
    """
    Find the closest point of the given point to a list of points.

    :param pt: (longitude, latitude)
    :type pt: tuple or list or shapely.geometry.Point
    :param ref_pts: a sequence of reference (tuple/list of length 2) points
    :type ref_pts: typing.Iterable or numpy.ndarray or list or tuple or
        shapely.geometry.Point or
        shapely.geometry.MultiPoint or
        shapely.geometry.LineString or
        shapely.geometry.MultiLineString or
        shapely.geometry.Polygon or
        shapely.geometry.MultiPolygon or
        shapely.geometry.GeometryCollection
    :param as_geom: whether to return `shapely.geometry.Point`_, defaults to ``True``
    :type as_geom: bool
    :return: the point closest to ``pt``
    :rtype: shapely.geometry.Point or numpy.ndarray

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import find_closest_point
        >>> from pyhelpers._cache import example_dataframe

        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> # Find the city closest to London
        >>> london = example_df.loc['London'].values
        >>> ref_cities = example_df.loc['Birmingham':, :].values
        >>> closest_to_london = find_closest_point(pt=london, ref_pts=ref_cities)
        >>> closest_to_london.wkt  # Birmingham
        'POINT (-1.9026911 52.4796992)'

        >>> # Find the city closest to Leeds
        >>> leeds = example_df.loc['Leeds'].values
        >>> ref_cities = example_df.loc[:'Manchester', :].values
        >>> closest_to_leeds = find_closest_point(pt=leeds, ref_pts=ref_cities)
        >>> closest_to_leeds.wkt  # Manchester
        'POINT (-2.2451148 53.4794892)'

        >>> closest_to_leeds = find_closest_point(pt=leeds, ref_pts=ref_cities, as_geom=False)
        >>> closest_to_leeds  # Manchester
        array([-2.2451148, 53.4794892])
    """

    if isinstance(pt, shapely.geometry.Point):
        pt_ = pt
    else:
        assert len(pt) <= 3
        pt_ = shapely.geometry.Point(pt)

    if isinstance(ref_pts, shapely.geometry.MultiPoint):
        ref_pts_ = ref_pts.geoms
    elif isinstance(ref_pts, typing.Iterable):
        ref_pts_ = (
            shapely.geometry.Point(x) for x in get_coordinates_as_array(geom_obj=ref_pts, unique=True))
    else:
        ref_pts_ = shapely.geometry.MultiPoint([ref_pts]).geoms

    # Find the min value using the distance function with coord parameter
    closest_point = min(ref_pts_, key=functools.partial(shapely.geometry.Point.distance, pt_))

    if not as_geom:
        closest_point = np.array(closest_point.coords)

        if closest_point.shape[0] == 1:
            closest_point = closest_point[0]

    return closest_point


def find_closest_points(pts, ref_pts, k=1, unique=False, as_geom=False, ret_idx=False, ret_dist=False,
                        **kwargs):
    """
    Find the closest points from a list of reference points (applicable for vectorized computation).

    See also [`GEOM-FCPB-1 <https://gis.stackexchange.com/questions/222315>`_].

    :param pts: an array (of size (n, 2)) of points
    :type pts: numpy.ndarray or list or tuple or typing.Iterable or
        shapely.geometry.Point or
        shapely.geometry.MultiPoint or
        shapely.geometry.LineString or
        shapely.geometry.MultiLineString or
        shapely.geometry.Polygon or
        shapely.geometry.MultiPolygon or
        shapely.geometry.GeometryCollection
    :param ref_pts: an array (of size (n, 2)) of reference points
    :type ref_pts: numpy.ndarray or list or tuple or
        shapely.geometry.Point or
        shapely.geometry.MultiPoint or
        shapely.geometry.LineString or
        shapely.geometry.MultiLineString or
        shapely.geometry.Polygon or
        shapely.geometry.MultiPolygon or
        shapely.geometry.GeometryCollection
    :param k: (up to) the ``k``-th nearest neighbour(s), defaults to ``1``
    :type k: int or list
    :param unique: whether to remove duplicated points, defaults to ``False``
    :type unique: bool
    :param as_geom: whether to return `shapely.geometry.Point`_, defaults to ``False``
    :type as_geom: bool
    :param ret_idx: whether to return indices of the closest points in ``ref_pts``, defaults to ``False``
    :type ret_idx: bool
    :param ret_dist: whether to return distances between ``pts`` and the closest points in ``ref_pts``,
        defaults to ``False``
    :type ret_dist: bool
    :param kwargs: [optional] parameters of `scipy.spatial.cKDTree`_
    :return: point (or points) among the list of ``ref_pts``, which is (or are) closest to ``pts``
    :rtype: numpy.ndarray or shapely.geometry.MultiPoint

    .. _`shapely.geometry.Point`:
        https://shapely.readthedocs.io/en/latest/manual.html#points
    .. _`scipy.spatial.cKDTree`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.html

    **Examples**::

        >>> from pyhelpers.geom import find_closest_points
        >>> from pyhelpers._cache import example_dataframe
        >>> from shapely.geometry import LineString, MultiPoint

        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> cities = [[-2.9916800, 53.4071991],  # Liverpool
        ...           [-4.2488787, 55.8609825],  # Glasgow
        ...           [-1.6131572, 54.9738474]]  # Newcastle
        >>> ref_cities = example_df.to_numpy()

        >>> closest_to_each = find_closest_points(pts=cities, ref_pts=ref_cities, k=1)
        >>> closest_to_each  # Liverpool: Manchester; Glasgow: Manchester; Newcastle: Leeds
        array([[-2.2451148, 53.4794892],
               [-2.2451148, 53.4794892],
               [-1.5437941, 53.7974185]])

        >>> closest_to_each = find_closest_points(pts=cities, ref_pts=ref_cities, k=1, as_geom=True)
        >>> closest_to_each.wkt
        'MULTIPOINT (-2.2451148 53.4794892, -2.2451148 53.4794892, -1.5437941 53.7974185)'

        >>> _, idx = find_closest_points(pts=cities, ref_pts=ref_cities, k=1, ret_idx=True)
        >>> idx
        array([2, 2, 3], dtype=int64)

        >>> _, _, dist = find_closest_points(cities, ref_cities, k=1, ret_idx=True, ret_dist=True)
        >>> dist
        array([0.75005697, 3.11232712, 1.17847198])

        >>> cities_geoms_1 = LineString(cities)
        >>> closest_to_each = find_closest_points(pts=cities_geoms_1, ref_pts=ref_cities, k=1)
        >>> closest_to_each
        array([[-2.2451148, 53.4794892],
               [-2.2451148, 53.4794892],
               [-1.5437941, 53.7974185]])

        >>> cities_geoms_2 = MultiPoint(cities)
        >>> closest_to_each = find_closest_points(cities_geoms_2, ref_cities, k=1, as_geom=True)
        >>> closest_to_each.wkt
        'MULTIPOINT (-2.2451148 53.4794892, -2.2451148 53.4794892, -1.5437941 53.7974185)'
    """

    ckdtree = _check_dependency(name='scipy.spatial')

    pts_, ref_pts_ = map(functools.partial(get_coordinates_as_array, unique=unique), [pts, ref_pts])

    ref_ckd_tree = ckdtree.cKDTree(ref_pts_, **kwargs)
    distances, indices = ref_ckd_tree.query(x=pts_, k=k)  # returns (distance, index)

    closest_points_ = [ref_pts_[i] for i in indices]
    if as_geom:
        closest_points = shapely.geometry.MultiPoint(closest_points_)
    else:
        closest_points = np.array(closest_points_)

    if ret_idx and ret_dist:
        closest_points = closest_points, indices, distances
    else:
        if ret_idx:
            closest_points = closest_points, indices
        elif ret_dist:
            closest_points = closest_points, distances

    return closest_points


def find_shortest_path(points_sequence, ret_dist=False, as_geom=False, **kwargs):
    """
    Find the shortest path through a sequence of points.

    :param points_sequence: a sequence of points
    :type points_sequence: numpy.ndarray
    :param ret_dist: whether to return the distance of the shortest path, defaults to ``False``
    :type ret_dist: bool
    :param as_geom: whether to return the sorted path as a line geometry object, defaults to ``False``
    :type as_geom: bool
    :param kwargs: (optional) parameters used by `sklearn.neighbors.NearestNeighbors`_
    :return: a sequence of sorted points given two-nearest neighbors
    :rtype: numpy.ndarray or shapely.geometry.LineString or tuple

    .. _`sklearn.neighbors.NearestNeighbors`:
        https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html

    **Examples**::

        >>> from pyhelpers.geom import find_shortest_path
        >>> from pyhelpers._cache import example_dataframe

        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> example_df_ = example_df.sample(frac=1, random_state=1)
        >>> example_df_
                    Longitude   Latitude
        City
        Leeds       -1.543794  53.797418
        Manchester  -2.245115  53.479489
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699

        >>> cities = example_df_.to_numpy()
        >>> cities
        array([[-1.5437941, 53.7974185],
               [-2.2451148, 53.4794892],
               [-0.1276474, 51.5073219],
               [-1.9026911, 52.4796992]])

        >>> cities_sorted = find_shortest_path(points_sequence=cities)
        >>> cities_sorted
        array([[-1.5437941, 53.7974185],
               [-2.2451148, 53.4794892],
               [-1.9026911, 52.4796992],
               [-0.1276474, 51.5073219]])

    This example is illustrated below (see :numref:`geom-find_shortest_path-demo`)::

        >>> import matplotlib.pyplot as plt
        >>> import matplotlib.gridspec as mgs
        >>> from pyhelpers.settings import mpl_preferences

        >>> mpl_preferences(font_name='Times New Roman')

        >>> fig = plt.figure(figsize=(7, 5))
        >>> gs = mgs.GridSpec(1, 2, figure=fig)

        >>> ax1 = fig.add_subplot(gs[:, 0])
        >>> ax1.plot(cities[:, 0], cities[:, 1], label='original')
        >>> for city, i, lonlat in zip(example_df_.index, range(len(cities)), cities):
        ...     ax1.scatter(lonlat[0], lonlat[1])
        ...     ax1.annotate(city + f' ({i})', xy=lonlat + 0.05)
        >>> ax1.legend(loc=3)

        >>> ax2 = fig.add_subplot(gs[:, 1])
        >>> ax2.plot(cities_sorted[:, 0], cities_sorted[:, 1], label='sorted', color='orange')
        >>> for city, i, lonlat in zip(example_df.index[::-1], range(len(cities)), cities_sorted):
        ...     ax2.scatter(lonlat[0], lonlat[1])
        ...     ax2.annotate(city + f' ({i})', xy=lonlat + 0.05)
        >>> ax2.legend(loc=3)

        >>> plt.tight_layout()
        >>> plt.show()

    .. figure:: ../_images/geom-find_shortest_path-demo.*
        :name: geom-find_shortest_path-demo
        :align: center
        :width: 85%

        An example of sorting a sequence of points given the shortest path.
    """

    if len(points_sequence) <= 2:
        shortest_path = points_sequence

    else:
        nx = _check_dependency(name='networkx')
        sklearn_neighbors = _check_dependency(name='sklearn.neighbors')

        nn_clf = sklearn_neighbors.NearestNeighbors(n_neighbors=2, **kwargs).fit(points_sequence)
        kn_g = nn_clf.kneighbors_graph()

        nx_g = nx.from_scipy_sparse_array(kn_g)

        possible_paths = [list(nx.dfs_preorder_nodes(nx_g, i)) for i in range(len(points_sequence))]

        min_dist, idx = np.inf, 0

        for i in range(len(points_sequence)):
            nodes_order = possible_paths[i]  # order of nodes
            ordered_nodes = points_sequence[nodes_order]  # ordered nodes

            # cost = the sum of euclidean distances between the i-th and (i+1)-th points
            dist = (((ordered_nodes[:-1] - ordered_nodes[1:]) ** 2).sum(axis=1)).sum()
            if dist <= min_dist:
                min_dist = dist
                idx = i

        shortest_path = points_sequence[possible_paths[idx]]

        if as_geom:
            shortest_path = shapely.geometry.LineString(shortest_path)

        if ret_dist:
            shortest_path = shortest_path, min_dist

    return shortest_path


# -- Locating --------------------------------------------------------------------------------------

def get_midpoint(x1, y1, x2, y2, as_geom=False):
    """
    Get the midpoint between two points (applicable for vectorized computation).

    :param x1: longitude(s) or easting(s) of a point (an array of points)
    :type x1: float or int or typing.Iterable or numpy.ndarray
    :param y1: latitude(s) or northing(s) of a point (an array of points)
    :type y1: float or int or typing.Iterable or numpy.ndarray
    :param x2: longitude(s) or easting(s) of another point (another array of points)
    :type x2: float or int or typing.Iterable or numpy.ndarray
    :param y2: latitude(s) or northing(s) of another point (another array of points)
    :type y2: float or int or typing.Iterable or numpy.ndarray
    :param as_geom: whether to return `shapely.geometry.Point`_, defaults to ``False``
    :type as_geom: bool
    :return: the midpoint between ``(x1, y1)`` and ``(x2, y2)``
        (or midpoints between two sequences of points)
    :rtype: numpy.ndarray or shapely.geometry.Point or shapely.geometry.MultiPoint

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import get_midpoint

        >>> x_1, y_1 = 1.5429, 52.6347
        >>> x_2, y_2 = 1.4909, 52.6271

        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2)
        >>> midpt
        array([ 1.5169, 52.6309])

        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2, as_geom=True)
        >>> midpt.wkt
        'POINT (1.5169 52.6309)'

        >>> x_1, y_1 = (1.5429, 1.4909), (52.6347, 52.6271)
        >>> x_2, y_2 = [2.5429, 2.4909], [53.6347, 53.6271]

        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2)
        >>> midpt
        array([[ 2.0429, 53.1347],
               [ 1.9909, 53.1271]])

        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2, as_geom=True)
        >>> midpt.wkt
        'MULTIPOINT (2.0429 53.1347, 1.9909 53.1271)'
    """

    x1_, y1_, x2_, y2_ = map(np.array, (x1, y1, x2, y2))

    mid_pts = (x1_ + x2_) / 2, (y1_ + y2_) / 2

    if as_geom:
        if all(isinstance(x, np.ndarray) for x in mid_pts):
            midpoint = shapely.geometry.MultiPoint(
                [shapely.geometry.Point(x_, y_) for x_, y_ in zip(list(mid_pts[0]), list(mid_pts[1]))])
        else:
            midpoint = shapely.geometry.Point(mid_pts)

    else:
        midpoint = np.array(mid_pts).T

    return midpoint


def get_geometric_midpoint(pt1, pt2, as_geom=False):
    """
    Get the midpoint between two points.

    :param pt1: a point
    :type pt1: shapely.geometry.Point or list or tuple or numpy.ndarray
    :param pt2: another point
    :type pt2: shapely.geometry.Point or list or tuple or numpy.ndarray
    :param as_geom: whether to return `shapely.geometry.Point`_, defaults to ``False``
    :type as_geom: bool
    :return: the midpoint between ``pt1`` and ``pt2``
    :rtype: tuple or shapely.geometry.Point or None

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import get_geometric_midpoint

        >>> pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)

        >>> geometric_midpoint = get_geometric_midpoint(pt_1, pt_2)
        >>> geometric_midpoint
        (1.5169, 52.6309)

        >>> geometric_midpoint = get_geometric_midpoint(pt_1, pt_2, as_geom=True)
        >>> geometric_midpoint.wkt
        'POINT (1.5169 52.6309)'

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.geom.get_geometric_midpoint_calc`.
    """

    pt_x_, pt_y_ = transform_geom_point_type(pt1, pt2, as_geom=True)

    midpoint = (pt_x_.x + pt_y_.x) / 2, (pt_x_.y + pt_y_.y) / 2

    if as_geom:
        midpoint = shapely.geometry.Point(midpoint)

    return midpoint


def get_geometric_midpoint_calc(pt1, pt2, as_geom=False):
    """
    Get the midpoint between two points by pure calculation.

    See also
    [`GEOM-GGMC-1 <https://code.activestate.com/recipes/577713/>`_]
    and
    [`GEOM-GGMC-2 <https://www.movable-type.co.uk/scripts/latlong.html>`_].

    :param pt1: a point
    :type pt1: shapely.geometry.Point or list or tuple or numpy.ndarray
    :param pt2: a point
    :type pt2: shapely.geometry.Point or list or tuple or numpy.ndarray
    :param as_geom: whether to return `shapely.geometry.Point`_. defaults to ``False``
    :type as_geom: bool
    :return: the midpoint between ``pt1`` and ``pt2``
    :rtype: tuple or shapely.geometry.Point or None

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import get_geometric_midpoint_calc

        >>> pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)

        >>> geometric_midpoint = get_geometric_midpoint_calc(pt_1, pt_2)
        >>> geometric_midpoint
        (1.5168977420748175, 52.630902845583094)

        >>> geometric_midpoint = get_geometric_midpoint_calc(pt_1, pt_2, as_geom=True)
        >>> geometric_midpoint.wkt
        'POINT (1.5168977420748175 52.630902845583094)'

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.geom.get_geometric_midpoint`.
    """

    pt_x_, pt_y_ = transform_geom_point_type(pt1, pt2, as_geom=True)

    # Input values as degrees, convert them to radians
    lon_1, lat_1 = np.radians(pt_x_.x), np.radians(pt_x_.y)
    lon_2, lat_2 = np.radians(pt_y_.x), np.radians(pt_y_.y)

    b_x, b_y = np.cos(lat_2) * np.cos(lon_2 - lon_1), np.cos(lat_2) * np.sin(lon_2 - lon_1)
    lat_3 = np.arctan2(np.sin(lat_1) + np.sin(lat_2), np.sqrt((np.cos(lat_1) + b_x) * (
            np.cos(lat_1) + b_x) + b_y ** 2))
    long_3 = lon_1 + np.arctan2(b_y, np.cos(lat_1) + b_x)

    midpoint = np.degrees(long_3), np.degrees(lat_3)

    if as_geom:
        midpoint = shapely.geometry.Point(midpoint)

    return midpoint


def get_rectangle_centroid(rectangle, as_geom=False):
    """
    Get coordinates of the centroid of a rectangle

    :param rectangle: polygon or multipolygon geometry object
    :type rectangle: list or tuple or numpy.ndarray or shapely.geometry.Polygon or
        shapely.geometry.MultiPolygon
    :param as_geom: whether to return a shapely.geometry object
    :type as_geom: bool
    :return: coordinate of the rectangle
    :rtype: numpy.ndarray or shapely.geometry.Point

    **Examples**::

        >>> from pyhelpers.geom import get_rectangle_centroid
        >>> from shapely.geometry import Polygon
        >>> import numpy

        >>> coords_1 = [[0, 0], [0, 1], [1, 1], [1, 0]]

        >>> rect_obj = Polygon(coords_1)
        >>> rect_cen = get_rectangle_centroid(rectangle=rect_obj)
        >>> rect_cen
        array([0.5, 0.5])

        >>> rect_obj = numpy.array(coords_1)
        >>> rect_cen = get_rectangle_centroid(rectangle=rect_obj)
        >>> rect_cen
        array([0.5, 0.5])

        >>> rect_cen = get_rectangle_centroid(rectangle=rect_obj, as_geom=True)
        >>> type(rect_cen)
        shapely.geometry.point.Point
        >>> rect_cen.wkt
        'POINT (0.5 0.5)'

        >>> coords_2 = [[(0, 0), (0, 1), (1, 1), (1, 0)], [(1, 1), (1, 2), (2, 2), (2, 1)]]

        >>> rect_cen = get_rectangle_centroid(rectangle=coords_2)

    """

    if isinstance(rectangle, typing.Iterable):  # (np.ndarray, list, tuple)
        try:
            rectangle_ = shapely.geometry.Polygon(rectangle)
        except (TypeError, ValueError, AttributeError):
            rectangle_ = shapely.geometry.MultiPolygon(shapely.geometry.Polygon(x) for x in rectangle)
            rectangle_ = rectangle_.convex_hull
    else:
        rectangle_ = copy.copy(rectangle)

    rec_centroid = rectangle_.centroid

    if not as_geom:
        rec_centroid = np.array(rec_centroid.coords[0])

    return rec_centroid


def get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta=0):
    """
    Get the four vertices of a square given its centre and side length.

    See also [`GEOM-GSV-1 <https://stackoverflow.com/questions/22361324/>`_].

    :param ctr_x: x coordinate of a square centre
    :type ctr_x: int or float
    :param ctr_y: y coordinate of a square centre
    :type ctr_y: int or float
    :param side_length: side length of a square
    :type side_length: int or float
    :param rotation_theta: rotate (anticlockwise) the square by ``rotation_theta`` (in degree),
        defaults to ``0``
    :type rotation_theta: int or float
    :return: vertices of the square as an array([ll, ul, ur, lr])
    :rtype: numpy.ndarray

    **Examples**::

        >>> from pyhelpers.geom import get_square_vertices

        >>> ctr_1, ctr_2 = -5.9375, 56.8125
        >>> side_len = 0.125

        >>> vts = get_square_vertices(ctr_1, ctr_2, side_len, rotation_theta=0)
        >>> vts
        array([[-6.   , 56.75 ],
               [-6.   , 56.875],
               [-5.875, 56.875],
               [-5.875, 56.75 ]])

        >>> # Rotate the square by 30° (anticlockwise)
        >>> vts = get_square_vertices(ctr_1, ctr_2, side_len, rotation_theta=30)
        >>> vts
        array([[-5.96037659, 56.72712341],
               [-6.02287659, 56.83537659],
               [-5.91462341, 56.89787659],
               [-5.85212341, 56.78962341]])
    """

    def _rot_mat(theta):
        return np.array([[np.sin(theta), np.cos(theta)], [-np.cos(theta), np.sin(theta)]])

    rotation_matrix = _rot_mat(np.deg2rad(rotation_theta))

    sides = np.ones(2) * side_length

    vertices_ = [
        np.array([ctr_x, ctr_y]) + functools.reduce(
            np.dot, [rotation_matrix, _rot_mat(-0.5 * np.pi * x), sides / 2])
        for x in range(4)]

    vertices = np.array(vertices_, dtype=np.float64)

    return vertices


def get_square_vertices_calc(ctr_x, ctr_y, side_length, rotation_theta=0):
    """
    Get the four vertices of a square given its centre and side length (by elementary calculation).

    See also [`GEOM-GSVC-1 <https://math.stackexchange.com/questions/1490115>`_].

    :param ctr_x: x coordinate of a square centre
    :type ctr_x: int or float
    :param ctr_y: y coordinate of a square centre
    :type ctr_y: int or float
    :param side_length: side length of a square
    :type side_length: int or float
    :param rotation_theta: rotate (anticlockwise) the square by ``rotation_theta`` (in degree),
        defaults to ``0``
    :type rotation_theta: int or float
    :return: vertices of the square as an array([ll, ul, ur, lr])
    :rtype: numpy.ndarray

    **Examples**::

        >>> from pyhelpers.geom import get_square_vertices_calc

        >>> ctr_1, ctr_2 = -5.9375, 56.8125
        >>> side_len = 0.125

        >>> vts = get_square_vertices_calc(ctr_1, ctr_2, side_len, rotation_theta=0)
        >>> vts
        array([[-6.   , 56.75 ],
               [-6.   , 56.875],
               [-5.875, 56.875],
               [-5.875, 56.75 ]])

        >>> # Rotate the square by 30° (anticlockwise)
        >>> vts = get_square_vertices_calc(ctr_1, ctr_2, side_len, rotation_theta=30)
        >>> vts
        array([[-5.96037659, 56.72712341],
               [-6.02287659, 56.83537659],
               [-5.91462341, 56.89787659],
               [-5.85212341, 56.78962341]])

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.geom.get_square_vertices`.
    """

    theta_rad = np.deg2rad(rotation_theta)

    ll = (ctr_x + 1 / 2 * side_length * (np.sin(theta_rad) - np.cos(theta_rad)),
          ctr_y - 1 / 2 * side_length * (np.sin(theta_rad) + np.cos(theta_rad)))
    ul = (ctr_x - 1 / 2 * side_length * (np.sin(theta_rad) + np.cos(theta_rad)),
          ctr_y - 1 / 2 * side_length * (np.sin(theta_rad) - np.cos(theta_rad)))
    ur = (ctr_x - 0.5 * side_length * (np.sin(theta_rad) - np.cos(theta_rad)),
          ctr_y + 0.5 * side_length * (np.sin(theta_rad) + np.cos(theta_rad)))
    lr = (ctr_x + 0.5 * side_length * (np.sin(theta_rad) + np.cos(theta_rad)),
          ctr_y + 0.5 * side_length * (np.sin(theta_rad) - np.cos(theta_rad)))

    vertices = np.array([ll, ul, ur, lr])

    return vertices


# ==================================================================================================
# Geometric data sketching
# ==================================================================================================


def _sketch_square_annotate(x, y, fontsize, margin=0.025, precision=2, **kwargs):
    p = '{' + '0:.{}f'.format(precision) + '}'
    text = f'({p}, {p})'
    args = {
        'text': text.format(x, y),
        'xy': (x, y),
        'fontsize': fontsize,
        'xytext': (x + margin, y + margin),
    }

    kwargs.update(args)

    return kwargs


def sketch_square(ctr_x, ctr_y, side_length, rotation_theta=0, annotation=False, annot_font_size=12,
                  fig_size=(6.4, 4.8), ret_vertices=False, **kwargs):
    """
    Sketch a square given its centre point, four vertices and rotation angle (in degree).

    :param ctr_x: x coordinate of a square centre
    :type ctr_x: int or float
    :param ctr_y: y coordinate of a square centre
    :type ctr_y: int or float
    :param side_length: side length of a square
    :type side_length: int or float
    :param rotation_theta: rotate (anticlockwise) the square by ``rotation_theta`` (in degree),
        defaults to ``0``
    :type rotation_theta: int or float
    :param annotation: whether to annotate vertices of the square, defaults to ``True``
    :type annotation: bool
    :param annot_font_size: font size annotation texts, defaults to ``12``
    :type annot_font_size: int
    :param fig_size: figure size, defaults to ``(6.4, 4.8)``
    :type fig_size: tuple or list
    :param ret_vertices: whether to return the vertices of the square, defaults to ``False``
    :type ret_vertices: bool
    :param kwargs: [optional] parameters of `matplotlib.axes.Axes.annotate`_
    :return: vertices of the square as an array([ll, ul, ur, lr])
    :rtype: numpy.ndarray

    .. _`matplotlib.axes.Axes.annotate`:
        https://matplotlib.org/3.2.1/api/_as_gen/matplotlib.axes.Axes.annotate.html

    **Examples**::

        >>> from pyhelpers.geom import sketch_square
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt

        >>> mpl_preferences()

        >>> c1, c2 = 1, 1
        >>> side_len = 2

        >>> sketch_square(c1, c2, side_len, rotation_theta=0, annotation=True, fig_size=(5, 5))
        >>> plt.show()

    The above exmaple is illustrated in :numref:`geom-sketch_square-demo-1`:

    .. figure:: ../_images/geom-sketch_square-demo-1.*
        :name: geom-sketch_square-demo-1
        :align: center
        :width: 65%

        An example of a sketch of a square, created by the function
        :py:func:`~pyhelpers.geom.sketch_square`.

    .. code-block:: python

        >>> sketch_square(c1, c2, side_len, rotation_theta=75, annotation=True, fig_size=(5, 5))
        >>> plt.show()

    This second example is illustrated in :numref:`geom-sketch_square-demo-2`:

    .. figure:: ../_images/geom-sketch_square-demo-2.*
        :name: geom-sketch_square-demo-2
        :align: center
        :width: 65%

        An example of a sketch of a square rotated 75 degrees anticlockwise about the centre.
    """

    mpl_plt, mpl_ticker = map(_check_dependency, ['matplotlib.pyplot', 'matplotlib.ticker'])

    vertices_ = get_square_vertices(
        ctr_x=ctr_x, ctr_y=ctr_y, side_length=side_length, rotation_theta=rotation_theta)
    vertices = np.append(vertices_, [tuple(vertices_[0])], axis=0)

    fig = mpl_plt.figure(figsize=fig_size)
    ax = fig.add_subplot(1, 1, 1)  # _, ax = plt.subplots(1, 1, figsize=fig_size)
    ax.plot(ctr_x, ctr_y, 'o', markersize=10)
    annotate_args = _sketch_square_annotate(x=ctr_x, y=ctr_y, fontsize=annot_font_size, **kwargs)
    ax.annotate(**annotate_args)

    if rotation_theta == 0:
        ax.plot(vertices[:, 0], vertices[:, 1], 'o-')
    else:
        label = "rotation $\\theta$ = {}°".format(rotation_theta)
        ax.plot(vertices[:, 0], vertices[:, 1], 'o-', label=label)
        ax.legend(loc="best")

    if annotation:
        for x, y in zip(vertices[:, 0], vertices[:, 1]):
            args = _sketch_square_annotate(x=x, y=y, fontsize=annot_font_size, **kwargs)
            ax.annotate(**args)

    ax.axis("equal")

    ax.yaxis.set_major_locator(mpl_ticker.MaxNLocator(integer=True))
    ax.xaxis.set_major_locator(mpl_ticker.MaxNLocator(integer=True))

    mpl_plt.tight_layout()

    if ret_vertices:
        return vertices
