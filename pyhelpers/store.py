""" Save and Load files """

import copy
import os
import pickle
import subprocess

import matplotlib.pyplot as plt
import pandas as pd
import pdfkit
import rapidjson


# Save Pickle file
def save_pickle(pickle_data, path_to_pickle):
    """
    :param pickle_data: any object that could be dumped by the 'pickle' package
    :param path_to_pickle: [str] local file path
    :return: whether the data has been successfully saved
    """
    pickle_filename = os.path.basename(path_to_pickle)
    print("{} \"{}\" ... ".format("Updating" if os.path.isfile(path_to_pickle) else "Saving", pickle_filename), end="")
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path_to_pickle)), exist_ok=True)
        pickle_out = open(path_to_pickle, 'wb')
        pickle.dump(pickle_data, pickle_out)
        pickle_out.close()
        print("Successfully.")
    except Exception as e:
        print("Failed. {}.".format(e))


# Load Pickle file
def load_pickle(path_to_pickle, verbose=False):
    """
    :param path_to_pickle: [str] local file path
    :param verbose: [bool] Whether to print note
    :return: the object retrieved from the pickle
    """
    print("Loading \"{}\" ... ".format(os.path.basename(path_to_pickle)), end="") if verbose else None
    try:
        pickle_in = open(path_to_pickle, 'rb')
        pickle_data = pickle.load(pickle_in)
        pickle_in.close()
        print("Successfully.") if verbose else None
    except Exception as e:
        print("Failed. {}.".format(e)) if verbose else None
        pickle_data = None
    return pickle_data


# Save JSON file
def save_json(json_data, path_to_json):
    """
    :param json_data: any object that could be dumped by the 'json' package
    :param path_to_json: [str] local file path
    :return: whether the data has been successfully saved
    """
    json_filename = os.path.basename(path_to_json)
    print("{} \"{}\" ... ".format("Updating" if os.path.isfile(path_to_json) else "Saving", json_filename), end="")
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path_to_json)), exist_ok=True)
        json_out = open(path_to_json, 'w')
        rapidjson.dump(json_data, json_out)
        json_out.close()
        print("Successfully.")
    except Exception as e:
        print("Failed. {}.".format(e))


# Load JSON file
def load_json(path_to_json, verbose=False):
    """
    :param path_to_json: [str] local file path
    :param verbose: [bool] Whether to print note
    :return: the json data retrieved
    """
    print("Loading \"{}\" ... ".format(os.path.basename(path_to_json)), end="") if verbose else None
    try:
        json_in = open(path_to_json, 'r')
        json_data = rapidjson.load(json_in)
        json_in.close()
        print("Successfully.") if verbose else None
    except Exception as e:
        print("Failed. {}.".format(e)) if verbose else None
        json_data = None
    return json_data


# Save Excel workbook
def save_excel(excel_data, path_to_excel, sep, index, sheet_name, engine='xlsxwriter'):
    """
    :param excel_data: any [DataFrame] that could be dumped saved as a Excel workbook, e.g. '.csv', '.xlsx'
    :param path_to_excel: [str] local file path
    :param sep: [str] separator for saving excel_data to a '.csv' file
    :param index: [bool]
    :param sheet_name: [str] name of worksheet for saving the excel_data to a e.g. '.xlsx' file
    :param engine: [str] ExcelWriter engine; pandas writes Excel files using the 'xlwt' module for '.xls' files and the
                        'openpyxl' or 'xlsxWriter' modules for '.xlsx' files.
    :return: whether the data has been successfully saved or updated
    """
    excel_filename = os.path.basename(path_to_excel)
    _, save_as = os.path.splitext(excel_filename)
    print("{} \"{}\" ... ".format("Updating" if os.path.isfile(path_to_excel) else "Saving", excel_filename), end="")
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path_to_excel)), exist_ok=True)
        if excel_filename.endswith(".csv"):  # Save the data to a .csv file
            excel_data.to_csv(path_to_excel, index=index, sep=sep, na_rep='', float_format=None, columns=None,
                              header=True, index_label=None, mode='w', encoding=None, compression='infer',
                              quoting=None, quotechar='"', line_terminator=None, chunksize=None,
                              tupleize_cols=None, date_format=None, doublequote=True, escapechar=None,
                              decimal='.')
        else:  # Save the data to a .xlsx or .xls file, e.g. excel_filename.endswith(".xlsx")
            xlsx_writer = pd.ExcelWriter(path_to_excel, engine)
            excel_data.to_excel(xlsx_writer, sheet_name, index=index, na_rep='', float_format=None,
                                columns=None, header=True, index_label=None, startrow=0, startcol=0,
                                engine=None, merge_cells=True, encoding=None, inf_rep='inf', verbose=True,
                                freeze_panes=None)
            xlsx_writer.save()
            xlsx_writer.close()
        print("Successfully.")
    except Exception as e:
        print("Failed. {}.".format(e))


