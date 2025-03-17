"""
Tests the :mod:`~pyhelpers.geom.shapes` submodule.
"""

import pytest

from pyhelpers.geom.shapes import *


def test_get_midpoint():
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
    pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)

    geometric_midpoint = get_geometric_midpoint(pt_1, pt_2)
    assert geometric_midpoint == (1.5169, 52.6309)

    geometric_midpoint = get_geometric_midpoint(pt_1, pt_2, as_geom=True)
    assert geometric_midpoint.wkt == 'POINT (1.5169 52.6309)'


def test_get_geometric_midpoint_calc():
    pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)

    midpoint = (1.5168977420748175, 52.630902845583094)

    geometric_midpoint = get_geometric_midpoint_calc(pt_1, pt_2)
    assert np.array_equal(np.round(geometric_midpoint, 8), np.round(midpoint, 8))

    geometric_midpoint = get_geometric_midpoint_calc(pt_1, pt_2, as_geom=True)
    assert isinstance(geometric_midpoint, shapely.geometry.Point)


@pytest.mark.parametrize('as_geom', [False, True])
def test_get_rectangle_centroid(as_geom):
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
    func_args = {'ctr_x': 1, 'ctr_y': 1, 'side_length': 2, 'annotation': True, 'ret_vertices': True}

    sketch_vtx = sketch_square(rotation_theta=0, **func_args)
    assert np.array_equal(
        np.round(sketch_vtx), np.array([[0., 0.], [0., 2.], [2., 2.], [2., 0.], [0., 0.]]))

    sketch_vtx = sketch_square(rotation_theta=75, **func_args)
    assert np.array_equal(sketch_vtx[0], sketch_vtx[-1])


if __name__ == '__main__':
    pytest.main()
