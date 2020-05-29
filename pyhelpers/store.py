""" Save and Load files """

import os
import pathlib
import pickle
import subprocess
import zipfile

import numpy as np
import pandas as pd
import rapidjson

from pyhelpers.ops import confirmed


# Get information about the path of a file
def get_specific_filepath_info(path_to_file, verbose=False, verbose_end=" ... ", ret_info=False):
    """
    :param path_to_file: [str] path where a file is saved
    :param verbose: [bool] whether to show illustrative messages (default: False)
    :param verbose_end: [str] (default: " ... ")
    :param ret_info: [bool] whether to return the file path information
    :return (f_dir_parent, f_dir, filename): parent directory, current directory and name of the file

    Example:
        from pyhelpers.dir import cd

        path_to_file = cd()
        verbose = True
        verbose_end = " ... "
        ret_info = True

        get_specific_filepath_info(path_to_file, verbose, verbose_end, ret_info)
    """
    abs_path_to_file = pathlib.Path(path_to_file).absolute()

    filename = pathlib.Path(abs_path_to_file).name
    rel_path = abs_path_to_file.parent.relative_to(abs_path_to_file.cwd())

    # The specified path exists?
    abs_path_to_file.parent.mkdir(exist_ok=True)  # os.makedirs(abs_path_to_file.parent, exist_ok=True)

    if verbose:
        status, prep = ("Updating", "to") if os.path.isfile(abs_path_to_file) else ("Saving", "at")
        print("{} \"{}\" {} \"..\\{}\"".format(status, filename, prep, rel_path),
              end=verbose_end if verbose_end else "\n")

    if ret_info:
        return rel_path, filename


# Save pickle file
def save_pickle(pickle_data, path_to_pickle, mode='wb', verbose=False, **kwargs):
    """
    :param pickle_data: data that could be dumped by the 'pickle' package
    :param path_to_pickle: [str] path where a pickle file is saved
    :param mode: [str] mode to `open()` file (default: 'wb')
    :param verbose: [bool] whether to show illustrative messages (default: False)
    :param kwargs: optional arguments used by `open()`

    Example:
        from pyhelpers.dir import cd

        pickle_data = 1
        path_to_pickle = cd("tests\\data", "dat.pickle")
        mode = 'wb'
        verbose = True

        save_pickle(pickle_data, path_to_pickle, mode, verbose)
    """
    get_specific_filepath_info(path_to_pickle, verbose=verbose, ret_info=False)

    try:
        pickle_out = open(path_to_pickle, mode=mode, **kwargs)
        pickle.dump(pickle_data, pickle_out)
        pickle_out.close()
        print("Successfully.") if verbose else ""
    except Exception as e:
        print("Failed. {}.".format(e))


# Load pickle file
def load_pickle(path_to_pickle, mode='rb', verbose=False, **kwargs):
    """
    :param path_to_pickle: [str] path where a pickle file is saved
    :param mode: [str] mode to `open()` file (default: 'rb')
    :param verbose: [bool] whether to show illustrative messages (default: False)
    :param kwargs: optional arguments used by `open()`
    :return pickle_data: data retrieved from the specified path

    Example:
        from pyhelpers.dir import cd

        path_to_pickle = cd("tests\\data", "dat.pickle")
        mode = 'rb'
        verbose = True

        pickle_data = load_pickle(path_to_pickle, mode, verbose)  # pickle_data == 1
    """
    print("Loading \"..\\{}\"".format(os.path.relpath(path_to_pickle)), end=" ... ") if verbose else ""
    try:
        pickle_in = open(path_to_pickle, mode=mode, **kwargs)
        pickle_data = pickle.load(pickle_in)
        pickle_in.close()
        print("Successfully.") if verbose else ""
        return pickle_data
    except Exception as e:
        print("Failed. {}".format(e)) if verbose else ""


# Save json file
def save_json(json_data, path_to_json, mode='w', verbose=False, **kwargs):
    """
    :param json_data: data that could be dumped by the 'json' package
    :param path_to_json: [str] path where a json file is saved
    :param mode: [str] mode to `open()` file (default: 'w')
    :param verbose: [bool] whether to show illustrative messages (default: False)
    :param kwargs: optional arguments used by `open()`

    Example:
        from pyhelpers.dir import cd

        json_data = {'a': 1, 'b': 2, 'c': 3}
        path_to_json = cd("tests\\data", "dat.json")
        mode = 'w'
        verbose = True

        save_json(json_data, path_to_json, mode, verbose)
    """
    get_specific_filepath_info(path_to_json, verbose=verbose, ret_info=False)

    try:
        json_out = open(path_to_json, mode=mode, **kwargs)
        rapidjson.dump(json_data, json_out)
        json_out.close()
        print("Successfully.") if verbose else ""
    except Exception as e:
        print("Failed. {}.".format(e))


