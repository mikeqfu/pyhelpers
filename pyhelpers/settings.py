"""
Altering the default settings of working environment.
"""

import copy
import os
import warnings

import numpy as np
import pandas as pd

""" == GDAL ================================================================================== """


def gdal_configurations(reset=False, max_tmpfile_size=5000, interleaved_reading=True,
                        custom_indexing=False, compress_nodes=True):
    """
    Alter some default `configuration options <https://gdal.org/user/configoptions.html>`_ of
    `GDAL/OGR <https://gdal.org/>`_ drivers.

    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool
    :param max_tmpfile_size: maximum size of the temporary file, defaults to ``5000``
    :type max_tmpfile_size: int
    :param interleaved_reading: whether to enable interleaved reading, defaults to ``True``
    :type interleaved_reading: bool
    :param custom_indexing: whether to enable custom indexing, defaults to ``False``
    :type custom_indexing: bool
    :param compress_nodes: whether to compress nodes in temporary DB. defaults to ``True``
    :type compress_nodes: bool

    **Example**::

        >>> from pyhelpers.settings import gdal_configurations

        >>> gdal_configurations()

    .. note::

        This can be very useful when using `GDAL`_ to parse a large PBF file.
        For example, ``gdal_configurations()`` is applied by default when importing the package
        `pydriosm`_, which can be used to work with `OpenStreetMap`_ data of `PBF format`_.

        .. _GDAL: https://pypi.org/project/GDAL/
        .. _pydriosm: https://pypi.org/project/pydriosm/
        .. _OpenStreetMap: https://www.openstreetmap.org/
        .. _PBF format: https://wiki.openstreetmap.org/wiki/PBF_Format

    .. seealso::

        - `OpenStreetMap XML and PBF <https://gdal.org/drivers/vector/osm.html>`_
        - `pydriosm Documentation <https://pydriosm.readthedocs.io/en/latest/>`_
    """

    import osgeo.gdal

    if reset is False:
        # Max. size (MB) of in-memory temporary file. Defaults to 100.
        osgeo.gdal.SetConfigOption('OSM_MAX_TMPFILE_SIZE', str(max_tmpfile_size))
        # If it exceeds that value, it will go to disk.

        val_dict = {True: 'YES', False: 'NO'}

        osgeo.gdal.SetConfigOption('OGR_INTERLEAVED_READING', val_dict[interleaved_reading])
        osgeo.gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', val_dict[custom_indexing])
        osgeo.gdal.SetConfigOption('OSM_COMPRESS_NODES', val_dict[compress_nodes])

    elif reset is True:
        osgeo.gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'NO')
        osgeo.gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'YES')
        osgeo.gdal.SetConfigOption('OSM_COMPRESS_NODES', 'NO')
        osgeo.gdal.SetConfigOption('OSM_MAX_TMPFILE_SIZE', '100')


""" == Matplotlib ============================================================================ """


