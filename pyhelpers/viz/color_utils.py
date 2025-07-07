"""
General color utility functions for visualization.
"""

import numpy as np

from .._cache import _check_dependencies


def cmap_discretization(cmap, n_colors):
    # noinspection PyShadowingNames
    """
    Creates a discrete colormap based on the input.

    Reference: [`OPS-CD-1
    <https://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: A colormap instance, e.g. built-in `colormaps`_ available via
        `matplotlib.colormaps.get_cmap`_.
    :type cmap:
        matplotlib.colors.ListedColormap | matplotlib.colors.LinearSegmentedColormap |
        matplotlib.colors.Colormap | str
    :param n_colors: Number of colors to discretize the colormap.
    :type n_colors: int
    :return: A discrete colormap derived from the continuous ``cmap``.
    :rtype: matplotlib.colors.LinearSegmentedColormap

    .. _`colormaps`:
        https://matplotlib.org/stable/tutorials/colors/colormaps.html
    .. _`matplotlib.colormaps.get_cmap`:
        https://matplotlib.org/stable/api/cm_api.html#matplotlib.cm.ColormapRegistry.get_cmap

    **Examples**::

        >>> from pyhelpers.viz import cmap_discretization
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np
        >>> mpl_preferences()
        >>> cm_accent = cmap_discretization(cmap=plt.colormaps['Accent'], n_colors=5)
        >>> cm_accent.name
        'Accent_5'
        >>> cm_accent = cmap_discretization(cmap='Accent', n_colors=5)
        >>> cm_accent.name
        'Accent_5'
        >>> fig = plt.figure(figsize=(10, 2), constrained_layout=True)
        >>> ax = fig.add_subplot()
        >>> ax.imshow(np.resize(range(100), (5, 100)), cmap=cm_accent, interpolation='nearest')
        >>> ax.axis('off')
        >>> fig.show()
        >>> # from pyhelpers.store import save_figure
        >>> # path_to_fig_ = "docs/source/_images/viz-cmap_discretisation-demo"
        >>> # save_figure(fig, f"{path_to_fig_}.svg", verbose=True)
        >>> # save_figure(fig, f"{path_to_fig_}.pdf", verbose=True)

    The exmaple is illustrated in :numref:`viz-cmap_discretization-demo`:

    .. figure:: ../_images/viz-cmap_discretization-demo.*
        :name: viz-cmap_discretization-demo
        :align: center
        :width: 60%

        An example of discrete colour ramp, created by the function
        :func:`~pyhelpers.viz.cmap_discretization`.
    """

    mpl, mpl_colors = _check_dependencies('matplotlib', 'matplotlib.colors')

    cmap_ = mpl.colormaps[cmap] if isinstance(cmap, str) else cmap

    colors_ = np.concatenate((np.linspace(0, 1., n_colors), (0., 0., 0., 0.)))
    colors_rgba = cmap_(colors_)

    indices = np.linspace(0, 1., n_colors + 1)
    c_dict = {}

    for ki, key in enumerate(('red', 'green', 'blue')):
        c_dict[key] = [
            (indices[x], colors_rgba[x - 1, ki], colors_rgba[x, ki]) for x in range(n_colors + 1)]

    color_map = mpl_colors.LinearSegmentedColormap(cmap_.name + '_%d' % n_colors, c_dict, 1024)

    return color_map


def color_bar_index(cmap, n_colors, labels=None, **kwargs):
    """
    Creates a color bar with correctly aligned labels.

    .. note::

        - To avoid off-by-one errors, this function takes a standard colormap,
          discretizes it, and then draws a color bar with labels aligned correctly.
        - See also [`VIZ-CBI-1
          <https://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html
          #.WbpP0T6GNQB>`_].

    :param cmap: A colormap instance,
        e.g. built-in `colormaps`_ accessible via `matplotlib.cm.get_cmap()`_.
    :type cmap: matplotlib.colors.ListedColormap | matplotlib.colors.Colormap
    :param n_colors: Number of discrete colors to use in the color bar.
    :type n_colors: int
    :param labels: Optional list of labels for the color bar; defaults to ``None``.
    :type labels: list | None
    :param kwargs: [Optional] Additional optional parameters for the
        `matplotlib.pyplot.colorbar()`_ function.
    :return: A color bar object.
    :rtype: matplotlib.colorbar.Colorbar

    .. _`colormaps`:
        https://matplotlib.org/tutorials/colors/colormaps.html
    .. _`matplotlib.cm.get_cmap()`:
        https://matplotlib.org/api/cm_api.html#matplotlib.cm.get_cmap
    .. _`matplotlib.pyplot.colorbar()`:
        https://matplotlib.org/api/_as_gen/matplotlib.pyplot.colorbar.html

    **Examples**::

        >>> from pyhelpers.viz import color_bar_index
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt
        >>> mpl_preferences()
        >>> fig1 = plt.figure(figsize=(2, 6), constrained_layout=True)
        >>> ax1 = fig1.add_subplot()
        >>> cbar1 = color_bar_index(cmap=plt.colormaps['Accent'], n_colors=5)
        >>> ax1.tick_params(axis='both', which='major', labelsize=14)
        >>> cbar1.ax.tick_params(labelsize=14)
        >>> # ax.axis('off')
        >>> fig1.show()
        >>> # from pyhelpers.store import save_figure
        >>> # path_to_fig1_ = "docs/source/_images/viz-color_bar_index-demo-1"
        >>> # save_figure(fig1, f"{path_to_fig1_}.svg", verbose=True)
        >>> # save_figure(fig1, f"{path_to_fig1_}.pdf", verbose=True)

    The above example is illustrated in :numref:`ops-color_bar_index-demo-1`:

    .. figure:: ../_images/viz-color_bar_index-demo-1.*
        :name: ops-color_bar_index-demo-1
        :align: center
        :width: 32%

        An example of colour bar with numerical index.

    .. code-block:: python

        >>> fig2 = plt.figure(figsize=(2, 6), constrained_layout=True)
        >>> ax2 = fig2.add_subplot()
        >>> labels_ = list('abcde')
        >>> cbar2 = color_bar_index(cmap=plt.colormaps['Accent'], n_colors=5, labels=labels_)
        >>> ax2.tick_params(axis='both', which='major', labelsize=14)
        >>> cbar2.ax.tick_params(labelsize=14)
        >>> # ax.axis('off')
        >>> fig2.show()
        >>> # path_to_fig2_ = "docs/source/_images/viz-color_bar_index-demo-2"
        >>> # save_figure(fig2, f"{path_to_fig2_}.svg", verbose=True)
        >>> # save_figure(fig2, f"{path_to_fig2_}.pdf", verbose=True)

    This second example is illustrated in :numref:`ops-color_bar_index-demo-2`:

    .. figure:: ../_images/viz-color_bar_index-demo-2.*
        :name: ops-color_bar_index-demo-2
        :align: center
        :width: 32%

        An example of colour bar with textual index.
    """

    mpl_cm, mpl_plt = _check_dependencies('matplotlib.cm', 'matplotlib.pyplot')

    cmap_ = cmap_discretization(cmap, n_colors)

    mappable = mpl_cm.ScalarMappable(cmap=cmap_)
    mappable.set_array(np.array([]))
    mappable.set_clim(-0.5, n_colors + 0.5)

    color_bar = mpl_plt.colorbar(mappable=mappable, ax=mpl_plt.gca(), **kwargs)
    color_bar.set_ticks(np.linspace(0, n_colors, n_colors))
    color_bar.set_ticklabels(range(n_colors))

    if labels:
        color_bar.set_ticklabels(labels)

    return color_bar
