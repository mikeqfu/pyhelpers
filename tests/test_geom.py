"""Test the module :mod:`~pyhelpers.geom`."""

import numpy as np
import pytest
import shapely.geometry

from pyhelpers._cache import example_dataframe


def test_transform_geom_point_type():
    from pyhelpers.geom import transform_geom_point_type

    example_df = example_dataframe()

    pt1 = example_df.loc['London'].values  # array([-0.1276474, 51.5073219])
    pt2 = example_df.loc['Birmingham'].values  # array([-1.9026911, 52.4796992])

    geom_points = [x.wkt for x in transform_geom_point_type(pt1, pt2)]
    assert geom_points == ['POINT (-0.1276474 51.5073219)', 'POINT (-1.9026911 52.4796992)']

    geom_points = list(transform_geom_point_type(pt1, pt2, as_geom=False))
    assert np.array_equal(
        geom_points, [np.array([-0.1276474, 51.5073219]), np.array([-1.9026911, 52.4796992])])

    pt1, pt2 = map(shapely.geometry.Point, (pt1, pt2))

    geom_points = [x.wkt for x in transform_geom_point_type(pt1, pt2)]
    assert geom_points == ['POINT (-0.1276474 51.5073219)', 'POINT (-1.9026911 52.4796992)']

    geom_points = list(transform_geom_point_type(pt1, pt2, as_geom=False))
    assert np.array_equal(
        geom_points, [np.array([-0.1276474, 51.5073219]), np.array([-1.9026911, 52.4796992])])


def test_wgs84_to_osgb36():
    from pyhelpers.geom import wgs84_to_osgb36

    example_df = example_dataframe()

    lon, lat = example_df.loc['London'].values
    x, y = wgs84_to_osgb36(longitudes=lon, latitudes=lat)
    assert (x, y) == (530039.558844505, 180371.68016544735)

    lonlat_array = example_df.to_numpy()

    lons, lats = lonlat_array.T  # lonlat_array[:, 0], lonlat_array[:, 1]
    xs, ys = wgs84_to_osgb36(longitudes=lons, latitudes=lats)

    assert np.allclose(
        xs, np.array([530039.5588445, 406705.8870136, 383830.03903573, 430147.44735387]))
    assert np.allclose(
        ys, np.array([180371.68016545, 286868.16664219, 398113.05583091, 433553.32711728]))

    xy_array = wgs84_to_osgb36(longitudes=lons, latitudes=lats, as_array=True)
    xy_array_ = np.array([[530039.5588445, 180371.68016545],
                          [406705.8870136, 286868.16664219],
                          [383830.03903573, 398113.05583091],
                          [430147.44735387, 433553.32711728]])
    assert np.allclose(xy_array, xy_array_)


def test_osgb36_to_wgs84():
    from pyhelpers.geom import osgb36_to_wgs84

    example_df = example_dataframe(osgb36=True)

    x, y = example_df.loc['London'].values
    lon, lat = osgb36_to_wgs84(eastings=x, northings=y)
    assert (lon, lat) == (-0.12764738749567286, 51.50732189539607)

    xy_array = example_df.to_numpy()
    xs, ys = xy_array.T  # xy_array[:, 0], xy_array[:, 1]
    lons, lats = osgb36_to_wgs84(eastings=xs, northings=ys)
    assert np.allclose(lons, np.array([-0.12764739, -1.90269109, -2.24511479, -1.54379409]))
    assert np.allclose(lats, np.array([51.5073219, 52.4796992, 53.4794892, 53.7974185]))

    lonlat_array = osgb36_to_wgs84(eastings=xs, northings=ys, as_array=True)
    lonlat_array_ = np.array([[-0.12764739, 51.5073219],
                              [-1.90269109, 52.4796992],
                              [-2.24511479, 53.4794892],
                              [-1.54379409, 53.7974185]])
    assert np.allclose(lonlat_array, lonlat_array_)


