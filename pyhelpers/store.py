""" Save and Load files """

import copy
import os
import pickle

from pyhelpers.ops import confirmed


# Save pickle file
def save_pickle(pickle_data, path_to_pickle, mode='wb', encoding=None, verbose=False):
    """
    :param pickle_data: data that could be dumped by the 'pickle' package
    :param path_to_pickle: [str] local file path
    :param mode: [str] (default: 'wb')
    :param encoding: [str; None (default)] e.g. 'UTF-8'
    :param verbose: [bool] (default: False) whether to print note
    :return: printing message showing whether or not the data has been successfully saved or updated
    """
    pickle_filename = os.path.basename(path_to_pickle)
    pickle_dir = os.path.basename(os.path.dirname(path_to_pickle))
    pickle_dir_parent = os.path.basename(os.path.dirname(os.path.dirname(path_to_pickle)))

    if verbose:
        print("{} \"{}\"".format("Updating" if os.path.isfile(path_to_pickle) else "Saving",
                                 " - ".join([x for x in (pickle_dir_parent, pickle_dir, pickle_filename) if x])),
              end=" ... ")

    try:
        os.makedirs(os.path.dirname(os.path.abspath(path_to_pickle)), exist_ok=True)
        pickle_out = open(path_to_pickle, mode=mode, encoding=encoding)
        pickle.dump(pickle_data, pickle_out)
        pickle_out.close()
        print("Successfully.") if verbose else None

    except Exception as e:
        print("Failed. {}.".format(e))


# Load pickle file
def load_pickle(path_to_pickle, mode='rb', encoding=None, verbose=False):
    """
    :param path_to_pickle: [str] local file path
    :param mode: [str] (default: 'rb')
    :param encoding: [str; None (default)] e.g. 'UTF-8'
    :param verbose: [bool] (default: False) whether to print note
    :return: data retrieved from the specified path
    """
    print("Loading \"{}\"".format(os.path.basename(path_to_pickle)), end=" ... ") if verbose else None
    pickle_in = open(path_to_pickle, mode=mode, encoding=encoding)
    pickle_data = pickle.load(pickle_in)
    pickle_in.close()
    print("Successfully.") if verbose else None
    return pickle_data


# Save json file
def save_json(json_data, path_to_json, mode='w', encoding=None, verbose=False):
    """
    :param json_data: data that could be dumped by the 'json' package
    :param path_to_json: [str] local file path
    :param mode: [str] (default: 'w')
    :param encoding: [str; None (default)] e.g. 'UTF-8'
    :param verbose: [bool] (default: False) whether to print note
    :return: printing message showing whether or not the data has been successfully saved or updated
    """
    json_filename = os.path.basename(path_to_json)
    json_dir = os.path.basename(os.path.dirname(path_to_json))
    json_dir_parent = os.path.basename(os.path.dirname(os.path.dirname(path_to_json)))

    print("{} \"{}\"".format("Updating" if os.path.isfile(path_to_json) else "Saving",
                             " - ".join([x for x in (json_dir_parent, json_dir, json_filename) if x])),
          end=" ... ") if verbose else None

    try:
        os.makedirs(os.path.dirname(os.path.abspath(path_to_json)), exist_ok=True)
        json_out = open(path_to_json, mode=mode, encoding=encoding)
        import rapidjson
        rapidjson.dump(json_data, json_out)
        json_out.close()
        print("Successfully.") if verbose else None

    except Exception as e:
        print("Failed. {}.".format(e))


# Load json file
def load_json(path_to_json, mode='r', encoding=None, verbose=False):
    """
    :param path_to_json: [str] local file path
    :param mode: [str] (default: 'r')
    :param encoding: [str; None (default)] e.g. 'UTF-8'
    :param verbose: [bool] (default: False) whether to print note
    :return: data retrieved from the specified path
    """
    print("Loading \"{}\"".format(os.path.basename(path_to_json)), end=" ... ") if verbose else None
    json_in = open(path_to_json, mode=mode, encoding=encoding)
    import rapidjson
    json_data = rapidjson.load(json_in)
    json_in.close()
    print("Successfully.") if verbose else None
    return json_data


