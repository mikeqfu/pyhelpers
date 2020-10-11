"""
Test module geom.py
"""

from pyhelpers.geom import *

""" Transformation ----------------------------------------------------------------- """


# Geometric type

def test_transform_geom_point_type():
    pt_x = 1.5429, 52.6347
    pt_y = 1.4909, 52.6271

    geom_points = transform_geom_point_type(pt_x, pt_y)
    for x in geom_points:
        print(x)
    # POINT (1.5429 52.6347)
    # POINT (1.4909 52.6271)

    as_geom = False
    geom_points = transform_geom_point_type(pt_x, pt_y, as_geom=as_geom)
    for x in geom_points:
        print(x)
    # (1.5429, 52.6347)
    # (1.4909, 52.6271)

    from shapely.geometry import Point

    pt_x = Point(pt_x)
    pt_y = Point(pt_y)

    geom_points = transform_geom_point_type(pt_x, pt_y)
    for x in geom_points:
        print(x)
    # POINT (1.5429 52.6347)
    # POINT (1.4909 52.6271)

    as_geom = False
    geom_points = transform_geom_point_type(pt_x, pt_y, as_geom=as_geom)
    for x in geom_points:
        print(x)
    # (1.5429, 52.6347)
    # (1.4909, 52.6271)


# Coordinate system

def test_wgs84_to_osgb36():
    longitude, latitude = -0.12772404, 51.507407

    easting, northing = wgs84_to_osgb36(longitude, latitude)
    print(f"Easting: {easting}")
    print(f"Northing: {northing}")
    # Easting: 530033.99829712
    # Northing: 180381.00751935126


def test_osgb36_to_wgs84():
    easting, northing = 530034, 180381

    longitude, latitude = osgb36_to_wgs84(easting, northing)
    print(f"Longitude: {longitude}")
    print(f"Latitude: {latitude}")
    # Longitude: -0.12772400574286874
    # Latitude: 51.50740692743041


def test_wgs84_to_osgb36_calc():
    longitude, latitude = -0.12772404, 51.507407

    easting, northing = wgs84_to_osgb36_calc(longitude, latitude)
    print(f"Easting: {easting}")
    print(f"Northing: {northing}")
    # Easting: 530034.0010406997
    # Northing: 180381.0084845958

    # cp.
    # wgs84_to_osgb36(longitude, latitude)
    # Easting: 530033.99829712
    # Northing: 180381.00751935126


def test_osgb36_to_wgs84_calc():
    easting, northing = 530034, 180381

    longitude, latitude = osgb36_to_wgs84_calc(easting, northing)
    print(f"Longitude: {longitude}")
    print(f"Latitude: {latitude}")
    # Longitude: -0.1277240422737611
    # Latitude: 51.50740676560936

    # cp.
    # test_osgb36_to_wgs84(longitude, latitude)
    # Longitude: -0.12772400574286874
    # Latitude: 51.50740692743041


""" Calculation -------------------------------------------------------------------- """


# Midpoint

def test_get_midpoint():
    x1, y1 = 1.5429, 52.6347
    x2, y2 = 1.4909, 52.6271

    midpoint = get_midpoint(x1, y1, x2, y2)
    print(midpoint)
    # [ 1.5169 52.6309]

    as_geom = True
    midpoint = get_midpoint(x1, y1, x2, y2, as_geom=as_geom)
    print(midpoint)
    # POINT (1.5169 52.6309)

    x1, y1 = np.array([1.5429, 1.4909]), np.array([52.6347, 52.6271])
    x2, y2 = np.array([2.5429, 2.4909]), np.array([53.6347, 53.6271])

    midpoint = get_midpoint(x1, y1, x2, y2)
    print(midpoint)
    # [[ 2.0429 53.1347]
    #  [ 1.9909 53.1271]]

    as_geom = True
    midpoint = get_midpoint(x1, y1, x2, y2, as_geom=as_geom)
    for x in midpoint:
        print(x)
    # POINT (2.0429 53.1347)
    # POINT (1.9909 53.1271)


def test_get_geometric_midpoint():
    pt_x = 1.5429, 52.6347
    pt_y = 1.4909, 52.6271

    geometric_midpoint = get_geometric_midpoint(pt_x, pt_y)
    print(geometric_midpoint)
    # (1.5169, 52.6309)

    as_geom = True
    geometric_midpoint = get_geometric_midpoint(pt_x, pt_y, as_geom)
    print(geometric_midpoint)
    # POINT (1.5169 52.6309)


def test_get_geometric_midpoint_calc():
    pt_x = 1.5429, 52.6347
    pt_y = 1.4909, 52.6271

    geometric_midpoint = get_geometric_midpoint_calc(pt_x, pt_y)
    print(geometric_midpoint)
    # (1.5168977420748175, 52.630902845583094)

    as_geom = True
    geometric_midpoint = get_geometric_midpoint_calc(pt_x, pt_y, as_geom)
    print(geometric_midpoint)
    # POINT (1.516897742074818 52.63090284558309)

    # cp. get_geometric_midpoint(pt_x, pt_y)


# Distance

def test_calc_distance_on_unit_sphere():
    pt_x = 1.5429, 52.6347
    pt_y = 1.4909, 52.6271

    arc_length = calc_distance_on_unit_sphere(pt_x, pt_y)
    print(arc_length)
    # 2.243709962588554


def test_calc_hypotenuse_distance():
    pt_x = 1.5429, 52.6347
    pt_y = 1.4909, 52.6271

    hypot_dist = calc_hypotenuse_distance(pt_x, pt_y)
    print(hypot_dist)
    # 0.05255244999046248