def mpl_preferences(reset=False, font_name='Times New Roman', font_size=13, legend_spacing=0.7,
                    fig_style=None):
    """
    Alter some `parameters
    <https://matplotlib.org/stable/api/matplotlib_configuration_api.html#matplotlib.rcParams>`_
    of `Matplotlib <https://matplotlib.org/stable/index.html>`_ plots.

    :param font_name: name of a font to be used, defaults to ``'Times New Roman'``
    :type font_name: None or str
    :param font_size: font size, defaults to ``13``
    :type font_size: int or float
    :param legend_spacing: spacing between labels in plot legend, defaults to ``0.7``
    :type legend_spacing: float or int
    :param fig_style: style of the figure, defaults to ``None``
    :type fig_style: str or None
    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool

    **Example**::

        >>> import numpy
        >>> import matplotlib.pyplot as plt

        >>> numpy.random.seed(0)

        >>> random_array = numpy.random.rand(1000, 2)
        >>> random_array
        array([[0.5488135 , 0.71518937],
               [0.60276338, 0.54488318],
               [0.4236548 , 0.64589411],
               ...,
               [0.41443887, 0.79128155],
               [0.72119811, 0.48010781],
               [0.64386404, 0.50177313]])

        >>> def example_plot(arr):
        ...     fig = plt.figure(figsize=(6, 6))
        ...     ax = fig.add_subplot(aspect='equal', adjustable='box')
        ...
        ...     ax.scatter(arr[:500, 0], arr[:500, 1], label='Group0')
        ...     ax.scatter(arr[500:, 0], arr[500:, 1], label='Group1')
        ...     ax.legend(loc='best')
        ...
        ...     plt.tight_layout()
        ...
        ...     plt.show()

        >>> example_plot(random_array)

    .. figure:: ../_images/settings-mpl_preferences-demo-1.*
        :name: settings-mpl_preferences-demo-1
        :align: center
        :width: 70%

        An example figure, before setting
        :py:func:`mpl_preferences()<pyhelpers.settings.mpl_preferences>`.

    .. code-block:: python

        >>> from pyhelpers.settings import mpl_preferences

        >>> mpl_preferences(fig_style='ggplot')

        >>> example_plot(random_array)

    .. figure:: ../_images/settings-mpl_preferences-demo-2.*
        :name: settings-mpl_preferences-demo-2
        :align: center
        :width: 70%

        After setting :py:func:`mpl_preferences()<pyhelpers.settings.mpl_preferences>`.

    Reset to default settings:

    .. code-block:: python

        >>> mpl_preferences(reset=True)

        >>> example_plot(random_array)

    .. figure:: ../_images/settings-mpl_preferences-demo-1.*
        :name: settings-mpl_preferences-demo-3
        :align: center
        :width: 70%

        Resetting the altered parameters to their default values.
    """

    import matplotlib.style
    import matplotlib.font_manager

    if reset is False:
        if fig_style is not None:
            matplotlib.style.use(style=fig_style)

        matplotlib.rcParams['font.size'] = font_size
        # matplotlib.rcParams['font.weight'] = 'normal'
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
        matplotlib.style.use(style='default')

        if reset == 'all':
            matplotlib.rcParams = matplotlib.rcParamsDefault

        elif reset is True:
            matplotlib.rcParams['font.size'] = 10.0
            matplotlib.rcParams['legend.labelspacing'] = 0.5
            matplotlib.rcParams['font.family'] = ['sans-serif']
            matplotlib.rcParams['font.serif'] = copy.copy(matplotlib.rcParamsDefault['font.serif'])


""" == NumPy ================================================================================= """


def np_preferences(reset=False, precision=4, head_tail=5, line_char=120, formatter=None, **kwargs):
    """
    Alter some default parameters for displaying
    `NumPy arrays <https://numpy.org/doc/stable/reference/generated/numpy.array.html>`_.

    :param reset: whether to reset to the default print options set by `numpy.set_printoptions`_,
        defaults to ``False``
    :type reset: bool
    :param precision: number of decimal points,
        which corresponds to ``precision`` of `numpy.set_printoptions`_, defaults to ``4``
    :type precision: int
    :param line_char: number of characters per line for the purpose of inserting line breaks,
        which corresponds to ``linewidth`` of `numpy.set_printoptions`_, defaults to ``120``
    :type line_char: int
    :param head_tail: number of array items in summary at beginning (head) and end (tail)
        of each dimension, which corresponds to ``edgeitems`` of `numpy.set_printoptions`_,
        defaults to ``5``
    :type head_tail: int
    :param formatter: specified format, which corresponds to ``formatter`` of `numpy.set_printoptions`_,
        if ``None`` (default), fill the empty decimal places with zeros for the specified ``precision``
    :type formatter: dict or None
    :kwargs: [optional] parameters used by `numpy.set_printoptions`_

    .. _numpy.set_printoptions:
        https://numpy.org/doc/stable/reference/generated/numpy.set_printoptions.html

    **Example**::

        >>> import numpy

        >>> numpy.random.seed(0)

        >>> random_array = numpy.random.rand(100, 100)
        >>> random_array
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

        >>> np_preferences(precision=2)

        >>> random_array
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

    Reset to default settings:

    .. code-block:: python

        >>> np_preferences(reset=True)

        >>> random_array
        array([[0.54881350, 0.71518937, 0.60276338, ..., 0.02010755, 0.82894003,
                0.00469548],
               [0.67781654, 0.27000797, 0.73519402, ..., 0.25435648, 0.05802916,
                0.43441663],
               [0.31179588, 0.69634349, 0.37775184, ..., 0.86219152, 0.97291949,
                0.96083466],
               ...,
               [0.89111234, 0.26867428, 0.84028499, ..., 0.57367960, 0.73729114,
                0.22519844],
               [0.26969792, 0.73882539, 0.80714479, ..., 0.94836806, 0.88130699,
                0.14193340],
               [0.88498232, 0.19701397, 0.56861333, ..., 0.75842952, 0.02378743,
                0.81357508]])
    """

    if reset is False:
        if formatter is None:
            formatter = dict(float=lambda x: "%.{}f".format(precision) % x)

        np.set_printoptions(
            precision=precision, linewidth=line_char, edgeitems=head_tail, formatter=formatter,
            **kwargs)

    elif reset is True:
        # true default linewidth = 75
        np.set_printoptions(
            precision=8, threshold=1000, edgeitems=3, linewidth=80, suppress=False, nanstr=np.nan,
            infstr=np.inf, formatter=None, sign='-', floatmode='maxprec_equal', legacy=False)


