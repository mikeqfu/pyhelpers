"""
Preferences.
"""

import copy
import os

from .._cache import _check_dependency


def pd_preferences(reset=False, max_columns=100, max_rows=20, precision=4, east_asian_text=False,
                   ignore_future_warning=True, **kwargs):
    """
    Alter parameters of some frequently-used
    `Pandas options and settings
    <https://pandas.pydata.org/pandas-docs/stable/user_guide/options.html>`_
    for displaying `pandas dataframes
    <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html>`_.

    This function allows adjusting various display options such as maximum number of columns,
    maximum number of rows, decimal precision, handling of East Asian text and suppression of
    future warnings.

    :param reset: Whether to reset all settings to their defaults; defaults to ``False``.
    :type reset: bool | str
    :param max_columns: Maximum number of columns to display; corresponds to
        ``'display.max_columns'`` in `pandas.set_option()`_; defaults to ``100``.
    :type max_columns: int
    :param max_rows: Maximum number of rows to display; corresponds to ``'display.max_rows'`` in
        `pandas.set_option()`_; defaults to ``20``.
    :type max_rows: int
    :param precision: Number of decimal places to display; corresponds to ``'display.precision'``
        in `pandas.set_option()`_; defaults to ``4``.
    :type precision: int
    :param east_asian_text: Whether to adjust the display for East Asian text;
        defaults to ``False``.
    :type east_asian_text: bool
    :param ignore_future_warning: Whether to ignore or suppress future warnings;
        defaults to ``True``.
    :type ignore_future_warning: bool
    :param kwargs: [Optional] Additional parameters for the function `pandas.set_option()`_. 

    .. _`pandas.set_option()`:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.set_option.html

    **Examples**::

        >>> import numpy as np
        >>> import pandas as pd
        >>> np.random.seed(0)
        >>> random_array = np.random.rand(100, 100)
        >>> data_frame = pd.DataFrame(random_array)
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

        Default values of all available options can be checked by running
        `pandas.describe_option()`_ or ``pandas._config.config._registered_options``.

        .. _`pandas.describe_option()`:
            https://pandas.pydata.org/docs/reference/api/pandas.describe_option.html
    """

    pd_ = _check_dependency(name='pandas')

    options = {
        'display.max_columns': max_columns,  # 0
        'display.max_rows': max_rows,  # 60
        'display.precision': precision,  # 6
        'display.width': 1000,  # 80
        'display.float_format': lambda x: '%.{}f'.format(precision) % x,  # None
        'display.expand_frame_repr': False,  # True
        'io.excel.xlsx.writer': 'openpyxl',  # 'auto'
        'mode.chained_assignment': None,  # 'warn'
    }

    if east_asian_text:
        options.update({'display.unicode.east_asian_width': True})

    kwargs.update(options)

    if reset is False:
        for key, val in kwargs.items():
            pd_.set_option(key, val)

    elif reset is True:
        registered_options = pd_._config.config._registered_options

        for key in kwargs:
            pd_.set_option(key, registered_options[key].defval)

    elif reset == 'all':
        pd_.reset_option('all', silent=ignore_future_warning)