# Save Excel workbook
def save_excel(excel_data, path_to_excel, sep, index, sheet_name, engine='xlsxwriter', verbose=False):
    """
    :param excel_data: [pd.DataFrame] data that could be saved as a Excel workbook, e.g. ".csv", ".xlsx"
    :param path_to_excel: [str] local file path
    :param sep: [str] separator for saving 'excel_data' as a ".csv" file
    :param index: [bool] whether to include the index as a column
    :param sheet_name: [str] name of worksheet for saving the excel_data (for example, as a ".xlsx" file)
    :param engine: [str] ExcelWriter engine. pandas writes Excel files using the 'xlwt' module for ".xls" files and the
                        'openpyxl' or 'xlsxwriter' (default) for ".xlsx" files.
    :param verbose: [bool] (default: False) whether to print note
    :return: printing message showing whether or not the data has been successfully saved or updated
    """
    import pandas as pd

    excel_filename = os.path.basename(path_to_excel)
    excel_dir = os.path.basename(os.path.dirname(path_to_excel))
    excel_dir_parent = os.path.basename(os.path.dirname(os.path.dirname(path_to_excel)))

    if verbose:
        print("{} \"{}\"".format("Updating" if os.path.isfile(path_to_excel) else "Saving",
                                 " - ".join([x for x in (excel_dir_parent, excel_dir, excel_filename) if x])),
              end=" ... ")

    try:
        os.makedirs(os.path.dirname(os.path.abspath(path_to_excel)), exist_ok=True)
        if excel_filename.endswith(".csv"):  # Save the data to a .csv file
            excel_data.to_csv(path_to_excel, index=index, sep=sep, na_rep='', float_format=None, columns=None,
                              header=True, index_label=None, mode='w', encoding=None, compression='infer',
                              quoting=None, quotechar='"', line_terminator=None, chunksize=None,
                              date_format=None, doublequote=True, escapechar=None, decimal='.')
        else:  # Save the data to a .xlsx or .xls file, e.g. excel_filename.endswith(".xlsx")
            xlsx_writer = pd.ExcelWriter(path_to_excel, engine)
            excel_data.to_excel(xlsx_writer, sheet_name, index=index, na_rep='', float_format=None,
                                columns=None, header=True, index_label=None, startrow=0, startcol=0,
                                engine=None, merge_cells=True, encoding=None, inf_rep='inf', verbose=True,
                                freeze_panes=None)
            xlsx_writer.save()
            xlsx_writer.close()
        print("Successfully.") if verbose else None

    except Exception as e:
        print("Failed. {}.".format(e)) if verbose else None


# Save feather file
def save_feather(feather_data, path_to_feather, verbose=False):
    """
    :param feather_data: [pd.DataFrame] to be saved as a 'feather-formatted' file
    :param path_to_feather: [str] local file path
    :param verbose: [bool] (default: False) whether to print note
    :return: printing message showing whether or not the data has been successfully saved or updated
    """
    # assert isinstance(feather_data, pd.DataFrame)
    feather_filename = os.path.basename(path_to_feather)
    feather_dir = os.path.basename(os.path.dirname(path_to_feather))
    feather_dir_parent = os.path.basename(os.path.dirname(os.path.dirname(path_to_feather)))

    msg = "{} \"{}\"".format("Updating" if os.path.isfile(path_to_feather) else "Saving",
                             " - ".join([x for x in (feather_dir_parent, feather_dir, feather_filename) if x]))

    if verbose:
        print(msg, end=" ... ")

    try:
        os.makedirs(os.path.dirname(os.path.abspath(path_to_feather)), exist_ok=True)
        feather_data.to_feather(path_to_feather)
        print("Successfully.") if verbose else None

    except ValueError as ve:
        print(ve)
        print("Trying again with \"feather-format\"", end=" ... \n") if verbose else None
        import feather
        feather.write_dataframe(feather_data, path_to_feather)
        if verbose:
            print("{} ... Successfully. "
                  "(Use \"load_feather()\" to retrieve the saved feather file and check the consistency.)".format(msg))

    except Exception as e:
        print("{} ... Failed. {}.".format(msg, e)) if verbose else None


# Load feather file
def load_feather(path_to_feather, columns=None, use_threads=True, verbose=False):
    """
    :param path_to_feather: [str] local file path to a feather-formatted file
    :param columns: [array-like; None (default)] column labels
    :param use_threads: [bool] (default: True)
    :param verbose: [bool] (default: False) whether to print note
    :return: [pd.DataFrame] retrieved from the specified path
    """
    print("Loading \"{}\"".format(os.path.basename(path_to_feather)), end=" ... ") if verbose else None
    try:
        try:
            import pandas as pd
            feather_data = pd.read_feather(path_to_feather, columns, use_threads=use_threads)
            print("Successfully.") if verbose else None
        except Exception as e:
            print(e)
            print("Try loading again \"feather-format\" ... ", end="")
            import feather
            feather_data = feather.read_dataframe(path_to_feather, columns, use_threads)
            print("Successfully.") if verbose else None
        return feather_data
    except Exception as e:
        print("Failed. {}".format(e)) if verbose else None