# Load json file
def load_json(path_to_json, mode='r', verbose=False, **kwargs):
    """
    :param path_to_json: [str] path where a json file is saved
    :param mode: [str] mode to `open()` file (default: 'r')
    :param verbose: [bool] whether to show illustrative messages (default: False)
    :param kwargs: optional arguments used by `open()`
    :return json_data: data retrieved from the specified path

    Example:
        from pyhelpers.dir import cd

        path_to_json = cd("tests\\data", "dat.json")
        mode = 'r'
        verbose = True

        json_data = load_json(path_to_json, mode, verbose)  # json_data == {'a': 1, 'b': 2, 'c': 3}
    """
    print("Loading \"..\\{}\"".format(os.path.relpath(path_to_json)), end=" ... ") if verbose else ""
    try:
        json_in = open(path_to_json, mode=mode, **kwargs)
        json_data = rapidjson.load(json_in)
        json_in.close()
        print("Successfully.") if verbose else ""
        return json_data
    except Exception as e:
        print("Failed. {}".format(e)) if verbose else ""


# Save feather file
def save_feather(feather_data, path_to_feather, verbose=False):
    """
    :param feather_data: [pd.DataFrame] to be saved as a 'feather-formatted' file
    :param path_to_feather: [str] path where a feather file is saved
    :param verbose: [bool] whether to show illustrative messages (default: False)

    Example:
        from pyhelpers.dir import cd

        feather_data = pd.DataFrame({'Col1': 1, 'Col2': 2}, index=[0])
        path_to_feather = cd("tests\\data", "dat.feather")
        verbose = True

        save_feather(feather_data, path_to_feather, verbose)
    """
    assert isinstance(feather_data, pd.DataFrame)
    get_specific_filepath_info(path_to_feather, verbose=verbose, ret_info=False)
    try:
        feather_data.to_feather(path_to_feather)
        print("Successfully.") if verbose else ""
    except Exception as e:
        print("Failed. {}.".format(e)) if verbose else ""


# Load feather file
def load_feather(path_to_feather, verbose=False, **kwargs):
    """
    :param path_to_feather: [str] path where a feather file is saved
    :param verbose: [bool] whether to show illustrative messages (default: False)
    :param kwargs: optional arguments used by `pd.read_feather()`
                    columns: [sequence; None (default)] a sequence of column names; if None, all columns
                    use_threads: [bool] whether to parallelize reading using multiple threads (default: True)
    :return: [pd.DataFrame] retrieved from the specified path

    Example:
        from pyhelpers.dir import cd

        path_to_feather = cd("tests\\data", "dat.feather")
        verbose = True

        feather_data = load_feather(path_to_feather, verbose)
    """
    print("Loading \"..\\{}\"".format(os.path.relpath(path_to_feather)), end=" ... ") if verbose else ""
    try:
        feather_data = pd.read_feather(path_to_feather, **kwargs)
        print("Successfully.") if verbose else ""
        return feather_data
    except Exception as e:
        print("Failed. {}".format(e)) if verbose else ""


