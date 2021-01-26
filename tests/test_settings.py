"""
Test module settings.py
"""

from pyhelpers.settings import *


def test_np_preferences():
    print("\nTesting 'np_preferences()':", end=" ... ")

    np_preferences(reset=False)

    np_preferences(reset=True)

    print("Done. ")


def test_pd_preferences():
    print("\nTesting 'pd_preferences()':", end=" ... ")

    pd_preferences(reset=False)

    import warnings
    warnings.filterwarnings(action='ignore')
    warnings.simplefilter(action='ignore', category=Warning)

    pd_preferences(reset=True)

    print("Done. ")


def test_mpl_preferences():
    print("\nTesting 'mpl_preferences()':", end=" ... ")

    mpl_preferences(reset=False)

    mpl_preferences(reset=True)

    print("Done. ")


def test_gdal_configurations():
    print("\nTesting 'gdal_configurations()':", end=" ... ")

    gdal_configurations(reset=False, max_tmpfile_size=5000)

    gdal_configurations(reset=True)

    print("Done. ")


if __name__ == '__main__':
    test_np_preferences()

    test_pd_preferences()

    test_mpl_preferences()

    test_gdal_configurations()
