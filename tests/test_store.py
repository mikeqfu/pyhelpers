"""Test the module :mod:`~pyhelpers.store`."""

import json
import os
import tempfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from pyhelpers._cache import example_dataframe
from pyhelpers.dirs import cd


def test__check_path_to_file(capfd):
    from pyhelpers.store import _check_saving_path

    file_path = os.getcwd()
    with pytest.raises(AssertionError, match="The input for `path_to_file` may not be a file path."):
        _check_saving_path(file_path, verbose=True)

    file_path = "pyhelpers.pdf"
    _check_saving_path(file_path, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{file_path}" ... ' in out

    file_path = "tests\\documents\\pyhelpers.pdf"
    _check_saving_path(file_path, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{os.path.basename(file_path)}"' in out and os.path.dirname(file_path) in out


def test__check_loading_path(capfd):
    from pyhelpers.store import _check_loading_path

    file_path = "tests\\documents\\pyhelpers.pdf"
    _check_loading_path(file_path, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Loading "{file_path}"' in out


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


# == Save data =====================================================================================

def _test_save(func, dat, file_ext, capfd):
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + file_ext
    filename = os.path.basename(pathname)

    func(dat, pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    os.remove(pathname)
    os.remove(pathname_.name)


def test_save_pickle(capfd):
    from pyhelpers.store import save_pickle

    # pickle_pathname = cd("tests\\data", "dat.pickle")
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ".xlsx"
    filename = os.path.basename(pathname)

    dat = 1
    save_pickle(dat, pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    dat = example_dataframe()
    save_pickle(dat, pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{filename}"' in out and "Done." in out

    os.remove(pathname)
    os.remove(pathname_.name)


@pytest.mark.parametrize('file_ext', [".csv", ".xlsx", ".xls", ".pickle"])
@pytest.mark.parametrize('engine', [None, 'xlwt', ".xls"])
def test_save_spreadsheet(capfd, file_ext, engine):
    from pyhelpers.store import save_spreadsheet

    dat = example_dataframe()

    pathname_ = tempfile.NamedTemporaryFile()

    pathname = pathname_.name + file_ext
    filename = os.path.basename(pathname)
    save_spreadsheet(dat, pathname, verbose=True)
    out, _ = capfd.readouterr()

    if file_ext == ".pickle":
        assert all(x in out for x in [f'Saving "{filename}"', "", "File extension must be"])
    else:
        assert f'Saving "{filename}"' in out and "Done." in out
        os.remove(pathname)
        os.remove(pathname_.name)


def test_save_spreadsheets(capfd):
    from pyhelpers.store import save_spreadsheets

    dat = [example_dataframe(), example_dataframe().T]
    sheets = ['TestSheet1', 'TestSheet2']

    # pathname = cd("tests\\data", "dat.xlsx")
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ".xlsx"
    filename = os.path.basename(pathname)

    save_spreadsheets(dat, pathname, sheet_names=sheets, verbose=True)
    out, _ = capfd.readouterr()
    assert all(x in out for x in [f'Saving "{filename}"', "Done."] + sheets)

    save_spreadsheets(dat, pathname, sheets, mode='a', if_sheet_exists='replace', verbose=True)
    out, _ = capfd.readouterr()
    assert all(x in out for x in [f'Updating "{filename}"', "Done."] + sheets)

    save_spreadsheets(dat, pathname, sheets, mode='a', if_sheet_exists='new', verbose=True)
    out, _ = capfd.readouterr()
    assert all(x in out for x in [f'Updating "{filename}"', " saved as ", "Done."] + sheets)

    os.remove(pathname)
    os.remove(pathname_.name)


def test_save_json(capfd):
    from pyhelpers.store import save_json

    # json_pathname = cd("tests\\data", "dat.json")

    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ".json"
    filename = os.path.basename(pathname)

    dat = {'a': 1, 'b': 2, 'c': 3, 'd': ['a', 'b', 'c']}

    save_json(dat, pathname, indent=4, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    dat = json.loads(example_dataframe().to_json(orient='index'))

    for engine in [None, 'orjson', 'ujson', 'rapidjson']:
        save_json(dat, pathname, engine=engine, indent=4, verbose=True)
        out, _ = capfd.readouterr()
        if engine == 'orjson':
            assert all(
                x in out for x in [f'Updating "{filename}"', "Failed.", "unexpected keyword argument"])
        else:
            assert f'Updating "{filename}"' in out and "Done." in out

    os.remove(pathname)
    os.remove(pathname_.name)


def test_save_joblib(capfd):
    from pyhelpers.store import save_joblib

    # joblib_pathname = cd("tests\\data", "dat.joblib")

    dat = example_dataframe().to_numpy()
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ".joblib"
    filename = os.path.basename(pathname)

    save_joblib(dat, pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    dat = np.random.rand(100, 100)

    save_joblib(dat, pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{filename}"' in out and "Done." in out


@pytest.mark.parametrize('index', [False, True])
def test_save_feather(capfd, index):
    from pyhelpers.store import save_feather

    feather_dat = example_dataframe()

    # feather_pathname = cd("tests\\data", "dat.feather")
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ".feather"
    filename = os.path.basename(pathname)

    save_feather(feather_dat, path_to_feather=pathname, index=index, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    save_feather(feather_dat.reset_index(), path_to_feather=pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{filename}"' in out and "Done." in out

    os.remove(pathname)
    os.remove(pathname_.name)


def test_save_svg_as_emf(capfd):
    from pyhelpers.store import save_svg_as_emf

    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    # svg_pathname = cd("tests\\images", "store-save_fig-demo.svg")
    # emf_pathname = cd("tests\\images", "store-save_fig-demo.emf")
    pathname_ = tempfile.NamedTemporaryFile()
    svg_pathname, emf_pathname = map(lambda file_ext: pathname_.name + file_ext, [".svg", ".emf"])

    plt.savefig(svg_pathname)  # Save the figure as a .svg file

    save_svg_as_emf(path_to_svg=svg_pathname, path_to_emf=emf_pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{os.path.basename(emf_pathname)}"' in out and "Done." in out

    plt.close()

    os.remove(pathname_.name)
    os.remove(svg_pathname)
    os.remove(emf_pathname)


def test_save_fig(capfd):
    from pyhelpers.store import save_fig

    x, y = (1, 1), (2, 2)

    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    # img_dir = cd("tests\\images")
    # png_pathname = cd(img_dir, "store-save_fig-demo.png")
    pathname_ = tempfile.NamedTemporaryFile()
    png_pathname = pathname_.name + ".png"
    png_filename = os.path.basename(png_pathname)

    save_fig(png_pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{png_filename}"' in out and "Done." in out

    os.remove(png_pathname)

    # svg_pathname = cd(img_dir, "store-save_fig-demo.svg")
    svg_pathname, emf_pathname = map(lambda file_ext: pathname_.name + file_ext, [".svg", ".emf"])
    svg_filename, emf_filename = map(os.path.basename, [svg_pathname, emf_pathname])
    save_fig(svg_pathname, verbose=True, conv_svg_to_emf=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{svg_filename}"' in out and f'Saving "{emf_filename}"' in out and "Done." in out

    plt.close()

    os.remove(svg_pathname)
    os.remove(emf_pathname)
    os.remove(pathname_.name)


def test_save_web_page_as_pdf(capfd):
    from pyhelpers.store import save_web_page_as_pdf

    # pdf_pathname = cd("tests\\documents", "pyhelpers.pdf")
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ".pdf"
    filename = os.path.basename(pathname)
    web_page_url = 'https://pyhelpers.readthedocs.io/en/latest/'

    save_web_page_as_pdf(web_page_url, pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done" in out

    os.remove(pathname)
    os.remove(pathname_.name)


@pytest.mark.parametrize(
    'ext', [".pickle", ".csv", ".json", ".joblib", ".feather", ".pdf", ".png", ".unknown"])
def test_save_data(capfd, recwarn, ext):
    from pyhelpers.store import save_data

    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ext
    filename = os.path.basename(pathname)

    if ext == ".json":
        dat = example_dataframe().to_json(orient='index')
    elif ext == ".pdf":
        dat = 'https://pyhelpers.readthedocs.io/en/latest/'
    elif ext == ".png":
        dat = None
        x, y = (1, 1), (2, 2)
        plt.figure()
        plt.plot([x[0], y[0]], [x[1], y[1]])
    else:
        dat = example_dataframe()

    save_data(dat, path_to_file=pathname, verbose=True, confirmation_required=False)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done" in out

    if ext == ".unknown":
        assert len(recwarn) == 1
        w = recwarn.pop()
        assert str(w.message) == "The specified file format (extension) is not recognisable by " \
                                 "`pyhelpers.store.save_data`."

    save_data(dat, path_to_file=pathname, verbose=True, confirmation_required=False)
    out, _ = capfd.readouterr()
    assert f'Updating "{filename}"' in out and "Done" in out

    os.remove(pathname)
    os.remove(pathname_.name)


# == Load data =====================================================================================

def test_load_spreadsheets(capfd):
    from pyhelpers.store import load_spreadsheets

    dat_dir = cd("tests\\data")
    path_to_xlsx = cd(dat_dir, "dat.xlsx")

    wb_data = load_spreadsheets(path_to_xlsx, verbose=True, index_col=0)
    out, _ = capfd.readouterr()
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
    out, _ = capfd.readouterr()
    assert out == f'Loading "{data_dir}\\dat.pickle" ... Done.\n'
    assert pickle_dat.equals(example_dataframe())
    _ = load_data(path_to_file=dat_pathname, verbose=True, test_arg=True)
    out, _ = capfd.readouterr()
    assert "'test_arg' is an invalid keyword argument for load()" in out

    dat_pathname = cd(data_dir, "dat.csv")
    csv_dat = load_data(path_to_file=dat_pathname, index=0, verbose=True)
    out, _ = capfd.readouterr()
    assert out == f'Loading "{data_dir}\\dat.csv" ... Done.\n'
    assert csv_dat.astype('float').equals(example_dataframe())

    dat_pathname = cd(data_dir, "dat.json")
    json_dat = load_data(path_to_file=dat_pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert out == f'Loading "{data_dir}\\dat.json" ... Done.\n'
    assert list(json_dat.keys()) == example_dataframe().index.to_list()

    dat_pathname = cd(data_dir, "dat.feather")
    feather_dat = load_data(path_to_file=dat_pathname, index=0, verbose=True)
    out, _ = capfd.readouterr()
    assert out == f'Loading "{data_dir}\\dat.feather" ... Done.\n'
    assert feather_dat.equals(example_dataframe())

    dat_pathname = cd(data_dir, "dat.joblib")
    joblib_dat = load_data(path_to_file=dat_pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert out == f'Loading "{data_dir}\\dat.joblib" ... Done.\n'
    np.random.seed(0)
    assert np.array_equal(joblib_dat, np.random.rand(100, 100))


# == Uncompress data ===============================================================================

def test_unzip(capfd):
    from pyhelpers.store import unzip

    zip_file_path = cd("tests\\data", "zipped.zip")

    unzip(path_to_zip_file=zip_file_path, verbose=True)

    out, _ = capfd.readouterr()
    assert out == 'Extracting "tests\\data\\zipped.zip" to "tests\\data\\zipped\\" ... Done.\n'


def test_seven_zip(capfd):
    from pyhelpers.store import seven_zip

    zip_file_pathname = cd("tests\\data", "zipped.zip")

    seven_zip(path_to_zip_file=zip_file_pathname, verbose=True)

    out, _ = capfd.readouterr()
    assert out.startswith('\r\n7-Zip')


# == Convert data ==================================================================================

def test_markdown_to_rst(capfd):
    from pyhelpers.store import markdown_to_rst

    dat_dir = cd("tests\\documents")

    path_to_md_file = cd(dat_dir, "readme.md")
    path_to_rst_file = cd(dat_dir, "readme.rst")

    markdown_to_rst(path_to_md_file, path_to_rst_file, engine='pypandoc', verbose=True)
    out, _ = capfd.readouterr()
    assert out == 'Updating "readme.rst" at "tests\\documents\\" ... Done.\n'

    markdown_to_rst(path_to_md_file, path_to_rst_file, verbose=True)
    out, _ = capfd.readouterr()
    assert out == 'Updating "readme.rst" at "tests\\documents\\" ... Done.\n'


@pytest.mark.parametrize('engine', [None, 'xlsx2csv'])
def test_xlsx_to_csv(engine, capfd):
    from pyhelpers.store import xlsx_to_csv, load_csv

    path_to_test_xlsx = cd("tests\\data", "dat.xlsx")

    temp_csv = xlsx_to_csv(path_to_test_xlsx, engine=engine, verbose=True)
    out, _ = capfd.readouterr()
    assert out.startswith("Converting") and "Done." in out

    data = load_csv(temp_csv, index=0)
    assert data.astype('float16').equals(example_dataframe().astype('float16'))

    if engine is None:
        os.remove(temp_csv)


if __name__ == '__main__':
    pytest.main()