# Save spreadsheet (".csv", ".xlsx" or ".xls")
def save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index=False, delimiter=',', verbose=False, **kwargs):
    """
    :param spreadsheet_data: [pd.DataFrame] data that could be saved as a spreadsheet, e.g. ".xlsx", ".csv"
    :param path_to_spreadsheet: [str] path where a spreadsheet is saved
    :param index: [bool] whether to include the index as a column (default: False)
    :param delimiter: [str] separator for saving ".xlsx"/".xls" as a ".csv" file (default: ',')
    :param verbose: [bool] whether to show illustrative messages (default: False)
    :param kwargs: optional arguments used by `pd.DataFrame.to_excel()` or `pd.DataFrame.to_csv()`

    engine: 'xlsxwriter'or 'openpyxl' for .xlsx; 'xlwt' for .xls

    Example:
        from pyhelpers.dir import cd

        spreadsheet_data = pd.DataFrame({'Col1': 1, 'Col2': 2}, index=['data'])
        index = False
        delimiter = ','
        verbose = True

        path_to_spreadsheet = cd("tests\\data", "dat.csv")
        save_spreadsheet(spreadsheet_data, path_to_spreadsheet, delimiter, index, verbose)

        path_to_spreadsheet = cd("tests\\data", "dat.xls")
        save_spreadsheet(spreadsheet_data, path_to_spreadsheet, delimiter, index, verbose)

        path_to_spreadsheet = cd("tests\\data", "dat.xlsx")
        save_spreadsheet(spreadsheet_data, path_to_spreadsheet, delimiter, index, verbose)

        path_to_spreadsheet = cd("tests\\data", "dat.txt")
        save_spreadsheet(spreadsheet_data, path_to_spreadsheet, delimiter, index, verbose)
    """
    _, spreadsheet_filename = get_specific_filepath_info(path_to_spreadsheet, verbose=verbose, ret_info=True)

    try:  # to save the data
        if spreadsheet_filename.endswith(".csv"):  # a .csv file
            spreadsheet_data.to_csv(path_to_spreadsheet, index=index, sep=delimiter, **kwargs)
        elif spreadsheet_filename.endswith(".xlsx"):  # a .xlsx file
            spreadsheet_data.to_excel(path_to_spreadsheet, index=index, engine='openpyxl', **kwargs)
        elif spreadsheet_filename.endswith(".xls"):  # a .xls file
            spreadsheet_data.to_excel(path_to_spreadsheet, index=index, engine='xlwt', **kwargs)
        else:
            raise AssertionError('File extension must be ".csv", ".xlsx" or ".xls"')
        print("Successfully.") if verbose else ""
    except Exception as e:
        print("Failed. {}.".format(e.args[0])) if verbose else ""


# Save multiple spreadsheets to an Excel workbook (".csv", ".xlsx" or ".xls")
def save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, mode='w', index=False,
                               confirmation_required=True, verbose=False, **kwargs):
    """
    :param spreadsheets_data: [list of pd.DataFrames]
    :param sheet_names: [list of str] sheet names of an Excel workbook
    :param path_to_spreadsheet: [str] path where a spreadsheet is saved
    :param mode: [str] {'w', 'a'} mode to write to excel file; 'w' (default) for 'write' and 'a' for 'append'
    :param index: [bool] whether to include the index as a column (default: False)
    :param confirmation_required: [bool] confirm before writing when the given sheet name already exists (default: True)
    :param verbose: [bool] whether to show illustrative messages (default: False)
    :param kwargs: optional arguments used by `pd.ExcelWriter()`

    Example:
        import numpy as np

        xy_array = np.array([(530034, 180381),   # London
                             (406689, 286822),   # Birmingham
                             (383819, 398052),   # Manchester
                             (582044, 152953)])  # Leeds
        dat1 = pd.DataFrame(xy_array, ['London', 'Birmingham', 'Manchester', 'Leeds'], ['Easting', 'Northing'])
        dat2 = dat1.T
        spreadsheets_data = [dat1, dat2]
        sheet_names = ['TestSheet1', 'TestSheet2']
        path_to_spreadsheet = cd("tests\\data", "dat.xlsx")
        index = True
        verbose = True

        mode = 'w'
        confirmation_required = True
        save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, mode, index,
                                   confirmation_required, verbose)

        mode = 'a'
        confirmation_required = True
        save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, mode, index,
                                   confirmation_required, verbose)

        mode = 'a'
        confirmation_required = False
        save_multiple_spreadsheets(spreadsheets_data, sheet_names, path_to_spreadsheet, mode, index,
                                   confirmation_required, verbose)
    """
    assert path_to_spreadsheet.endswith(".xlsx") or path_to_spreadsheet.endswith(".xls")

    get_specific_filepath_info(path_to_spreadsheet, verbose=verbose, ret_info=False)

    if os.path.isfile(path_to_spreadsheet) and mode == 'a':
        excel_file_reader = pd.ExcelFile(path_to_spreadsheet)
        cur_sheet_names = excel_file_reader.sheet_names
    else:
        cur_sheet_names = []
        mode = 'w'

    excel_file_writer = pd.ExcelWriter(path_to_spreadsheet, engine='openpyxl', mode=mode, **kwargs)

    def write_excel(dat, name, idx, suffix_msg=None):
        try:
            dat.to_excel(excel_file_writer, sheet_name=name, index=idx)
            print("Successfully. {}".format(suffix_msg) if suffix_msg else "Successfully.") if verbose else ""
        except Exception as e:
            print("Failed. {}.".format(e)) if verbose else ""

    print("per sheet ... ") if verbose else ""
    for sheet_dat, sheet_name in zip(spreadsheets_data, sheet_names):
        print("  '{}'".format(sheet_name), end=" ... ") if verbose else ""
        if sheet_name in cur_sheet_names:
            if confirmed("The sheet name '{}' already exists. "
                         "Adding a suffix to the sheet name to proceed with appending data?".format(sheet_name),
                         confirmation_required=confirmation_required):
                write_excel(sheet_dat, sheet_name, index,
                            suffix_msg="(Note: A suffix has been added to the sheet name.)")
        else:
            write_excel(sheet_dat, sheet_name, index)
    excel_file_writer.close()


