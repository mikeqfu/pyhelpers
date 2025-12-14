"""
Tests the :mod:`~pyhelpers.store.savers` submodule.
"""

import gc
import json
import tempfile
import threading

import matplotlib.pyplot as plt
import numpy as np
import pytest

from pyhelpers._cache import example_dataframe
from pyhelpers.store.savers import *


def _test_save(func, dat, file_ext, capfd):
    with tempfile.NamedTemporaryFile() as f:
        pathname = f.name + file_ext
        filename = os.path.basename(pathname)

        func(dat, pathname, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{filename}"' in out and "Done." in out

        os.remove(pathname)


@pytest.mark.parametrize('ext', [".pickle", ".pkl", ".gz", ".xz", ".bz2"])
def test_save_pickle(ext, tmp_path, capfd):
    # path_to_file = importlib.resources.files(__package__).joinpath("data/dat.pickle")
    filename = f'test_save_pickle{ext}'
    path_to_file = tmp_path / filename

    dat = 1
    save_pickle(dat, path_to_file=path_to_file, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    dat = example_dataframe()
    save_pickle(dat, path_to_file=path_to_file, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{filename}"' in out and "Done." in out

    dat = threading.Thread(target=lambda: print("Hello"))
    with pytest.raises(Exception):
        save_pickle(dat, path_to_file=path_to_file, raise_error=True)


@pytest.mark.parametrize('ext', [".csv", ".xlsx", ".xls", ".pkl", ".ods", ".odt"])
@pytest.mark.parametrize('engine', [None, 'xlwt', 'openpyxl'])
@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
def test_save_spreadsheet(ext, engine, capfd, tmp_path):
    filename = f'test_save_spreadsheet{ext}'
    path_to_file = tmp_path / filename

    dat = example_dataframe()

    if ext in {".pickle", ".pkl"}:
        with pytest.raises(AssertionError, match=r"File extension must be"):
            save_spreadsheet(dat, path_to_file=path_to_file, engine=engine, raise_error=True)
    else:
        save_spreadsheet(dat, path_to_file=path_to_file, engine=engine, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{filename}"' in out and "Done." in out

    del dat
    gc.collect()

    dat = threading.Thread(target=lambda: print("Hello"))
    # noinspection PyTypeChecker
    with pytest.raises((AssertionError, AttributeError, IndexError)):
        # noinspection PyTypeChecker
        save_spreadsheet(dat, path_to_file=path_to_file, engine=engine, raise_error=True)


def test_save_spreadsheets(tmp_path, capfd):
    dat = [example_dataframe(), example_dataframe().T]
    sheets = ['TestSheet1', 'TestSheet2']

    # path_to_file = importlib.resources.files(__package__).joinpath("data/dat.xlsx")
    filename = "test_save_spreadsheets.xlsx"
    path_to_file = tmp_path / filename

    save_spreadsheets(dat, path_to_file=path_to_file, sheet_names=sheets, verbose=True)
    out, _ = capfd.readouterr()
    assert all(x in out for x in [f'Saving "{filename}"', "Done."] + sheets)

    save_spreadsheets(
        dat, path_to_file=path_to_file, sheet_names=sheets, mode='a', if_sheet_exists='replace',
        verbose=True)
    out, _ = capfd.readouterr()
    assert all(x in out for x in [f'Updating "{filename}"', "Done."] + sheets)

    save_spreadsheets(
        dat, path_to_file=path_to_file, sheet_names=sheets, mode='a', if_sheet_exists='new',
        verbose=True)
    out, _ = capfd.readouterr()
    assert all(x in out for x in [f'Updating "{filename}"', " saved as ", "Done."] + sheets)

    os.remove(path_to_file)

    save_spreadsheets(
        dat, path_to_file=path_to_file, sheet_names=sheets, mode='a', if_sheet_exists='replace',
        verbose=True)
    out, _ = capfd.readouterr()
    assert all(x in out for x in [f'Saving "{filename}"', "Done."] + sheets)

    dat = threading.Thread(target=lambda: print("Hello"))
    with pytest.raises(Exception):
        # noinspection PyTypeChecker
        save_spreadsheets(dat, path_to_file=path_to_file, sheet_names=sheets, raise_error=True)


@pytest.mark.parametrize('engine', [None, 'orjson', 'ujson', 'rapidjson'])
def test_save_json(engine, tmp_path, capfd):
    # path_to_file = importlib.resources.files(__package__).joinpath("data/dat.json")
    filename = "test_save_json.json"
    path_to_file = tmp_path / filename

    dat = {'a': 1, 'b': 2, 'c': 3, 'd': ['a', 'b', 'c']}

    save_json(dat, path_to_file=path_to_file, indent=4, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    dat = json.loads(example_dataframe().to_json(orient='index'))

    save_json(dat, path_to_file=path_to_file, engine=engine, indent=4, verbose=True)
    out, _ = capfd.readouterr()
    if engine == 'orjson':
        assert all(
            x in out for x in
            [f'Updating "{filename}"', "Failed.", "unexpected keyword argument"])
    else:
        assert f'Updating "{filename}"' in out and "Done." in out

    dat = threading.Thread(target=lambda: print("Hello"))

    with pytest.raises(Exception):
        save_json(dat, path_to_file=path_to_file, engine=engine, verbose=True, raise_error=True)


def test_save_joblib(tmp_path, capfd):
    # path_to_file = importlib.resources.files(__package__).joinpath("data/dat.joblib")
    dat = example_dataframe().to_numpy()

    filename = "test_save_joblib.joblib"
    path_to_file = tmp_path / filename

    save_joblib(dat, path_to_file=path_to_file, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    dat = np.random.rand(100, 100)

    save_joblib(dat, path_to_file=path_to_file, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{filename}"' in out and "Done." in out

    dat = threading.Thread(target=lambda: print("Hello"))
    with pytest.raises(Exception):
        save_joblib(dat, path_to_file=path_to_file, raise_error=True)


@pytest.mark.parametrize('index', [False, True])
def test_save_feather(index, tmp_path, capfd):
    dat = example_dataframe()

    # path_to_file = importlib.resources.files(__package__).joinpath("data/dat.feather")
    filename = "test_save_feather.feather"
    path_to_file = tmp_path / filename

    save_feather(dat, path_to_file=path_to_file, index=index, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    save_feather(dat.reset_index(), path_to_file=path_to_file, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{filename}"' in out and "Done." in out

    dat = threading.Thread(target=lambda: print("Hello"))
    with pytest.raises(Exception):
        # noinspection PyTypeChecker
        save_feather(dat, path_to_file=path_to_file, verbose=True, raise_error=True)


def test_save_svg_as_emf(tmp_path, capfd):
    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    # path_to_svg = cd("tests/images", "store-save_fig-demo.svg")
    # path_to_emf = cd("tests/images", "store-save_fig-demo.emf")
    path_to_svg, path_to_emf = map(
        lambda ext: tmp_path / f"test_save_svg_as_emf{ext}", [".svg", ".emf"])

    plt.savefig(path_to_svg)  # Save the figure as a .svg file

    save_svg_as_emf(path_to_svg=path_to_svg, path_to_emf=path_to_emf, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{os.path.basename(path_to_emf)}"' in out and "Done." in out

    with pytest.raises(Exception):
        save_svg_as_emf(
            path_to_svg, path_to_emf, verbose=True, inkscape_exe="test_inkscape.exe",
            raise_error=True)

    plt.close()


def test_save_fig_and_figure(tmp_path, capfd):
    x, y = (1, 1), (2, 2)

    fig = plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    # img_dir = cd("tests/images")
    # path_to_png = cd(img_dir, "store-save_fig-demo.png")
    png_filename = "test_save_fig_and_figure.png"
    path_to_png = tmp_path / png_filename

    save_fig(path_to_file=path_to_png, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{png_filename}"' in out and "Done." in out

    save_figure(fig, path_to_file=path_to_png, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{png_filename}"' in out and "Done." in out

    # path_to_svg = cd(img_dir, "store-save_fig-demo.svg")
    svg_filename, emf_filename = "test_save_fig_and_figure.svg", "test_save_fig_and_figure.emf"
    path_to_svg, path_to_emf = map(lambda f: tmp_path / f, [svg_filename, emf_filename])
    save_fig(path_to_file=path_to_svg, verbose=True, conv_svg_to_emf=True)
    out, _ = capfd.readouterr()
    assert (f'Saving "{svg_filename}"' in out and
            f'Saving "{emf_filename}"' in out and "Done." in out)

    save_figure(fig, path_to_file=path_to_svg, verbose=True, conv_svg_to_emf=True)
    out, _ = capfd.readouterr()
    assert (f'Updating "{svg_filename}"' in out and
            f'Updating "{emf_filename}"' in out and "Done." in out)

    plt.close()


def test_save_html_as_pdf(tmp_path, capfd):
    filename = "test_save_html_as_pdf.pdf"
    path_to_file = tmp_path / filename
    web_page_url = 'https://github.com/mikeqfu/pyhelpers#readme'
    # web_page_url = 'https://www.python.org/'

    # noinspection PyBroadException
    save_html_as_pdf(web_page_url, path_to_file=path_to_file, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out


@pytest.mark.parametrize(
    'ext', [".pickle", ".csv", ".json", ".joblib", ".feather", ".pdf", ".png", ".unknown"])
def test_save_data(ext, tmp_path, capfd, caplog):
    filename = f"test_save_data{ext}"
    path_to_file = tmp_path / filename

    if ext == ".json":
        dat = example_dataframe().to_json(orient='index')
    elif ext == ".pdf":
        dat = 'https://github.com/mikeqfu/pyhelpers#readme'
    elif ext == ".png":
        x, y = (1, 1), (2, 2)
        dat = plt.figure()
        plt.plot([x[0], y[0]], [x[1], y[1]])
    else:
        dat = example_dataframe()

    save_data(dat, path_to_file=path_to_file, verbose=True, confirmation_required=False)
    out, _ = capfd.readouterr()
    if ext == ".pdf":
        assert f'Saving "{filename}"' in out
    else:
        assert f'Saving "{filename}"' in out and "Done." in out

    if ext == ".unknown":
        # assert len(recwarn) == 1
        # w = recwarn.pop()
        # assert str(w.message) == "The specified file format (extension) is not recognisable by " \
        #                          "`pyhelpers.store.save_data`."
        for record in caplog.records:
            assert record.levelname == 'WARNING'
        assert ("The specified file format (extension) is not recognisable by "
                "`pyhelpers.store.save_data`.") in caplog.text

    save_data(dat, path_to_file=path_to_file, verbose=True, confirmation_required=False)
    out, _ = capfd.readouterr()
    assert f'Updating "{filename}"' in out
    if ext == ".pdf":
        assert "Done." in out


if __name__ == '__main__':
    pytest.main()
