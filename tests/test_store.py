"""
Test module store.py
"""

import matplotlib.pyplot as plt
import numpy as np

from pyhelpers.dir import cd, cdd
from pyhelpers.store import *


# General use ------------------------------------------------------------------------------------

def test_get_specific_filepath_info():
    verbose = True
    vb_end = " ... "
    ret_info = False

    path_to_file = cd()
    try:
        get_specific_filepath_info(path_to_file, verbose, vb_end, ret_info)
    except AssertionError as e:
        print(e)
    # The input for `path_to_file` may not be a file path.

    path_to_file = cd("test_store.py")
    get_specific_filepath_info(path_to_file, verbose, vb_end, ret_info)
    print("Pass.")
    # Updating "test_store.py" ... Pass.


# Save files -------------------------------------------------------------------------------------

def test_save():
    data = pd.DataFrame(
        [(530034, 180381), (406689, 286822), (383819, 398052), (582044, 152953)],
        index=['London', 'Birmingham', 'Manchester', 'Leeds'],
        columns=['Easting', 'Northing'])

    path_to_file = cdd("dat.txt")
    save(data, path_to_file, verbose=True)
    # Saving "dat.csv" to "\\data" ... Done.

    path_to_file = cdd("dat.csv")
    save(data, path_to_file, verbose=True)
    # Saving "dat.csv" to "\\data" ... Done.

    path_to_file = cdd("dat.xlsx")
    save(data, path_to_file, verbose=True)
    # Saving "dat.xlsx" to "\\data" ... Done.

    path_to_file = cdd("dat.pickle")
    save(data, path_to_file, verbose=True)
    # Saving "dat.pickle" to "\\data" ... Done.

    path_to_file = cdd("dat.feather")
    save(data.reset_index(), path_to_file, verbose=True)
    # Saving "dat.feather" to "\\data" ... Done.


def test_save_pickle():
    pickle_data = 1
    path_to_pickle = cdd("dat.pickle")
    mode = 'wb'
    verbose = True

    save_pickle(pickle_data, path_to_pickle, mode, verbose)
    # Updating "dat.pickle" at "\\data" ... Done.


def test_save_spreadsheet():
    import warnings

    warnings.simplefilter(action='ignore', category=FutureWarning)

    spreadsheet_data = pd.DataFrame({'Col1': 1, 'Col2': 2}, index=['data'])
    index = False
    engine = None
    delimiter = ','
    verbose = True

    path_to_spreadsheet = cdd("dat.csv")
    # path_to_spreadsheet = cdd("dat.txt")
    save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index, engine, delimiter, verbose)
    # Updating "dat.csv" at "\\data" ... Done.

    path_to_spreadsheet = cdd("dat.xls")
    save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index, engine, delimiter, verbose)
    # Saving "dat.xls" to "\\data" ... Done.

    path_to_spreadsheet = cdd("dat.xlsx")
    save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index, engine, delimiter, verbose)
    # Updating "dat.xlsx" at "\\data" ... Done.


def test_save_multiple_spreadsheets():
    xy_array = np.array([(530034, 180381),  # London
                         (406689, 286822),  # Birmingham
                         (383819, 398052),  # Manchester
                         (582044, 152953)])  # Leeds

    dat1 = pd.DataFrame(xy_array,
                        index=['London', 'Birmingham', 'Manchester', 'Leeds'],
                        columns=['Easting', 'Northing'])

    dat2 = dat1.T

    spreadsheets_data = [dat1, dat2]
    sheet_names = ['TestSheet1', 'TestSheet2']
    path_to_spreadsheet = cdd("dat.xlsx")
    engine = None
    index = True
    verbose = True

    mode = 'w'
    save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, engine, mode, index,
                               verbose=verbose)
    # Updating "dat.xlsx" at "\\data" ...
    # 	'TestSheet1' ... Done.
    # 	'TestSheet2' ... Done.

    mode = 'a'
    save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, engine, mode, index,
                               verbose=verbose)
    # Updating "dat.xlsx" at "\\data" ...
    # 	'TestSheet1' ... This sheet already exists;
    # 		add a suffix to the sheet name? [No]|Yes: yes
    # 		saved as 'TestSheet11' ... Done.
    # 	'TestSheet2' ... This sheet already exists;
    # 		add a suffix to the sheet name? [No]|Yes: yes
    # 		saved as 'TestSheet21' ... Done.

    mode = 'a'
    confirmation_required = False
    save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, engine, mode, index,
                               confirmation_required, verbose)
    # Updating "dat.xlsx" at "\\data" ...
    # 	'TestSheet1' ...
    # 		saved as 'TestSheet12' ... Done.
    # 	'TestSheet2' ...
    # 		saved as 'TestSheet22' ... Done.


