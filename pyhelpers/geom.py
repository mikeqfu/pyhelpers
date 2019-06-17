""" Geometry-related utilities """

import functools

import math
import pyproj


# Convert british national grid (OSBG36) to latitude and longitude (WGS84)
def osgb36_to_wgs84(easting, northing):
    osgb36 = pyproj.Proj(init='EPSG:27700')  # UK Ordnance Survey, 1936 datum
    wgs84 = pyproj.Proj(init='EPSG:4326')  # LonLat with WGS84 datum used by GPS units and Google Earth
    longitude, latitude = pyproj.transform(osgb36, wgs84, easting, northing)
    return longitude, latitude


# Convert latitude and longitude (WGS84) to british national grid (OSBG36)
def wgs84_to_osgb36(longitude, latitude):
    wgs84 = pyproj.Proj(init='EPSG:4326')  # LonLat with WGS84 datum used by GPS units and Google Earth
    osgb36 = pyproj.Proj(init='EPSG:27700')  # UK Ordnance Survey, 1936 datum
    easting, northing = pyproj.transform(wgs84, osgb36, longitude, latitude)
    return easting, northing


#
def find_closest_point(pt, pts):
    """
    :param pt: [tuple] (lon, lat)
    :param pts: [iterable] a sequence of reference points
    :return: [tuple]
    """
    # Define a function calculating distance between two points
    def distance(o, d):
        """
        math.hypot(x, y) return the Euclidean norm, sqrt(x*x + y*y).
        This is the length of the vector from the origin to point (x, y).
        """
        return math.hypot(o[0] - d[0], o[1] - d[1])

    # Find the min value using the distance function with coord parameter
    return min(pts, key=functools.partial(distance, pt))


#
def calc_distance_on_unit_sphere(x_pt, y_pt):
    """
    :param x_pt: [shapely.geometry.point.Point]
    :param y_pt: [shapely.geometry.point.Point]
    :return: [float]

    Reference: http://www.johndcook.com/blog/python_longitude_latitude/

    The following function returns the distance between two locations based on each point’s  longitude and latitude. The
    distance returned is relative to Earth’s radius. To get the distance in miles, multiply by 3960. To get the
    distance in kilometers, multiply by 6373.

    Latitude is measured in degrees north of the equator; southern locations have negative latitude. Similarly,
    longitude is measured in degrees east of the Prime Meridian. A location 10° west of the Prime Meridian,
    for example, could be expressed as either 350° east or as -10° east.

    The function assumes the earth is perfectly spherical. For a discussion of how accurate this assumption is,
    see my blog post on http://www.johndcook.com/blog/2009/03/02/what-is-the-shape-of-the-earth/

    The algorithm used to calculate distances is described in detail at http://www.johndcook.com/lat_long_details.html

    A web page to calculate the distance between to cities based on longitude and latitude is available at
    http://www.johndcook.com/lat_long_distance.html

    This function is in the public domain. Do whatever you want with it, no strings attached.

    """
    # Convert latitude and longitude to spherical coordinates in radians.
    degrees_to_radians = math.pi / 180.0

    # phi = 90 - latitude
    phi1 = (90.0 - x_pt.y) * degrees_to_radians
    phi2 = (90.0 - y_pt.y) * degrees_to_radians

    # theta = longitude
    theta1 = x_pt.x * degrees_to_radians
    theta2 = y_pt.x * degrees_to_radians

    # Compute spherical distance from spherical coordinates.

    # For two locations in spherical coordinates
    # (1, theta, phi) and (1, theta', phi')
    # cosine( arc length ) = sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length

    cosine = (math.sin(phi1) * math.sin(phi2) * math.cos(theta1 - theta2) + math.cos(phi1) * math.cos(phi2))
    arc = math.acos(cosine) * 3960  # in miles

    # Remember to multiply arc by the radius of the earth
    # in your favorite set of units to get length.
    return arc


# Get the midpoint between two GPS points
def get_midpoint_along_earth_surface(x_pt, y_pt):
    """
    :param x_pt: [shapely.geometry.point.Point]
    :param y_pt: [shapely.geometry.point.Point]
    :return: [tuple]

    Reference:
    http://code.activestate.com/recipes/577713-midpoint-of-two-gps-points/
    http://www.movable-type.co.uk/scripts/latlong.html
    """
    # Input values as degrees, convert them to radians
    lon_1, lat_1 = math.radians(x_pt.x), math.radians(x_pt.y)
    lon_2, lat_2 = math.radians(y_pt.x), math.radians(y_pt.y)

    b_x, b_y = math.cos(lat_2) * math.cos(lon_2 - lon_1), math.cos(lat_2) * math.sin(lon_2 - lon_1)
    lat_3 = math.atan2(math.sin(lat_1) + math.sin(lat_2),
                       math.sqrt((math.cos(lat_1) + b_x) * (math.cos(lat_1) + b_x) + b_y ** 2))
    long_3 = lon_1 + math.atan2(b_y, math.cos(lat_1) + b_x)

    midpoint = math.degrees(long_3), math.degrees(lat_3)

    return midpoint


# (between <shapely.geometry.point.Point>s)
def get_geometric_midpoint(x_pt, y_pt):
    """
    :param x_pt: [shapely.geometry.point.Point]
    :param y_pt: [shapely.geometry.point.Point]
    :return: [tuple]
    """
    # assert isinstance(x_pt, shapely.geometry.point.Point)
    # assert isinstance(y_pt, shapely.geometry.point.Point)

    midpoint = (x_pt.x + y_pt.x) / 2, (x_pt.y + y_pt.y) / 2
    return midpoint
