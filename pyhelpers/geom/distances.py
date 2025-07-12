"""
Utilities for distance-related calculations and proximity operations.
"""

import copy
import functools
import os
import typing

import numpy as np
import shapely.geometry
import shapely.ops

from .transforms import get_coordinates_as_array, transform_point_type
from .._cache import _check_dependencies


def calc_distance_on_unit_sphere(pt1, pt2, unit='mile', precision=None):
    """
    Calculates the distance between two points on a unit sphere.

    This function computes the spherical distance between two points ``pt1`` and ``pt2``.
    The distance can be returned in either miles (``'mile'``) or kilometers (``'km'``) based on
    the ``unit`` parameter.

    :param pt1: One point.
    :type pt1: shapely.geometry.Point | tuple | numpy.ndarray
    :param pt2: Another point.
    :type pt2: shapely.geometry.Point | tuple | numpy.ndarray
    :param unit: Unit of distance for output; options include ``'mile'`` (default) and ``'km'``.
    :type unit: str
    :param precision: Number of decimal places for the calculated result;
        defaults to ``None`` (no rounding).
    :type precision: int | None
    :return: Distance between ``pt1`` and ``pt2`` in miles or kilometers
        (relative to the earth's radius).
    :rtype: float | None

    **Examples**::

        >>> from pyhelpers.geom import calc_distance_on_unit_sphere
        >>> from pyhelpers._cache import example_dataframe
        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> london, birmingham = example_df.loc[['London', 'Birmingham']].values
        >>> london
        array([-0.1276474, 51.5073219])
        >>> birmingham
        array([-1.9026911, 52.4796992])
        >>> arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham)
        >>> arc_len_in_miles  # in miles
        101.10431101941569
        >>> arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham, precision=4)
        >>> arc_len_in_miles
        101.1043

    .. note::

        This function is modified from the original code available at
        [`GEOM-CDOUS-1 <https://www.johndcook.com/blog/python_longitude_latitude/>`_].
        It assumes the earth is perfectly spherical and returns the distance based on each
        point's longitude and latitude.
    """

    earth_radius = 3960.0 if unit == "mile" else 6371.0

    # Convert latitude and longitude to spherical coordinates in radians.
    degrees_to_radians = np.pi / 180.0

    if not all(isinstance(x, shapely.geometry.Point) for x in (pt1, pt2)):
        try:
            pt1_, pt2_ = shapely.geometry.Point(pt1), shapely.geometry.Point(pt2)
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
    arc_length = np.arccos(cosine) * earth_radius

    if precision:
        arc_length = np.round(arc_length, precision)

    # To multiply arc by the radius of the earth in a set of units to get length.
    return arc_length


def calc_hypotenuse_distance(pt1, pt2):
    """
    Calculates the hypotenuse distance between two points.

    See also [`GEOM-CHD-1 <https://numpy.org/doc/stable/reference/generated/numpy.hypot.html>`_].

    :param pt1: One point.
    :type pt1: shapely.geometry.Point | list | tuple | numpy.ndarray
    :param pt2: Another point.
    :type pt2: shapely.geometry.Point | list | tuple | numpy.ndarray
    :return: Hypotenuse distance between ``pt1`` and ``pt2``.
    :rtype: float

    .. note::

        - The hypotenuse distance is the straight-line distance between `pt1` and `pt2`.
        - Calculated using the formula: ``sqrt((x2 - x1)^2 + (y2 - y1)^2)``
        - Equivalent to ``numpy.hypot(x, y)`` which computes ``sqrt(x*x + y*y)``.

    **Examples**::

        >>> from pyhelpers.geom import calc_hypotenuse_distance
        >>> from shapely.geometry import Point
        >>> pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)
        >>> hypot_distance = calc_hypotenuse_distance(pt_1, pt_2)
        >>> hypot_distance
        0.05255244999046248
        >>> pt_1_, pt_2_ = map(lambda p: Point(p), (pt_1, pt_2))
        >>> pt_1_.wkt
        'POINT (1.5429 52.6347)'
        >>> pt_2_.wkt
        'POINT (1.4909 52.6271)'
        >>> hypot_distance = calc_hypotenuse_distance(pt_1_, pt_2_)
        >>> hypot_distance
        0.05255244999046248
    """

    pt1_, pt2_ = transform_point_type(pt1, pt2, as_geom=False)

    x_diff, y_diff = pt1_[0] - pt2_[0], pt1_[1] - pt2_[1]

    hypot_dist = np.hypot(x_diff, y_diff)

    return hypot_dist


