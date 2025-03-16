"""
Geometric properties (e.g. midpoints, centroids and vertices) and shape sketching.
"""

import copy
import functools
import typing

import numpy as np
import shapely.geometry
import shapely.ops

from .._cache import _check_dependency, _transform_point_type


def get_midpoint(x1, y1, x2, y2, as_geom=False):
    """
    Gets the midpoint between two points (applicable for vectorised computation).

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
    Gets the midpoint between two points.

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

    pt_x_, pt_y_ = _transform_point_type(pt1, pt2, as_geom=True)

    midpoint = (pt_x_.x + pt_y_.x) / 2, (pt_x_.y + pt_y_.y) / 2

    if as_geom:
        midpoint = shapely.geometry.Point(midpoint)

    return midpoint


def get_geometric_midpoint_calc(pt1, pt2, as_geom=False):
    """
    Gets the midpoint between two points by pure calculation.

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

    pt_x_, pt_y_ = _transform_point_type(pt1, pt2, as_geom=True)

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
    Gets coordinates of the centroid of a rectangle.

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
            rectangle_ = shapely.geometry.MultiPolygon(
                shapely.geometry.Polygon(x) for x in rectangle)
            rectangle_ = rectangle_.convex_hull
    else:
        rectangle_ = copy.copy(rectangle)

    rec_centroid = rectangle_.centroid

    if not as_geom:
        rec_centroid = np.array(rec_centroid.coords[0])

    return rec_centroid


