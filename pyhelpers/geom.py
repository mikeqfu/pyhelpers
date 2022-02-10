"""
Manipulation of geometric/geographical data.
"""

import collections.abc
import copy
import functools
import typing

import numpy as np
import pyproj
import scipy.spatial.ckdtree
import shapely.geometry
import shapely.ops

from .ops import create_rotation_matrix

""" == Geometric transformation ============================================================== """


# Geometric type

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
    :rtype: typing.Generator[shapely.geometry.Point, tuple]

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import transform_geom_point_type
        >>> from shapely.geometry import Point

        >>> pt1 = 1.5429, 52.6347
        >>> pt2 = 1.4909, 52.6271

        >>> geom_points = transform_geom_point_type(pt1, pt2)
        >>> for x in geom_points:
        ...     print(x)
        POINT (1.5429 52.6347)
        POINT (1.4909 52.6271)

        >>> geom_points = transform_geom_point_type(pt1, pt2, as_geom=False)
        >>> for x in geom_points:
        ...     print(x)
        (1.5429, 52.6347)
        (1.4909, 52.6271)

        >>> pt1, pt2 = Point(pt1), Point(pt2)

        >>> geom_points = transform_geom_point_type(pt1, pt2)
        >>> for x in geom_points:
        ...     print(x)
        POINT (1.5429 52.6347)
        POINT (1.4909 52.6271)

        >>> geom_points = transform_geom_point_type(pt1, pt2, as_geom=False)
        >>> for x in geom_points:
        ...     print(x)
        (1.5429, 52.6347)
        (1.4909, 52.6271)
    """

    for pt in pts:
        if isinstance(pt, shapely.geometry.Point):
            pt_ = copy.copy(pt) if as_geom else ((pt.x, pt.y, pt.z) if pt.has_z else (pt.x, pt.y))

        elif isinstance(pt, collections.abc.Iterable):
            assert len(list(pt)) <= 3
            pt_ = shapely.geometry.Point(pt) if as_geom else copy.copy(pt)

        else:
            pt_ = None

        yield pt_


# Coordinate system

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
    :rtype: tuple

    .. _`pyproj.Transformer.transform`:
        https://pyproj4.github.io/pyproj/stable/api/transformer.html?
        #pyproj.transformer.Transformer.transform

    .. _geom-wgs84_to_osgb36-example:

    **Examples**::

        >>> from pyhelpers.geom import wgs84_to_osgb36
        >>> from pyhelpers._cache import example_dataframe

        >>> lon, lat = -0.1277, 51.5074
        >>> x, y = wgs84_to_osgb36(lon, lat)
        >>> print(f"(Easting, Northing): {(x, y)}")
        (Easting, Northing): (530035.6864715678, 180380.27177236252)

        >>> lonlat_array = example_dataframe(osgb36=False).to_numpy()
        >>> lonlat_array
        array([[-0.12772401, 51.50740693],
               [-1.90294064, 52.47928436],
               [-2.24527795, 53.47894006],
               [ 0.60693267, 51.24669501]])

        >>> lons, lats = lonlat_array.T  # lonlat_array[:, 0], lonlat_array[:, 1]
        >>> xs, ys = wgs84_to_osgb36(longitudes=lons, latitudes=lats)
        >>> xs
        array([530034.00057811, 406689.00100754, 383819.00096473, 582044.00120751])
        >>> ys
        array([180380.99978837, 286821.99910345, 398051.99922367, 152952.99925431])

        >>> xy_array = wgs84_to_osgb36(longitudes=lons, latitudes=lats, as_array=True)
        >>> xy_array
        array([[530034.00057811, 180380.99978837],
               [406689.00100754, 286821.99910345],
               [383819.00096473, 398051.99922367],
               [582044.00120751, 152952.99925431]])
    """

    wgs84 = 'EPSG:4326'  # LonLat with WGS84 datum used by GPS units and Google Earth
    osgb36 = 'EPSG:27700'  # UK Ordnance Survey, 1936 datum

    transformer = pyproj.Transformer.from_crs(crs_from=wgs84, crs_to=osgb36)
    xy_data = transformer.transform(xx=latitudes, yy=longitudes, **kwargs)  # easting, northing

    # if all(isinstance(coords, pd.Series) for coords in (latitude, longitude)):
    #     xy_data = tuple(map(pd.Series, xy_data))
    if as_array:
        xy_data = np.asarray(xy_data).T

    return xy_data


