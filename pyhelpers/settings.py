"""
Altering the default settings of working environment.
"""

import os
import warnings

import numpy as np
import numpy.core.arrayprint
import pandas as pd

""" == NumPy ================================================================================= """


def np_preferences(reset=False, line_width=120, edge_items=5, decimal_digits=4):
    """
    Alter some parameters for displaying
    `NumPy arrays <https://numpy.org/doc/stable/reference/generated/numpy.array.html>`_ in a console.

    :param line_width: number of characters per line for the purpose of inserting line breaks,
        defaults to ``120``
    :type line_width: int
    :param edge_items: number of array items in summary at beginning and end of each dimension,
        defaults to ``5``
    :type edge_items: int
    :param decimal_digits: number of decimal points
    :type decimal_digits: int
    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool

    **Example**::

        >>> import numpy

        >>> numpy.random.seed(0)
        >>> array = numpy.random.rand(100, 100)
        >>> array
        array([[0.5488135 , 0.71518937, 0.60276338, ..., 0.02010755, 0.82894003,
                0.00469548],
               [0.67781654, 0.27000797, 0.73519402, ..., 0.25435648, 0.05802916,
                0.43441663],
               [0.31179588, 0.69634349, 0.37775184, ..., 0.86219152, 0.97291949,
                0.96083466],
               ...,
               [0.89111234, 0.26867428, 0.84028499, ..., 0.5736796 , 0.73729114,
                0.22519844],
               [0.26969792, 0.73882539, 0.80714479, ..., 0.94836806, 0.88130699,
                0.1419334 ],
               [0.88498232, 0.19701397, 0.56861333, ..., 0.75842952, 0.02378743,
                0.81357508]])

        >>> from pyhelpers.settings import np_preferences

        >>> np_preferences(decimal_digits=2)

        >>> array
        array([[0.55, 0.72, 0.60, 0.54, 0.42, ..., 0.18, 0.59, 0.02, 0.83, 0.00],
               [0.68, 0.27, 0.74, 0.96, 0.25, ..., 0.49, 0.23, 0.25, 0.06, 0.43],
               [0.31, 0.70, 0.38, 0.18, 0.02, ..., 0.22, 0.10, 0.86, 0.97, 0.96],
               [0.91, 0.77, 0.33, 0.08, 0.41, ..., 0.96, 0.36, 0.36, 0.02, 0.19],
               [0.40, 0.93, 0.10, 0.95, 0.87, ..., 0.27, 0.46, 0.40, 0.25, 0.51],
               ...,
               [0.03, 0.99, 0.09, 0.45, 0.84, ..., 0.12, 0.29, 0.37, 0.91, 0.14],
               [0.62, 0.20, 0.29, 0.45, 0.55, ..., 0.48, 0.87, 0.22, 0.14, 0.93],
               [0.89, 0.27, 0.84, 0.76, 1.00, ..., 0.98, 0.41, 0.57, 0.74, 0.23],
               [0.27, 0.74, 0.81, 0.20, 0.31, ..., 0.51, 0.23, 0.95, 0.88, 0.14],
               [0.88, 0.20, 0.57, 0.93, 0.56, ..., 0.55, 0.40, 0.76, 0.02, 0.81]])
    """

    if not reset:
        numpy.core.arrayprint._line_width = line_width
        np.set_printoptions(linewidth=line_width, edgeitems=edge_items,
                            formatter=dict(float=lambda x: "%.{}f".format(decimal_digits) % x))

    else:
        numpy.core.arrayprint._line_width = 80  # 75
        np.set_printoptions(edgeitems=3, linewidth=80)


""" == Pandas ================================================================================ """


