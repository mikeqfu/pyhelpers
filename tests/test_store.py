"""
Test module store.py
"""

import matplotlib.pyplot as plt
import numpy as np

from pyhelpers.store import *


# General use --------------------------------------------------------------------------

def test_get_specific_filepath_info():
    verbose = True
    vb_end = " ... "
    ret_info = False

    from pyhelpers.dir import cd

    path_to_file = cd()
    try:
        get_specific_filepath_info(path_to_file, verbose, vb_end, ret_info)
    except AssertionError as e:
        print(e)
    # The input for `path_to_file` may not be a file path.

    path_to_file = cd(cd("test_store.py"))
    get_specific_filepath_info(path_to_file, verbose, vb_end, ret_info)
    print("Pass.")
    # Saving "test_store.py" ... Pass.

    path_to_file = cd("tests", "test_store.py")
    get_specific_filepath_info(path_to_file, verbose, vb_end, ret_info)
    print("Pass.")
    # Updating "test_store.py" at "\\tests" ... Pass.


# Save files ---------------------------------------------------------------------------

def test_save():
    from pyhelpers.dir import cd

    data = pd.DataFrame(
        [(530034, 180381), (406689, 286822), (383819, 398052), (582044, 152953)],
        index=['London', 'Birmingham', 'Manchester', 'Leeds'],
        columns=['Easting', 'Northing'])

    dat_dir = cd("tests\\data")

    path_to_file = cd(dat_dir, "dat.txt")
    save(data, path_to_file, verbose=True)
    # Updating "dat.txt" at "\\tests\\data" ... Done.

    path_to_file = cd(dat_dir, "dat.csv")
    save(data, path_to_file, verbose=True)
    # Updating "dat.csv" at "\\tests\\data" ... Done.

    path_to_file = cd(dat_dir, "dat.xlsx")
    save(data, path_to_file, verbose=True)
    # Updating "dat.xlsx" at "\\tests\\data" ... Done.

    path_to_file = cd(dat_dir, "dat.pickle")
    save(data, path_to_file, verbose=True)
    # Updating "dat.pickle" at "\\tests\\data" ... Done.

    path_to_file = cd(dat_dir, "dat.feather")
    save(data.reset_index(), path_to_file, verbose=True)
    # Updating "dat.feather" at "\\tests\\data" ... Done.


def test_save_pickle():
    from pyhelpers.dir import cd

    pickle_data = 1
    path_to_pickle = cd("tests\\data", "dat.pickle")
    mode = 'wb'
    verbose = True

    save_pickle(pickle_data, path_to_pickle, mode, verbose)
    # Saving "dat.pickle" to "\\tests\\data" ... Done.


def test_save_spreadsheet():
    from pyhelpers.dir import cd

    spreadsheet_data = pd.DataFrame({'Col1': 1, 'Col2': 2}, index=['data'])
    index = False
    delimiter = ','
    verbose = True

    path_to_spreadsheet = cd("tests\\data", "dat.csv")
    # path_to_spreadsheet = cd("tests\\data", "dat.txt")
    save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index, delimiter, verbose)
    # Saving "dat.csv" to "\\tests\\data" ... Done.

    path_to_spreadsheet = cd("tests\\data", "dat.xls")
    save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index, delimiter, verbose)
    # Saving "dat.xls" to "\\tests\\data" ... Done.

    path_to_spreadsheet = cd("tests\\data", "dat.xlsx")
    save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index, delimiter, verbose)
    # Saving "dat.xlsx" to "\\tests\\data" ... Done.


def test_save_multiple_spreadsheets():
    from pyhelpers.dir import cd

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
    path_to_spreadsheet = cd("tests\\data", "dat.xlsx")
    index = True
    verbose = True

    mode = 'w'
    save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet,
                               mode, index, verbose=verbose)
    # Updating "dat.xlsx" at "\\tests\\data" ...
    #   'TestSheet1' ... Done.
    #   'TestSheet2' ... Done.

    mode = 'a'
    save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet,
                               mode, index, verbose=verbose)
    # Updating "dat.xlsx" at "\\tests\\data" ...
    # 	'TestSheet1' ... This sheet already exists;
    # 		add a suffix to the sheet name? [No]|Yes: >? yes
    # 		saved as 'TestSheet11' ... Done.
    # 	'TestSheet2' ... This sheet already exists;
    # 		add a suffix to the sheet name? [No]|Yes: >? yes
    # 		saved as 'TestSheet21' ... Done.

    mode = 'a'
    confirmation_required = False
    save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet,
                               mode, index, confirmation_required, verbose)
    # Updating "dat.xlsx" at "\tests\data" ...
    # 	'TestSheet1' ...
    # 		saved as 'TestSheet12' ... Done.
    # 	'TestSheet2' ...
    # 		saved as 'TestSheet22' ... Done.


def test_save_json():
    from pyhelpers.dir import cd

    json_data = {'a': 1, 'b': 2, 'c': 3}
    path_to_json = cd("tests\\data", "dat.json")
    mode = 'w'
    verbose = True

    save_json(json_data, path_to_json, mode, verbose)
    # Saving "dat.json" to "\\tests\\data" ... Done.


def test_save_feather():
    from pyhelpers.dir import cd

    feather_data = pd.DataFrame({'Col1': 1, 'Col2': 2}, index=[0])
    path_to_feather = cd("tests\\data", "dat.feather")
    verbose = True

    save_feather(feather_data, path_to_feather, verbose)
    # Saving "dat.feather" to "\\tests\\data" ... Done.