def np_preferences(reset=False, precision=4, head_tail=5, line_char=120, formatter=None, **kwargs):
    """
    Alter some default parameters for displaying
    `NumPy arrays <https://numpy.org/doc/stable/reference/generated/numpy.array.html>`_.

    This function allows customising the display options for NumPy arrays, including
    decimal precision, summary at the beginning and end of each dimension, line width for
    inserting line breaks and optional custom formatting.

    :param reset: Whether to reset to the default print options set by the function
        `numpy.set_printoptions()`_; defaults to ``False``.
    :type reset: bool
    :param precision: Number of decimal points to display, corresponding to ``precision`` of
        the function `numpy.set_printoptions()`_; defaults to ``4``.
    :type precision: int
    :param line_char: Number of characters per line for inserting line breaks, corresponding to
        ``linewidth`` of the function `numpy.set_printoptions()`_; defaults to ``120``.
    :type line_char: int
    :param head_tail: Number of array items to summarise at the beginning (head) and end (tail)
        of each dimension, corresponding to ``edgeitems`` of the function
        `numpy.set_printoptions()`_; defaults to ``5``.
    :type head_tail: int
    :param formatter: Custom format specification, corresponding to ``formatter`` of the function
        `numpy.set_printoptions()`_; if ``formatter=None`` (default), empty decimal places are
        filled with zeros for the specified ``precision``.
    :type formatter: dict | None
    :param kwargs: [Optional] Additional parameters for the function `numpy.set_printoptions()`_.

    .. _`numpy.set_printoptions()`:
        https://numpy.org/doc/stable/reference/generated/numpy.set_printoptions.html

    **Examples**::

        >>> import numpy as np
        >>> np.random.seed(0)
        >>> random_array = np.random.rand(100, 100)
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

    np_ = _check_dependency(name='numpy')

    if reset is False:
        if formatter is None:
            formatter = dict(float=lambda x: "%.{}f".format(precision) % x)

        np_.set_printoptions(
            precision=precision, linewidth=line_char, edgeitems=head_tail, formatter=formatter,
            **kwargs)

    elif reset is True:
        # true default linewidth = 75
        np_.set_printoptions(
            precision=8, threshold=1000, edgeitems=3, linewidth=80, suppress=False, nanstr=np_.nan,
            infstr=np_.inf, formatter=None, sign='-', floatmode='maxprec_equal', legacy=False)


def mpl_preferences(reset=False, backend=None, font_name='Times New Roman', font_size=13,
                    legend_spacing=0.7, fig_style=None):
    """
    Alter some `Matplotlib parameters
    <https://matplotlib.org/stable/api/matplotlib_configuration_api.html#matplotlib.rcParams>`_
    for plotting.

    This function allows customising various Matplotlib parameters such as backend, font settings,
    legend spacing and figure style.

    :param reset: Whether to reset all parameters to their default settings; defaults to ``False``.
    :type reset: bool
    :param backend: Specify the backend used for rendering and GUI integration; defaults to ``None``.
    :type backend: str | None
    :param font_name: Name of the font to be used; defaults to ``'Times New Roman'``.
    :type font_name: str | None
    :param font_size: Font size; defaults to ``13``.
    :type font_size: int | float
    :param legend_spacing: Spacing between labels in the plot legend; defaults to ``0.7``.
    :type legend_spacing: float | int
    :param fig_style: Style of the figure; defaults to ``None``.
    :type fig_style: str | None

    **Examples**::

        >>> import numpy as np
        >>> import matplotlib
        >>> matplotlib.use('TkAgg')
        >>> import matplotlib.pyplot as plt
        >>> np.random.seed(0)
        >>> random_array = np.random.rand(1000, 2)
        >>> random_array
        array([[0.5488135 , 0.71518937],
               [0.60276338, 0.54488318],
               [0.4236548 , 0.64589411],
               ...,
               [0.41443887, 0.79128155],
               [0.72119811, 0.48010781],
               [0.64386404, 0.50177313]])
        >>> def example_plot(arr):
        ...     fig = plt.figure(constrained_layout=True)
        ...     ax = fig.add_subplot(aspect='equal', adjustable='box')
        ...     ax.scatter(arr[:500, 0], arr[:500, 1], label='Group0')
        ...     ax.scatter(arr[500:, 0], arr[500:, 1], label='Group1')
        ...     ax.legend(frameon=False, bbox_to_anchor=(1.0, 0.95))
        ...     fig.show()
        >>> example_plot(random_array)
        >>> # from pyhelpers.store import save_fig
        >>> # save_fig("docs/source/_images/settings-mpl_preferences-demo-1.svg", verbose=True)
        >>> # save_fig("docs/source/_images/settings-mpl_preferences-demo-1.pdf", verbose=True)

    .. _label: settings-mpl_preferences-demo-1
    .. figure:: ../_images/settings-mpl_preferences-demo-1.*
        :name: settings-mpl_preferences-demo-1
        :align: center
        :width: 65%

        An example figure, before applying the function :func:`~pyhelpers.settings.mpl_preferences`.

    .. code-block:: python

        >>> from pyhelpers.settings import mpl_preferences
        >>> mpl_preferences(fig_style='ggplot')
        >>> example_plot(random_array)
        >>> # save_fig("docs/source/_images/settings-mpl_preferences-demo-2.svg", verbose=True)
        >>> # save_fig("docs/source/_images/settings-mpl_preferences-demo-2.pdf", verbose=True)

    .. figure:: ../_images/settings-mpl_preferences-demo-2.*
        :name: settings-mpl_preferences-demo-2
        :align: center
        :width: 65%

        After applying the function :func:`~pyhelpers.settings.mpl_preferences`.

    Reset to default settings:

    .. code-block:: python

        >>> mpl_preferences(reset=True)
        >>> # The altered parameters are now set to their default values.
        >>> example_plot(random_array)

    (The above code should display the same figure as :numref:`settings-mpl_preferences-demo-1`.)
    """

    mpl, mpl_style = map(_check_dependency, ['matplotlib', 'matplotlib.style'])

    if backend:
        mpl.use(backend=backend)

    if reset is False:
        if fig_style is not None:
            mpl_style.use(style=fig_style)

        mpl.rcParams['font.size'] = font_size
        # matplotlib.rcParams['font.weight'] = 'normal'
        mpl.rcParams['legend.labelspacing'] = legend_spacing

        if font_name:  # Use the font, 'Cambria'
            mpl_font_manager = _check_dependency(name='matplotlib.font_manager')

            if os.path.isfile(mpl_font_manager.findfont(font_name)):
                # Set 'font.family' to 'serif', then matplotlib will use that list
                mpl.rcParams['font.family'] = 'serif'
                serif_fonts = mpl.rcParams['font.serif']
                if font_name not in serif_fonts:
                    mpl.rcParams['font.serif'] = [font_name] + mpl.rcParams['font.serif']
                else:
                    serif_fonts.insert(0, serif_fonts.pop(serif_fonts.index(font_name)))
                    mpl.rcParams['font.serif'] = serif_fonts

    else:
        mpl_style.use(style='default')

        if reset == 'all':
            mpl.rcParams = mpl.rcParamsDefault

        elif reset is True:
            mpl.rcParams['font.size'] = 10.0
            mpl.rcParams['legend.labelspacing'] = 0.5
            mpl.rcParams['font.family'] = ['sans-serif']
            mpl.rcParams['font.serif'] = copy.copy(mpl.rcParamsDefault['font.serif'])
