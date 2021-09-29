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

    :param pts: points (e.g. list of lists/tuples or shapely.geometry.Points)
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

def wgs84_to_osgb36(longitude, latitude, **kwargs):
    """
    Convert latitude and longitude (`WGS84 <https://en.wikipedia.org/wiki/World_Geodetic_System>`_)
    to British national grid (`OSGB36 <https://en.wikipedia.org/wiki/Ordnance_Survey_National_Grid>`_).

    :param longitude: the longitude (abbr: long., λ, or lambda) of a point on Earth's surface
    :type longitude: float or int
    :param latitude: the latitude (abbr: lat., φ, or phi) of a point on Earth's surface
    :type latitude: float or int
    :return: geographic Cartesian coordinate (Easting, Northing) or (X, Y)
    :rtype: tuple

    .. _wgs84_to_osgb36-example:

    **Example**::

        >>> from pyhelpers.geom import wgs84_to_osgb36

        >>> lon, lat = -0.1277, 51.5074

        >>> x, y = wgs84_to_osgb36(lon, lat)

        >>> print("(Easting, Northing): {}".format((x, y)))
        (Easting, Northing): (530035.6864715678, 180380.27177236252)
    """

    wgs84 = 'EPSG:4326'  # LonLat with WGS84 datum used by GPS units and Google Earth
    osgb36 = 'EPSG:27700'  # UK Ordnance Survey, 1936 datum

    transformer = pyproj.Transformer.from_crs(wgs84, osgb36)
    easting, northing = transformer.transform(latitude, longitude, **kwargs)

    return easting, northing


def osgb36_to_wgs84(easting, northing, **kwargs):
    """
    Convert British national grid
    (`OSGB36 <https://en.wikipedia.org/wiki/Ordnance_Survey_National_Grid>`_)
    to latitude and longitude (`WGS84 <https://en.wikipedia.org/wiki/World_Geodetic_System>`_).

    :param easting: Easting (X), eastward-measured distance (or the x-coordinate)
    :type easting: int or float
    :param northing: Northing (Y), northward-measured distance (or the y-coordinate)
    :type northing: int or float
    :return: geographic coordinate (Longitude, Latitude)
    :rtype: tuple

    .. _osgb36_to_wgs84-example:

    **Example**::

        >>> from pyhelpers.geom import osgb36_to_wgs84

        >>> x, y = 530034, 180381

        >>> lon, lat = osgb36_to_wgs84(x, y)

        >>> print("(Longitude, Latitude): {}".format((lon, lat)))
        (Longitude, Latitude): (-0.12772400574286916, 51.50740692743041)
    """

    osgb36 = 'EPSG:27700'  # UK Ordnance Survey, 1936 datum
    wgs84 = 'EPSG:4326'  # LonLat with WGS84 datum used by GPS units and Google Earth

    transformer = pyproj.Transformer.from_crs(osgb36, wgs84)
    latitude, longitude = transformer.transform(easting, northing, **kwargs)

    return longitude, latitude