def test_save_fig():
    from pyhelpers.dir import cd

    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])
    # plt.show()

    img_dir = cd("tests\\images")

    path_to_fig_file = cd(img_dir, "fig.png")
    save_fig(path_to_fig_file, dpi=300, verbose=True)
    # Saving "fig.png" to "\\tests\\images" ... Done.

    path_to_fig_file = cd(img_dir, "fig.svg")
    save_fig(path_to_fig_file, dpi=300, verbose=True, conv_svg_to_emf=True)
    # Saving "fig.svg" to "\\tests\\images" ... Done.
    # Saving the "fig.svg" as "\\tests\\images\\fig.emf" ... Done.


def test_save_svg_as_emf():
    from pyhelpers.dir import cd

    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    img_dir = cd("tests\\images")

    path_to_svg = cd(img_dir, "fig.svg")
    path_to_emf = cd(img_dir, "fig.emf")

    save_svg_as_emf(path_to_svg, path_to_emf, verbose=True)
    # Saving the "fig.svg" as "\\tests\\images\\fig.emf" ... Done.


def test_save_web_page_as_pdf():
    from pyhelpers.dir import cd

    page_size = 'A4'
    zoom = 1.0
    encoding = 'UTF-8'
    verbose = True

    url_to_web_page = 'https://github.com/mikeqfu/pyhelpers'
    path_to_pdf = cd("tests\\data", "pyhelpers.pdf")

    save_web_page_as_pdf(url_to_web_page, path_to_pdf, page_size, zoom, encoding, verbose)
    # Saving "pyhelpers.pdf" to "..\\tests\\data" ...
    # Loading pages (1/6)
    # Counting pages (2/6)
    # Resolving links (4/6)
    # Loading headers and footers (5/6)
    # Printing pages (6/6)
    # Done


# Load files ---------------------------------------------------------------------------

def test_load_pickle():
    from pyhelpers.dir import cd

    path_to_pickle = cd("tests\\data", "dat.pickle")
    mode = 'rb'
    verbose = True

    pickle_data = load_pickle(path_to_pickle, mode, verbose)
    # Loading "\\tests\\data\\dat.pickle" ... Done.
    print(pickle_data)
    # 1


def test_load_multiple_spreadsheets():
    from pyhelpers.dir import cd

    path_to_spreadsheet = cd("tests\\data", "dat.xlsx")
    verbose = True

    as_dict = True
    workbook_data = load_multiple_spreadsheets(path_to_spreadsheet, as_dict, verbose,
                                               index_col=0)
    # Loading "\\tests\\data\\dat.xlsx" ...
    #   'TestSheet1'. ... Done.
    #   'TestSheet2'. ... Done.
    #   'TestSheet11'. ... Done.
    #   'TestSheet21'. ... Done.
    #   'TestSheet12'. ... Done.
    #   'TestSheet22'. ... Done.
    print(list(workbook_data.keys()))
    # ['TestSheet1', 'TestSheet2', 'TestSheet11', 'TestSheet21',
    #  'TestSheet12', 'TestSheet22']

    as_dict = False
    workbook_data = load_multiple_spreadsheets(path_to_spreadsheet, as_dict, verbose,
                                               index_col=0)
    # Loading "\\tests\\data\\dat.xlsx" ...
    #   'TestSheet1'. ... Done.
    #   'TestSheet2'. ... Done.
    #   'TestSheet11'. ... Done.
    #   'TestSheet21'. ... Done.
    #   'TestSheet12'. ... Done.
    #   'TestSheet22'. ... Done.
    print(len(workbook_data))
    # 6


def test_load_json():
    from pyhelpers.dir import cd

    path_to_json = cd("tests\\data", "dat.json")
    mode = 'r'
    verbose = True

    json_data = load_json(path_to_json, mode, verbose)
    # Loading "..\tests\data\dat.json" ... Done.
    print(json_data)
    # {'a': 1, 'b': 2, 'c': 3}


def test_load_feather():
    from pyhelpers.dir import cd

    path_to_feather = cd("tests\\data", "dat.feather")
    verbose = True

    feather_data = load_feather(path_to_feather, verbose)
    # Loading "\\tests\\data\\dat.feather" ... Done.
    print(feather_data)
    #    Col1  Col2
    # 0     1     2


# Uncompress files ---------------------------------------------------------------------

def test_unzip():
    from pyhelpers.dir import cd

    dat_dir = cd("tests\\data")

    path_to_zip_file = cd(dat_dir, "zipped.zip")
    out_dir = cd(dat_dir)
    mode = 'r'

    unzip(path_to_zip_file, out_dir, mode, verbose=True)
    # Unzipping "\\tests\\data\\zipped.zip" ... Done.


def test_seven_zip():
    from pyhelpers.dir import cd

    out_dir = cd("tests\\data")
    mode = 'aoa'

    path_to_zip_file = cd(out_dir, "zipped.zip")
    seven_zip(path_to_zip_file, out_dir, mode, verbose=True)

    path_to_zip_file = cd(out_dir, "zipped.7z")
    seven_zip(path_to_zip_file, out_dir, mode, verbose=True)


if __name__ == '__main__':
    # General use ----------------------------------------------------------------------

    print("\nTesting 'get_specific_filepath_info()':")
    test_get_specific_filepath_info()

    # Save files -----------------------------------------------------------------------

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

    # Load files -----------------------------------------------------------------------

    print("\nTesting 'load_pickle()':")
    test_load_pickle()

    print("\nTesting 'load_multiple_spreadsheets()':")
    test_load_multiple_spreadsheets()

    print("\nTesting 'load_json()':")
    test_load_json()

    print("\nTesting 'load_feather()':")
    test_load_feather()

    # Uncompress files -----------------------------------------------------------------

    print("\nTesting 'unzip()':")
    test_unzip()

    print("\nTesting 'seven_zip()':")
    test_seven_zip()