def osgb36_to_wgs84(eastings, northings, as_array=False, **kwargs):
    """
    Convert British national grid
    (`OSGB36 <https://en.wikipedia.org/wiki/Ordnance_Survey_National_Grid>`_)
    to latitude and longitude (`WGS84 <https://en.wikipedia.org/wiki/World_Geodetic_System>`_).

    :param eastings: Easting (X), eastward-measured distance (or the x-coordinate)
    :type eastings: int or float or typing.Iterable[int, float]
    :param northings: Northing (Y), northward-measured distance (or the y-coordinate)
    :type northings: int or float or typing.Iterable[int, float]
    :param as_array: whether to return an array, defaults to ``False``
    :type as_array: bool
    :param kwargs: [optional] parameters of `pyproj.Transformer.transform`_
    :return: geographic coordinate (Longitude, Latitude)
    :rtype: tuple

    .. _`pyproj.Transformer.transform`:
        https://pyproj4.github.io/pyproj/stable/api/transformer.html?
        #pyproj.transformer.Transformer.transform

    .. _osgb36_to_wgs84-example:

    **Examples**::

        >>> from pyhelpers.geom import osgb36_to_wgs84
        >>> from pyhelpers._cache import example_dataframe

        >>> x, y = 530034, 180381
        >>> lon, lat = osgb36_to_wgs84(x, y)
        >>> print(f"(Longitude, Latitude): {(lon, lat)}")
        (Longitude, Latitude): (-0.12772400574286916, 51.50740692743041)

        >>> xy_array = example_dataframe().to_numpy()
        >>> xs, ys = xy_array.T  # xy_array[:, 0], xy_array[:, 1]
        >>> lons, lats = osgb36_to_wgs84(xs, ys)
        >>> lons
        array([-0.12772401, -1.90294064, -2.24527795,  0.60693267])
        >>> lats
        array([51.50740693, 52.47928436, 53.47894006, 51.24669501])

        >>> lonlat_array = osgb36_to_wgs84(xs, ys, as_array=True)
        >>> lonlat_array
        array([[-0.12772401, 51.50740693],
               [-1.90294064, 52.47928436],
               [-2.24527795, 53.47894006],
               [ 0.60693267, 51.24669501]])
    """

    osgb36 = 'EPSG:27700'  # UK Ordnance Survey, 1936 datum
    wgs84 = 'EPSG:4326'  # LonLat with WGS84 datum used by GPS units and Google Earth

    transformer = pyproj.Transformer.from_crs(crs_from=osgb36, crs_to=wgs84)
    latlon_data = transformer.transform(xx=eastings, yy=northings, **kwargs)

    lonlat_data = [latlon_data[1], latlon_data[0]]
    # if all(isinstance(coords, pd.Series) for coords in (eastings, northings)):
    #     lonlat_data = tuple(map(pd.Series, lonlat_data))
    if as_array:
        lonlat_data = np.asarray(lonlat_data).T

    return lonlat_data


# Dimension / Shape

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

    geom_obj = shapely.ops.transform(func=eval(f'_drop_{axis}'), geom=geom)

    if as_array:
        sim_typ = ('Point', 'LineString')
        if geom_obj.type in sim_typ:
            geom_obj = np.array(geom_obj.coords)
        elif geom_obj.type.startswith('Multi'):
            geom_obj = np.array(
                [np.asarray(g.coords) if g.type in sim_typ else np.asarray(g.exterior.coords)
                 for g in geom_obj.geoms]
            )
        else:
            geom_obj = np.array(geom_obj.exterior.coords)

        if geom_obj.shape[0] == 1:
            geom_obj = geom_obj[0]

    return geom_obj


""" == Geometry calculation ================================================================== """


# Distance