""" == Pandas ================================================================================ """


def pd_preferences(reset=False, max_columns=100, max_rows=20, precision=4, ignore_future_warning=True):
    """
    Alter parameters of some frequently-used
    `Pandas options and settings <https://pandas.pydata.org/pandas-docs/stable/user_guide/options.html>`_
    for displaying `data frame <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html>`_.

    :param reset: whether to reset all to default settings, defaults to ``False``
    :type reset: bool or str
    :param max_columns: maximum number of columns, which corresponds to ``'display.max_columns'`` for
        `pandas.set_option`_, defaults to ``100``
    :type max_columns: int
    :param max_rows: maximum number of rows, which corresponds to ``'display.max_rows'`` for
        `pandas.set_option`_, defaults to ``20``
    :type max_rows: int
    :param precision: number of decimal places, which corresponds to ``'display.precision'`` for
        `pandas.set_option`_, defaults to ``4``
    :type precision: int
    :param ignore_future_warning: whether to ignore/suppress future warnings, defaults to ``True``
    :type ignore_future_warning: bool

    .. _pandas.set_option:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.set_option.html

    **Example**::

        >>> import numpy
        >>> import pandas

        >>> numpy.random.seed(0)

        >>> random_array = numpy.random.rand(100, 100)

        >>> data_frame = pandas.DataFrame(random_array)
        >>> data_frame
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

    Limit to display of at most ``6`` columns and round the numbers to ``2`` decimal places:

    .. code-block:: python

        >>> from pyhelpers.settings import pd_preferences

        >>> pd_preferences(max_columns=6, precision=2)

        >>> data_frame
             0    1    2   ...   97   98   99
        0  0.55 0.72 0.60  ... 0.02 0.83 0.00
        1  0.68 0.27 0.74  ... 0.25 0.06 0.43
        2  0.31 0.70 0.38  ... 0.86 0.97 0.96
        3  0.91 0.77 0.33  ... 0.36 0.02 0.19
        4  0.40 0.93 0.10  ... 0.40 0.25 0.51
        ..  ...  ...  ...  ...  ...  ...  ...
        95 0.03 0.99 0.09  ... 0.37 0.91 0.14
        96 0.62 0.20 0.29  ... 0.22 0.14 0.93
        97 0.89 0.27 0.84  ... 0.57 0.74 0.23
        98 0.27 0.74 0.81  ... 0.95 0.88 0.14
        99 0.88 0.20 0.57  ... 0.76 0.02 0.81

        [100 rows x 100 columns]

    Reset to default settings:

    .. code-block:: python

        >>> pd_preferences(reset=True)

        >>> data_frame
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

    .. note::

        - Default values of all available options can be checked by running `pandas.describe_option()`_
          or ``pandas._config.config._registered_options``

        .. _pandas.describe_option():
            https://pandas.pydata.org/docs/reference/api/pandas.describe_option.html
    """

    if reset is False:
        pd.set_option('display.max_columns', max_columns)
        pd.set_option('display.max_rows', max_rows)
        pd.set_option('display.precision', precision)
        pd.set_option('display.width', 1000)  # Set the display width
        pd.set_option('display.float_format', lambda x: '%.{}f'.format(precision) % x)
        pd.set_option('display.expand_frame_repr', False)  # NOT to wrap
        pd.set_option('io.excel.xlsx.writer', 'openpyxl')
        pd.set_option('mode.chained_assignment', None)

    else:
        # registered_options = pd._config.config._registered_options

        if reset == 'all':
            if ignore_future_warning:
                warnings.simplefilter(action='ignore', category=FutureWarning)
            pd.reset_option('all')

        elif reset is True:
            pd.set_option('display.max_columns', 20)
            pd.set_option('display.max_rows', 60)
            pd.set_option('display.precision', 6)
            pd.set_option('display.width', 80)  # Set the display width
            pd.set_option('display.float_format', None)
            pd.set_option('display.expand_frame_repr', True)
            pd.set_option('io.excel.xlsx.writer', 'auto')
            pd.set_option('mode.chained_assignment', 'warn')
