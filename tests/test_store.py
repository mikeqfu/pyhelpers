"""Test the module :mod:`~pyhelpers.store`."""

import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from pyhelpers._cache import example_dataframe
from pyhelpers.dirs import cd
from pyhelpers.settings import mpl_preferences


def test__check_path_to_file(capfd):
    from pyhelpers.store import _check_path_to_file

    file_path = os.getcwd()
    try:
        _check_path_to_file(file_path, verbose=True)
    except AssertionError as e:
        print(e)

    out, err = capfd.readouterr()
    assert out == "The input for `path_to_file` may not be a file path.\n"

    file_path = cd("pyhelpers.pdf")
    _check_path_to_file(file_path, verbose=True)
    print("Passed.")

    out, err = capfd.readouterr()
    assert out == "Saving \"pyhelpers.pdf\" ... Passed.\n"

    file_path = cd("tests\\documents", "pyhelpers.pdf")
    _check_path_to_file(file_path, verbose=True)
    print("Passed.")

    out, err = capfd.readouterr()
    assert out == "Updating \"pyhelpers.pdf\" at \"tests\\documents\\\" ... Passed.\n"


def test__check_loading_path(capfd):
    from pyhelpers.store import _check_loading_path

    file_path = cd("tests\\documents", "pyhelpers.pdf")
    _check_loading_path(file_path, verbose=True)
    print("Passed.")

    out, err = capfd.readouterr()
    assert out == "Loading \"tests\\documents\\pyhelpers.pdf\" ... Passed.\n"


def test__check_exe_pathname():
    from pyhelpers.store import _check_exe_pathname

    possibilities = ["C:\\Python39\\python.exe", "C:\\Program Files\\Python39\\python.exe"]

    python_exists, path_to_exe = _check_exe_pathname("python.exe", None, possibilities)
    assert path_to_exe.endswith('python.exe')
    assert os.path.basename(path_to_exe) == 'python.exe'


def test__set_index():
    from pyhelpers.store import _set_index

    example_df = example_dataframe()

    assert example_df.equals(_set_index(example_df))

    example_df_ = _set_index(example_df, index=0)
    assert example_df.iloc[:, 0].to_list() == example_df_.index.to_list()


def test_save_pickle(capfd):
    from pyhelpers.store import save_pickle

    pickle_dat = 1

    pickle_pathname = cd("tests\\data", "dat.pickle")
    save_pickle(pickle_dat, pickle_pathname, verbose=True)

    assert os.path.exists(pickle_pathname)

    out, err = capfd.readouterr()
    assert out == 'Updating "dat.pickle" at "tests\\data\\" ... Done.\n'

    pickle_dat = example_dataframe()
    save_pickle(pickle_dat, pickle_pathname, verbose=True)

    out, err = capfd.readouterr()
    assert out == 'Updating "dat.pickle" at "tests\\data\\" ... Done.\n'


def test_save_spreadsheet(capfd):
    from pyhelpers.store import save_spreadsheet

    spreadsheet_dat = example_dataframe()

    spreadsheet_pathname = cd("tests\\data", "dat.csv")
    save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)

    out, err = capfd.readouterr()
    assert out == 'Updating "dat.csv" at "tests\\data\\" ... Done.\n'

    spreadsheet_pathname = cd("tests\\data", "dat.xlsx")
    save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)

    out, err = capfd.readouterr()
    assert out == 'Updating "dat.xlsx" at "tests\\data\\" ... Done.\n'


