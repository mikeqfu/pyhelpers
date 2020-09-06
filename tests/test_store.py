import matplotlib.pyplot as plt

from pyhelpers.store import *


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
    # `path_to_file` may not be a file path.

    path_to_file = cd(cd("test_store.py"))
    get_specific_filepath_info(path_to_file, verbose, vb_end, ret_info)
    print("Pass.")
    # Saving "test_store.py" to "<cwd>" ... Pass.

    path_to_file = cd("tests", "test_store.py")
    get_specific_filepath_info(path_to_file, verbose, vb_end, ret_info)
    print("Pass.")
    # Updating "test_store.py" at "..\\tests" ... Pass.


def test_save_pickle():
    from pyhelpers.dir import cd

    pickle_data = 1
    path_to_pickle = cd("tests\\data", "dat.pickle")
    mode = 'wb'
    verbose = True

    save_pickle(pickle_data, path_to_pickle, mode, verbose)
    # Saving "dat.pickle" to "..\\tests\\data" ... Done.


def test_load_pickle():
    from pyhelpers.dir import cd

    path_to_pickle = cd("tests\\data", "dat.pickle")
    mode = 'rb'
    verbose = True

    pickle_data = load_pickle(path_to_pickle, mode, verbose)
    # Loading "..\\tests\\data\\dat.pickle" ... Done.
    print(pickle_data)
    # 1


def test_save_json():
    from pyhelpers.dir import cd

    json_data = {'a': 1, 'b': 2, 'c': 3}
    path_to_json = cd("tests\\data", "dat.json")
    mode = 'w'
    verbose = True

    save_json(json_data, path_to_json, mode, verbose)
    # Saving "dat.json" to "..\\tests\\data" ... Done.


def test_load_json():
    from pyhelpers.dir import cd

    path_to_json = cd("tests\\data", "dat.json")
    mode = 'r'
    verbose = True

    json_data = load_json(path_to_json, mode, verbose)
    # Loading "..\tests\data\dat.json" ... Done.
    print(json_data)
    # {'a': 1, 'b': 2, 'c': 3}


def test_save_feather():
    from pyhelpers.dir import cd

    feather_data = pd.DataFrame({'Col1': 1, 'Col2': 2}, index=[0])
    path_to_feather = cd("tests\\data", "dat.feather")
    verbose = True

    save_feather(feather_data, path_to_feather, verbose)
    # Saving "dat.feather" to "..\\tests\\data" ... Done.


def test_load_feather():
    from pyhelpers.dir import cd

    path_to_feather = cd("tests\\data", "dat.feather")
    verbose = True

    feather_data = load_feather(path_to_feather, verbose)
    # Loading "..\\tests\\data\\dat.feather" ... Done.
    print(feather_data)
    #    Col1  Col2
    # 0     1     2


def test_save_spreadsheet():
    from pyhelpers.dir import cd

    spreadsheet_data = pd.DataFrame({'Col1': 1, 'Col2': 2}, index=['data'])
    index = False
    delimiter = ','
    verbose = True

    path_to_spreadsheet = cd("tests\\data", "dat.csv")
    # path_to_spreadsheet = cd("tests\\data", "dat.txt")
    save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index, delimiter, verbose)
    # Saving "dat.csv" to "..\\tests\\data" ... Done.

    path_to_spreadsheet = cd("tests\\data", "dat.xls")
    save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index, delimiter, verbose)
    # Saving "dat.xls" to "..\\tests\\data" ... Done.

    path_to_spreadsheet = cd("tests\\data", "dat.xlsx")
    save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index, delimiter, verbose)
    # Saving "dat.xlsx" to "..\\tests\\data" ... Done.


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
    save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, mode, index, verbose=verbose)
    # Updating "dat.xlsx" at "..\\tests\\data" ...
    #   'TestSheet1' ... Done.
    #   'TestSheet2' ... Done.

    mode = 'a'
    save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, mode, index, verbose=verbose)
    # Updating "dat.xlsx" at "..\\tests\\data" ...
    #   'TestSheet1' ... 'TestSheet1' already exists; adding a suffix to the sheet name? [No]|Yes: yes
    # TestSheet11 ... Done.
    #   'TestSheet2' ... 'TestSheet2' already exists; adding a suffix to the sheet name? [No]|Yes: yes
    # TestSheet21 ... Done.

    mode = 'a'
    confirmation_required = False
    save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, mode, index,
                               confirmation_required, verbose)
    # Updating "dat.xlsx" at "..\\tests\\data" ...
    #   'TestSheet1' ... TestSheet12 ... Done.
    #   'TestSheet2' ... TestSheet22 ... Done.


def test_load_multiple_spreadsheets():
    from pyhelpers.dir import cd

    path_to_spreadsheet = cd("tests\\data", "dat.xlsx")
    verbose = True

    as_dict = True
    workbook_data = load_multiple_spreadsheets(path_to_spreadsheet, as_dict, verbose, index_col=0)
    # Loading "..\\tests\\data\\dat.xlsx" ...
    #   'TestSheet1'. ... Done.
    #   'TestSheet2'. ... Done.
    #   'TestSheet11'. ... Done.
    #   'TestSheet21'. ... Done.
    #   'TestSheet12'. ... Done.
    #   'TestSheet22'. ... Done.
    print(workbook_data.keys())
    # dict_keys(['TestSheet1', 'TestSheet2', 'TestSheet11', 'TestSheet21', 'TestSheet12', 'TestSheet22'])

    as_dict = False
    workbook_data = load_multiple_spreadsheets(path_to_spreadsheet, as_dict, verbose, index_col=0)
    # Loading "..\\tests\\data\\dat.xlsx" ...
    #   'TestSheet1'. ... Done.
    #   'TestSheet2'. ... Done.
    #   'TestSheet11'. ... Done.
    #   'TestSheet21'. ... Done.
    #   'TestSheet12'. ... Done.
    #   'TestSheet22'. ... Done.
    print(len(workbook_data))
    # 6