def calc_distance_on_unit_sphere(pt1, pt2):
    """
    Calculate distance between two points.

    :param pt1: a point
    :type pt1: shapely.geometry.Point or list or tuple or numpy.ndarray
    :param pt2: another point
    :type pt2: shapely.geometry.Point or list or tuple or numpy.ndarray
    :return: distance (in miles) between ``pt1`` and ``pt2`` (relative to the earth's radius)
    :rtype: float

    .. note::

        This function is modified from the original code available at
        [`GEOM-CDOUS-1 <https://www.johndcook.com/blog/python_longitude_latitude/>`_].
        It assumes the earth is perfectly spherical and returns the distance based on each
        point's longitude and latitude.

    **Example**::

        >>> from pyhelpers.geom import calc_distance_on_unit_sphere

        >>> pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)

        >>> arc_len = calc_distance_on_unit_sphere(pt_1, pt_2)
        >>> arc_len
        2.243709962588554
    """

    # Convert latitude and longitude to spherical coordinates in radians.
    degrees_to_radians = np.pi / 180.0

    if not all(isinstance(x, shapely.geometry.Point) for x in (pt1, pt2)):
        try:
            pt1_, pt2_ = map(shapely.geometry.Point, (pt1, pt2))
        except Exception as e:
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


def find_closest_point(pt, ref_pts, as_geom=True):
    """
    Find the closest point of the given point to a list of points.

    :param pt: (longitude, latitude)
    :type pt: tuple or list or shapely.geometry.Point
    :param ref_pts: a sequence of reference (tuple/list of length 2) points
    :type ref_pts: typing.Iterable or shapely.geometry.base.BaseGeometry
    :param as_geom: whether to return `shapely.geometry.Point`_, defaults to ``True``
    :type as_geom: bool
    :return: the point closest to ``pt``
    :rtype: shapely.geometry.Point or numpy.ndarray

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import find_closest_point
        >>> from shapely.geometry import Point

        >>> pt_1 = (2.5429, 53.6347)
        >>> pt_reference_1 = [(1.5429, 52.6347),
        ...                   (1.4909, 52.6271),
        ...                   (1.4248, 52.63075)]
        >>> pt_closest_1 = find_closest_point(pt=pt_1, ref_pts=pt_reference_1)
        >>> pt_closest_1.wkt
        'POINT (1.5429 52.6347)'

        >>> pt_2 = Point((2.5429, 53.6347))
        >>> pt_reference_2 = [Point((1.5429, 52.6347)),
        ...                   Point((1.4909, 52.6271)),
        ...                   Point((1.4248, 52.63075))]
        >>> pt_closest_2 = find_closest_point(pt=pt_2, ref_pts=pt_reference_2)
        >>> pt_closest_2.wkt
        'POINT (1.5429 52.6347)'

        >>> pt_closest_3 = find_closest_point(pt=pt_2, ref_pts=pt_reference_2, as_geom=False)
        >>> pt_closest_3
        array([ 1.5429, 52.6347])
    """

    if not isinstance(pt, shapely.geometry.Point):
        assert len(pt) <= 3
        pt_ = shapely.geometry.Point(pt)
    else:
        pt_ = pt

    if not isinstance(ref_pts, typing.Iterable):
        ref_pts_ = shapely.geometry.MultiPoint(ref_pts.coords)
    else:
        ref_pts_ = (
            shapely.geometry.Point(x) if not isinstance(x, shapely.geometry.Point) else x
            for x in ref_pts)

    # Find the min value using the distance function with coord parameter
    closest_point = min(ref_pts_, key=functools.partial(shapely.geometry.Point.distance, pt_))

    if not as_geom:
        closest_point = np.array(closest_point.coords)

        if closest_point.shape[0] == 1:
            closest_point = closest_point[0]

    return closest_point


