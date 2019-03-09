""" Settings """

import matplotlib.pyplot
import numpy.core.arrayprint
import pandas


# Set preferences for plotting
def mpl_preferences(use_cambria=False, reset=False):
    """
    Get a list of supported file formats for matplotlib savefig() function
      plt.gcf().canvas.get_supported_filetypes()  # Aside: "gcf" is short for "get current fig" manager
      plt.gcf().canvas.get_supported_filetypes_grouped()
    """
    if not reset:
        if use_cambria:  # Use the font, 'Cambria'
            # Add 'Cambria' and 'Cambria Math' to the front of the 'font.serif' list
            matplotlib.pyplot.rcParams['font.serif'] = ['Cambria'] + matplotlib.pyplot.rcParams['font.serif']
            matplotlib.pyplot.rcParams['font.serif'] = ['Cambria Math'] + matplotlib.pyplot.rcParams['font.serif']
            # Set 'font.family' to 'serif', so that matplotlib will use that list
            matplotlib.pyplot.rcParams['font.family'] = 'serif'
        matplotlib.pyplot.rcParams['font.size'] = 13
        matplotlib.pyplot.rcParams['font.weight'] = 'normal'
        matplotlib.pyplot.rcParams['legend.labelspacing'] = 0.7
        matplotlib.pyplot.style.use('ggplot')
    else:
        matplotlib.pyplot.rcParams = matplotlib.rcParamsDefault
        matplotlib.pyplot.style.use('classic')


# Set preferences for displaying results
def np_preferences(reset=False):
    if not reset:
        numpy.core.arrayprint._line_width = 120
    else:
        numpy.core.arrayprint._line_width = 80  # 75


# Set preferences for displaying results
def pd_preferences(reset=False):
    if not reset:
        # pandas.set_option('display.float_format', lambda x: '%.4f' % x)
        pandas.set_option('display.precision', 2)
        pandas.set_option('expand_frame_repr', False)  # Set the representation of DataFrame NOT to wrap
        pandas.set_option('display.width', 600)  # Set the display width
        pandas.set_option('precision', 4)
        pandas.set_option('display.max_columns', 100)
        pandas.set_option('display.max_rows', 20)
        pandas.set_option('io.excel.xlsx.writer', 'xlsxwriter')
        pandas.set_option('mode.chained_assignment', None)
        # pandas.set_option('display.float_format', lambda x: '%.4f' % x)
    else:
        pandas.reset_option('all')


mpl_preferences(use_cambria=False, reset=False)
np_preferences(reset=False)
pd_preferences(reset=False)
