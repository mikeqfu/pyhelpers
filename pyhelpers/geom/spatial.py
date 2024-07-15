"""
Geometric data computation.
"""

import copy
import functools
import os
import typing

import numpy as np
import shapely.geometry
import shapely.ops

from .trans import get_coordinates_as_array, transform_point_type
from .._cache import _check_dependency


# Distance

def calc_distance_on_unit_sphere(pt1, pt2, unit='mile', precision=None):
    """
    Calculate the distance between two points on a unit sphere.

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
    arc_length = np.arccos(cosine) * earth_radius

    if precision:
        arc_length = np.round(arc_length, precision)

    # To multiply arc by the radius of the earth in a set of units to get length.
    return arc_length


def calc_hypotenuse_distance(pt1, pt2):
    """
    Calculate the hypotenuse distance between two points.

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
        >>> pt_1_, pt_2_ = map(Point, (pt_1, pt_2))
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
    Find the closest point in a sequence of reference points to a given point.

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
    Find the closest points from a list of reference points to a set of query points.

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
        >>> closest_to_each = find_closest_points(pts=cities, ref_pts=ref_cities, k=1, as_geom=True)
        >>> closest_to_each.wkt
        'MULTIPOINT (-2.2451148 53.4794892, -2.2451148 53.4794892, -1.5437941 53.7974185)'
        >>> _, idx = find_closest_points(pts=cities, ref_pts=ref_cities, k=1, ret_idx=True)
        >>> idx
        array([2, 2, 3], dtype=int64)
        >>> _, _, dist = find_closest_points(cities, ref_cities, k=1, ret_idx=True, ret_dist=True)
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

    ckdtree = _check_dependency(name='scipy.spatial')

    pts_, ref_pts_ = map(functools.partial(get_coordinates_as_array, unique=unique), [pts, ref_pts])

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
    Find the shortest path through a sequence of points.

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
        >>> # save_figure(fig, "docs/source/_images/geom-find_shortest_path-demo.svg", verbose=True)
        >>> # save_figure(fig, "docs/source/_images/geom-find_shortest_path-demo.pdf", verbose=True)

    .. figure:: ../_images/geom-find_shortest_path-demo.*
        :name: geom-find_shortest_path-demo
        :align: center
        :width: 85%

        An example of sorting a sequence of points given the shortest path.
    """

    if len(points_sequence) <= 2:
        shortest_path = points_sequence

    else:
        nx = _check_dependency(name='networkx')
        sklearn_neighbors = _check_dependency(name='sklearn.neighbors')

        nn_clf = sklearn_neighbors.NearestNeighbors(n_neighbors=2, **kwargs).fit(points_sequence)
        kn_g = nn_clf.kneighbors_graph()

        nx_g = nx.from_scipy_sparse_array(kn_g)

        possible_paths = [list(nx.dfs_preorder_nodes(nx_g, i)) for i in range(len(points_sequence))]

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


# Locating

def get_midpoint(x1, y1, x2, y2, as_geom=False):
    """
    Get the midpoint between two points (applicable for vectorised computation).

    :param x1: Longitude(s) or easting(s) of a point (an array of points).
    :type x1: float | int | typing.Iterable | numpy.ndarray
    :param y1: Latitude(s) or northing(s) of a point (an array of points).
    :type y1: float | int | typing.Iterable | numpy.ndarray
    :param x2: Longitude(s) or easting(s) of another point (another array of points).
    :type x2: float | int | typing.Iterable | numpy.ndarray
    :param y2: Latitude(s) or northing(s) of another point (another array of points).
    :type y2: float | int | typing.Iterable | numpy.ndarray
    :param as_geom: Whether to return `shapely.geometry.Point`_; defaults to ``False``.
    :type as_geom: bool
    :return: The midpoint between ``(x1, y1)`` and ``(x2, y2)``
        (or midpoints between two sequences of points).
    :rtype: numpy.ndarray | shapely.geometry.Point | shapely.geometry.MultiPoint

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import get_midpoint
        >>> x_1, y_1 = 1.5429, 52.6347
        >>> x_2, y_2 = 1.4909, 52.6271
        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2)
        >>> midpt
        array([ 1.5169, 52.6309])
        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2, as_geom=True)
        >>> midpt.wkt
        'POINT (1.5169 52.6309)'
        >>> x_1, y_1 = (1.5429, 1.4909), (52.6347, 52.6271)
        >>> x_2, y_2 = [2.5429, 2.4909], [53.6347, 53.6271]
        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2)
        >>> midpt
        array([[ 2.0429, 53.1347],
               [ 1.9909, 53.1271]])
        >>> midpt = get_midpoint(x_1, y_1, x_2, y_2, as_geom=True)
        >>> midpt.wkt
        'MULTIPOINT (2.0429 53.1347, 1.9909 53.1271)'
    """

    x1_, y1_, x2_, y2_ = map(np.array, (x1, y1, x2, y2))

    mid_pts = (x1_ + x2_) / 2, (y1_ + y2_) / 2

    if as_geom:
        if all(isinstance(x, np.ndarray) for x in mid_pts):
            midpoint = shapely.geometry.MultiPoint(
                [shapely.geometry.Point(x_, y_)
                 for x_, y_ in zip(list(mid_pts[0]), list(mid_pts[1]))]
            )
        else:
            midpoint = shapely.geometry.Point(mid_pts)

    else:
        midpoint = np.array(mid_pts).T

    return midpoint


def get_geometric_midpoint(pt1, pt2, as_geom=False):
    """
    Get the midpoint between two points.

    :param pt1: One point.
    :type pt1: shapely.geometry.Point | list | tuple | numpy.ndarray
    :param pt2: Another point represented similarly to ``pt1``.
    :type pt2: shapely.geometry.Point | list | tuple | numpy.ndarray
    :param as_geom: Whether to return `shapely.geometry.Point`_; defaults to ``False``.
    :type as_geom: bool
    :return: The midpoint between ``pt1`` and ``pt2``.
    :rtype: tuple | shapely.geometry.Point | None

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import get_geometric_midpoint
        >>> pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)
        >>> geometric_midpoint = get_geometric_midpoint(pt_1, pt_2)
        >>> geometric_midpoint
        (1.5169, 52.6309)
        >>> geometric_midpoint = get_geometric_midpoint(pt_1, pt_2, as_geom=True)
        >>> geometric_midpoint.wkt
        'POINT (1.5169 52.6309)'

    .. seealso::

        - Examples for the function :func:`~pyhelpers.geom.get_geometric_midpoint_calc`.
    """

    pt_x_, pt_y_ = transform_point_type(pt1, pt2, as_geom=True)

    midpoint = (pt_x_.x + pt_y_.x) / 2, (pt_x_.y + pt_y_.y) / 2

    if as_geom:
        midpoint = shapely.geometry.Point(midpoint)

    return midpoint


def get_geometric_midpoint_calc(pt1, pt2, as_geom=False):
    """
    Get the midpoint between two points by pure calculation.

    See also
    [`GEOM-GGMC-1 <https://code.activestate.com/recipes/577713/>`_]
    and
    [`GEOM-GGMC-2 <https://www.movable-type.co.uk/scripts/latlong.html>`_].

    :param pt1: One point.
    :type pt1: shapely.geometry.Point | list | tuple | numpy.ndarray
    :param pt2: Another point represented similarly to ``pt1``.
    :type pt2: shapely.geometry.Point | list | tuple | numpy.ndarray
    :param as_geom: Whether to return `shapely.geometry.Point`_; defaults to ``False``.
    :type as_geom: bool
    :return: The midpoint between ``pt1`` and ``pt2``.
    :rtype: tuple | shapely.geometry.Point | None

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import get_geometric_midpoint_calc
        >>> pt_1, pt_2 = (1.5429, 52.6347), (1.4909, 52.6271)
        >>> geometric_midpoint = get_geometric_midpoint_calc(pt_1, pt_2)
        >>> geometric_midpoint
        (1.5168977420748175, 52.630902845583094)
        >>> geometric_midpoint = get_geometric_midpoint_calc(pt_1, pt_2, as_geom=True)
        >>> geometric_midpoint.wkt
        'POINT (1.5168977420748175 52.630902845583094)'

    .. seealso::

        - Examples for the function :func:`~pyhelpers.geom.get_geometric_midpoint`.
    """

    pt_x_, pt_y_ = transform_point_type(pt1, pt2, as_geom=True)

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
    Get coordinates of the centroid of a rectangle.

    :param rectangle: Variable/object representing a rectangle.
    :type rectangle: list | tuple | numpy.ndarray | shapely.geometry.Polygon |
        shapely.geometry.MultiPolygon
    :param as_geom: Whether to return a `shapely.geometry.Point`_ object; defaults to ``False``.
    :type as_geom: bool
    :return: Coordinates of the centroid of the rectangle.
    :rtype: numpy.ndarray | shapely.geometry.Point

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers.geom import get_rectangle_centroid
        >>> from shapely.geometry import Polygon
        >>> import numpy
        >>> coords_1 = [[0, 0], [0, 1], [1, 1], [1, 0]]
        >>> rect_obj = Polygon(coords_1)
        >>> rect_cen = get_rectangle_centroid(rectangle=rect_obj)
        >>> rect_cen
        array([0.5, 0.5])
        >>> rect_obj = numpy.array(coords_1)
        >>> rect_cen = get_rectangle_centroid(rectangle=rect_obj)
        >>> rect_cen
        array([0.5, 0.5])
        >>> rect_cen = get_rectangle_centroid(rectangle=rect_obj, as_geom=True)
        >>> type(rect_cen)
        shapely.geometry.point.Point
        >>> rect_cen.wkt
        'POINT (0.5 0.5)'
        >>> coords_2 = [[(0, 0), (0, 1), (1, 1), (1, 0)], [(1, 1), (1, 2), (2, 2), (2, 1)]]
        >>> rect_cen = get_rectangle_centroid(rectangle=coords_2)
        >>> rect_cen
        array([1., 1.])
    """

    if isinstance(rectangle, typing.Iterable):  # (np.ndarray, list, tuple)
        try:
            rectangle_ = shapely.geometry.Polygon(rectangle)
        except (TypeError, ValueError, AttributeError):
            rectangle_ = shapely.geometry.MultiPolygon(shapely.geometry.Polygon(x) for x in rectangle)
            rectangle_ = rectangle_.convex_hull
    else:
        rectangle_ = copy.copy(rectangle)

    rec_centroid = rectangle_.centroid

    if not as_geom:
        rec_centroid = np.array(rec_centroid.coords[0])

    return rec_centroid