def find_closest_point(pt, ref_pts, as_geom=True):
    """
    Finds the closest point in a sequence of reference points to a given point.

    This function calculates and returns the point closest to ``pt`` from a sequence
    of reference points ``ref_pts``. The closest point can be returned either as a
    Shapely Point geometry (`shapely.geometry.Point`_) or as a `numpy.ndarray`_.

    :param pt: Point for which the closest point is to be found.
    :type pt: tuple | list | shapely.geometry.Point
    :param ref_pts: Sequence of reference points to search for the closest point.
    :type ref_pts: typing.Iterable | numpy.ndarray | list | tuple |
        shapely.geometry.base.BaseGeometry
    :param as_geom: Whether to return the closest point as a `shapely.geometry.Point`_;
        defaults to ``True``.
    :type as_geom: bool
    :return: Closest point to ``pt`` from ``ref_pts``.
    :rtype: shapely.geometry.Point | numpy.ndarray

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points
    .. _`numpy.ndarray`: https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html

    **Examples**::

        >>> from pyhelpers.geom import find_closest_point
        >>> from pyhelpers._cache import example_dataframe
        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> # Find the city closest to London
        >>> london = example_df.loc['London'].values
        >>> ref_cities = example_df.loc['Birmingham':, :].values
        >>> closest_to_london = find_closest_point(pt=london, ref_pts=ref_cities)
        >>> closest_to_london.wkt  # Birmingham
        'POINT (-1.9026911 52.4796992)'
        >>> # Find the city closest to Leeds
        >>> leeds = example_df.loc['Leeds'].values
        >>> ref_cities = example_df.loc[:'Manchester', :].values
        >>> closest_to_leeds = find_closest_point(pt=leeds, ref_pts=ref_cities)
        >>> closest_to_leeds.wkt  # Manchester
        'POINT (-2.2451148 53.4794892)'
        >>> closest_to_leeds = find_closest_point(pt=leeds, ref_pts=ref_cities, as_geom=False)
        >>> closest_to_leeds  # Manchester
        array([-2.2451148, 53.4794892])
    """

    if isinstance(pt, shapely.geometry.Point):
        pt_ = pt
    else:
        assert len(pt) <= 3
        pt_ = shapely.geometry.Point(pt)

    if isinstance(ref_pts, shapely.geometry.MultiPoint):
        ref_pts_ = ref_pts.geoms
    elif isinstance(ref_pts, typing.Iterable):
        ref_pts_ = (
            shapely.geometry.Point(x)
            for x in get_coordinates_as_array(geom_obj=ref_pts, unique=True))
    else:
        ref_pts_ = shapely.geometry.MultiPoint([ref_pts]).geoms

    # Find the min value using the distance function with coord parameter
    closest_point = min(ref_pts_, key=functools.partial(shapely.geometry.Point.distance, pt_))

    if not as_geom:
        closest_point = np.array(closest_point.coords)

        if closest_point.shape[0] == 1:
            closest_point = closest_point[0]

    return closest_point