def test_save_json():
    json_data = {'a': 1, 'b': 2, 'c': 3}
    path_to_json = cdd("dat.json")
    mode = 'w'
    verbose = True

    save_json(json_data, path_to_json, mode, verbose)
    # Saving "dat.json" to "\\data" ... Done.


def test_save_feather():
    feather_data = pd.DataFrame({'Col1': 1, 'Col2': 2}, index=[0])
    path_to_feather = cdd("dat.feather")
    verbose = True

    save_feather(feather_data, path_to_feather, verbose)
    # Updating "dat.feather" at "\\data" ... Done.


def test_save_fig():
    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])
    # plt.show()

    path_to_fig_file = cd("images", "fig.png")
    save_fig(path_to_fig_file, dpi=300, verbose=True)
    # Saving "fig.png" to "\\images" ... Done.

    path_to_fig_file = cd("images", "fig.svg")
    save_fig(path_to_fig_file, dpi=300, verbose=True, conv_svg_to_emf=True)
    # Saving "fig.svg" to "\\images" ... Done.
    # Saving the "fig.svg" as "\\images\\fig.emf" ... Done.


def test_save_svg_as_emf():
    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    path_to_svg = cd("images", "fig.svg")
    path_to_emf = cd("images", "fig.emf")

    save_svg_as_emf(path_to_svg, path_to_emf, verbose=True)
    # Saving the "fig.svg" as "\\images\\fig.emf" ... Done.


def test_save_web_page_as_pdf():
    page_size = 'A4'
    zoom = 1.0
    encoding = 'UTF-8'
    verbose = True

    url_to_web_page = 'https://github.com/mikeqfu/pyhelpers'
    path_to_pdf = cdd("pyhelpers.pdf")

    save_web_page_as_pdf(url_to_web_page, path_to_pdf, page_size, zoom, encoding, verbose)
    # Saving "pyhelpers.pdf" to "\\data" ...
    # Loading pages (1/6)
    # Counting pages (2/6)
    # Resolving links (4/6)
    # Loading headers and footers (5/6)
    # Printing pages (6/6)
    # Done


# Load files -------------------------------------------------------------------------------------

def test_load_pickle():
    path_to_pickle = cdd("dat.pickle")
    mode = 'rb'
    verbose = True

    pickle_data = load_pickle(path_to_pickle, mode, verbose)
    # Loading "\\data\\dat.pickle" ... Done.
    print(pickle_data)
    # 1


def test_load_multiple_spreadsheets():
    path_to_spreadsheet = cdd("dat.xlsx")
    verbose = True

    as_dict = True
    workbook_data = load_multiple_spreadsheets(path_to_spreadsheet, as_dict, verbose, index_col=0)
    # Loading "\\data\\dat.xlsx" ...
    # 	'TestSheet1'. ... Done.
    # 	'TestSheet2'. ... Done.
    # 	'TestSheet11'. ... Done.
    # 	'TestSheet21'. ... Done.
    # 	'TestSheet12'. ... Done.
    # 	'TestSheet22'. ... Done.
    print(list(workbook_data.keys()))
    # ['TestSheet1', 'TestSheet2', 'TestSheet11', 'TestSheet21', 'TestSheet12', 'TestSheet22']

    as_dict = False
    workbook_data = load_multiple_spreadsheets(path_to_spreadsheet, as_dict, verbose, index_col=0)
    # Loading "\\data\\dat.xlsx" ...
    # 	'TestSheet1'. ... Done.
    # 	'TestSheet2'. ... Done.
    # 	'TestSheet11'. ... Done.
    # 	'TestSheet21'. ... Done.
    # 	'TestSheet12'. ... Done.
    # 	'TestSheet22'. ... Done.
    print(len(workbook_data))
    # 6