def find_closest_points(pts, ref_pts, k=1, unique_pts=False, as_geom=False, ret_idx=False,
                        ret_dist=False, **kwargs):
    """
    Find the closest points from a list of reference points (applicable for vectorized computation).

    See also [`GEOM-FCPB-1 <https://gis.stackexchange.com/questions/222315>`_].

    :param pts: an array (of size (n, 2)) of points
    :type pts: numpy.ndarray or shapely.geometry.Point or shapely.geometry.MultiPoint or
        shapely.geometry.LineString
    :param ref_pts: an array (of size (n, 2)) of reference points
    :type ref_pts: numpy.ndarray or shapely.geometry.MultiPoint or list or tuple
    :param k: (up to) the ``k``-th nearest neighbour(s), defaults to ``1``
    :type k: int or list
    :param unique_pts: whether to remove duplicated points, defaults to ``False``
    :type unique_pts: bool
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
        >>> from shapely.geometry import LineString, MultiPoint
        >>> import numpy

        >>> pts_1 = numpy.array([[1.5429, 52.6347],
        ...                      [1.4909, 52.6271],
        ...                      [1.4248, 52.63075]])
        >>> pts_ref = numpy.array([[2.5429, 53.6347],
        ...                        [2.4909, 53.6271],
        ...                        [2.4248, 53.63075]])

        >>> pts_closest = find_closest_points(pts_1, pts_ref, k=1)
        >>> pts_closest
        array([[ 2.4248 , 53.63075],
               [ 2.4248 , 53.63075],
               [ 2.4248 , 53.63075]])

        >>> pts_closest = find_closest_points(pts_1, pts_ref, k=1, as_geom=True)
        >>> pts_closest.wkt
        'MULTIPOINT (2.4248 53.63075, 2.4248 53.63075, 2.4248 53.63075)'

        >>> _, idx = find_closest_points(pts_1, pts_ref, k=1, ret_idx=True)
        >>> idx
        array([2, 2, 2], dtype=int64)

        >>> _, _, dist = find_closest_points(pts_1, pts_ref, k=1, ret_idx=True, ret_dist=True)
        >>> dist
        array([1.33036206, 1.37094221, 1.41421356])

        >>> pts_2 = LineString(pts_1)
        >>> pts_closest = find_closest_points(pts_2, pts_ref, k=1)
        >>> pts_closest
        array([[ 2.4248 , 53.63075],
               [ 2.4248 , 53.63075],
               [ 2.4248 , 53.63075]])

        >>> pts_3 = MultiPoint(pts_1)
        >>> pts_closest = find_closest_points(pts_3, pts_ref, k=1, as_geom=True)
        >>> pts_closest.wkt
        'MULTIPOINT (2.4248 53.63075, 2.4248 53.63075, 2.4248 53.63075)'
    """

    if isinstance(ref_pts, np.ndarray):
        ref_pts_ = copy.copy(ref_pts)
    else:
        ref_pts_ = np.concatenate([np.asarray(geom.coords) for geom in ref_pts])

    # noinspection PyArgumentList
    ref_ckd_tree = scipy.spatial.ckdtree.cKDTree(ref_pts_, **kwargs)

    if isinstance(pts, np.ndarray):
        pts_ = copy.copy(pts)
    else:
        geom_type = pts.__getattribute__('type')
        if geom_type.startswith('Multi'):
            if geom_type.endswith('Point'):
                pts_ = np.vstack([np.asarray(x.coords) for x in pts.geoms])
            else:
                pts_ = np.concatenate([np.asarray(x.coords) for x in pts.geoms])
        else:
            pts_ = np.asarray(pts.coords)

    if unique_pts:
        _, tmp_idx = np.unique(pts_, axis=0, return_index=True)
        pts_ = pts_[np.sort(tmp_idx)]

    # noinspection PyUnresolvedReferences
    distances, indices = ref_ckd_tree.query(x=pts_, k=k)  # returns (distance, index)

    closest_points_ = [ref_pts_[i] for i in indices]
    if as_geom:
        closest_points = shapely.geometry.MultiPoint(closest_points_)
    else:
        closest_points = np.asarray(closest_points_)

    if ret_idx and ret_dist:
        closest_points = closest_points, indices, distances
    else:
        if ret_idx:
            closest_points = closest_points, indices
        elif ret_dist:
            closest_points = closest_points, distances

    return closest_points


# Locating