def wgs84_to_osgb36_calc(longitude, latitude):
    """
    Convert latitude and longitude (`WGS84 <https://en.wikipedia.org/wiki/World_Geodetic_System>`_)
    to British national grid (`OSGB36 <https://en.wikipedia.org/wiki/Ordnance_Survey_National_Grid>`_)
    by calculation.

    :param longitude: the longitude (abbr: long., λ, or lambda) of a point on Earth's surface
    :type longitude: float or int
    :param latitude: the latitude (abbr: lat., φ, or phi) of a point on Earth's surface
    :type latitude: float or int
    :return: geographic Cartesian coordinate (Easting, Northing) or (X, Y)
    :rtype: tuple

    **Example**::

        >>> from pyhelpers.geom import wgs84_to_osgb36_calc

        >>> lon, lat = -0.1277, 51.5074

        >>> easting, northing = wgs84_to_osgb36_calc(lon, lat)

        >>> print("(Easting, Northing): {}".format((easting, northing)))
        (Easting, Northing): (530035.689215283, 180380.27273760783)

    .. note::

        - This function is slightly modified from the original code available at
          [`GEOM-WTOC-1 <http://blogs.casa.ucl.ac.uk/2014/12/26/>`_].

        - Compare also :ref:`wgs84_to_osgb36(lon, lat)<wgs84_to_osgb36-example>`.
    """

    # First convert to radians. These are on the wrong ellipsoid currently: GRS80.
    # (Denoted by _1)
    lon_1, lat_1 = longitude * np.pi / 180, latitude * np.pi / 180

    # Want to convert to the Airy 1830 ellipsoid, which has the following:
    # The GSR80 semi-major and semi-minor axes used for WGS84(m)
    a_1, b_1 = 6378137.000, 6356752.3141
    e2_1 = 1 - (b_1 * b_1) / (a_1 * a_1)  # The eccentricity of the GRS80 ellipsoid
    nu_1 = a_1 / np.sqrt(1 - e2_1 * np.sin(lat_1) ** 2)

    # First convert to cartesian from spherical polar coordinates
    h = 0  # Third spherical coord.
    x_1 = (nu_1 + h) * np.cos(lat_1) * np.cos(lon_1)
    y_1 = (nu_1 + h) * np.cos(lat_1) * np.sin(lon_1)
    z_1 = ((1 - e2_1) * nu_1 + h) * np.sin(lat_1)

    # Perform Helmut transform (to go between GRS80 (_1) and Airy 1830 (_2))
    s = 20.4894 * 10 ** -6  # The scale factor -1
    # The translations along x,y,z axes respectively:
    tx, ty, tz = -446.448, 125.157, -542.060
    # The rotations along x,y,z respectively, in seconds:
    rxs, rys, rzs = -0.1502, -0.2470, -0.8421
    rx = rxs * np.pi / (180 * 3600.)
    ry = rys * np.pi / (180 * 3600.)
    rz = rzs * np.pi / (180 * 3600.)  # In radians
    x_2 = tx + (1 + s) * x_1 + (-rz) * y_1 + ry * z_1
    y_2 = ty + rz * x_1 + (1 + s) * y_1 + (-rx) * z_1
    z_2 = tz + (-ry) * x_1 + rx * y_1 + (1 + s) * z_1

    # Back to spherical polar coordinates from cartesian
    # Need some of the characteristics of the new ellipsoid
    # The GSR80 semi-major and semi-minor axes used for WGS84(m)
    a, b = 6377563.396, 6356256.909
    e2 = 1 - (b * b) / (a * a)  # The eccentricity of the Airy 1830 ellipsoid
    p = np.sqrt(x_2 ** 2 + y_2 ** 2)

    # Lat is obtained by an iterative procedure:
    latitude = np.arctan2(z_2, (p * (1 - e2)))  # Initial value
    lat_old = 2 * np.pi
    nu = 0
    while abs(latitude - lat_old) > 10 ** -16:
        latitude, lat_old = lat_old, latitude
        nu = a / np.sqrt(1 - e2 * np.sin(lat_old) ** 2)
        latitude = np.arctan2(z_2 + e2 * nu * np.sin(lat_old), p)

    # Lon and height are then pretty easy
    longitude = np.arctan2(y_2, x_2)
    # h = p / cos(lat) - nu

    # e, n are the British national grid coordinates - easting and northing
    # scale factor on the central meridian
    f0 = 0.9996012717
    # Latitude of true origin (radians)
    lat0 = 49 * np.pi / 180
    # Longitude of true origin and central meridian (radians)
    lon0 = -2 * np.pi / 180
    # Northing & easting of true origin (m)
    n0, e0 = -100000, 400000
    y = (a - b) / (a + b)

    # meridional radius of curvature
    rho = a * f0 * (1 - e2) * (1 - e2 * np.sin(latitude) ** 2) ** (-1.5)
    eta2 = nu * f0 / rho - 1

    m1 = (1 + y + (5 / 4) * y ** 2 + (5 / 4) * y ** 3) * (latitude - lat0)
    m2 = (3 * y + 3 * y ** 2 + (21 / 8) * y ** 3) * np.sin(latitude - lat0) * np.cos(latitude + lat0)
    m3 = ((15 / 8) * y ** 2 +
          (15 / 8) * y ** 3) * np.sin(2 * (latitude - lat0)) * np.cos(2 * (latitude + lat0))
    m4 = (35 / 24) * y ** 3 * np.sin(3 * (latitude - lat0)) * np.cos(3 * (latitude + lat0))

    # meridional arc
    m = b * f0 * (m1 - m2 + m3 - m4)

    i = m + n0
    ii = nu * f0 * np.sin(latitude) * np.cos(latitude) / 2
    iii = nu * f0 * np.sin(latitude) * np.cos(latitude) ** 3 * (
            5 - np.tan(latitude) ** 2 + 9 * eta2) / 24
    iii_a = nu * f0 * np.sin(latitude) * np.cos(latitude) ** 5 * (
            61 - 58 * np.tan(latitude) ** 2 + np.tan(latitude) ** 4) / 720
    iv = nu * f0 * np.cos(latitude)
    v = nu * f0 * np.cos(latitude) ** 3 * (nu / rho - np.tan(latitude) ** 2) / 6
    vi = nu * f0 * np.cos(latitude) ** 5 * (
            5 - 18 * np.tan(latitude) ** 2 + np.tan(latitude) ** 4 + 14 * eta2 -
            58 * eta2 * np.tan(latitude) ** 2) / 120

    y = i + ii * (longitude - lon0) ** 2 + iii * (
            longitude - lon0) ** 4 + iii_a * (longitude - lon0) ** 6
    x = e0 + iv * (longitude - lon0) + v * (longitude - lon0) ** 3 + vi * (longitude - lon0) ** 5

    return x, y


