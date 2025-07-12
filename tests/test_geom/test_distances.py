"""
Tests the :mod:`~pyhelpers.geom.distances` submodule.
"""

import pytest

from pyhelpers._cache import example_dataframe
from pyhelpers.geom.distances import *


def test_calc_distance_on_unit_sphere():
    example_df = example_dataframe()

    london, birmingham = example_df.loc[['London', 'Birmingham']].values
    arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham)
    assert arc_len_in_miles == 101.10431101941569
    arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham, unit='km')
    assert arc_len_in_miles == 162.66049633957005
    arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham, precision=4)
    assert arc_len_in_miles == 101.1043

    leeds, manchester = map(
        lambda x: shapely.geometry.Point(x), example_df.loc[['Leeds', 'Manchester']].values)
    arc_len_in_miles = calc_distance_on_unit_sphere(leeds, manchester)
    assert arc_len_in_miles == 36.175811917161276

    with pytest.raises(Exception) as err:
        calc_distance_on_unit_sphere([1], [2])
        assert isinstance(err.value.__cause__, IndexError)


def test_calc_hypotenuse_distance():
    from pyhelpers.geom import calc_hypotenuse_distance

    pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)
    hypot_distance = calc_hypotenuse_distance(pt_1, pt_2)
    assert hypot_distance == 0.05255244999046248

    pt_1_, pt_2_ = map(lambda x: shapely.geometry.Point(x), (pt_1, pt_2))
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

    ref_rslt = np.array(
        [(-2.2451148, 53.4794892),
         (-2.2451148, 53.4794892),
         (-1.5437941, 53.7974185)])
    ref_rslt_ = ('MULTIPOINT '
                 '((-2.2451148 53.4794892), (-2.2451148 53.4794892), (-1.5437941 53.7974185))')

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

    _, idx, dist = find_closest_points(
        pts=cities_1, ref_pts=ref_cities_1, ret_idx=True, ret_dist=True)
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


if __name__ == '__main__':
    pytest.main()