def get_midpoint(x1, y1, x2, y2, as_geom=False):
    """
    Get the midpoint between two points (applicable for vectorized computation).

    :param x1: longitude(s) or easting(s) of a point (an array of points)
    :type x1: float or int or numpy.ndarray
    :param y1: latitude(s) or northing(s) of a point (an array of points)
    :type y1: float or int or numpy.ndarray
    :param x2: longitude(s) or easting(s) of another point (another array of points)
    :type x2: float or int or numpy.ndarray
    :param y2: latitude(s) or northing(s) of another point (another array of points)
    :type y2: float or int or numpy.ndarray
    :param as_geom: whether to return `shapely.geometry.Point`_, defaults to ``False``
    :type as_geom: bool
    :return: the midpoint between ``(x1, y1)`` and ``(x2, y2)``
        (or midpoints between two sequences of points)
    :rtype: numpy.ndarray or shapely.geometry.Point or shapely.geometry.MultiPoint

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import get_midpoint
        >>> import numpy

        >>> x_1, y_1 = 1.5429, 52.6347
        >>> x_2, y_2 = 1.4909, 52.6271

        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2)
        >>> midpt
        array([ 1.5169, 52.6309])

        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2, as_geom=True)
        >>> midpt.wkt
        'POINT (1.5169 52.6309)'

        >>> x_1, y_1 = numpy.array([1.5429, 1.4909]), numpy.array([52.6347, 52.6271])
        >>> x_2, y_2 = numpy.array([2.5429, 2.4909]), numpy.array([53.6347, 53.6271])

        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2)
        >>> midpt
        array([[ 2.0429, 53.1347],
               [ 1.9909, 53.1271]])

        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2, as_geom=True)
        >>> midpt.wkt
        'MULTIPOINT (2.0429 53.1347, 1.9909 53.1271)'
    """

    mid_pts = (x1 + x2) / 2, (y1 + y2) / 2

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
        'POINT (1.516897742074818 52.6309028455831)'

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
    :type rectangle: numpy.ndarray or shapely.geometry.Polygon or shapely.geometry.MultiPolygon
    :param as_geom: whether to return a shapely.geometry object
    :type as_geom: bool
    :return: coordinate of the rectangle
    :rtype: numpy.ndarray or shapely.geometry.Point

    **Example**::

        >>> from pyhelpers.geom import get_rectangle_centroid
        >>> from shapely.geometry import Polygon

        >>> rectangle_obj = Polygon([[0, 0], [0, 1], [1, 1], [1, 0]])

        >>> rect_cen = get_rectangle_centroid(rectangle=rectangle_obj)
        >>> rect_cen
        array([0.5, 0.5])
    """

    if isinstance(rectangle, np.ndarray):
        try:
            rectangle_geom = shapely.geometry.Polygon(rectangle)
        except (ValueError, AttributeError):
            rectangle_geom = shapely.geometry.MultiPolygon(rectangle)

        ll_lon, ll_lat, ur_lon, ur_lat = rectangle_geom.bounds

        rec_centroid = np.array([np.round((ur_lon + ll_lon) / 2, 4), np.round((ll_lat + ur_lat) / 2, 4)])

        if as_geom:
            rec_centroid = shapely.geometry.Point(rec_centroid)

    else:
        rec_centroid = rectangle.centroid

        if not as_geom:
            rec_centroid = np.array(rec_centroid.coords)

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

    sides = np.ones(2) * side_length

    rotation_matrix = create_rotation_matrix(np.deg2rad(rotation_theta))

    vertices_ = [
        np.array([ctr_x, ctr_y]) + functools.reduce(
            np.dot, [rotation_matrix, create_rotation_matrix(-0.5 * np.pi * x), sides / 2])
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

        - Exmaples for the function :py:func:`pyhelpers.geom.get_square_vertices`.
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


""" == Geometric data visualisation ========================================================== """


# Sketch

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


def sketch_square(ctr_x, ctr_y, side_length=None, rotation_theta=0, annotation=False,
                  annot_font_size=12, fig_size=(6.4, 4.8), ret_vertices=False, **kwargs):
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
        >>> import matplotlib.pyplot as plt

        >>> c1, c2 = 1, 1
        >>> side_len = 2

        >>> sketch_square(c1, c2, side_len, rotation_theta=0, annotation=True, fig_size=(5, 5))
        >>> plt.show()

    The above exmaple is illustrated in :numref:`sketch-square-1`:

    .. figure:: ../_images/sketch-square-1.*
        :name: sketch-square-1
        :align: center
        :width: 53%

        An example of a sketch of a square, created by the function
        :py:func:`sketch_square()<pyhelpers.geom.sketch_square>`.

    .. code-block:: python

        >>> sketch_square(c1, c2, side_len, rotation_theta=75, annotation=True, fig_size=(5, 5))
        >>> plt.show()

    This second example is illustrated in :numref:`sketch-square-2`:

    .. figure:: ../_images/sketch-square-2.*
        :name: sketch-square-2
        :align: center
        :width: 53%

        An example of a sketch of a square rotated 75 degrees anticlockwise about the centre.

    .. code-block:: python

        >>> plt.close(fig='all')
    """

    import matplotlib.pyplot
    import matplotlib.ticker

    vertices_ = get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta)
    vertices = np.append(vertices_, [tuple(vertices_[0])], axis=0)

    fig = matplotlib.pyplot.figure(figsize=fig_size)
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

    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))

    matplotlib.pyplot.tight_layout()

    if ret_vertices:
        return vertices