# Load multiple spreadsheets from an Excel workbook (".xlsx" or ".xls")
def load_multiple_spreadsheets(path_to_spreadsheet, as_dict=True, verbose=False, **kwargs):
    """
    :param path_to_spreadsheet: [str] path where a spreadsheet is saved
    :param as_dict: [bool] whether to return the retrieved data as a dictionary type (default: True)
    :param verbose: [bool] whether to show illustrative messages (default: False)
    :param kwargs: optional arguments used by `pd.ExcelFile.parse()`
    :return workbook_data: [list of pd.DataFrame; or dict]

    Example:
        from pyhelpers.dir import cd

        path_to_spreadsheet = cd("tests\\data", "dat.xlsx")
        verbose = True

        as_dict = True
        workbook_data = load_multiple_spreadsheets(path_to_spreadsheet, as_dict, verbose, index_col=0)

        as_dict = False
        workbook_data = load_multiple_spreadsheets(path_to_spreadsheet, as_dict, verbose, index_col=0)
    """
    excel_file_reader = pd.ExcelFile(path_to_spreadsheet)

    sheet_names = excel_file_reader.sheet_names
    workbook_dat = []

    print("Loading \"..\\{}\" ... ".format(os.path.basename(path_to_spreadsheet))) if verbose else ""
    for sheet_name in sheet_names:
        print("  '{}'.".format(sheet_name), end=" ... ") if verbose else ""
        try:
            sheet_dat = excel_file_reader.parse(sheet_name, **kwargs)
            print("Successfully.") if verbose else ""
        except Exception as e:
            sheet_dat = None
            print("Failed. {}.".format(e)) if verbose else ""
        workbook_dat.append(sheet_dat)
    excel_file_reader.close()

    if as_dict:
        workbook_data = dict(zip(sheet_names, workbook_dat))
    else:
        workbook_data = workbook_dat

    return workbook_data


# Save data
def save(data, path_to_file, warning=False, **kwargs):
    """
    :param data: data that could be dumped as .feather, .json, .pickle and .csv/.xlsx/.xls
    :param path_to_file: [str] path where a file is saved
    :param warning: [bool] whether to show a warning messages (default: False)
    :param kwargs: optional arguments used by `save_*()` functions
    """
    # Make a copy the original data
    dat = data.copy()
    if isinstance(data, pd.DataFrame) and data.index.nlevels > 1:
        dat.reset_index(inplace=True)

    # Save the data according to the file extension
    if path_to_file.endswith((".csv", ".xlsx", ".xls")):
        save_spreadsheet(dat, path_to_file, **kwargs)
    elif path_to_file.endswith(".feather"):
        save_feather(dat, path_to_file)
    elif path_to_file.endswith(".json"):
        save_json(dat, path_to_file, **kwargs)
    elif path_to_file.endswith(".pickle"):
        save_pickle(dat, path_to_file, **kwargs)
    else:
        if warning:
            print("Note that the current file extension is not recognisable by this \"save()\" function.")
        if confirmed("To save \"{}\" as a .pickle file? ".format(os.path.basename(path_to_file))):
            save_pickle(dat, path_to_file, **kwargs)