def get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta=0):
    """
    Gets the four vertices of a square given its centre and side length.

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
    Gets the four vertices of a square given its centre and side length (by elementary calculation).

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


def _sketch_square_annotate(x, y, fontsize, margin=0.025, precision=2, **kwargs):
    """
    Generates annotation parameters for annotating a point on a square plot.

    This function constructs annotation parameters for annotating a point ``(x, y)``
    on a square plot. The annotation text format is defined by the precision parameter,
    with a default of ``2`` decimal places.

    :param x: X-coordinate of the point to annotate.
    :type x: float
    :param y: Y-coordinate of the point to annotate.
    :type y: float
    :param fontsize: Font size of the annotation text.
    :type fontsize: int
    :param margin: Margin distance from the annotated point to the annotation text;
        defaults to ``0.025``.
    :type margin: float
    :param precision: Number of decimal places to display in the annotation text; defaults to ``2``.
    :type precision: int
    :param kwargs: [Optional] Additional parameters for annotation customisation.
    :return: Updated ``kwargs`` dictionary containing annotation parameters.
    :rtype: dict
    """

    p = '{' + '0:.{}f'.format(precision) + '}'
    text = f'({p}, {p})'
    args = {
        'text': text.format(x, y),
        'xy': (x, y),
        'fontsize': fontsize,
        'xytext': (x + margin, y + margin),
    }

    kwargs.update(args)

    return kwargs


def sketch_square(ctr_x, ctr_y, side_length, rotation_theta=0, annotation=False, annot_font_size=12,
                  fig_size=(6.4, 4.8), ret_vertices=False, **kwargs):
    """
    Sketches a square on a plot given its centre coordinates, side length and rotation angle.

    This function plots a square with its centre at coordinates ``(ctr_x, ctr_y)``,
    side length ``side_length``, and rotated by `rotation_theta` degrees (anticlockwise).

    :param ctr_x: X coordinate of the centre of the square.
    :type ctr_x: int | float
    :param ctr_y: Y coordinate of the centre of the square.
    :type ctr_y: int | float
    :param side_length: Side length of the square.
    :type side_length: int | float
    :param rotation_theta: Rotation angle of the square in degrees; defaults to ``0``.
    :type rotation_theta: int | float
    :param annotation: Whether to annotate vertices of the square; defaults to ``True``.
    :type annotation: bool
    :param annot_font_size: Font size of annotation texts; defaults to ``12``.
    :type annot_font_size: int
    :param fig_size: Size of the figure; defaults to ``(6.4, 4.8)``.
    :type fig_size: tuple | list
    :param ret_vertices: Whether to return the vertices of the square; defaults to ``False``.
    :type ret_vertices: bool
    :param kwargs: Additional parameters for ``matplotlib.axes.Axes.annotate``.
    :return: Vertices of the square as an array([ll, ul, ur, lr]).
    :rtype: numpy.ndarray

    .. _`matplotlib.axes.Axes.annotate`:
        https://matplotlib.org/3.2.1/api/_as_gen/matplotlib.axes.Axes.annotate.html

    **Examples**::

        >>> from pyhelpers.geom import sketch_square
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt
        >>> mpl_preferences(backend='TkAgg')
        >>> c1, c2 = 1, 1
        >>> side_len = 2
        >>> sketch_square(c1, c2, side_len, rotation_theta=0, annotation=True, fig_size=(5, 5))
        >>> plt.show()
        >>> # from pyhelpers.store import save_fig
        >>> # path_to_fig_ = "docs/source/_images/geom-sketch_square-demo-1"
        >>> # save_fig(f"{path_to_fig_}.svg", verbose=True)
        >>> # save_fig(f"{path_to_fig_}.pdf", verbose=True)

    The above exmaple is illustrated in :numref:`geom-sketch_square-demo-1`:

    .. figure:: ../_images/geom-sketch_square-demo-1.*
        :name: geom-sketch_square-demo-1
        :align: center
        :width: 65%

        An example of a sketch of a square, created by the function
        :func:`~pyhelpers.geom.sketch_square`.

    .. code-block:: python

        >>> sketch_square(c1, c2, side_len, rotation_theta=75, annotation=True, fig_size=(5, 5))
        >>> plt.show()
        >>> # save_fig("docs/source/_images/geom-sketch_square-demo-2.svg", verbose=True)
        >>> # save_fig("docs/source/_images/geom-sketch_square-demo-2.pdf", verbose=True)

    This second example is illustrated in :numref:`geom-sketch_square-demo-2`:

    .. figure:: ../_images/geom-sketch_square-demo-2.*
        :name: geom-sketch_square-demo-2
        :align: center
        :width: 65%

        An example of a sketch of a square rotated 75 degrees anticlockwise about the centre.
    """

    mpl_plt, mpl_ticker = map(_check_dependency, ['matplotlib.pyplot', 'matplotlib.ticker'])

    vertices_ = get_square_vertices(
        ctr_x=ctr_x, ctr_y=ctr_y, side_length=side_length, rotation_theta=rotation_theta)
    vertices = np.append(vertices_, values=[vertices_[0]], axis=0)

    fig = mpl_plt.figure(figsize=fig_size)
    ax = fig.add_subplot(1, 1, 1)  # _, ax = plt.subplots(1, 1, figsize=fig_size)
    ax.plot(ctr_x, ctr_y, 'o', markersize=10)
    annotate_args = _sketch_square_annotate(x=ctr_x, y=ctr_y, fontsize=annot_font_size, **kwargs)
    ax.annotate(**annotate_args)

    if rotation_theta == 0:
        ax.plot(vertices[:, 0], vertices[:, 1], 'o-')
    else:
        label = "rotation $\\theta$ = {}°".format(rotation_theta)
        ax.plot(vertices[:, 0], vertices[:, 1], 'o-', label=label)
        ax.legend(loc="best")

    if annotation:
        for x, y in zip(vertices[:, 0], vertices[:, 1]):
            args = _sketch_square_annotate(x=x, y=y, fontsize=annot_font_size, **kwargs)
            ax.annotate(**args)

    ax.axis("equal")

    ax.yaxis.set_major_locator(mpl_ticker.MaxNLocator(integer=True))
    ax.xaxis.set_major_locator(mpl_ticker.MaxNLocator(integer=True))

    mpl_plt.tight_layout()

    if ret_vertices:
        return vertices