def get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta=0):
    """
    Get the four vertices of a square given its centre and side length.

    See also [`GEOM-GSV-1 <https://stackoverflow.com/questions/22361324/>`_].

    :param ctr_x: X-coordinate of the square's centre.
    :type ctr_x: int | float
    :param ctr_y: Y-coordinate of the square's centre.
    :type ctr_y: int | float
    :param side_length: Side length of the square.
    :type side_length: int | float
    :param rotation_theta: Rotation angle (in degrees) to rotate the square anticlockwise;
        defaults to ``0``.
    :type rotation_theta: int | float
    :return: Vertices of the square as an array([Lower left, Upper left, Upper right, Lower right]).
    :rtype: numpy.ndarray

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

    def _rot_mat(theta):
        return np.array([[np.sin(theta), np.cos(theta)], [-np.cos(theta), np.sin(theta)]])

    rotation_matrix = _rot_mat(np.deg2rad(rotation_theta))

    sides = np.ones(2) * side_length

    vertices_ = [
        np.array([ctr_x, ctr_y]) + functools.reduce(
            np.dot, [rotation_matrix, _rot_mat(-0.5 * np.pi * x), sides / 2])
        for x in range(4)]

    vertices = np.array(vertices_, dtype=np.float64)

    return vertices


def get_square_vertices_calc(ctr_x, ctr_y, side_length, rotation_theta=0):
    """
    Get the four vertices of a square given its centre and side length (by elementary calculation).

    See also [`GEOM-GSVC-1 <https://math.stackexchange.com/questions/1490115>`_].

    :param ctr_x: X-coordinate of the square's centre.
    :type ctr_x: int | float
    :param ctr_y: Y-coordinate of the square's centre.
    :type ctr_y: int | float
    :param side_length: Side length of the square.
    :type side_length: int | float
    :param rotation_theta: Rotation angle (in degrees) to rotate the square anticlockwise;
        defaults to ``0``.
    :type rotation_theta: int | float
    :return: Vertices of the square as an array([Lower left, Upper left, Upper right, Lower right]).
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

    .. seealso::

        - Examples for the function :func:`~pyhelpers.geom.get_square_vertices`.
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
