"""
Tests the :mod:`~pyhelpers.geom.transforms` submodule.
"""

import pytest

from pyhelpers._cache import example_dataframe
from pyhelpers.geom.transforms import *


def test_transform_geom_point_type():
    example_df = example_dataframe()

    pt1 = example_df.loc['London'].values  # array([-0.1276474, 51.5073219])
    pt2 = example_df.loc['Birmingham'].values  # array([-1.9026911, 52.4796992])

    ref_rslt_1 = ['POINT (-0.1276474 51.5073219)', 'POINT (-1.9026911 52.4796992)']
    ref_rslt_2 = [np.array([-0.1276474, 51.5073219]), np.array([-1.9026911, 52.4796992])]

    geom_points = [x.wkt for x in transform_point_type(pt1, pt2)]
    assert geom_points == ref_rslt_1

    geom_points = list(transform_point_type(pt1, pt2, as_geom=False))
    assert np.array_equal(geom_points, ref_rslt_2)

    pt1, pt2 = map(lambda x: shapely.geometry.Point(x), (pt1, pt2))

    geom_points = [x.wkt for x in transform_point_type(pt1, pt2)]
    assert geom_points == ref_rslt_1

    geom_points = list(transform_point_type(pt1, pt2, as_geom=False))
    assert np.array_equal(geom_points, ref_rslt_2)

    geom_points_ = transform_point_type(shapely.geometry.Point([1, 2, 3]), as_geom=False)
    assert np.array_equal(list(geom_points_), [(1.0, 2.0, 3.0)])