def test_load_json():
    path_to_json = cdd("dat.json")
    mode = 'r'
    verbose = True

    json_data = load_json(path_to_json, mode, verbose)
    # Loading "\\data\\dat.json" ... Done.
    print(json_data)
    # {'a': 1, 'b': 2, 'c': 3}


def test_load_feather():
    path_to_feather = cdd("dat.feather")
    verbose = True

    feather_data = load_feather(path_to_feather, verbose)
    # Loading "\\data\\dat.feather" ... Done.
    print(feather_data)
    #    Col1  Col2
    # 0     1     2


# Uncompress files -------------------------------------------------------------------------------

def test_unzip():
    path_to_zip_file = cdd("zipped.zip")
    out_dir = cdd()
    mode = 'r'

    unzip(path_to_zip_file, out_dir, mode, verbose=True)
    # Unzipping "\\data\\zipped.zip" ... Done.


def test_seven_zip():
    out_dir = cdd()
    mode = 'aoa'

    path_to_zip_file = cd(out_dir, "zipped.zip")
    seven_zip(path_to_zip_file, out_dir, mode, verbose=True)
    # 7-Zip 20.00 alpha (x64) : Copyright (c) 1999-2020 Igor Pavlov : 2020-02-06
    #
    # Scanning the drive for archives:
    # 1 file, 158 bytes (1 KiB)
    #
    # Extracting archive: D:\DataShare\Experiments\pyhelpers\tests\data\zipped.zip
    # --
    # Path = D:\DataShare\Experiments\pyhelpers\tests\data\zipped.zip
    # Type = zip
    # Physical Size = 158
    #
    # Everything is Ok
    #
    # Size:       4
    # Compressed: 158
    #
    # File extracted successfully.

    path_to_zip_file = cd(out_dir, "zipped.7z")
    seven_zip(path_to_zip_file, out_dir, mode, verbose=True)
    # 7-Zip 20.00 alpha (x64) : Copyright (c) 1999-2020 Igor Pavlov : 2020-02-06
    #
    # Scanning the drive for archives:
    # 1 file, 138 bytes (1 KiB)
    #
    # Extracting archive: D:\DataShare\Experiments\pyhelpers\tests\data\zipped.7z
    # --
    # Path = D:\DataShare\Experiments\pyhelpers\tests\data\zipped.7z
    # Type = 7z
    # Physical Size = 138
    # Headers Size = 130
    # Method = LZMA2:12
    # Solid = -
    # Blocks = 1
    #
    # Everything is Ok
    #
    # Size:       4
    # Compressed: 138
    #
    # File extracted successfully.


if __name__ == '__main__':
    # General use --------------------------------------------------------------------------------

    print("\nTesting 'get_specific_filepath_info()':")
    test_get_specific_filepath_info()

    # Save files ---------------------------------------------------------------------------------

    print("\nTesting 'save()':")
    test_save()

    print("\nTesting 'save_pickle()':")
    test_save_pickle()

    print("\nTesting 'save_spreadsheet()':")
    test_save_spreadsheet()

    print("\nTesting 'save_multiple_spreadsheets()':")
    test_save_multiple_spreadsheets()

    print("\nTesting 'save_json()':")
    test_save_json()

    print("\nTesting 'save_feather()':")
    test_save_feather()

    print("\nTesting 'save_fig()':")
    test_save_fig()

    plt.show()

    print("\nTesting 'save_svg_as_emf()':")
    test_save_svg_as_emf()

    plt.show()

    print("\nTesting 'save_web_page_as_pdf()':")
    test_save_web_page_as_pdf()

    # Load files ---------------------------------------------------------------------------------

    print("\nTesting 'load_pickle()':")
    test_load_pickle()

    print("\nTesting 'load_multiple_spreadsheets()':")
    test_load_multiple_spreadsheets()

    print("\nTesting 'load_json()':")
    test_load_json()

    print("\nTesting 'load_feather()':")
    test_load_feather()

    # Uncompress files ---------------------------------------------------------------------------

    print("\nTesting 'unzip()':")
    test_unzip()

    print("\nTesting 'seven_zip()':")
    test_seven_zip()