def test_save_spreadsheets(capfd):
    from pyhelpers.store import save_spreadsheets

    dat1 = example_dataframe()  # Get an example dataframe

    dat2 = dat1.T

    dat = [dat1, dat2]
    sheets = ['TestSheet1', 'TestSheet2']
    pathname = cd("tests\\data", "dat.xlsx")

    msg_1 = 'Updating "dat.xlsx" at "tests\\data\\" ... \n' \
            '\t\'TestSheet1\' ... Done.\n' \
            '\t\'TestSheet2\' ... Done.\n'

    save_spreadsheets(dat, pathname, sheets, verbose=True)
    out, err = capfd.readouterr()
    assert out == msg_1

    save_spreadsheets(dat, pathname, sheets, mode='a', if_sheet_exists='replace', verbose=True)
    out, err = capfd.readouterr()
    assert out == msg_1

    save_spreadsheets(dat, pathname, sheets, mode='a', if_sheet_exists='new', verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "dat.xlsx" at "tests\\data\\" ... \n' \
                  '\t\'TestSheet1\' ... saved as \'TestSheet11\' ... Done.\n' \
                  '\t\'TestSheet2\' ... saved as \'TestSheet21\' ... Done.\n'


def test_save_json(capfd):
    from pyhelpers.store import save_json

    json_pathname = cd("tests\\data", "dat.json")

    json_dat = {'a': 1, 'b': 2, 'c': 3, 'd': ['a', 'b', 'c']}
    save_json(json_dat, json_pathname, indent=4, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "dat.json" at "tests\\data\\" ... Done.\n'

    example_df = example_dataframe()
    json_dat = json.loads(example_df.to_json(orient='index'))

    save_json(json_dat, json_pathname, indent=4, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "dat.json" at "tests\\data\\" ... Done.\n'

    save_json(json_dat, json_pathname, engine='orjson', verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "dat.json" at "tests\\data\\" ... Done.\n'

    save_json(json_dat, json_pathname, engine='ujson', indent=4, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "dat.json" at "tests\\data\\" ... Done.\n'

    save_json(json_dat, json_pathname, engine='rapidjson', indent=4, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "dat.json" at "tests\\data\\" ... Done.\n'


def test_save_joblib(capfd):
    from pyhelpers.store import save_joblib

    joblib_pathname = cd("tests\\data", "dat.joblib")

    joblib_dat = example_dataframe().to_numpy()

    save_joblib(joblib_dat, joblib_pathname, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "dat.joblib" at "tests\\data\\" ... Done.\n'

    np.random.seed(0)
    joblib_dat = np.random.rand(100, 100)
    save_joblib(joblib_dat, joblib_pathname, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "dat.joblib" at "tests\\data\\" ... Done.\n'


def test_save_feather(capfd):
    from pyhelpers.store import save_feather

    feather_dat = example_dataframe()

    feather_pathname = cd("tests\\data", "dat.feather")

    save_feather(feather_dat, feather_pathname, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "dat.feather" at "tests\\data\\" ... Done.\n'

    save_feather(feather_dat, feather_pathname, index=True, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "dat.feather" at "tests\\data\\" ... Done.\n'


def test_save_svg_as_emf(capfd):
    from pyhelpers.store import save_svg_as_emf

    mpl_preferences()

    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])
    # plt.show()

    svg_file_pathname = cd("tests\\images", "store-save_fig-demo.svg")
    plt.savefig(svg_file_pathname)  # Save the figure as a .svg file

    emf_file_pathname = cd("tests\\images", "store-save_fig-demo.emf")
    save_svg_as_emf(svg_file_pathname, emf_file_pathname, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "store-save_fig-demo.emf" at "tests\\images\\" ... Done.\n'

    plt.close()

    mpl_preferences(reset=True)


def test_save_fig(capfd):
    from pyhelpers.store import save_fig

    mpl_preferences()

    x, y = (1, 1), (2, 2)

    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    img_dir = cd("tests\\images")

    png_file_pathname = cd(img_dir, "store-save_fig-demo.png")

    save_fig(png_file_pathname, dpi=600, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "store-save_fig-demo.png" at "tests\\images\\" ... Done.\n'

    svg_file_pathname = cd(img_dir, "store-save_fig-demo.svg")
    save_fig(svg_file_pathname, dpi=600, verbose=True, conv_svg_to_emf=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "store-save_fig-demo.svg" at "tests\\images\\" ... Done.\n' \
                  'Updating "store-save_fig-demo.emf" at "tests\\images\\" ... Done.\n'

    plt.close()

    mpl_preferences(reset=True)


# def test_save_web_page_as_pdf(capfd):
#     from pyhelpers.store import save_web_page_as_pdf
#
#     pdf_pathname = cd("tests\\documents", "pyhelpers.pdf")
#     web_page_url = 'https://pyhelpers.readthedocs.io/en/latest/'
#
#     save_web_page_as_pdf(web_page_url, pdf_pathname, verbose=True)
#     out, err = capfd.readouterr()
#     assert out.startswith('Updating "pyhelpers.pdf"')


def test_load_spreadsheets(capfd):
    from pyhelpers.store import load_spreadsheets

    dat_dir = cd("tests\\data")
    path_to_xlsx = cd(dat_dir, "dat.xlsx")

    wb_data = load_spreadsheets(path_to_xlsx, verbose=True, index_col=0)
    out, err = capfd.readouterr()
    assert 'Loading "tests\\data\\dat.xlsx" ... \n' in out
    assert isinstance(wb_data, dict)

    wb_data = load_spreadsheets(path_to_xlsx, as_dict=False, index_col=0)
    assert isinstance(wb_data, list)
    assert all(isinstance(x, pd.DataFrame) for x in wb_data)


def test_load_data(capfd):
    from pyhelpers.store import load_data

    data_dir = "tests\\data"

    dat_pathname = cd(data_dir, "dat.pickle")
    pickle_dat = load_data(path_to_file=dat_pathname, verbose=True)
    out, err = capfd.readouterr()
    assert out == f'Loading "{data_dir}\\dat.pickle" ... Done.\n'
    assert pickle_dat.equals(example_dataframe())

    dat_pathname = cd(data_dir, "dat.csv")
    csv_dat = load_data(path_to_file=dat_pathname, index=0, verbose=True)
    out, err = capfd.readouterr()
    assert out == f'Loading "{data_dir}\\dat.csv" ... Done.\n'
    assert csv_dat.astype('float').equals(example_dataframe())

    dat_pathname = cd(data_dir, "dat.json")
    json_dat = load_data(path_to_file=dat_pathname, verbose=True)
    out, err = capfd.readouterr()
    assert out == f'Loading "{data_dir}\\dat.json" ... Done.\n'
    assert list(json_dat.keys()) == example_dataframe().index.to_list()

    dat_pathname = cd(data_dir, "dat.feather")
    feather_dat = load_data(path_to_file=dat_pathname, index=0, verbose=True)
    out, err = capfd.readouterr()
    assert out == f'Loading "{data_dir}\\dat.feather" ... Done.\n'
    assert feather_dat.equals(example_dataframe())

    dat_pathname = cd(data_dir, "dat.joblib")
    joblib_dat = load_data(path_to_file=dat_pathname, verbose=True)
    out, err = capfd.readouterr()
    assert out == f'Loading "{data_dir}\\dat.joblib" ... Done.\n'
    np.random.seed(0)
    assert np.array_equal(joblib_dat, np.random.rand(100, 100))


def test_unzip(capfd):
    from pyhelpers.store import unzip

    zip_file_path = cd("tests\\data", "zipped.zip")

    unzip(path_to_zip_file=zip_file_path, verbose=True)

    out, err = capfd.readouterr()
    assert out == 'Extracting "tests\\data\\zipped.zip" to "tests\\data\\zipped\\" ... Done.\n'


def test_seven_zip(capfd):
    from pyhelpers.store import seven_zip

    zip_file_pathname = cd("tests\\data", "zipped.zip")

    seven_zip(path_to_zip_file=zip_file_pathname, verbose=True)

    out, err = capfd.readouterr()
    assert out.startswith('\r\n7-Zip')


def test_markdown_to_rst(capfd):
    from pyhelpers.store import markdown_to_rst

    dat_dir = cd("tests\\documents")

    path_to_md_file = cd(dat_dir, "readme.md")
    path_to_rst_file = cd(dat_dir, "readme.rst")

    markdown_to_rst(path_to_md_file, path_to_rst_file, engine='pypandoc', verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "readme.rst" at "tests\\documents\\" ... Done.\n'

    markdown_to_rst(path_to_md_file, path_to_rst_file, verbose=True)
    out, err = capfd.readouterr()
    assert out == 'Updating "readme.rst" at "tests\\documents\\" ... Done.\n'


def test_xlsx_to_csv(capfd):
    from pyhelpers.store import xlsx_to_csv, load_csv

    path_to_test_xlsx = cd("tests\\data", "dat.xlsx")

    path_to_temp_csv = xlsx_to_csv(path_to_test_xlsx)
    assert os.path.exists(path_to_temp_csv)

    data = load_csv(path_to_temp_csv, index=0)
    assert data.astype('float16').equals(example_dataframe().astype('float16'))
    os.remove(path_to_temp_csv)

    temp_csv_buffer = xlsx_to_csv(path_to_test_xlsx, engine='xlsx2csv')
    data = load_csv(temp_csv_buffer, index=0)
    assert data.astype('float16').equals(example_dataframe().astype('float16'))


if __name__ == '__main__':
    pytest.main()
