""" Geometry-related utilities """

import functools
import math


#
def find_closest_point(point, pts):
    """
    :param point: (long, lat)
    :param pts: a sequence of reference points
    :return:

    math.hypot(x, y) return the Euclidean norm, sqrt(x*x + y*y).
    This is the length of the vector from the origin to point (x, y).

    """

    # Define a function calculating distance between two points
    def distance(o, d):
        return math.hypot(o[0] - d[0], o[1] - d[1])

    # Find the min value using the distance function with coord parameter
    return min(pts, key=functools.partial(distance, point))


#
def distance_on_unit_sphere(x_coord, y_coord):
    """
    :param x_coord: [list]
    :param y_coord: [list]
    :return:

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
    lat1, long1 = x_coord[0], x_coord[1]
    lat2, long2 = y_coord[0], y_coord[1]

    # Convert latitude and longitude to spherical coordinates in radians.
    degrees_to_radians = math.pi / 180.0

    # phi = 90 - latitude
    phi1 = (90.0 - lat1) * degrees_to_radians
    phi2 = (90.0 - lat2) * degrees_to_radians

    # theta = longitude
    theta1 = long1 * degrees_to_radians
    theta2 = long2 * degrees_to_radians

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


# Midpoint of two GPS points
def get_gps_midpoint(x_long, x_lat, y_long, y_lat):
    """
    Reference:
    http://code.activestate.com/recipes/577713-midpoint-of-two-gps-points/
    http://www.movable-type.co.uk/scripts/latlong.html
    """
    # Input values as degrees, convert them to radians
    long_1, lat_1 = math.radians(x_long), math.radians(x_lat)
    long_2, lat_2 = math.radians(y_long), math.radians(y_lat)

    b_x, b_y = math.cos(lat_2) * math.cos(long_2 - long_1), math.cos(lat_2) * math.sin(long_2 - long_1)
    lat_3 = math.atan2(math.sin(lat_1) + math.sin(lat_2),
                       math.sqrt((math.cos(lat_1) + b_x) * (math.cos(lat_1) + b_x) + b_y ** 2))
    long_3 = long_1 + math.atan2(b_y, math.cos(lat_1) + b_x)

    midpoint = math.degrees(long_3), math.degrees(lat_3)

    return midpoint


# (between <shapely.geometry.point.Point>s)
def get_midpoint(start_point, end_point):
    """
    :param start_point: [shapely.geometry.point.Point]
    :param end_point: [shapely.geometry.point.Point]
    :return:
    """
    midpoint = (start_point.x + end_point.x) / 2, (start_point.y + end_point.y) / 2
    return midpoint