# Save a figure using matplotlib.pyplot.savefig and Inkscape
def save_fig(path_to_fig_file, dpi=None, verbose=False, **kwargs):
    """
    :param path_to_fig_file: [str] path where a figure file is saved
    :param dpi: [int; None (default)] the resolution in dots per inch; if None, rcParams["savefig.dpi"]
    :param verbose: [bool] whether to show illustrative messages (default: False)

    Example:
        from pyhelpers.dir import cd
        import matplotlib.pyplot as plt

        x, y = (1, 1), (2, 2)
        plt.figure()
        plt.plot([x[0], y[0]], [x[1], y[1]])
        dpi = 300
        verbose = True

        path_to_fig_file = cd("tests\\data", "fig.png")
        save_fig(path_to_fig_file, dpi, verbose)

        path_to_fig_file = cd("tests\\data", "fig.svg")
        save_fig(path_to_fig_file, dpi, verbose)
    """
    get_specific_filepath_info(path_to_fig_file, verbose=verbose, ret_info=False)

    try:
        import matplotlib.pyplot as plt

        file_ext = pathlib.Path(path_to_fig_file).suffix
        # assert save_as.strip(".") in plt.gcf().canvas.get_supported_filetypes().keys()

        plt.savefig(path_to_fig_file, dpi=dpi, **kwargs)
        print("Successfully.") if verbose else ""

        if file_ext == ".svg":
            inkscape_exe = "C:\\Program Files\\Inkscape\\inkscape.exe"
            if os.path.isfile(inkscape_exe):
                path_to_emf = path_to_fig_file.replace(file_ext, ".emf")
                get_specific_filepath_info(path_to_emf, verbose=verbose, ret_info=False)
                subprocess.call([inkscape_exe, '-z', path_to_fig_file, '-M', path_to_emf])
                print("Conversion from .svg to .emf successfully.") if verbose else ""

    except Exception as e:
        print("Failed. {}.".format(e)) if verbose else ""


# Save a .svg file as a .emf file
def save_svg_as_emf(path_to_svg, path_to_emf, verbose=False, **kwargs):
    """
    :param path_to_svg: [str]
    :param path_to_emf: [str]
    :param verbose: [bool] whether to show illustrative messages (default: False)

    Test:
        from pyhelpers.dir import cd

        path_to_svg = cd("tests\\data", "fig.svg")
        path_to_emf = cd("tests\\data", "fig.emf")
        verbose = True

        save_svg_as_emf(path_to_svg, path_to_emf, verbose)
    """
    assert pathlib.Path(path_to_svg).suffix == ".svg"
    inkscape_exe = "C:\\Program Files\\Inkscape\\inkscape.exe"

    if os.path.isfile(inkscape_exe):
        print("Converting \".svg\" to \".emf\"", end=" ... ") if verbose else ""

        try:
            os.makedirs(os.path.dirname(path_to_emf), exist_ok=True)
            subprocess.call([inkscape_exe, '-z', path_to_svg, '-M', path_to_emf], **kwargs)
            print("Successfully. \nThe .emf file is saved to \"{}\".".format(path_to_emf)) if verbose else ""
        except Exception as e:
            print("Failed. {}".format(e)) if verbose else ""

    else:
        print("\"Inkscape\" (https://inkscape.org) is required to run this function. It is not found on this device.") \
            if verbose else ""


# Save a web page as a PDF file
def save_web_page_as_pdf(url_to_web_page, path_to_pdf, page_size='A4', zoom=1.0, encoding='UTF-8', verbose=False,
                         **kwargs):
    """
    :param url_to_web_page: [str] URL of a web page
    :param path_to_pdf: [str] path where a .pdf is saved
    :param page_size: [str] (default: 'A4')
    :param zoom: [float] (default: 1.0)
    :param encoding: [str] (default: 'UTF-8')
    :param verbose: [bool] whether or not show illustrative messages (default: False)
    :param kwargs: optional arguments used by `pdfkit.from_url()`

    Example:
        from pyhelpers.dir import cd

        page_size = 'A4'
        zoom = 1.0
        encoding = 'UTF-8'
        verbose = True

        url_to_web_page = 'https://github.com/'
        path_to_pdf = cd("tests\\data", "github.pdf")

        save_web_page_as_pdf(url_to_web_page, path_to_pdf, verbose=verbose)
    """
    path_to_wkhtmltopdf = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"

    if os.path.isfile(path_to_wkhtmltopdf):
        get_specific_filepath_info(path_to_pdf, verbose=verbose, verbose_end=" ... ", ret_info=False)

        try:
            import pdfkit

            # print("Saving the web page \"{}\" as PDF".format(url_to_web_page)) if verbose else ""
            config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
            pdf_options = {'page-size': page_size,
                           # 'margin-top': '0',
                           # 'margin-right': '0',
                           # 'margin-left': '0',
                           # 'margin-bottom': '0',
                           'zoom': str(float(zoom)),
                           'encoding': encoding}
            os.makedirs(os.path.dirname(path_to_pdf), exist_ok=True)
            if os.path.isfile(path_to_pdf):
                os.remove(path_to_pdf)
            status = pdfkit.from_url(url_to_web_page, path_to_pdf, configuration=config, options=pdf_options, **kwargs)
            if verbose and not status:
                print("Failed. Check if the URL is available.")

        except Exception as e:
            print("Failed. {}".format(e)) if verbose else ""

    else:
        print("\"wkhtmltopdf\" (https://wkhtmltopdf.org/) is required to run this function. "
              "It is not found on this device.") if verbose else ""


