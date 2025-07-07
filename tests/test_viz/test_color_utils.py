import matplotlib.cm
import matplotlib.pyplot as plt
import pytest

from pyhelpers.viz.color_utils import *


def test_cmap_discretisation():
    cm_accent = cmap_discretization(matplotlib.colormaps['Accent'], n_colors=5)
    assert cm_accent.name == 'Accent_5'


def test_colour_bar_index():
    plt.figure(figsize=(2, 6))

    cbar = color_bar_index(cmap=matplotlib.colormaps['Accent'], n_colors=5, labels=list('abcde'))
    cbar.ax.tick_params(labelsize=14)

    plt.close(fig='all')


if __name__ == '__main__':
    pytest.main()