# Save data locally (".pickle", ".csv", ".xlsx" or ".xls")
def save(data, path_to_file, sep=',', index=False, sheet_name='Sheet1', engine='xlsxwriter', encoding=None,
         deep_copy=True, verbose=False):
    """
    :param data: data that could be dumped as .feather, .json, .pickle and .csv/.xlsx/.xls
    :param path_to_file: [str] local file path
    :param sep: [str] (default: ',') separator for ".csv"
    :param index: [bool] (default: False) whether to include the index as a column
    :param sheet_name: [str] (default: 'Sheet1') name of worksheet
    :param engine: [str] 'xlsxwriter' (default) or 'openpyxl' for .xlsx; 'xlwt' for .xls
    :param encoding: [str; None (default)] e.g. 'UTF-8'
    :param deep_copy: [bool] (default: True) whether make a deep copy of the data before saving it
    :param verbose: [bool] (default: False) whether to print note
    :return: printing message showing whether or not the data has been successfully saved or updated
    """
    # Make a copy the original data
    dat = copy.deepcopy(data) if deep_copy else copy.copy(data)

    # The specified path exists?
    os.makedirs(os.path.dirname(os.path.abspath(path_to_file)), exist_ok=True)

    import pandas as pd
    if isinstance(dat, pd.DataFrame) and dat.index.nlevels > 1:
        dat.reset_index(inplace=True)

    # Save the data according to the file extension
    if path_to_file.endswith((".csv", ".xlsx", ".xls")):
        save_excel(dat, path_to_file, sep, index, sheet_name, engine, verbose=verbose)
    elif path_to_file.endswith(".feather"):
        save_feather(dat, path_to_file, verbose=verbose)
    elif path_to_file.endswith(".json"):
        save_json(dat, path_to_file, encoding=encoding, verbose=verbose)
    else:
        if path_to_file.endswith(".pickle"):
            save_pickle(dat, path_to_file, encoding=encoding, verbose=verbose)
        else:
            print("Note that the current file extension is not recognisable by this \"save()\" function.")
            if confirmed("To save \"{}\" as a .pickle file? ".format(os.path.basename(path_to_file))):
                save_pickle(dat, path_to_file, encoding=encoding, verbose=verbose)


# Save a figure using matplotlib.pyplot.savefig and Inkscape
def save_fig(path_to_fig_file, dpi=None, verbose=False):
    """
    :param path_to_fig_file: [str]
    :param dpi: [int; None (default)]
    :param verbose: [bool] (default: False) whether to print note
    :return: printing message showing whether or not the figure has been successfully saved or updated
    """
    fig_filename = os.path.basename(path_to_fig_file)
    fig_dir = os.path.basename(os.path.dirname(path_to_fig_file))
    fig_dir_parent = os.path.basename(os.path.dirname(os.path.dirname(path_to_fig_file)))

    if verbose:
        print("{} \"{}\"".format("Updating" if os.path.isfile(path_to_fig_file) else "Saving",
                                 " - ".join([x for x in (fig_dir_parent, fig_dir, fig_filename) if x])), end=" ... ")

    try:
        _, save_as = os.path.splitext(path_to_fig_file)
        # assert save_as.strip(".") in plt.gcf().canvas.get_supported_filetypes().keys()
        import matplotlib.pyplot as plt
        plt.savefig(path_to_fig_file, dpi=dpi)
        if save_as == ".svg" and os.path.isfile("C:\\Program Files\\Inkscape\\inkscape.exe"):
            path_to_emf = path_to_fig_file.replace(save_as, ".emf")
            import subprocess
            subprocess.call(["C:\\Program Files\\Inkscape\\inkscape.exe", '-z', path_to_fig_file, '-M', path_to_emf])
        print("Successfully.") if verbose else None

    except Exception as e:
        print("Failed. {}.".format(e)) if verbose else None


# Save a .svg file as a .emf file
def save_svg_as_emf(path_to_svg, path_to_emf, verbose=False):
    """
    :param path_to_svg: [str]
    :param path_to_emf: [str]
    :param verbose: [bool] (default: False) whether to print note
    :return: printing message showing whether or not the figure has been successfully saved or updated
    """
    path_to_inkscape = "C:\\Program Files\\Inkscape\\inkscape.exe"

    if os.path.isfile(path_to_inkscape):
        print("Converting \".svg\" to \".emf\"", end=" ... ") if verbose else None

        try:
            import subprocess
            subprocess.call([path_to_inkscape, '-z', path_to_svg, '-M', path_to_emf])
            print("Done. \nThe .emf file is saved to \"{}\".".format(path_to_emf)) if verbose else None
        except Exception as e:
            print("Failed. {}".format(e)) if verbose else None

    else:
        print("\"Inkscape\" (https://inkscape.org) is required to run this function. It is not found on this device.") \
            if verbose else None


# Save a web page as a PDF file
def save_web_page_as_pdf(url_to_web_page, path_to_pdf, page_size='A4', zoom=1.0, encoding='UTF-8', verbose=False):
    """
    :param url_to_web_page: [str] URL of a web page
    :param path_to_pdf: [str] local file path
    :param page_size: [str] (default: 'A4')
    :param zoom: [float] (default: 1.0)
    :param encoding: [str] (default: 'UTF-8')
    :param verbose: [bool] (default: False) whether to print note
    """
    import pdfkit

    path_to_wkhtmltopdf = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
    if os.path.isfile(path_to_wkhtmltopdf):
        try:
            print("Saving the web page \"{}\" as PDF".format(url_to_web_page), end=" ... ") if verbose else None
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
                  if status else "Failed. Check if the URL is available.") if verbose else None
        except Exception as e:
            print("Failed. {}".format(e)) if verbose else None
    else:
        print("\"wkhtmltopdf\" (https://wkhtmltopdf.org) is required to run this function. "
              "It is not found on this device.") if verbose else None