def find_closest_points(pts, ref_pts, k=1, unique=False, as_geom=False, ret_idx=False,
                        ret_dist=False, **kwargs):
    """
    Finds the closest points from a list of reference points to a set of query points.

    This function computes the closest points from a list of reference points ``ref_pts``
    to a set of query points ``pts``. Various options are available for customisation,
    such as returning multiple nearest neighbours (``k``), removing duplicated points,
    returning points as Shapely Points (`shapely.geometry.Point`_), returning indices
    of the closest points, and returning distances between ``pts`` and the closest
    points in ``ref_pts``.

    See also [`GEOM-FCPB-1 <https://gis.stackexchange.com/questions/222315>`_].

    :param pts: Array of query points with shape (n, 2).
    :type pts: numpy.ndarray | list | tuple | typing.Iterable | shapely.geometry.base.BaseGeometry
    :param ref_pts: Array of reference points with shape (m, 2).
    :type ref_pts: numpy.ndarray | list | tuple | shapely.geometry.base.BaseGeometry
    :param k: Number of closest neighbours to find; defaults to 1.
    :type k: int | list
    :param unique: Whether to remove duplicated points from the results; defaults to False.
    :type unique: bool
    :param as_geom: Whether to return the closest points as `shapely.geometry.Point`_;
        defaults to ``False``.
    :type as_geom: bool
    :param ret_idx: Whether to return indices of the closest points in ``ref_pts``;
        defaults to ``False``.
    :type ret_idx: bool
    :param ret_dist: Whether to return distances between ``pts`` and
        the closest points in ``ref_pts``; defaults to ``False``.
    :type ret_dist: bool
    :param kwargs: [Optional] Additional parameters for the class `scipy.spatial.cKDTree`_.
    :return: Closest points among ``ref_pts`` to each point in ``pts``.
    :rtype: numpy.ndarray | shapely.geometry.MultiPoint

    .. _`shapely.geometry.Point`:
        https://shapely.readthedocs.io/en/latest/manual.html#points
    .. _`scipy.spatial.cKDTree`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.html

    **Examples**::

        >>> from pyhelpers.geom import find_closest_points
        >>> from pyhelpers._cache import example_dataframe
        >>> from shapely.geometry import LineString, MultiPoint
        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> cities = [[-2.9916800, 53.4071991],  # Liverpool
        ...           [-4.2488787, 55.8609825],  # Glasgow
        ...           [-1.6131572, 54.9738474]]  # Newcastle
        >>> ref_cities = example_df.to_numpy()
        >>> closest_to_each = find_closest_points(pts=cities, ref_pts=ref_cities, k=1)
        >>> closest_to_each  # Liverpool: Manchester; Glasgow: Manchester; Newcastle: Leeds
        array([[-2.2451148, 53.4794892],
               [-2.2451148, 53.4794892],
               [-1.5437941, 53.7974185]])
        >>> closest_to_each = find_closest_points(
        ...     pts=cities, ref_pts=ref_cities, k=1, as_geom=True)
        >>> closest_to_each.wkt
        'MULTIPOINT (-2.2451148 53.4794892, -2.2451148 53.4794892, -1.5437941 53.7974185)'
        >>> _, idx = find_closest_points(pts=cities, ref_pts=ref_cities, k=1, ret_idx=True)
        >>> idx
        array([2, 2, 3], dtype=int64)
        >>> _, _, dist = find_closest_points(
        ...     cities, ref_cities, k=1, ret_idx=True, ret_dist=True)
        >>> dist
        array([0.75005697, 3.11232712, 1.17847198])
        >>> cities_geoms_1 = LineString(cities)
        >>> closest_to_each = find_closest_points(pts=cities_geoms_1, ref_pts=ref_cities, k=1)
        >>> closest_to_each
        array([[-2.2451148, 53.4794892],
               [-2.2451148, 53.4794892],
               [-1.5437941, 53.7974185]])
        >>> cities_geoms_2 = MultiPoint(cities)
        >>> closest_to_each = find_closest_points(cities_geoms_2, ref_cities, k=1, as_geom=True)
        >>> closest_to_each.wkt
        'MULTIPOINT (-2.2451148 53.4794892, -2.2451148 53.4794892, -1.5437941 53.7974185)'
    """

    ckdtree = _check_dependencies('scipy.spatial')

    pts_, ref_pts_ = map(
        functools.partial(get_coordinates_as_array, unique=unique), [pts, ref_pts])

    ref_ckd_tree = ckdtree.cKDTree(ref_pts_, **kwargs)
    n_workers = os.cpu_count() - 1

    # returns (distance, index)
    distances, indices = ref_ckd_tree.query(x=pts_, k=k, workers=n_workers)

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