def pd_preferences(max_columns=100, max_rows=20, precision=4, float_format='%.4f', reset=False,
                   ignore_future_warning=True):
    """
    Alter the default parameters of some frequently-used
    `options and settings <https://pandas.pydata.org/pandas-docs/stable/user_guide/options.html>`_
    for `Pandas <https://pandas.pydata.org/>`_.

    :param max_columns:
    :type max_columns: int
    :param max_rows:
    :type max_rows: int
    :param precision:
    :type precision: int
    :param float_format:
    :type float_format: str
    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool
    :param ignore_future_warning: whether to ignore/suppress future warnings, defaults to ``True``
    :type ignore_future_warning: bool

    **Example**::

        >>> import numpy
        >>> import pandas

        >>> numpy.random.seed(0)
        >>> array = numpy.random.rand(100, 100)
        >>> dataframe = pandas.DataFrame(array)
        >>> dataframe
                  0         1         2   ...        97        98        99
        0   0.548814  0.715189  0.602763  ...  0.020108  0.828940  0.004695
        1   0.677817  0.270008  0.735194  ...  0.254356  0.058029  0.434417
        2   0.311796  0.696343  0.377752  ...  0.862192  0.972919  0.960835
        3   0.906555  0.774047  0.333145  ...  0.356707  0.016329  0.185232
        4   0.401260  0.929291  0.099615  ...  0.401714  0.248413  0.505866
        ..       ...       ...       ...  ...       ...       ...       ...
        95  0.029929  0.985128  0.094747  ...  0.369907  0.910011  0.142890
        96  0.616935  0.202908  0.288809  ...  0.215006  0.143577  0.933162
        97  0.891112  0.268674  0.840285  ...  0.573680  0.737291  0.225198
        98  0.269698  0.738825  0.807145  ...  0.948368  0.881307  0.141933
        99  0.884982  0.197014  0.568613  ...  0.758430  0.023787  0.813575
        [100 rows x 100 columns]

        >>> from pyhelpers.settings import pd_preferences

        >>> pd_preferences()

        >>> # Now all the 100 columns can be displayed
        >>> dataframe
               0      1      2      3      4      5      6      7      8      9      10     11 ...
        0  0.5488 0.7152 0.6028 0.5449 0.4237 0.6459 0.4376 0.8918 0.9637 0.3834 0.7917 0.5289 ...
        1  0.6778 0.2700 0.7352 0.9622 0.2488 0.5762 0.5920 0.5723 0.2231 0.9527 0.4471 0.8464 ...
        2  0.3118 0.6963 0.3778 0.1796 0.0247 0.0672 0.6794 0.4537 0.5366 0.8967 0.9903 0.2169 ...
        3  0.9066 0.7740 0.3331 0.0811 0.4072 0.2322 0.1325 0.0534 0.7256 0.0114 0.7706 0.1469 ...
        4  0.4013 0.9293 0.0996 0.9453 0.8695 0.4542 0.3267 0.2327 0.6145 0.0331 0.0156 0.4288 ...
        ..    ...    ...    ...    ...    ...    ...    ...    ...    ...    ...    ...    ... ...
        95 0.0299 0.9851 0.0947 0.4510 0.8387 0.4216 0.2488 0.4140 0.8239 0.0449 0.4888 0.1935 ...
        96 0.6169 0.2029 0.2888 0.4451 0.5472 0.1754 0.5955 0.6072 0.4085 0.2007 0.3339 0.0980 ...
        97 0.8911 0.2687 0.8403 0.7570 0.9954 0.1634 0.8974 0.0570 0.6731 0.6692 0.9157 0.2279 ...
        98 0.2697 0.7388 0.8071 0.2006 0.3087 0.0087 0.3848 0.9011 0.4013 0.7590 0.0574 0.5879 ...
        99 0.8850 0.1970 0.5686 0.9310 0.5645 0.2116 0.2650 0.6786 0.7470 0.5918 0.2814 0.1868 ...
        [100 rows x 100 columns]

    .. note::

        Due to the maximum limit of page width of the documentation,
        the columns 12-99 are omitted, and replaced with "..." in the above demonstration.
    """

    if not reset:
        pd.set_option('display.max_columns', max_columns)
        pd.set_option('display.max_rows', max_rows)
        pd.set_option('display.precision', precision)
        # pd.set_option('precision', precision)
        pd.set_option('display.float_format', lambda x: float_format % x)
        pd.set_option('expand_frame_repr', False)  # Set the representation of DataFrame NOT to wrap
        pd.set_option('display.width', 1000)  # Set the display width
        pd.set_option('io.excel.xlsx.writer', 'openpyxl')
        pd.set_option('mode.chained_assignment', None)

    else:
        if ignore_future_warning:
            warnings.simplefilter(action='ignore', category=FutureWarning)
        pd.reset_option('all')


""" == Matplotlib ============================================================================ """