def test_wgs84_to_osgb36():
    example_df = example_dataframe()

    lon, lat = example_df.loc['London'].values
    x, y = wgs84_to_osgb36(longitudes=lon, latitudes=lat)
    assert np.allclose((x, y), (530039.55884451, 180371.68016545))

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
    example_df = example_dataframe(osgb36=True)

    x, y = example_df.loc['London'].values
    lon, lat = osgb36_to_wgs84(eastings=x, northings=y)
    assert np.allclose((lon, lat), (-0.12764738749567286, 51.50732189539607))

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
    # 1. Point (3D)
    geom_1 = shapely.geometry.Point([1, 2, 3])
    assert geom_1.wkt == 'POINT Z (1 2 3)'
    geom_1_ = drop_axis(geom_1, 'x')
    assert geom_1_.wkt == 'POINT (2 3)'
    geom_1_arr = drop_axis(geom_1, 'x', as_array=True)
    assert np.array_equal(geom_1_arr, np.array([2., 3.]))

    # 2. LineString (3D)
    geom_2 = shapely.geometry.LineString([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    assert geom_2.wkt == 'LINESTRING Z (1 2 3, 2 3 4, 3 4 5)'
    geom_2_ = drop_axis(geom_2, 'y')
    assert geom_2_.wkt == 'LINESTRING (1 3, 2 4, 3 5)'
    geom_2_arr = drop_axis(geom_2, 'y', as_array=True)
    assert np.array_equal(geom_2_arr, np.array([[1., 3.], [2., 4.], [3., 5.]]))

    # 3. Polygon (3D)
    geom_3 = shapely.geometry.Polygon([[6, 3, 5], [6, 3, 0], [6, 1, 0], [6, 1, 5], [6, 3, 5]])
    assert geom_3.wkt == 'POLYGON Z ((6 3 5, 6 3 0, 6 1 0, 6 1 5, 6 3 5))'
    geom_3_ = drop_axis(geom_3, 'z')
    assert geom_3_.wkt == 'POLYGON ((6 3, 6 3, 6 1, 6 1, 6 3))'
    geom_3_arr = drop_axis(geom_3, 'z', as_array=True)
    assert np.array_equal(geom_3_arr, np.array([[6., 3.], [6., 3.], [6., 1.], [6., 1.], [6., 3.]]))

    # 4. MultiLineString (Uniform lengths -> single numpy array)
    ls1 = shapely.geometry.LineString([[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    ls2 = shapely.geometry.LineString([[2, 3, 4], [1, 2, 3], [3, 4, 5]])
    geom_4 = shapely.geometry.MultiLineString([ls1, ls2])
    assert geom_4.wkt == 'MULTILINESTRING Z ((1 2 3, 2 3 4, 3 4 5), (2 3 4, 1 2 3, 3 4 5))'
    geom_4_ = drop_axis(geom_4, 'z')
    assert geom_4_.wkt == 'MULTILINESTRING ((1 2, 2 3, 3 4), (2 3, 1 2, 3 4))'
    geom_4_arr = drop_axis(geom_4, 'z', as_array=True)
    assert np.array_equal(
        geom_4_arr,
        np.array([[[1., 2.], [2., 3.], [3., 4.]], [[2., 3.], [1., 2.], [3., 4.]]])
    )

    # 5. Multi-geometry with variable lengths (Triggers `except ValueError` in as_array)
    ls_short = shapely.geometry.LineString([[1, 2, 3], [2, 3, 4]])
    ls_long = shapely.geometry.LineString([[2, 3, 4], [1, 2, 3], [3, 4, 5]])
    geom_var = shapely.geometry.MultiLineString([ls_short, ls_long])
    geom_var_arr = drop_axis(geom_var, 'z', as_array=True)
    assert isinstance(geom_var_arr, list)
    assert len(geom_var_arr) == 2

    # 6. Case-insensitivity ('Z' vs 'z')
    assert drop_axis(geom_1, 'Z').wkt == 'POINT (1 2)'
    assert drop_axis(geom_1, 'X').wkt == 'POINT (2 3)'

    # 7. Invalid axis exception
    with pytest.raises(ValueError, match="`axis` must be 'x', 'y' or 'z'"):
        drop_axis(geom_1, 'invalid_axis')


def test_project_point_to_line():
    pt = shapely.geometry.Point([399297, 655095, 43])

    # 1. Coincident endpoints (u == v)
    ls_degen = shapely.geometry.LineString([[399299, 655091, 42], [399299, 655091, 42]])
    pt_, pt_proj = project_point_to_line(point=pt, line=ls_degen)
    assert pt_proj.wkt == 'POINT Z (399299 655091 42)'
    assert pt_.wkt == 'POINT Z (399297 655095 43)'

    # 2. Segment-level zero length (u == v inside a multi-segment line)
    # Line length > 0, but segment 1 has identical vertices: (0,0,0) -> (0,0,0)
    pt_dup = shapely.geometry.Point([1, 1, 0])
    ls_dup_seg = shapely.geometry.LineString([[0, 0, 0], [0, 0, 0], [10, 0, 0]])
    assert ls_dup_seg.length > 0  # Bypasses the early line.length == 0 check
    _, pt_proj_dup = project_point_to_line(point=pt_dup, line=ls_dup_seg)
    assert pt_proj_dup.wkt == 'POINT Z (1 0 0)'  # Reaches and covers `if np.array_equal(u, v):`

    # 3. Standard 3D Projection
    ls_ = shapely.geometry.LineString([
        [399299, 655091, 42], [399295, 655099, 42], [399295, 655107, 42]
    ])
    _, pt_proj = project_point_to_line(point=pt, line=ls_)
    assert pt_proj.wkt == 'POINT Z (399297.9411764706 655095.2352941176 42)'

    # 4. Dimension dropping with lowercase and uppercase ('z' / 'Z')
    pt_dropped, pt_proj_2d = project_point_to_line(point=pt, line=ls_, drop_dimension='z')
    assert pt_dropped.wkt == 'POINT (399297 655095)'
    assert pt_proj_2d.wkt == 'POINT (399297.9411764706 655095.2352941176)'

    _, pt_proj_uppercase = project_point_to_line(point=pt, line=ls_, drop_dimension='Z')
    assert pt_proj_uppercase.wkt == 'POINT (399297.9411764706 655095.2352941176)'

    # 5. Line becoming degenerate strictly after axis dropping
    ls_vert = shapely.geometry.LineString([[10, 10, 0], [10, 10, 5]])
    _, pt_proj_vert = project_point_to_line(point=pt, line=ls_vert, drop_dimension='z')
    assert pt_proj_vert.wkt == 'POINT (10 10)'

    # 6. Invalid drop_dimension assertion check
    with pytest.raises(AssertionError):
        project_point_to_line(point=pt, line=ls_, drop_dimension='invalid')


if __name__ == '__main__':
    pytest.main()
