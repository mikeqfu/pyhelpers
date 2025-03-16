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


@pytest.mark.parametrize('ext', [".pickle", ".gz", ".xz", ".bz2"])
def test_save_pickle(ext, capfd, tmp_path):
    # pickle_pathname = importlib.resources.files(__package__).joinpath("data/dat.pickle")
    with tempfile.NamedTemporaryFile() as f:
        pathname = f.name + ext
        filename = os.path.basename(pathname)

        dat = 1
        save_pickle(dat, pathname, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{filename}"' in out and "Done." in out

        dat = example_dataframe()
        save_pickle(dat, pathname, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Updating "{filename}"' in out and "Done." in out

        dat = threading.Thread(target=lambda: print("Hello"))
        with pytest.raises(Exception):
            save_pickle(dat, pathname, raise_error=True)

        os.remove(pathname)


@pytest.mark.parametrize('ext', [".csv", ".xlsx", ".xls", ".pkl", ".ods", ".odt"])
@pytest.mark.parametrize('engine', [None, 'xlwt', 'openpyxl'])
@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
def test_save_spreadsheet(ext, engine, capfd, tmp_path):
    filename = f'test_save_spreadsheet{ext}'
    pathname = tmp_path / filename

    dat = example_dataframe()

    if ext in {".pickle", ".pkl"}:
        with pytest.raises(AssertionError, match=r"File extension must be"):
            save_spreadsheet(dat, path_to_file=pathname, engine=engine, raise_error=True)
    else:
        save_spreadsheet(dat, path_to_file=pathname, engine=engine, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{filename}"' in out and "Done." in out

    del dat
    gc.collect()

    dat = threading.Thread(target=lambda: print("Hello"))
    # noinspection PyTypeChecker
    with pytest.raises((AssertionError, AttributeError, IndexError)):
        # noinspection PyTypeChecker
        save_spreadsheet(dat, path_to_file=pathname, engine=engine, raise_error=True)


def test_save_spreadsheets(capfd):
    dat = [example_dataframe(), example_dataframe().T]
    sheets = ['TestSheet1', 'TestSheet2']

    # pathname = importlib.resources.files(__package__).joinpath("data/dat.xlsx")
    with tempfile.NamedTemporaryFile() as f:
        pathname = f.name + ".xlsx"
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
        os.remove(f.name)

        save_spreadsheets(dat, pathname, sheets, mode='a', if_sheet_exists='replace', verbose=True)
        out, _ = capfd.readouterr()
        assert all(x in out for x in [f'Saving "{filename}"', "Done."] + sheets)

        dat = threading.Thread(target=lambda: print("Hello"))
        with pytest.raises(Exception):
            # noinspection PyTypeChecker
            save_spreadsheets(dat, pathname, sheet_names=sheets, raise_error=True)

        os.remove(pathname)


@pytest.mark.parametrize('engine', [None, 'orjson', 'ujson', 'rapidjson'])
def test_save_json(capfd, engine):
    # json_pathname = importlib.resources.files(__package__).joinpath("data/dat.json")
    with tempfile.NamedTemporaryFile() as f:
        pathname = f.name + ".json"
        filename = os.path.basename(pathname)

        dat = {'a': 1, 'b': 2, 'c': 3, 'd': ['a', 'b', 'c']}

        save_json(dat, pathname, indent=4, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{filename}"' in out and "Done." in out

        dat = json.loads(example_dataframe().to_json(orient='index'))

        save_json(dat, pathname, engine=engine, indent=4, verbose=True)
        out, _ = capfd.readouterr()
        if engine == 'orjson':
            assert all(
                x in out for x in
                [f'Updating "{filename}"', "Failed.", "unexpected keyword argument"])
        else:
            assert f'Updating "{filename}"' in out and "Done." in out

        dat = threading.Thread(target=lambda: print("Hello"))

        with pytest.raises(Exception):
            save_json(dat, pathname, engine=engine, verbose=True, raise_error=True)

        os.remove(pathname)


def test_save_joblib(capfd):
    # joblib_pathname = importlib.resources.files(__package__).joinpath("data/dat.joblib")
    dat = example_dataframe().to_numpy()

    with tempfile.NamedTemporaryFile() as f:
        pathname = f.name + ".joblib"
        filename = os.path.basename(pathname)

        save_joblib(dat, pathname, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{filename}"' in out and "Done." in out

        dat = np.random.rand(100, 100)

        save_joblib(dat, pathname, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Updating "{filename}"' in out and "Done." in out

        dat = threading.Thread(target=lambda: print("Hello"))
        with pytest.raises(Exception):
            save_joblib(dat, pathname, raise_error=True)

        os.remove(pathname)


@pytest.mark.parametrize('index', [False, True])
def test_save_feather(index, capfd):
    dat = example_dataframe()

    # feather_pathname = importlib.resources.files(__package__).joinpath("data/dat.feather")
    with tempfile.NamedTemporaryFile() as f:
        pathname = f.name + ".feather"
        filename = os.path.basename(pathname)

        save_feather(dat, path_to_file=pathname, index=index, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{filename}"' in out and "Done." in out

        save_feather(dat.reset_index(), path_to_file=pathname, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Updating "{filename}"' in out and "Done." in out

        dat = threading.Thread(target=lambda: print("Hello"))
        with pytest.raises(Exception):
            # noinspection PyTypeChecker
            save_feather(dat, path_to_file=pathname, verbose=True, raise_error=True)

        os.remove(pathname)


def test_save_svg_as_emf(capfd):
    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    # svg_pathname = cd("tests/images", "store-save_fig-demo.svg")
    # emf_pathname = cd("tests/images", "store-save_fig-demo.emf")
    with tempfile.NamedTemporaryFile() as f:
        path_to_svg, path_to_emf = map(lambda file_ext: f.name + file_ext, [".svg", ".emf"])

        plt.savefig(path_to_svg)  # Save the figure as a .svg file

        save_svg_as_emf(path_to_svg=path_to_svg, path_to_emf=path_to_emf, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{os.path.basename(path_to_emf)}"' in out and "Done." in out

        with pytest.raises(Exception):
            save_svg_as_emf(
                path_to_svg, path_to_emf, verbose=True, inkscape_exe="test_inkscape.exe",
                raise_error=True)

        plt.close()

        os.remove(path_to_svg)
        os.remove(path_to_emf)


def test_save_fig_and_figure(capfd):
    x, y = (1, 1), (2, 2)

    fig = plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    # img_dir = cd("tests/images")
    # png_pathname = cd(img_dir, "store-save_fig-demo.png")
    with tempfile.NamedTemporaryFile() as f:
        png_pathname = f.name + ".png"
        png_filename = os.path.basename(png_pathname)

        save_fig(png_pathname, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{png_filename}"' in out and "Done." in out

        save_figure(fig, png_pathname, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Updating "{png_filename}"' in out and "Done." in out

        os.remove(png_pathname)

        # svg_pathname = cd(img_dir, "store-save_fig-demo.svg")
        svg_pathname, emf_pathname = map(lambda file_ext: f.name + file_ext, [".svg", ".emf"])
        svg_filename, emf_filename = map(os.path.basename, [svg_pathname, emf_pathname])
        save_fig(svg_pathname, verbose=True, conv_svg_to_emf=True)
        out, _ = capfd.readouterr()
        assert (f'Saving "{svg_filename}"' in out and
                f'Saving "{emf_filename}"' in out and "Done." in out)

        save_figure(fig, svg_pathname, verbose=True, conv_svg_to_emf=True)
        out, _ = capfd.readouterr()
        assert (f'Updating "{svg_filename}"' in out and
                f'Updating "{emf_filename}"' in out and "Done." in out)

        plt.close()

        os.remove(svg_pathname)
        os.remove(emf_pathname)


def test_save_html_as_pdf(capfd):
    with tempfile.NamedTemporaryFile() as f:
        pathname = f.name + ".pdf"
        filename = os.path.basename(pathname)
        web_page_url = 'https://github.com/mikeqfu/pyhelpers#readme'
        # web_page_url = 'https://www.python.org/'

        # noinspection PyBroadException
        save_html_as_pdf(web_page_url, pathname, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{filename}"' in out

        os.remove(pathname)


@pytest.mark.parametrize(
    'ext', [".pickle", ".csv", ".json", ".joblib", ".feather", ".pdf", ".png", ".unknown"])
def test_save_data(ext, capfd, caplog):
    with tempfile.NamedTemporaryFile() as f:
        pathname = f.name + ext
        filename = os.path.basename(pathname)

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

        save_data(dat, path_to_file=pathname, verbose=True, confirmation_required=False)
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

        save_data(dat, path_to_file=pathname, verbose=True, confirmation_required=False)
        out, _ = capfd.readouterr()
        assert f'Updating "{filename}"' in out
        if ext == ".pdf":
            assert "Done." in out

        os.remove(pathname)


if __name__ == '__main__':
    pytest.main()
