"""
Altering settings of working environment.
"""

import os

import numpy as np
import pandas as pd

""" NumPy -------------------------------------------------------------------------- """


def np_preferences(reset=False):
    """
    Set preferences for displaying results.

    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool

    **Example**::

        >>> from pyhelpers.settings import np_preferences

        >>> np_preferences()
    """

    if not reset:
        np.core.arrayprint._line_width = 120
    else:
        np.core.arrayprint._line_width = 80  # 75


""" Pandas ------------------------------------------------------------------------- """


def pd_preferences(reset=False, ignore_future_warning=True):
    """
    Set preferences for displaying results.

    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool
    :param ignore_future_warning: whether to ignore/suppress future warnings,
        defaults to ``True``
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
        pd.set_option('io.excel.xlsx.writer', 'xlsxwriter')
        pd.set_option('mode.chained_assignment', None)
        # pandas.set_option('display.float_format', lambda x: '%.4f' % x)
    else:
        if ignore_future_warning:
            import warnings
            warnings.simplefilter(action='ignore', category=FutureWarning)
        pd.reset_option('all')


""" Matplotlib --------------------------------------------------------------------- """


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
                pass
    else:
        plt.rcParams = plt.rcParamsDefault
        plt.style.use('default')


""" GDAL --------------------------------------------------------------------------- """


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

    import gdal

    if not reset:
        # Whether to enable interleaved reading. Defaults to NO.
        gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'YES')
        # Whether to enable custom indexing. Defaults to YES.
        gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'YES')
        # Whether to compress nodes in temporary DB. Defaults to NO.
        gdal.SetConfigOption('OSM_COMPRESS_NODES', 'YES')
        # Maximum size in MB of in-memory temporary file.
        # If it exceeds that value, it will go to disk. Defaults to 100.
        gdal.SetConfigOption('OSM_MAX_TMPFILE_SIZE', str(max_tmpfile_size))
    else:
        gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'NO')
        gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'YES')
        gdal.SetConfigOption('OSM_COMPRESS_NODES', 'NO')
        gdal.SetConfigOption('OSM_MAX_TMPFILE_SIZE', '100')