def mpl_preferences(font_name='Times New Roman', font_size=13, legend_spacing=0.7, style='default',
                    reset=False):
    """
    Alter some default `parameters
    <https://matplotlib.org/stable/api/matplotlib_configuration_api.html#matplotlib.rcParams>`_
    of `Matplotlib <https://matplotlib.org/stable/index.html>`_.

    :param font_name: name of a font to be used, defaults to ``'Times New Roman'``
    :type font_name: None or str
    :param font_size: font size, defaults to ``13``
    :type font_size: int or float
    :param legend_spacing: spacing between labels in plot legend, defaults to ``0.7``
    :type legend_spacing: float or int
    :param style:
    :type style:
    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool

    **Example**::

        >>> import numpy
        >>> import matplotlib.pyplot as plt

        >>> numpy.random.seed(0)
        >>> array = numpy.random.rand(1000, 2)
        >>> array
        array([[0.5488135 , 0.71518937],
               [0.60276338, 0.54488318],
               [0.4236548 , 0.64589411],
               ...,
               [0.41443887, 0.79128155],
               [0.72119811, 0.48010781],
               [0.64386404, 0.50177313]])

        >>> fig = plt.figure(figsize=(6, 6))
        >>> ax = fig.add_subplot(aspect='equal', adjustable='box')
        >>> ax.scatter(array[:500, 0], array[:500, 1], label='Group0')
        >>> ax.scatter(array[500:, 0], array[500:, 1], label='Group1')
        >>> ax.legend()
        >>> plt.tight_layout()
        >>> plt.show()

    .. figure:: ../_images/settings-mpl_preferences-demo-1.*
        :name: settings-mpl_preferences-demo-1
        :align: center
        :width: 70%

        An example figure, before setting
        :py:func:`mpl_preferences()<pyhelpers.settings.mpl_preferences>`.

    .. code-block:: python

        >>> from pyhelpers.settings import mpl_preferences

        >>> mpl_preferences(style='ggplot')

        >>> fig = plt.figure(figsize=(6, 6))
        >>> ax = fig.add_subplot(aspect='equal', adjustable='box')
        >>> ax.scatter(array[:500, 0], array[:500, 1], label='Group0')
        >>> ax.scatter(array[500:, 0], array[500:, 1], label='Group1')
        >>> ax.legend()
        >>> plt.tight_layout()
        >>> plt.show()

    .. figure:: ../_images/settings-mpl_preferences-demo-2.*
        :name: settings-mpl_preferences-demo-2
        :align: center
        :width: 70%

        An example figure, after setting
        :py:func:`mpl_preferences()<pyhelpers.settings.mpl_preferences>`.
    """

    import matplotlib.style
    import matplotlib.font_manager

    if not reset:
        matplotlib.style.use(style=style)

        matplotlib.rcParams['font.size'] = font_size
        matplotlib.rcParams['font.weight'] = 'normal'
        matplotlib.rcParams['legend.labelspacing'] = legend_spacing

        if font_name:  # Use the font, 'Cambria'
            if os.path.isfile(matplotlib.font_manager.findfont(font_name)):
                # Set 'font.family' to 'serif', then matplotlib will use that list
                matplotlib.rcParams['font.family'] = 'serif'
                serif_fonts = matplotlib.rcParams['font.serif']
                if font_name not in serif_fonts:
                    matplotlib.rcParams['font.serif'] = [font_name] + matplotlib.rcParams['font.serif']
                else:
                    serif_fonts.insert(0, serif_fonts.pop(serif_fonts.index(font_name)))
                    matplotlib.rcParams['font.serif'] = serif_fonts

    else:
        matplotlib.style.use('default')
        matplotlib.rcParams = matplotlib.rcParamsDefault


""" == GDAL ================================================================================== """


def gdal_configurations(reset=False, max_tmpfile_size=5000):
    """
    Alter some default behaviours of GDAL/OGR drivers via
    `configuration options <https://gdal.org/user/configoptions.html>`_.

    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool
    :param max_tmpfile_size: maximum size of the temporary file, defaults to ``5000``
    :type max_tmpfile_size: int

    **Example**::

        >>> from pyhelpers.settings import gdal_configurations

        >>> gdal_configurations()

    .. note::

        This can be very useful when using `GDAL <https://pypi.org/project/GDAL/>`_ to parse a large
        PBF file. For example, :py:func:`gdal_configurations()<pyhelpers.settings.gdal_configurations>`
        is run by default for importing `pydriosm <https://pypi.org/project/pydriosm/>`_,
        which can be used to parse `OpenStreetMap PBF <https://wiki.openstreetmap.org/wiki/PBF_Format>`_.

    .. seealso::

        `OSM - OpenStreetMap XML and PBF <https://gdal.org/drivers/vector/osm.html>`_ and
        `Pydriosm Documentation <https://pydriosm.readthedocs.io/en/latest/>`_.
    """

    import osgeo.gdal

    if not reset:
        # Whether to enable interleaved reading. Defaults to NO.
        osgeo.gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'YES')
        # Whether to enable custom indexing. Defaults to YES.
        osgeo.gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'YES')
        # Whether to compress nodes in temporary DB. Defaults to NO.
        osgeo.gdal.SetConfigOption('OSM_COMPRESS_NODES', 'YES')
        # Maximum size (MB) of in-memory temporary file. Defaults to 100.
        #   If it exceeds that value, it will go to disk.
        osgeo.gdal.SetConfigOption('OSM_MAX_TMPFILE_SIZE', str(max_tmpfile_size))

    else:
        osgeo.gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'NO')
        osgeo.gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'YES')
        osgeo.gdal.SetConfigOption('OSM_COMPRESS_NODES', 'NO')
        osgeo.gdal.SetConfigOption('OSM_MAX_TMPFILE_SIZE', '100')