def test_drop_axis():
    from pyhelpers.geom import drop_axis

    geom_1 = shapely.geometry.Point([1, 2, 3])
    assert geom_1.wkt == 'POINT Z (1 2 3)'
    geom_1_ = drop_axis(geom_1, 'x')
    assert geom_1_.wkt == 'POINT (2 3)'
    geom_1_ = drop_axis(geom_1, 'x', as_array=True)
    assert np.array_equal(geom_1_, np.array([2., 3.]))

    geom_2 = shapely.geometry.LineString([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    assert geom_2.wkt
    'LINESTRING Z (1 2 3, 2 3 4, 3 4 5)'
    geom_2_ = drop_axis(geom_2, 'y')
    assert geom_2_.wkt
    'LINESTRING (1 3, 2 4, 3 5)'
    geom_2_ = drop_axis(geom_2, 'y', as_array=True)
    assert np.array_equal(geom_2_, np.array([[1., 3.], [2., 4.], [3., 5.]]))

    geom_3 = shapely.geometry.Polygon([[6, 3, 5], [6, 3, 0], [6, 1, 0], [6, 1, 5], [6, 3, 5]])
    assert geom_3.wkt
    'POLYGON Z ((6 3 5, 6 3 0, 6 1 0, 6 1 5, 6 3 5))'
    geom_3_ = drop_axis(geom_3, 'z')
    assert geom_3_.wkt
    'POLYGON ((6 3, 6 3, 6 1, 6 1, 6 3))'
    geom_3_ = drop_axis(geom_3, 'z', as_array=True)
    assert np.array_equal(geom_3_, np.array([[6., 3.], [6., 3.], [6., 1.], [6., 1.], [6., 3.]]))

    ls1 = shapely.geometry.LineString([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    ls2 = shapely.geometry.LineString([[2, 3, 4], [1, 2, 3], [3, 4, 5]])
    geom_4 = shapely.geometry.MultiLineString([ls1, ls2])
    assert geom_4.wkt == 'MULTILINESTRING Z ((1 2 3, 2 3 4, 3 4 5), (2 3 4, 1 2 3, 3 4 5))'
    geom_4_ = drop_axis(geom_4, 'z')
    assert geom_4_.wkt == 'MULTILINESTRING ((1 2, 2 3, 3 4), (2 3, 1 2, 3 4))'
    geom_4_ = drop_axis(geom_4, 'z', as_array=True)
    assert np.array_equal(
        geom_4_, np.array([[[1., 2.], [2., 3.], [3., 4.]], [[2., 3.], [1., 2.], [3., 4.]]]))


def test_project_point_to_line():
    from pyhelpers.geom import project_point_to_line

    pt = shapely.geometry.Point([399297, 655095, 43])
    ls = shapely.geometry.LineString([[399299, 655091, 42], [399295, 655099, 42]])

    _, pt_proj = project_point_to_line(point=pt, line=ls)
    assert pt_proj.wkt == 'POINT Z (399297 655095 42)'


def test_calc_distance_on_unit_sphere():
    from pyhelpers.geom import calc_distance_on_unit_sphere

    example_df = example_dataframe()

    london, birmingham = example_df.loc[['London', 'Birmingham']].values

    arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham)
    assert arc_len_in_miles == 101.10431101941569


def test_calc_hypotenuse_distance():
    from pyhelpers.geom import calc_hypotenuse_distance
    from shapely.geometry import Point

    pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)
    hypot_distance = calc_hypotenuse_distance(pt_1, pt_2)
    assert hypot_distance == 0.05255244999046248

    pt_1_, pt_2_ = map(Point, (pt_1, pt_2))
    assert pt_1_.wkt == 'POINT (1.5429 52.6347)'
    assert pt_2_.wkt == 'POINT (1.4909 52.6271)'
    hypot_distance = calc_hypotenuse_distance(pt_1_, pt_2_)
    assert hypot_distance == 0.05255244999046248


def test_find_closest_point():
    from pyhelpers.geom import find_closest_point

    example_df = example_dataframe()

    # Find the city closest to London
    london = example_df.loc['London'].values
    ref_cities = example_df.loc['Birmingham':, :].values
    closest_to_london = find_closest_point(pt=london, ref_pts=ref_cities)
    assert closest_to_london.wkt == 'POINT (-1.9026911 52.4796992)'

    # Find the city closest to Leeds
    leeds = example_df.loc['Leeds'].values
    ref_cities = example_df.loc[:'Manchester', :].values
    closest_to_leeds = find_closest_point(pt=leeds, ref_pts=ref_cities)
    assert closest_to_leeds.wkt == 'POINT (-2.2451148 53.4794892)'

    closest_to_leeds = find_closest_point(pt=leeds, ref_pts=ref_cities, as_geom=False)
    assert np.array_equal(closest_to_leeds, np.array([-2.2451148, 53.4794892]))


def test_find_closest_points():
    from pyhelpers.geom import find_closest_points

    example_df = example_dataframe()

    cities = [[-2.9916800, 53.4071991], [-4.2488787, 55.8609825], [-1.6131572, 54.9738474]]
    ref_cities = example_df.to_numpy()

    closest_to_each = find_closest_points(pts=cities, ref_pts=ref_cities, k=1)
    x1 = np.array([[-2.2451148, 53.4794892], [-2.2451148, 53.4794892], [-1.5437941, 53.7974185]])
    assert np.array_equal(closest_to_each, x1)

    closest_to_each = find_closest_points(pts=cities, ref_pts=ref_cities, k=1, as_geom=True)
    assert closest_to_each.wkt == \
           'MULTIPOINT (-2.2451148 53.4794892, -2.2451148 53.4794892, -1.5437941 53.7974185)'

    _, idx = find_closest_points(pts=cities, ref_pts=ref_cities, k=1, ret_idx=True)
    assert np.array_equal(idx, np.array([2, 2, 3], dtype=np.int64))

    _, _, dist = find_closest_points(cities, ref_cities, k=1, ret_idx=True, ret_dist=True)
    assert np.array_equal(np.round(dist, 8), np.array([0.75005697, 3.11232712, 1.17847198]))

    cities_geoms_1 = shapely.geometry.LineString(cities)
    closest_to_each = find_closest_points(pts=cities_geoms_1, ref_pts=ref_cities, k=1)
    x2 = np.array([[-2.2451148, 53.4794892], [-2.2451148, 53.4794892], [-1.5437941, 53.7974185]])
    assert np.array_equal(np.round(closest_to_each, 7), x2)

    cities_geoms_2 = shapely.geometry.MultiPoint(cities)
    closest_to_each = find_closest_points(cities_geoms_2, ref_cities, k=1, as_geom=True)
    assert closest_to_each.wkt == \
           'MULTIPOINT (-2.2451148 53.4794892, -2.2451148 53.4794892, -1.5437941 53.7974185)'


def test_find_shortest_path():
    from pyhelpers.geom import find_shortest_path

    example_df = example_dataframe()
    example_df_ = example_df.sample(frac=1, random_state=1)
    cities = example_df_.to_numpy()

    cities_sorted = find_shortest_path(points_sequence=cities)
    cities_sorted_ = np.array([[-1.5437941, 53.7974185],
                               [-2.2451148, 53.4794892],
                               [-1.9026911, 52.4796992],
                               [-0.1276474, 51.5073219]])
    assert np.array_equal(cities_sorted, cities_sorted_)


def test_get_midpoint():
    from pyhelpers.geom import get_midpoint

    x_1, y_1 = 1.5429, 52.6347
    x_2, y_2 = 1.4909, 52.6271

    midpt = get_midpoint(x_1, y_1, x_2, y_2)
    assert np.array_equal(midpt, np.array([1.5169, 52.6309]))

    midpt = get_midpoint(x_1, y_1, x_2, y_2, as_geom=True)
    assert midpt.wkt == 'POINT (1.5169 52.6309)'

    x_1, y_1 = (1.5429, 1.4909), (52.6347, 52.6271)
    x_2, y_2 = [2.5429, 2.4909], [53.6347, 53.6271]

    midpt = get_midpoint(x_1, y_1, x_2, y_2)
    assert np.array_equal(midpt, np.array([[2.0429, 53.1347], [1.9909, 53.1271]]))

    midpt = get_midpoint(x_1, y_1, x_2, y_2, as_geom=True)
    assert midpt.wkt == 'MULTIPOINT (2.0429 53.1347, 1.9909 53.1271)'


def test_get_geometric_midpoint():
    from pyhelpers.geom import get_geometric_midpoint

    pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)

    geometric_midpoint = get_geometric_midpoint(pt_1, pt_2)
    assert geometric_midpoint == (1.5169, 52.6309)

    geometric_midpoint = get_geometric_midpoint(pt_1, pt_2, as_geom=True)
    assert geometric_midpoint.wkt == 'POINT (1.5169 52.6309)'


def test_get_geometric_midpoint_calc():
    from pyhelpers.geom import get_geometric_midpoint_calc

    pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)

    midpoint = (1.5168977420748175, 52.630902845583094)

    geometric_midpoint = get_geometric_midpoint_calc(pt_1, pt_2)
    assert np.array_equal(np.round(geometric_midpoint, 8), np.round(midpoint, 8))

    geometric_midpoint = get_geometric_midpoint_calc(pt_1, pt_2, as_geom=True)
    assert isinstance(geometric_midpoint, shapely.geometry.Point)


