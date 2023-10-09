"""
Geometric data sketching.
"""

import numpy as np

from .spatial import get_square_vertices
from .._cache import _check_dependency


def _sketch_square_annotate(x, y, fontsize, margin=0.025, precision=2, **kwargs):
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
    Sketch a square given its centre point, four vertices and rotation angle (in degree).

    :param ctr_x: x coordinate of a square centre
    :type ctr_x: int | float
    :param ctr_y: y coordinate of a square centre
    :type ctr_y: int | float
    :param side_length: side length of a square
    :type side_length: int | float
    :param rotation_theta: rotate (anticlockwise) the square by ``rotation_theta`` (in degree),
        defaults to ``0``
    :type rotation_theta: int | float
    :param annotation: whether to annotate vertices of the square, defaults to ``True``
    :type annotation: bool
    :param annot_font_size: font size annotation texts, defaults to ``12``
    :type annot_font_size: int
    :param fig_size: figure size, defaults to ``(6.4, 4.8)``
    :type fig_size: tuple | list
    :param ret_vertices: whether to return the vertices of the square, defaults to ``False``
    :type ret_vertices: bool
    :param kwargs: [optional] parameters of `matplotlib.axes.Axes.annotate`_
    :return: vertices of the square as an array([ll, ul, ur, lr])
    :rtype: numpy.ndarray

    .. _`matplotlib.axes.Axes.annotate`:
        https://matplotlib.org/3.2.1/api/_as_gen/matplotlib.axes.Axes.annotate.html

    **Examples**::

        >>> from pyhelpers.geom import sketch_square
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt

        >>> mpl_preferences()

        >>> c1, c2 = 1, 1
        >>> side_len = 2

        >>> sketch_square(c1, c2, side_len, rotation_theta=0, annotation=True, fig_size=(5, 5))
        >>> plt.show()

    The above exmaple is illustrated in :numref:`geom-sketch_square-demo-1`:

    .. figure:: ../_images/geom-sketch_square-demo-1.*
        :name: geom-sketch_square-demo-1
        :align: center
        :width: 65%

        An example of a sketch of a square, created by the function
        :py:func:`~pyhelpers.geom.sketch_square`.

    .. code-block:: python

        >>> sketch_square(c1, c2, side_len, rotation_theta=75, annotation=True, fig_size=(5, 5))
        >>> plt.show()

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
