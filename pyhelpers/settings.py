"""
Altering settings of working environment.
"""

import os
import warnings

import numpy as np
import numpy.core.arrayprint
import pandas as pd

""" == NumPy ================================================================================= """


def np_preferences(reset=False, line_width=120, edge_items=5, decimal_digits=4):
    """
    Set preferences for displaying results.

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
        >>> x = numpy.random.rand(100, 100)
        >>> x
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

        >>> x
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


def pd_preferences(reset=False, ignore_future_warning=True):
    """
    Set preferences for displaying results.

    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool
    :param ignore_future_warning: whether to ignore/suppress future warnings, defaults to ``True``
    :type ignore_future_warning: bool

    **Example**::

        >>> from pyhelpers.settings import pd_preferences

        >>> pd_preferences()
    """

    if not reset:
        # pandas.set_option('display.float_format', lambda x: '%.4f' % x)
        pd.set_option('display.precision', 2)
        pd.set_option('expand_frame_repr', False)  # Set the representation of DataFrame NOT to wrap
        pd.set_option('display.width', 600)  # Set the display width
        pd.set_option('precision', 4)
        pd.set_option('display.max_columns', 100)
        pd.set_option('display.max_rows', 20)
        pd.set_option('io.excel.xlsx.writer', 'openpyxl')
        pd.set_option('mode.chained_assignment', None)
        # pandas.set_option('display.float_format', lambda x: '%.4f' % x)

    else:
        if ignore_future_warning:
            warnings.simplefilter(action='ignore', category=FutureWarning)
        pd.reset_option('all')


""" == Matplotlib ============================================================================ """


def mpl_preferences(reset=False, font_name=None):
    """
    Set preferences for plotting.

    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool
    :param font_name: name of a font to be used, defaults to ``None``
    :type font_name: None or str

    **Example**::

        >>> from pyhelpers.settings import mpl_preferences

        >>> mpl_preferences()

        >>> mpl_preferences(font_name='Times New Roman')
    """

    import matplotlib.pyplot as plt
    import matplotlib.font_manager

    if not reset:
        plt.rcParams['font.size'] = 13
        plt.rcParams['font.weight'] = 'normal'
        plt.rcParams['legend.labelspacing'] = 0.7
        # plt.style.use('ggplot')
        if font_name:  # Use the font, 'Cambria'
            if os.path.isfile(matplotlib.font_manager.findfont(font_name)):
                # Set 'font.family' to 'serif', then matplotlib will use that list
                plt.rcParams['font.family'] = 'serif'
                serif_fonts = plt.rcParams['font.serif']
                if font_name not in serif_fonts:
                    plt.rcParams['font.serif'] = [font_name] + plt.rcParams['font.serif']
                else:
                    serif_fonts.insert(0, serif_fonts.pop(serif_fonts.index(font_name)))
                    plt.rcParams['font.serif'] = serif_fonts

    else:
        plt.rcParams = plt.rcParamsDefault
        plt.style.use('default')


""" == GDAL ================================================================================== """


def gdal_configurations(reset=False, max_tmpfile_size=5000):
    """
    Set GDAL configurations.

    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool
    :param max_tmpfile_size: maximum size of the temporary file, defaults to ``5000``
    :type max_tmpfile_size: int

    **Example**::

        >>> from pyhelpers.settings import gdal_configurations

        >>> gdal_configurations()
    """

    import osgeo.gdal

    if not reset:
        # Whether to enable interleaved reading. Defaults to NO.
        osgeo.gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'YES')
        # Whether to enable custom indexing. Defaults to YES.
        osgeo.gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'YES')
        # Whether to compress nodes in temporary DB. Defaults to NO.
        osgeo.gdal.SetConfigOption('OSM_COMPRESS_NODES', 'YES')
        # Maximum size in MB of in-memory temporary file.
        #   If it exceeds that value, it will go to disk. Defaults to 100.
        osgeo.gdal.SetConfigOption('OSM_MAX_TMPFILE_SIZE', str(max_tmpfile_size))

    else:
        osgeo.gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'NO')
        osgeo.gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'YES')
        osgeo.gdal.SetConfigOption('OSM_COMPRESS_NODES', 'NO')
        osgeo.gdal.SetConfigOption('OSM_MAX_TMPFILE_SIZE', '100')
