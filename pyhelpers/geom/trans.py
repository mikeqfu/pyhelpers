"""
Geometric data transformation.
"""

import collections.abc
import copy
import functools
import typing

import numpy as np
import pyproj
import shapely.geometry
import shapely.ops


# Data type

def transform_point_type(*pts, as_geom=True):
    """
    Transform iterable to
    `shapely.geometry.Point <https://shapely.readthedocs.io/en/latest/manual.html#points>`_ type,
    or the other way round.

    :param pts: data of points (e.g. list of lists/tuples)
    :type pts: list | tuple | shapely.geometry.Point
    :param as_geom: whether to return point(s) as `shapely.geometry.Point`_, defaults to ``True``
    :type as_geom: bool
    :return: a sequence of points (incl. ``None`` if errors occur)
    :rtype: typing.Generator[shapely.geometry.Point, list, tuple, numpy.ndarray]

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import transform_point_type
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

        >>> geom_points = transform_point_type(pt1, pt2)
        >>> for x in geom_points:
        ...     print(x)
        POINT (-0.1276474 51.5073219)
        POINT (-1.9026911 52.4796992)

        >>> geom_points = transform_point_type(pt1, pt2, as_geom=False)
        >>> for x in geom_points:
        ...     print(x)
        [-0.1276474 51.5073219]
        [-1.9026911 52.4796992]

        >>> pt1, pt2 = map(Point, (pt1, pt2))

        >>> geom_points = transform_point_type(pt1, pt2)
        >>> for x in geom_points:
        ...     print(x)
        POINT (-0.1276474 51.5073219)
        POINT (-1.9026911 52.4796992)

        >>> geom_points = transform_point_type(pt1, pt2, as_geom=False)
        >>> for x in geom_points:
        ...     print(x)
        (-0.1276474, 51.5073219)
        (-1.9026911, 52.4796992)

        >>> geom_points_ = transform_point_type(Point([1, 2, 3]), as_geom=False)
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


def get_coordinates_as_array(geom_obj, unique=False):
    """
    Get an array of coordinates of the input geometry object.

    :param geom_obj: geometry object
    :type geom_obj: numpy.ndarray | list | tuple | typing.Iterable | shapely.geometry.base.BaseGeometry
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


# Coordinate system

def wgs84_to_osgb36(longitudes, latitudes, as_array=False, **kwargs):
    """
    Convert latitude and longitude
    (`WGS84 <https://en.wikipedia.org/wiki/World_Geodetic_System>`_)
    to British national grid
    (`OSGB36 <https://en.wikipedia.org/wiki/Ordnance_Survey_National_Grid>`_).

    :param longitudes: the longitude (abbr: long., λ, or lambda) of a point on Earth's surface
    :type longitudes: int | float | typing.Iterable[int, float]
    :param latitudes: the latitude (abbr: lat., φ, or phi) of a point on Earth's surface
    :type latitudes: int | float | typing.Iterable[int, float]
    :param as_array: whether to return an array, defaults to ``False``
    :type as_array: bool
    :param kwargs: [optional] parameters of `pyproj.Transformer.transform`_
    :return: geographic Cartesian coordinate (Easting, Northing) or (X, Y)
    :rtype: tuple | numpy.ndarry

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
    :type eastings: int | float | typing.Iterable[int, float]
    :param northings: Northing (Y), northward-measured distance (or the y-coordinate)
    :type northings: int | float | typing.Iterable[int, float]
    :param as_array: whether to return an array, defaults to ``False``
    :type as_array: bool
    :param kwargs: [optional] parameters of `pyproj.Transformer.transform`_
    :return: geographic coordinate (Longitude, Latitude)
    :rtype: tuple | numpy.ndarry

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


# Dimension / Projection

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
    :rtype: shapely.geometry.base.BaseGeometry | numpy.ndarray

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
    :type drop_dimension: str | None
    :return: the original point (with all or partial dimensions, given ``drop``) and
        the projected one
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
        ...     ax.text3D(pos[0], pos[1], pos[2], str(pos))

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
            assert drop_dimension in {'x', 'y', 'z'}, \
                "`drop_dimension` must be one of {'x', 'y', 'z'}."
            point_, line_ = map(functools.partial(drop_axis, axis=drop_dimension), [point, line])
        else:
            point_, line_ = map(copy.copy, [point, line])

        x, u, v = map(
            np.array, [point_.coords[0], line_.coords[0], line_.coords[len(line_.coords) - 1]])

        n = v - u
        n /= np.linalg.norm(n, 2)

        line_ = shapely.geometry.Point(u + n * np.dot(x - u, n))

    return point_, line_