def test_get_rectangle_centroid():
    from pyhelpers.geom import get_rectangle_centroid

    rectangle_obj = shapely.geometry.Polygon([[0, 0], [0, 1], [1, 1], [1, 0]])

    rect_cen = get_rectangle_centroid(rectangle=rectangle_obj)
    assert np.array_equal(rect_cen, np.array([[0.5, 0.5]]))


def test_get_square_vertices():
    from pyhelpers.geom import get_square_vertices

    ctr_1, ctr_2 = -5.9375, 56.8125
    side_len = 0.125

    vts = get_square_vertices(ctr_1, ctr_2, side_len, rotation_theta=0)
    assert np.array_equal(vts, np.array([[-6., 56.75],
                                         [-6., 56.875],
                                         [-5.875, 56.875],
                                         [-5.875, 56.75]]))

    # Rotate the square by 30° (anticlockwise)
    vts = get_square_vertices(ctr_1, ctr_2, side_len, rotation_theta=30)
    assert np.array_equal(np.round(vts, 8), np.array([[-5.96037659, 56.72712341],
                                                      [-6.02287659, 56.83537659],
                                                      [-5.91462341, 56.89787659],
                                                      [-5.85212341, 56.78962341]]))


def test_get_square_vertices_calc():
    from pyhelpers.geom import get_square_vertices_calc

    ctr_1, ctr_2 = -5.9375, 56.8125
    side_len = 0.125

    vts = get_square_vertices_calc(ctr_1, ctr_2, side_len, rotation_theta=0)
    assert np.array_equal(vts, np.array([[-6., 56.75],
                                         [-6., 56.875],
                                         [-5.875, 56.875],
                                         [-5.875, 56.75]]))

    # Rotate the square by 30° (anticlockwise)
    vts = get_square_vertices_calc(ctr_1, ctr_2, side_len, rotation_theta=30)
    assert np.array_equal(np.round(vts, 8), np.array([[-5.96037659, 56.72712341],
                                                      [-6.02287659, 56.83537659],
                                                      [-5.91462341, 56.89787659],
                                                      [-5.85212341, 56.78962341]]))


def test_sketch_square():
    from pyhelpers.geom import sketch_square

    c1, c2 = 1, 1
    side_len = 2

    sketch_vertices = sketch_square(
        c1, c2, side_len, rotation_theta=0, annotation=True, fig_size=(5, 5), ret_vertices=True)
    assert np.array_equal(
        np.round(sketch_vertices), np.array([[0., 0.], [0., 2.], [2., 2.], [2., 0.], [0., 0.]]))


if __name__ == '__main__':
    pytest.main()