def find_shortest_path(points_sequence, ret_dist=False, as_geom=False, **kwargs):
    """
    Finds the shortest path through a sequence of points.

    :param points_sequence: Sequence of points
    :type points_sequence: numpy.ndarray | list | typing.Iterable
    :param ret_dist: Whether to return the distance of the shortest path; defaults to ``False``.
    :type ret_dist: bool
    :param as_geom: Whether to return the sorted path as a line geometry object;
        defaults to ``False``.
    :type as_geom: bool
    :param kwargs: [Optional] Additional parameters of the class
        `sklearn.neighbors.NearestNeighbors`_.
    :return: a sequence of sorted points given two-nearest neighbors
    :rtype: numpy.ndarray | shapely.geometry.LineString | tuple

    .. _`sklearn.neighbors.NearestNeighbors`:
        https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html

    **Examples**::

        >>> from pyhelpers.geom import find_shortest_path
        >>> from pyhelpers._cache import example_dataframe
        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> example_df_ = example_df.sample(frac=1, random_state=1)
        >>> example_df_
                    Longitude   Latitude
        City
        Leeds       -1.543794  53.797418
        Manchester  -2.245115  53.479489
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        >>> cities = example_df_.to_numpy()
        >>> cities
        array([[-1.5437941, 53.7974185],
               [-2.2451148, 53.4794892],
               [-0.1276474, 51.5073219],
               [-1.9026911, 52.4796992]])
        >>> cities_sorted = find_shortest_path(points_sequence=cities)
        >>> cities_sorted
        array([[-1.5437941, 53.7974185],
               [-2.2451148, 53.4794892],
               [-1.9026911, 52.4796992],
               [-0.1276474, 51.5073219]])

    This example is illustrated below (see :numref:`geom-find_shortest_path-demo`)::

        >>> import matplotlib.pyplot as plt
        >>> import matplotlib.gridspec as mgs
        >>> from pyhelpers.settings import mpl_preferences
        >>> mpl_preferences(backend='TkAgg')
        >>> fig = plt.figure(figsize=(7, 5))
        >>> gs = mgs.GridSpec(1, 2, figure=fig)
        >>> ax1 = fig.add_subplot(gs[:, 0])
        >>> ax1.plot(cities[:, 0], cities[:, 1], label='original')
        >>> for city, i, lonlat in zip(example_df_.index, range(len(cities)), cities):
        ...     ax1.scatter(lonlat[0], lonlat[1])
        ...     ax1.annotate(city + f' ({i})', xy=lonlat + 0.05)
        >>> ax1.legend(loc=3)
        >>> ax2 = fig.add_subplot(gs[:, 1])
        >>> ax2.plot(cities_sorted[:, 0], cities_sorted[:, 1], label='sorted', color='orange')
        >>> for city, i, lonlat in zip(example_df.index[::-1], range(len(cities)), cities_sorted):
        ...     ax2.scatter(lonlat[0], lonlat[1])
        ...     ax2.annotate(city + f' ({i})', xy=lonlat + 0.05)
        >>> ax2.legend(loc=3)
        >>> fig.tight_layout()
        >>> fig.show()
        >>> # from pyhelpers.store import save_figure
        >>> # path_to_fig_ = "docs/source/_images/geom-find_shortest_path-demo"
        >>> # save_figure(fig, f"{path_to_fig_}.svg", verbose=True)
        >>> # save_figure(fig, f"{path_to_fig_}.pdf", verbose=True)

    .. figure:: ../_images/geom-find_shortest_path-demo.*
        :name: geom-find_shortest_path-demo
        :align: center
        :width: 85%

        An example of sorting a sequence of points given the shortest path.
    """

    if len(points_sequence) <= 2:
        shortest_path = points_sequence

    else:
        nx, sklearn_neighbors = _check_dependencies('networkx', 'sklearn.neighbors')

        nn_clf = sklearn_neighbors.NearestNeighbors(n_neighbors=2, **kwargs).fit(points_sequence)
        kn_g = nn_clf.kneighbors_graph()

        nx_g = nx.from_scipy_sparse_array(kn_g)

        possible_paths = [
            list(nx.dfs_preorder_nodes(nx_g, i)) for i in range(len(points_sequence))]

        min_dist, idx = np.inf, 0

        for i in range(len(points_sequence)):
            nodes_order = possible_paths[i]  # order of nodes
            ordered_nodes = points_sequence[nodes_order]  # ordered nodes

            # cost = the sum of Euclidean distances between the i-th and (i+1)-th points
            dist = (((ordered_nodes[:-1] - ordered_nodes[1:]) ** 2).sum(axis=1)).sum()
            if dist <= min_dist:
                min_dist = dist
                idx = i

        shortest_path = points_sequence[possible_paths[idx]]

        if as_geom:
            shortest_path = shapely.geometry.LineString(shortest_path)

        if ret_dist:
            shortest_path = shortest_path, min_dist

    return shortest_path
