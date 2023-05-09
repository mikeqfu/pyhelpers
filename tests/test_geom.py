"""Test the module :mod:`~pyhelpers.geom`."""

import functools

import numpy as np
import pytest
import shapely.geometry

from pyhelpers._cache import example_dataframe


def test_transform_geom_point_type():
    from pyhelpers.geom import transform_geom_point_type

    example_df = example_dataframe()

    pt1 = example_df.loc['London'].values  # array([-0.1276474, 51.5073219])
    pt2 = example_df.loc['Birmingham'].values  # array([-1.9026911, 52.4796992])

    ref_rslt_1 = ['POINT (-0.1276474 51.5073219)', 'POINT (-1.9026911 52.4796992)']
    ref_rslt_2 = [np.array([-0.1276474, 51.5073219]), np.array([-1.9026911, 52.4796992])]

    geom_points = [x.wkt for x in transform_geom_point_type(pt1, pt2)]
    assert geom_points == ref_rslt_1

    geom_points = list(transform_geom_point_type(pt1, pt2, as_geom=False))
    assert np.array_equal(geom_points, ref_rslt_2)

    pt1, pt2 = map(shapely.geometry.Point, (pt1, pt2))

    geom_points = [x.wkt for x in transform_geom_point_type(pt1, pt2)]
    assert geom_points == ref_rslt_1

    geom_points = list(transform_geom_point_type(pt1, pt2, as_geom=False))
    assert np.array_equal(geom_points, ref_rslt_2)

    geom_points_ = transform_geom_point_type(shapely.geometry.Point([1, 2, 3]), as_geom=False)
    assert np.array_equal(list(geom_points_), [(1.0, 2.0, 3.0)])


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
    ls = shapely.geometry.LineString([[399299, 655091, 42], [399299, 655091, 42]])
    _, pt_proj = project_point_to_line(point=pt, line=ls)
    assert pt_proj.wkt == 'POINT Z (399299 655091 42)'

    pt = shapely.geometry.Point([399297, 655095, 43])
    ls_ = shapely.geometry.LineString([[399299, 655091, 42], [399295, 655099, 42], [399295, 655107, 42]])
    _, pt_proj = project_point_to_line(point=pt, line=ls_)
    assert pt_proj.wkt == 'POINT Z (399297.9411764706 655095.2352941176 42)'

    _, pt_proj = project_point_to_line(point=pt, line=ls_, drop_dimension='z')
    assert pt_proj.wkt == 'POINT (399297.9411764706 655095.2352941176)'


def test_calc_distance_on_unit_sphere():
    from pyhelpers.geom import calc_distance_on_unit_sphere

    example_df = example_dataframe()

    london, birmingham = example_df.loc[['London', 'Birmingham']].values
    arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham)
    assert arc_len_in_miles == 101.10431101941569
    arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham, unit='km')
    assert arc_len_in_miles == 162.66049633957005
    arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham, precision=4)
    assert arc_len_in_miles == 101.1043

    leeds, manchester = map(shapely.geometry.Point, example_df.loc[['Leeds', 'Manchester']].values)
    arc_len_in_miles = calc_distance_on_unit_sphere(leeds, manchester)
    assert arc_len_in_miles == 36.175811917161276

    with pytest.raises(Exception) as err:
        calc_distance_on_unit_sphere([1], [2])
        assert isinstance(err.value.__cause__, IndexError)


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
    london = [example_df.loc['London'].values, shapely.geometry.Point(example_df.loc['London'])]
    ref_cities = example_df.loc['Birmingham':, :].values
    for x in london:
        closest_to_london = find_closest_point(pt=x, ref_pts=ref_cities)
        assert closest_to_london.wkt == 'POINT (-1.9026911 52.4796992)'

    # Find the city closest to Leeds
    leeds = example_df.loc['Leeds'].values
    ref_cities_ = example_df.loc[:'Manchester', :].values
    ref_cities = [ref_cities_, shapely.geometry.MultiPoint(ref_cities_)]
    for y in ref_cities:
        closest_to_leeds = find_closest_point(pt=leeds, ref_pts=y)
        assert closest_to_leeds.wkt == 'POINT (-2.2451148 53.4794892)'

        closest_to_leeds = find_closest_point(pt=leeds, ref_pts=y, as_geom=False)
        assert np.array_equal(closest_to_leeds, np.array([-2.2451148, 53.4794892]))

    ref_cities = shapely.geometry.Point(ref_cities_[0])
    closest_to_leeds = find_closest_point(pt=leeds, ref_pts=ref_cities)
    assert closest_to_leeds.wkt == ref_cities.wkt