# Save data locally (".pickle", ".csv", ".xlsx" or ".xls")
def save(data, path_to_file, sep=',', index=False, sheet_name='Sheet1', engine='xlsxwriter', deep_copy=True):
    """
    :param data: any object that could be dumped
    :param path_to_file: [str] local file path
    :param sep: [str] separator for '.csv'
    :param index:
    :param engine: [str] 'xlwt' for .xls; 'xlsxwriter' or 'openpyxl' for .xlsx
    :param sheet_name: [str] name of worksheet
    :param deep_copy: [bool] whether make a deep copy of the data before saving it
    :return: whether the data has been successfully saved or updated
    """
    # Make a copy the original data
    dat = copy.deepcopy(data) if deep_copy else copy.copy(data)

    # The specified path exists?
    os.makedirs(os.path.dirname(os.path.abspath(path_to_file)), exist_ok=True)

    if isinstance(dat, pd.DataFrame) and dat.index.nlevels > 1:
        dat.reset_index(inplace=True)

    # Save the data according to the file extension
    if path_to_file.endswith((".csv", ".xlsx", ".xls")):
        save_excel(dat, path_to_file, sep, index, sheet_name, engine)
    elif path_to_file.endswith(".json"):
        save_json(dat, path_to_file)
    else:
        save_pickle(dat, path_to_file)
        if not path_to_file.endswith(".pickle"):
            print("Note that the file extension is not among the recognisable formats of this 'save()' function.")


# Save a figure using matplotlib.pyplot.savefig and Inkscape
def save_fig(path_to_fig_file, dpi):
    fig_filename = os.path.basename(path_to_fig_file)
    print("{} \"{}\" ... ".format("Updating" if os.path.isfile(path_to_fig_file) else "Saving", fig_filename), end="")
    try:
        plt.savefig(path_to_fig_file, dpi=dpi)
        _, save_as = os.path.splitext(path_to_fig_file)
        if save_as == ".svg":
            path_to_emf = path_to_fig_file.replace(save_as, ".emf")
            subprocess.call(["C:\\Program Files\\Inkscape\\inkscape.exe", '-z', path_to_fig_file, '-M', path_to_emf])
        print("Successfully.")
    except Exception as e:
        print("Failed. {}.".format(e))


# Save a .svg file as a .emf file
def save_svg_as_emf(path_to_svg, path_to_emf):
    path_to_inkscape = "C:\\Program Files\\Inkscape\\inkscape.exe"
    if os.path.isfile(path_to_inkscape):
        print("Converting \".svg\" to \".emf\" ... ", end="")
        try:
            subprocess.call([path_to_inkscape, '-z', path_to_svg, '-M', path_to_emf])
            print("Done. \nThe .emf file is saved to \"{}\".".format(path_to_emf))
        except Exception as e:
            print("Failed. {}".format(e))
    else:
        print("\"Inkscape\" (https://inkscape.org) is required to run this function. It is not found on this device.")


# Save a web page as a PDF file
def save_web_page_as_pdf(url_to_web_page, path_to_pdf, page_size='A4', zoom=1.0, encoding='UTF-8'):
    """
    :param url_to_web_page: [str] URL of a web page
    :param path_to_pdf: [str] local file path
    :param page_size: [str]
    :param zoom: [float]
    :param encoding: [str]
    """
    path_to_wkhtmltopdf = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
    if os.path.isfile(path_to_wkhtmltopdf):
        try:
            print("Saving the web page \"{}\" as PDF ... ".format(url_to_web_page), end="")
            config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
            pdf_options = {'page-size': page_size,
                           # 'margin-top': '0',
                           # 'margin-right': '0',
                           # 'margin-left': '0',
                           # 'margin-bottom': '0',
                           'zoom': str(float(zoom)),
                           'encoding': encoding}
            status = pdfkit.from_url(url_to_web_page, path_to_pdf, configuration=config, options=pdf_options)
            print("Done. \nThe web page is saved to \"{}\"".format(path_to_pdf)
                  if status else "Failed. Check if the URL is available.")
        except Exception as e:
            print("Failed. {}".format(e))
    else:
        print("\"wkhtmltopdf\" (https://wkhtmltopdf.org) not found. It is required to run this function.")