def test_save():
    from pyhelpers.dir import cd

    data = pd.DataFrame([(530034, 180381), (406689, 286822), (383819, 398052), (582044, 152953)],
                        index=['London', 'Birmingham', 'Manchester', 'Leeds'],
                        columns=['Easting', 'Northing'])

    path_to_file = cd("tests\\data", "dat.txt")
    save(data, path_to_file, verbose=True)
    # Updating "dat.txt" at "..\\tests\\data" ... Done.

    path_to_file = cd("tests\\data", "dat.csv")
    save(data, path_to_file, verbose=True)
    # Updating "dat.csv" at "..\\tests\\data" ... Done.

    path_to_file = cd("tests\\data", "dat.xlsx")
    save(data, path_to_file, verbose=True)
    # Updating "dat.xlsx" at "..\\tests\\data" ... Done.

    path_to_file = cd("tests\\data", "dat.pickle")
    save(data, path_to_file, verbose=True)
    # Updating "dat.pickle" at "..\\tests\\data" ... Done.

    path_to_file = cd("tests\\data", "dat.feather")
    # `save(data, path_to_file, verbose=True)` will produce an error due to the index of `data`
    save(data.reset_index(), path_to_file, verbose=True)
    # Updating "dat.feather" at "..\\tests\\data" ... Done.


def test_save_fig():

    from pyhelpers.dir import cd

    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])
    # plt.show()

    path_to_fig_file = cd("tests\\images", "fig.png")
    save_fig(path_to_fig_file, dpi=300, verbose=True)
    # Saving "fig.png" to "..\\tests\\images" ... Done.

    path_to_fig_file = cd("tests\\images", "fig.svg")
    save_fig(path_to_fig_file, dpi=300, verbose=True, conv_svg_to_emf=True)
    # Saving "fig.svg" to "..\\tests\\images" ... Done.
    # Saving the "fig.svg" as "..\\tests\\images\\fig.emf" ... Done.


def test_save_svg_as_emf():
    from pyhelpers.dir import cd

    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    path_to_svg = cd("tests\\images", "fig.svg")
    path_to_emf = cd("tests\\images", "fig.emf")

    save_svg_as_emf(path_to_svg, path_to_emf, verbose=True)
    # Saving the "fig.svg" as "..\\tests\\images\\fig.emf" ... Done.


def test_unzip():
    from pyhelpers.dir import cd

    path_to_zip_file = cd("tests\\data", "zipped.zip")
    out_dir = cd("tests\\data")
    mode = 'r'

    unzip(path_to_zip_file, out_dir, mode, verbose=True)
    # Unzipping "..\\tests\\data\\zipped.zip" ... Done.


def test_seven_zip():
    from pyhelpers.dir import cd

    out_dir = cd("tests\\data")
    mode = 'aoa'

    path_to_zip_file = cd("tests\\data", "zipped.zip")
    seven_zip(path_to_zip_file, out_dir, mode, verbose=True)

    path_to_zip_file = cd("tests\\data", "zipped.7z")
    seven_zip(path_to_zip_file, out_dir, mode, verbose=True)


def test_load_csr_matrix():
    import scipy.sparse
    from pyhelpers.dir import cd

    indptr = np.array([0, 2, 3, 6])
    indices = np.array([0, 2, 2, 0, 1, 2])
    data = np.array([1, 2, 3, 4, 5, 6])
    csr_m = scipy.sparse.csr_matrix((data, indices, indptr), shape=(3, 3))

    path_to_csr = cd("tests\\data", "csr_mat.npz")
    np.savez_compressed(path_to_csr,
                        indptr=csr_m.indptr,
                        indices=csr_m.indices,
                        data=csr_m.data,
                        shape=csr_m.shape)

    csr_mat = load_csr_matrix(path_to_csr, verbose=True)
    # Loading "..\\tests\\data\\csr_mat.npz" ... Done.

    # .nnz gets the count of explicitly-stored values (non-zeros)
    print((csr_mat != csr_m).count_nonzero() == 0)
    # True

    print((csr_mat != csr_m).nnz == 0)
    # True


if __name__ == '__main__':
    print("\nTesting 'get_specific_filepath_info()':")

    test_get_specific_filepath_info()

    print("\nTesting 'save_pickle()':")

    test_save_pickle()

    print("\nTesting 'load_pickle()':")

    test_load_pickle()

    print("\nTesting 'save_json()':")

    test_save_json()

    print("\nTesting 'load_json()':")

    test_load_json()

    print("\nTesting 'save_feather()':")

    test_save_feather()

    print("\nTesting 'load_feather()':")

    test_load_feather()

    print("\nTesting 'save_spreadsheet()':")

    test_save_spreadsheet()

    print("\nTesting 'save_multiple_spreadsheets()':")

    test_save_multiple_spreadsheets()

    print("\nTesting 'load_multiple_spreadsheets()':")

    test_load_multiple_spreadsheets()

    print("\nTesting 'save()':")

    test_save()

    print("\nTesting 'save_fig()':")

    test_save_fig()

    plt.show()

    print("\nTesting 'save_svg_as_emf()':")

    test_save_svg_as_emf()

    plt.show()

    print("\nTesting 'unzip()':")

    test_unzip()

    print("\nTesting 'seven_zip()':")

    test_seven_zip()

    print("\nTesting 'load_csr_matrix()':")

    test_load_csr_matrix()