# Search

def test_find_closest_point_from():
    pt = (2.5429, 53.6347)
    ref_pts = ((1.5429, 52.6347),
               (1.4909, 52.6271),
               (1.4248, 52.63075))

    closest_point = find_closest_point_from(pt, ref_pts)
    print(closest_point)
    # (1.5429, 52.6347)

    from shapely.geometry import Point

    pt = Point((2.5429, 53.6347))
    ref_pts = (Point((1.5429, 52.6347)), Point((1.4909, 52.6271)), Point((1.4248, 52.63075)))

    closest_point = find_closest_point_from(pt, ref_pts)
    print(closest_point)
    # (1.5429, 52.6347)

    as_geom = True
    closest_point = find_closest_point_from(pt, ref_pts, as_geom)
    print(closest_point)
    # POINT (1.5429 52.6347)


def test_find_closest_points_between():
    pts = np.array([[1.5429, 52.6347],
                    [1.4909, 52.6271],
                    [1.4248, 52.63075]])

    ref_pts = np.array([[2.5429, 53.6347],
                        [2.4909, 53.6271],
                        [2.4248, 53.63075]])

    k = 1

    closest_points = find_closest_points_between(pts, ref_pts, k)
    print(closest_points)
    # [[ 2.4248  53.63075]
    #  [ 2.4248  53.63075]
    #  [ 2.4248  53.63075]]

    as_geom = True
    closest_points = find_closest_points_between(pts, ref_pts, k, as_geom)
    for x in closest_points:
        print(x)
    # POINT (2.4248 53.63075)
    # POINT (2.4248 53.63075)
    # POINT (2.4248 53.63075)


def test_get_square_vertices():
    ctr_x, ctr_y = -5.9375, 56.8125
    side_length = 0.125

    rotation_theta = 0
    vertices = get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta)
    print(vertices)
    # [[-6.    56.75 ]
    #  [-6.    56.875]
    #  [-5.875 56.875]
    #  [-5.875 56.75 ]]

    rotation_theta = 30  # rotate the square by 30° (anticlockwise)
    vertices = get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta)
    print(vertices)
    # [[-5.96037659 56.72712341]
    #  [-6.02287659 56.83537659]
    #  [-5.91462341 56.89787659]
    #  [-5.85212341 56.78962341]]


def test_get_square_vertices_calc():
    ctr_x, ctr_y = -5.9375, 56.8125
    side_length = 0.125

    rotation_theta = 0
    vertices = get_square_vertices_calc(ctr_x, ctr_y, side_length, rotation_theta)
    print(vertices)
    # [[-6.    56.75 ]
    #  [-6.    56.875]
    #  [-5.875 56.875]
    #  [-5.875 56.75 ]]

    rotation_theta = 30  # rotate the square by 30° (anticlockwise)
    vertices = get_square_vertices_calc(ctr_x, ctr_y, side_length, rotation_theta)
    print(vertices)
    # [[-5.96037659 56.72712341]
    #  [-6.02287659 56.83537659]
    #  [-5.91462341 56.89787659]
    #  [-5.85212341 56.78962341]]


""" Visualisation ------------------------------------------------------------------ """


# Sketch

def test_sketch_square():
    ctr_x, ctr_y = 1, 1
    side_length = 2
    fig_size = (5, 5)
    annotation = True

    import matplotlib.pyplot as plt

    rotation_theta = 0
    print("Figure 1", end=" ... ")
    sketch_square(ctr_x, ctr_y, side_length, rotation_theta, annotation, fig_size=fig_size)
    print("Done.")

    rotation_theta = 75
    print("Figure 1", end=" ... ")
    sketch_square(ctr_x, ctr_y, side_length, rotation_theta, annotation, fig_size=fig_size)
    print("Done.")

    plt.show()


if __name__ == '__main__':
    """ Transformation ------------------------------------------------------------- """

    # Geometric type
    print("\nTesting 'transform_geom_point_type()':")
    test_transform_geom_point_type()

    # Coordinate system
    print("\nTesting 'wgs84_to_osgb36()':")
    test_wgs84_to_osgb36()

    print("\nTesting 'osgb36_to_wgs84()':")
    test_osgb36_to_wgs84()

    print("\nTesting 'wgs84_to_osgb36_calc()':")
    test_wgs84_to_osgb36_calc()

    print("\nTesting 'osgb36_to_wgs84_calc()':")
    test_osgb36_to_wgs84_calc()

    """ Calculation ---------------------------------------------------------------- """

    # Midpoint
    print("\nTesting 'get_midpoint()':")
    test_get_midpoint()

    print("\nTesting 'get_geometric_midpoint()':")
    test_get_geometric_midpoint()

    print("\nTesting 'get_geometric_midpoint_calc()':")
    test_get_geometric_midpoint_calc()

    # Distance
    print("\nTesting 'calc_distance_on_unit_sphere()':")
    test_calc_distance_on_unit_sphere()

    print("\nTesting 'calc_hypotenuse_distance()':")
    test_calc_hypotenuse_distance()

    # Search
    print("\nTesting 'find_closest_point_from()':")
    test_find_closest_point_from()

    print("\nTesting 'find_closest_points_between()':")
    test_find_closest_points_between()

    print("\nTesting 'get_square_vertices()':")
    test_get_square_vertices()

    print("\nTesting 'get_square_vertices_calc()':")
    test_get_square_vertices_calc()

    """ Visualisation -------------------------------------------------------------- """

    # Sketch
    print("\nTesting 'sketch_square()':")
    test_sketch_square()