def test_find_closest_points():
    from pyhelpers.geom import find_closest_points

    cities_1 = [(-2.9916800, 53.4071991), (-4.2488787, 55.8609825), (-1.6131572, 54.9738474)]
    cities_2 = np.array(cities_1)
    cities_3 = shapely.geometry.LineString(cities_1)
    cities_4 = shapely.geometry.MultiLineString([cities_3, cities_3])
    cities_5 = shapely.geometry.Polygon(cities_1)
    cities_6 = shapely.geometry.MultiPolygon([cities_5, cities_5])
    cities_7 = shapely.geometry.GeometryCollection([cities_3, cities_4, cities_5, cities_6])

    example_df = example_dataframe()
    ref_cities_1 = example_df.to_numpy()
    ref_cities_2 = shapely.geometry.MultiPoint(ref_cities_1)

    ref_rslt = np.array([(-2.2451148, 53.4794892), (-2.2451148, 53.4794892), (-1.5437941, 53.7974185)])
    ref_rslt_ = 'MULTIPOINT (-2.2451148 53.4794892, -2.2451148 53.4794892, -1.5437941 53.7974185)'

    ref_dist = np.array([0.75005697, 3.11232712, 1.17847198])

    rslt = find_closest_points(pts=cities_1, ref_pts=ref_cities_1)
    assert np.array_equal(rslt, ref_rslt)

    rslt = find_closest_points(pts=cities_1, ref_pts=ref_cities_2)
    assert np.array_equal(rslt, ref_rslt)

    rslt = find_closest_points(pts=cities_2, ref_pts=ref_cities_2)
    assert np.array_equal(rslt, ref_rslt)

    rslt = find_closest_points(pts=cities_3, ref_pts=ref_cities_1)
    assert np.array_equal(np.round(rslt, 7), ref_rslt)

    rslt = find_closest_points(pts=cities_1, ref_pts=ref_cities_1, as_geom=True)
    assert rslt.wkt == ref_rslt_

    rslt = find_closest_points(pts=cities_4, ref_pts=ref_cities_1, as_geom=True, unique=True)
    assert rslt.wkt == ref_rslt_

    rslt = find_closest_points(pts=cities_5, ref_pts=ref_cities_1, as_geom=True, unique=True)
    assert rslt.wkt == ref_rslt_

    rslt = find_closest_points(pts=cities_6, ref_pts=ref_cities_1, as_geom=True, unique=True)
    assert rslt.wkt == ref_rslt_

    rslt = find_closest_points(pts=cities_7, ref_pts=ref_cities_2, as_geom=True, unique=True)
    assert rslt.wkt == ref_rslt_

    _, idx = find_closest_points(pts=cities_1, ref_pts=ref_cities_1, ret_idx=True)
    assert np.array_equal(idx, np.array([2, 2, 3], dtype=np.int64))

    _, dist = find_closest_points(pts=cities_1, ref_pts=ref_cities_1, ret_dist=True)
    assert np.array_equal(np.round(dist, 8), ref_dist)

    _, idx, dist = find_closest_points(pts=cities_1, ref_pts=ref_cities_1, ret_idx=True, ret_dist=True)
    assert np.array_equal(idx, np.array([2, 2, 3], dtype=np.int64))
    assert np.array_equal(np.round(dist, 8), ref_dist)


def test_find_shortest_path():
    from pyhelpers.geom import find_shortest_path

    example_df = example_dataframe()
    example_df_ = example_df.sample(frac=1, random_state=1)
    cities = example_df_.to_numpy()

    cities_sorted_1 = find_shortest_path(points_sequence=cities)
    cities_sorted_ = np.array([[-1.5437941, 53.7974185],
                               [-2.2451148, 53.4794892],
                               [-1.9026911, 52.4796992],
                               [-0.1276474, 51.5073219]])
    assert np.array_equal(cities_sorted_1, cities_sorted_)

    cities_sorted_2, min_dist = find_shortest_path(
        points_sequence=cities, as_geom=True, ret_dist=True)
    assert 'LINESTRING' in cities_sorted_2.wkt
    assert np.round(min_dist, 1) == 5.8

    cities_ = cities[:2]
    cities_sorted = find_shortest_path(points_sequence=cities_)
    assert np.array_equal(cities_, cities_sorted)


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


@pytest.mark.parametrize('as_geom', [False, True])
def test_get_rectangle_centroid(as_geom):
    from pyhelpers.geom import get_rectangle_centroid

    coords_1 = [[0, 0], [0, 1], [1, 1], [1, 0]]
    rect_objs = [shapely.geometry.Polygon(coords_1), np.array(coords_1)]
    rect_cen_rslt = map(functools.partial(get_rectangle_centroid, as_geom=as_geom), rect_objs)

    for x in rect_cen_rslt:
        if as_geom:
            assert isinstance(x, shapely.geometry.Point)
            assert x.wkt == 'POINT (0.5 0.5)'
        else:
            assert np.array_equal(x, np.array([0.5, 0.5]))

    coords_2 = [[(0, 0), (0, 1), (1, 1), (1, 0)], [(1, 1), (1, 2), (2, 2), (2, 1)]]
    rect_objs_2 = get_rectangle_centroid(rectangle=coords_2)
    assert np.array_equal(rect_objs_2, np.array([1., 1.]))


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

    func_args = {'ctr_x': 1, 'ctr_y': 1, 'side_length': 2, 'annotation': True, 'ret_vertices': True}

    sketch_vtx = sketch_square(rotation_theta=0, **func_args)
    assert np.array_equal(
        np.round(sketch_vtx), np.array([[0., 0.], [0., 2.], [2., 2.], [2., 0.], [0., 0.]]))

    sketch_vtx = sketch_square(rotation_theta=75, **func_args)
    assert np.array_equal(sketch_vtx[0], sketch_vtx[-1])


if __name__ == '__main__':
    pytest.main()