def osgb36_to_wgs84_calc(easting, northing):
    """
    Convert british national grid
    (`OSGB36 <https://en.wikipedia.org/wiki/Ordnance_Survey_National_Grid>`_)
    to latitude and longitude (`WGS84 <https://en.wikipedia.org/wiki/World_Geodetic_System>`_)
    by calculation.

    :param easting: Easting (X), eastward-measured distance (or the x-coordinate)
    :type easting: int or float
    :param northing: Northing (Y), northward-measured distance (or the y-coordinate)
    :type northing: int or float
    :return: geographic coordinate (Longitude, Latitude)
    :rtype: tuple

    **Example**::

        >>> from pyhelpers.geom import osgb36_to_wgs84_calc

        >>> x, y = 530034, 180381

        >>> longitude, latitude = osgb36_to_wgs84_calc(x, y)

        >>> print("(Longitude, Latitude): {}".format((longitude, latitude)))
        (Longitude, Latitude): (-0.1277240422737611, 51.50740676560936)

    .. note::

        - This function is slightly modified from the original code available at
          [`GEOM-OTWC-1 <http://blogs.casa.ucl.ac.uk/2014/12/26/>`_].

        - Compare also :ref:`osgb36_to_wgs84(longitude, latitude)<osgb36_to_wgs84-example>`.
    """

    # The Airy 180 semi-major and semi-minor axes used for OSGB36 (m)
    a, b = 6377563.396, 6356256.909
    # Scale factor on the central meridian
    f0 = 0.9996012717
    # Latitude of true origin (radians)
    lat0 = 49 * np.pi / 180
    # Longitude of true origin and central meridian (radians):
    lon0 = -2 * np.pi / 180
    # Northing and Easting of true origin (m):
    n0, e0 = -100000, 400000
    e2 = 1 - (b * b) / (a * a)  # eccentricity squared
    n = (a - b) / (a + b)

    # Initialise the iterative variables
    lat, m = lat0, 0

    while northing - n0 - m >= 0.00001:  # Accurate to 0.01mm
        lat += (northing - n0 - m) / (a * f0)
        m1 = (1 + n + (5. / 4) * n ** 2 + (5. / 4) * n ** 3) * (lat - lat0)
        m2 = (3 * n + 3 * n ** 2 + (21. / 8) * n ** 3) * np.sin(lat - lat0) * np.cos(lat + lat0)
        m3 = ((15. / 8) * n ** 2 + (15. / 8) * n ** 3) * np.sin(
            2 * (lat - lat0)) * np.cos(2 * (lat + lat0))
        m4 = (35. / 24) * n ** 3 * np.sin(3 * (lat - lat0)) * np.cos(3 * (lat + lat0))
        # meridional arc
        m = b * f0 * (m1 - m2 + m3 - m4)

    # transverse radius of curvature
    nu = a * f0 / np.sqrt(1 - e2 * np.sin(lat) ** 2)

    # meridional radius of curvature
    rho = a * f0 * (1 - e2) * (1 - e2 * np.sin(lat) ** 2) ** (-1.5)
    eta2 = nu / rho - 1

    sec_lat = 1. / np.cos(lat)
    vii = np.tan(lat) / (2 * rho * nu)
    viii = np.tan(lat) / (24 * rho * nu ** 3) * (
            5 + 3 * np.tan(lat) ** 2 + eta2 - 9 * np.tan(lat) ** 2 * eta2)
    ix = np.tan(lat) / (720 * rho * nu ** 5) * (
            61 + 90 * np.tan(lat) ** 2 + 45 * np.tan(lat) ** 4)
    x_ = sec_lat / nu
    xi = sec_lat / (6 * nu ** 3) * (nu / rho + 2 * np.tan(lat) ** 2)
    xii = sec_lat / (120 * nu ** 5) * (5 + 28 * np.tan(lat) ** 2 + 24 * np.tan(lat) ** 4)
    xiia = sec_lat / (5040 * nu ** 7) * (
            61 + 662 * np.tan(lat) ** 2 + 1320 * np.tan(lat) ** 4 + 720 * np.tan(lat) ** 6)
    de = easting - e0

    # These are on the wrong ellipsoid currently: Airy1830. (Denoted by _1)
    lat_1 = lat - vii * de ** 2 + viii * de ** 4 - ix * de ** 6
    lon_1 = lon0 + x_ * de - xi * de ** 3 + xii * de ** 5 - xiia * de ** 7

    """ Want to convert to the GRS80 ellipsoid. """
    # First convert to cartesian from spherical polar coordinates
    h = 0  # Third spherical coord.
    x_1 = (nu / f0 + h) * np.cos(lat_1) * np.cos(lon_1)
    y_1 = (nu / f0 + h) * np.cos(lat_1) * np.sin(lon_1)
    z_1 = ((1 - e2) * nu / f0 + h) * np.sin(lat_1)

    # Perform Helmut transform (to go between Airy 1830 (_1) and GRS80 (_2))
    s = -20.4894 * 10 ** -6  # The scale factor -1
    # The translations along x,y,z axes respectively
    tx, ty, tz = 446.448, -125.157, + 542.060
    # The rotations along x,y,z respectively, in seconds
    rxs, rys, rzs = 0.1502, 0.2470, 0.8421
    rx, ry = rxs * np.pi / (180 * 3600.), rys * np.pi / (180 * 3600.)
    rz = rzs * np.pi / (180 * 3600.)  # In radians
    x_2 = tx + (1 + s) * x_1 + (-rz) * y_1 + ry * z_1
    y_2 = ty + rz * x_1 + (1 + s) * y_1 + (-rx) * z_1
    z_2 = tz + (-ry) * x_1 + rx * y_1 + (1 + s) * z_1

    # Back to spherical polar coordinates from cartesian
    # Need some of the characteristics of the new ellipsoid
    # The GSR80 semi-major and semi-minor axes used for WGS84(m)
    a_2, b_2 = 6378137.000, 6356752.3141
    e2_2 = 1 - (b_2 * b_2) / (a_2 * a_2)  # The eccentricity of the GRS80 ellipsoid
    p = np.sqrt(x_2 ** 2 + y_2 ** 2)

    # Lat is obtained by an iterative procedure:
    lat = np.arctan2(z_2, (p * (1 - e2_2)))  # Initial value
    lat_old = 2 * np.pi
    while abs(lat - lat_old) > 10 ** -16:
        lat, lat_old = lat_old, lat
        nu_2 = a_2 / np.sqrt(1 - e2_2 * np.sin(lat_old) ** 2)
        lat = np.arctan2(z_2 + e2_2 * nu_2 * np.sin(lat_old), p)

    # Lon and height are then pretty easy
    lon = np.arctan2(y_2, x_2)
    # h = p / cos(lat) - nu_2

    # Print the results
    # print([(lat - lat_1) * 180 / pi, (lon - lon_1) * 180 / pi])

    # Convert to degrees
    lon = lon * 180 / np.pi
    lat = lat * 180 / np.pi

    return lon, lat


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
        >>> geom_1_ = drop_axis(geom_1, 'x')
        >>> geom_1_.wkt
        'POINT (2 3)'
        >>> geom_1_ = drop_axis(geom_1, 'x', as_array=True)
        >>> geom_1_
        array([2., 3.])

        >>> geom_2 = LineString([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
        >>> geom_2_ = drop_axis(geom_2, 'y')
        >>> geom_2_.wkt
        'LINESTRING (1 3, 2 4, 3 5)'
        >>> geom_2_ = drop_axis(geom_2, 'y', as_array=True)
        >>> geom_2_
        array([[1., 3.],
               [2., 4.],
               [3., 5.]])

        >>> geom_3 = Polygon([[6, 3, 5], [6, 3, 0], [6, 1, 0], [6, 1, 5], [6, 3, 5]])
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

        >>> geom_4 = MultiLineString(
        ...     [LineString([[1, 2, 3], [2, 3, 4], [3, 4, 5]]),
        ...      LineString([[2, 3, 4], [1, 2, 3], [3, 4, 5]])])
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

    drop_func = eval(f'_drop_{axis}')
    geom_ = shapely.ops.transform(drop_func, geom)

    if as_array:
        sim_typ = ('Point', 'LineString')
        if geom_.type in sim_typ:
            geom_ = np.asarray(geom_)
        elif 'Multi' in geom_.type:
            geom_ = np.array(
                [np.asarray(g) if g.type in sim_typ else np.asarray(g.exterior) for g in geom_])
        else:
            geom_ = np.asarray(geom_.exterior)

    return geom_


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
    Calculate hypotenuse given two points (the right angled triangle, given its side and perpendicular).

    :param pt1: a point
    :type pt1: shapely.geometry.Point or list or tuple or numpy.ndarray
    :param pt2: another point
    :type pt2: shapely.geometry.Point or list or tuple or numpy.ndarray
    :return: hypotenuse
    :rtype: float

    .. note::

        This is the length of the vector from the ``orig_pt`` to ``dest_pt``.

        ``numpy.hypot(x, y)`` return the Euclidean norm, ``sqrt(x*x + y*y)``.

        See also [`GEOM-CHD-1 <https://numpy.org/doc/stable/reference/generated/numpy.hypot.html>`_].

    **Examples**::

        >>> from pyhelpers.geom import calc_hypotenuse_distance
        >>> from shapely.geometry import Point

        >>> pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)

        >>> hypot_distance = calc_hypotenuse_distance(pt_1, pt_2)
        >>> hypot_distance
        0.05255244999046248

        >>> pt_1 = Point(1.5429, 52.6347)
        >>> pt_2 = Point(1.4909, 52.6271)

        >>> hypot_distance = calc_hypotenuse_distance(pt_1, pt_2)
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

        >>> pt_closest_1 = find_closest_point(pt_1, pt_reference_1)
        >>> pt_closest_1.wkt
        'POINT (1.5429 52.6347)'

        >>> pt_2 = Point((2.5429, 53.6347))

        >>> pt_reference_2 = [Point((1.5429, 52.6347)),
        ...                   Point((1.4909, 52.6271)),
        ...                   Point((1.4248, 52.63075))]

        >>> pt_closest_2 = find_closest_point(pt_2, pt_reference_2)
        >>> pt_closest_2.wkt
        'POINT (1.5429 52.6347)'

        >>> pt_closest_3 = find_closest_point(pt_2, pt_reference_2, as_geom=False)
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
            for x in ref_pts
        )

    # Find the min value using the distance function with coord parameter
    closest_point = min(ref_pts_, key=functools.partial(shapely.geometry.Point.distance, pt_))

    if not as_geom:
        closest_point = np.asarray(closest_point)

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
    :param kwargs: optional parameters of `scipy.spatial.cKDTree`_
    :return: ``pts``'s closest point(s) in ``ref_pts``
    :rtype: numpy.ndarray or shapely.geometry.MultiPoint

    .. _`shapely.geometry.Point`:
        https://shapely.readthedocs.io/en/latest/manual.html#points
    .. _`scipy.spatial.cKDTree`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.html

    **Examples**::

        >>> from pyhelpers.geom import find_closest_points
        >>> import numpy
        >>> from shapely.geometry import LineString, MultiPoint

        >>> pts_1 = numpy.array([[1.5429, 52.6347],
        ...                      [1.4909, 52.6271],
        ...                      [1.4248, 52.63075]])

        >>> pts_reference = numpy.array([[2.5429, 53.6347],
        ...                              [2.4909, 53.6271],
        ...                              [2.4248, 53.63075]])

        >>> pts_closest = find_closest_points(pts_1, pts_reference, k=1)
        >>> pts_closest
        array([[ 2.4248 , 53.63075],
               [ 2.4248 , 53.63075],
               [ 2.4248 , 53.63075]])

        >>> pts_closest = find_closest_points(pts_1, pts_reference, k=1, as_geom=True)
        >>> pts_closest.wkt
        'MULTIPOINT (2.4248 53.63075, 2.4248 53.63075, 2.4248 53.63075)'

        >>> _, idx = find_closest_points(pts_1, pts_reference, k=1, ret_idx=True)
        >>> idx
        array([2, 2, 2], dtype=int64)

        >>> _, _, dist = find_closest_points(pts_1, pts_reference, k=1, ret_idx=True, ret_dist=True)
        >>> dist
        array([1.33036206, 1.37094221, 1.41421356])

        >>> pts_2 = LineString(pts_1)
        >>> pts_closest = find_closest_points(pts_2, pts_reference, k=1)
        array([[ 2.4248 , 53.63075],
               [ 2.4248 , 53.63075],
               [ 2.4248 , 53.63075]])

        >>> pts_3 = MultiPoint(pts_1)
        >>> pts_closest = find_closest_points(pts_3, pts_reference, k=1, as_geom=True)
        >>> pts_closest.wkt
        'MULTIPOINT (2.4248 53.63075, 2.4248 53.63075, 2.4248 53.63075)'
    """

    if isinstance(ref_pts, np.ndarray):
        ref_pts_ = copy.copy(ref_pts)
    else:
        ref_pts_ = np.concatenate([np.array(geom.coords) for geom in ref_pts])

    # noinspection PyArgumentList
    ref_ckd_tree = scipy.spatial.ckdtree.cKDTree(ref_pts_, **kwargs)

    if isinstance(pts, np.ndarray):
        pts_ = copy.copy(pts)
    else:
        geom_type = pts.__getattribute__('type')
        if geom_type.startswith('Multi'):
            if geom_type.endswith('Point'):
                pts_ = np.vstack([np.array(x) for x in list(pts)])
            else:
                pts_ = np.concatenate([np.array(x) for x in list(pts)])
        else:
            pts_ = np.asarray(pts)

    if unique_pts:
        _, tmp_idx = np.unique(pts_, axis=0, return_index=True)
        pts_ = pts_[np.sort(tmp_idx)]

    # noinspection PyUnresolvedReferences
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

        >>> import numpy
        >>> from pyhelpers.geom import get_midpoint

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

    .. _get_geometric_midpoint-example:

    **Examples**::

        >>> from pyhelpers.geom import get_geometric_midpoint

        >>> pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)

        >>> geometric_midpoint = get_geometric_midpoint(pt_1, pt_2)
        >>> geometric_midpoint
        (1.5169, 52.6309)

        >>> geometric_midpoint = get_geometric_midpoint(pt_1, pt_2, as_geom=True)
        >>> geometric_midpoint.wkt
        'POINT (1.5169 52.6309)'
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
    [`GEOM-GGMC-1 <https://code.activestate.com/recipes/577713-midpoint-of-two-gps-points/>`_]
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

    .. note::

        Compare also :ref:`get_geometric_midpoint(pt_1, pt_2)<get_geometric_midpoint-example>`
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

    **Test**::

        >>> from pyhelpers.geom import get_rectangle_centroid
        >>> from shapely.geometry import Polygon

        >>> rect_cen = get_rectangle_centroid(rectangle=Polygon([[0, 0], [0, 1], [1, 1], [1, 0]]))

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
            rec_centroid = np.array(rec_centroid)

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

    .. _get_square_vertices-example:

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

    .. note::

        Compare also :ref:`get_square_vertices()<get_square_vertices-example>`.
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

def sketch_square(ctr_x, ctr_y, side_length=None, rotation_theta=0, annotation=False,
                  annot_font_size=12, fig_size=(6.4, 4.8), ret_vertices=False, **kwargs):
    """
    Visualise the square given its centre point, four vertices and rotation angle (in degree).

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
    :param kwargs: optional parameters of `matplotlib.axes.Axes.annotate`_
    :return: vertices of the square as an array([ll, ul, ur, lr])
    :rtype: numpy.ndarray

    .. _`matplotlib.axes.Axes.annotate`:
        https://matplotlib.org/3.2.1/api/_as_gen/matplotlib.axes.Axes.annotate.html

    **Examples**::

        >>> import matplotlib.pyplot as plt
        >>> from pyhelpers.geom import sketch_square

        >>> c1, c2 = 1, 1
        >>> side_len = 2

        >>> sketch_square(c1, c2, side_len, rotation_theta=0, annotation=True, fig_size=(5, 5))
        >>> plt.show()

    The above exmaple is illustrated in :numref:`sketch-square-1`:

    .. figure:: ../_images/sketch-square-1.*
        :name: sketch-square-1
        :align: center
        :width: 53%

        An example of a sketch of a square, created by
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
    """

    import matplotlib.pyplot
    import matplotlib.ticker

    vertices_ = get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta)
    vertices = np.append(vertices_, [tuple(vertices_[0])], axis=0)

    fig = matplotlib.pyplot.figure(figsize=fig_size)
    ax = fig.add_subplot(1, 1, 1)  # _, ax = plt.subplots(1, 1, figsize=fig_size)
    ax.plot(ctr_x, ctr_y, 'o', markersize=10)
    ax.annotate("({0:.2f}, {0:.2f})".format(ctr_x, ctr_y), xy=(ctr_x, ctr_y),
                xytext=(ctr_x + 0.025, ctr_y + 0.025), fontsize=annot_font_size, **kwargs)

    if rotation_theta == 0:
        ax.plot(vertices[:, 0], vertices[:, 1], 'o-')
    else:
        ax.plot(vertices[:, 0], vertices[:, 1], 'o-',
                label="rotation $\\theta$ = {}°".format(rotation_theta))
        ax.legend(loc="best")

    if annotation:
        for x, y in zip(vertices[:, 0], vertices[:, 1]):
            ax.annotate("({0:.2f}, {0:.2f})".format(x, y), xy=(x, y),
                        xytext=(x + 0.025, y + 0.025), fontsize=annot_font_size, **kwargs)

    ax.axis("equal")

    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))

    matplotlib.pyplot.tight_layout()

    if ret_vertices:
        return vertices