# Extract data from a zip file
def unzip(path_to_zip_file, out_dir, mode='r', verbose=False, **kwargs):
    """
    :param path_to_zip_file: [str] path where a zipped file is saved
    :param out_dir: [str]
    :param mode: [str] (default: 'r')
    :param verbose: [bool] (default: False)
    :param kwargs: optional arguments used by `extractall()`
    :return:

    Example:
        from pyhelpers.dir import cd

        path_to_zip_file = cd("tests\\data", "zipped.zip")
        out_dir = cd("tests\\data")
        mode = 'r'
        verbose = True

        unzip(path_to_zip_file, out_path, mode, verbose)
    """
    if verbose:
        print("Unzipping \"..\\{}\"".format(os.path.relpath(path_to_zip_file)), end=" ... ")

    try:
        with zipfile.ZipFile(path_to_zip_file, mode) as zf:
            zf.extractall(out_dir, **kwargs)
        print('File extracted successfully.') if verbose else ""
        zf.close()
    except Exception as e:
        print("Failed to extract files. {}".format(e))


# Use 7-zip to extract data from a compressed file
def seven_zip(path_to_zip_file, out_dir, mode='aoa', verbose=False, **kwargs):
    """
    :param path_to_zip_file: [str] path where a zipped file is saved
    :param out_dir: [str] directory where an extracted file is saved
    :param mode: [str] (default: 'aoa')
    :param verbose: [bool] (default: False)
    :param kwargs: optional arguments used by `subprocess.call()`

    Example:
        from pyhelpers.dir import cd

        out_dir = cd("tests\\data")
        mode = 'aoa'
        verbose = True

        path_to_zip_file = cd("tests\\data", "zipped.zip")
        seven_zip(path_to_zip_file, out_dir, mode, verbose)

        path_to_zip_file = cd("tests\\data", "zipped.7z")
        seven_zip(path_to_zip_file, out_dir, mode, verbose)
    """
    seven_zip_exe = "C:\\Program Files\\7-Zip\\7z.exe"
    if os.path.isfile(seven_zip_exe):
        try:
            subprocess.call('"{}" x "{}" -o"{}" -{}'.format(seven_zip_exe, path_to_zip_file, out_dir, mode), **kwargs)
            print("\nFile extracted successfully.")
        except Exception as e:
            print("\nFailed to unzip \"{}\". {}.".format(path_to_zip_file, e))
    else:
        print("\"7-Zip\" (https://www.7-zip.org/) is required to run this function. "
              "It is not found on this device.") if verbose else ""


# Load in a compressed sparse row (CSR) or compressed row storage (CRS)
def load_csr_matrix(path_to_csr, **kwargs):
    """
    :param path_to_csr: [str] path where a CSR (e.g. .npz) file is saved
    :param kwargs: optional arguments used by `np.load()`
    :return: [scipy.sparse.csr.csr_matrix]

    Example:
        from pyhelpers.dir import cd

        path_to_csr = cd("tests\\data", "csr_mat.npz")
        # indptr = np.array([0, 2, 3, 6])
        # indices = np.array([0, 2, 2, 0, 1, 2])
        # data = np.array([1, 2, 3, 4, 5, 6])
        # csr_m = scipy.sparse.csr_matrix((data, indices, indptr), shape=(3, 3))
        # np.savez_compressed(path_to_csr,
        #                     indptr=csr_m.indptr, indices=csr_m.indices, data=csr_m.data, shape=csr_m.shape)

        csr_mat = load_csr_matrix(path_to_csr)
    """
    csr_loader = np.load(path_to_csr, **kwargs)
    data, indices, indptr = csr_loader['data'], csr_loader['indices'], csr_loader['indptr']
    shape = csr_loader['shape']

    import scipy.sparse
    csr_mat = scipy.sparse.csr_matrix((data, indices, indptr), shape)

    return csr_mat
