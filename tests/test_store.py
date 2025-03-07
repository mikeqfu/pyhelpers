"""Test the module :mod:`~pyhelpers.store`."""

import importlib.resources
import json

import matplotlib.pyplot as plt
import pytest
from scipy.sparse import csr_matrix

from pyhelpers._cache import _add_slashes, _check_relative_pathname, example_dataframe
from pyhelpers.store import *


# ==================================================================================================
# svr - Save data.
# ==================================================================================================

def test__check_saving_path(capfd):
    from pyhelpers.store import _check_saving_path

    file_path = os.getcwd()
    with pytest.raises(
            AssertionError, match="The input for `path_to_file` may not be a file path."):
        _check_saving_path(file_path, verbose=True)

    file_path = "pyhelpers.pdf"
    _check_saving_path(file_path, verbose=True)
    out, _ = capfd.readouterr()
    assert "Saving " in out

    file_path_ = importlib.resources.files(__package__).joinpath(
        os.path.join("documents", "pyhelpers.pdf"))
    with importlib.resources.as_file(file_path_) as file_path:
        _check_saving_path(file_path, verbose=True)
        out, _ = capfd.readouterr()
        assert "Updating " in out


def _test_save(func, dat, file_ext, capfd):
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + file_ext
    filename = os.path.basename(pathname)

    func(dat, pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    os.remove(pathname)
    os.remove(pathname_.name)


@pytest.mark.parametrize('ext', [".pickle", ".gz", ".xz", ".bz2"])
def test_save_pickle(ext, capfd):
    # pickle_pathname = importlib.resources.files(__package__).joinpath("data\\dat.pickle")
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ext
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


@pytest.mark.parametrize('ext', [".csv", ".xlsx", ".xls", ".pkl", ".ods", ".odt"])
@pytest.mark.parametrize('engine', [None, 'xlwt', 'openpyxl'])
def test_save_spreadsheet(ext, engine, capfd):
    dat = example_dataframe()

    pathname_ = tempfile.NamedTemporaryFile()

    pathname = pathname_.name + ext
    filename = os.path.basename(pathname)

    if ext in {".pickle", ".pkl"}:
        with pytest.raises(AssertionError, match=r"File extension must be"):
            save_spreadsheet(dat, pathname, engine=engine, verbose=True)
    else:
        save_spreadsheet(dat, pathname, engine=engine, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Saving "{filename}"' in out and "Done." in out
        os.remove(pathname)
        os.remove(pathname_.name)


def test_save_spreadsheets(capfd):
    dat = [example_dataframe(), example_dataframe().T]
    sheets = ['TestSheet1', 'TestSheet2']

    # pathname = importlib.resources.files(__package__).joinpath("data\\dat.xlsx")
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
    # json_pathname = importlib.resources.files(__package__).joinpath("data\\dat.json")
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
                x in out for x in
                [f'Updating "{filename}"', "Failed.", "unexpected keyword argument"])
        else:
            assert f'Updating "{filename}"' in out and "Done." in out

    os.remove(pathname)
    os.remove(pathname_.name)


def test_save_joblib(capfd):
    # joblib_pathname = importlib.resources.files(__package__).joinpath("data\\dat.joblib")
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
def test_save_feather(index, capfd):
    feather_dat = example_dataframe()

    # feather_pathname = importlib.resources.files(__package__).joinpath("data\\dat.feather")
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ".feather"
    filename = os.path.basename(pathname)

    save_feather(feather_dat, path_to_file=pathname, index=index, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out and "Done." in out

    save_feather(feather_dat.reset_index(), path_to_file=pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{filename}"' in out and "Done." in out

    os.remove(pathname)
    os.remove(pathname_.name)


def test_save_svg_as_emf(capfd):
    x, y = (1, 1), (2, 2)
    plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    # svg_pathname = cd("tests\\images", "store-save_fig-demo.svg")
    # emf_pathname = cd("tests\\images", "store-save_fig-demo.emf")
    pathname_ = tempfile.NamedTemporaryFile()
    path_to_svg, path_to_emf = map(lambda file_ext: pathname_.name + file_ext, [".svg", ".emf"])

    plt.savefig(path_to_svg)  # Save the figure as a .svg file

    save_svg_as_emf(path_to_svg=path_to_svg, path_to_emf=path_to_emf, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{os.path.basename(path_to_emf)}"' in out and "Done." in out

    plt.close()

    os.remove(pathname_.name)
    os.remove(path_to_svg)
    os.remove(path_to_emf)


def test_save_fig_and_figure(capfd):
    x, y = (1, 1), (2, 2)

    fig = plt.figure()
    plt.plot([x[0], y[0]], [x[1], y[1]])

    # img_dir = cd("tests\\images")
    # png_pathname = cd(img_dir, "store-save_fig-demo.png")
    pathname_ = tempfile.NamedTemporaryFile()
    png_pathname = pathname_.name + ".png"
    png_filename = os.path.basename(png_pathname)

    save_fig(png_pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{png_filename}"' in out and "Done." in out

    save_figure(fig, png_pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{png_filename}"' in out and "Done." in out

    os.remove(png_pathname)

    # svg_pathname = cd(img_dir, "store-save_fig-demo.svg")
    svg_pathname, emf_pathname = map(lambda file_ext: pathname_.name + file_ext, [".svg", ".emf"])
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
    os.remove(pathname_.name)


def test_save_html_as_pdf(capfd):
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ".pdf"
    filename = os.path.basename(pathname)
    web_page_url = 'https://github.com/mikeqfu/pyhelpers#readme'
    # web_page_url = 'https://www.python.org/'

    # noinspection PyBroadException
    save_html_as_pdf(web_page_url, pathname, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Saving "{filename}"' in out

    os.remove(pathname)
    os.remove(pathname_.name)


@pytest.mark.parametrize(
    'ext', [".pickle", ".csv", ".json", ".joblib", ".feather", ".pdf", ".png", ".unknown"])
def test_save_data(ext, capfd, caplog):
    pathname_ = tempfile.NamedTemporaryFile()
    pathname = pathname_.name + ext
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
    if ext == ".pdf":
        assert f'Updating "{filename}"' in out
    else:
        assert f'Updating "{filename}"' in out and "Done." in out

    os.remove(pathname)
    os.remove(pathname_.name)


# ==================================================================================================
# ldr - Load data.
# ==================================================================================================

def test__check_loading_path(capfd):
    from pyhelpers.store import _check_loading_path

    file_path = os.path.join("documents", "pyhelpers.pdf")
    _check_loading_path(file_path, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Loading {_add_slashes(file_path)}' in out


def test__set_index():
    from pyhelpers.store import _set_index

    example_df = example_dataframe()
    assert example_df.equals(_set_index(example_df))

    example_df_ = _set_index(example_df, index=0)
    assert example_df.iloc[:, 0].to_list() == example_df_.index.to_list()

    example_df_ = example_df.copy()
    example_df_.index.name = ''
    example_df_ = _set_index(example_df_.reset_index(), index=None)
    assert np.array_equal(example_df_.values, example_df.values)


def test_load_spreadsheets(capfd):
    file_path_ = os.path.join("data", "dat.xlsx")
    path_to_xlsx_ = importlib.resources.files(__package__).joinpath(file_path_)

    with importlib.resources.as_file(path_to_xlsx_) as path_to_xlsx:
        wb_data = load_spreadsheets(path_to_xlsx, verbose=True, index_col=0)
        out, _ = capfd.readouterr()
        assert f'Loading {_add_slashes(_check_relative_pathname(path_to_xlsx_.__str__()))} ... \n' \
               '\t\'TestSheet1\'. ... Done.\n' \
               '\t\'TestSheet2\'. ... Done.\n' \
               '\t\'TestSheet11\'. ... Done.\n' \
               '\t\'TestSheet21\'. ... Done.\n' \
               '\t\'TestSheet12\'. ... Done.\n' \
               '\t\'TestSheet22\'. ... Done.\n' in out
        assert isinstance(wb_data, dict)

        wb_data = load_spreadsheets(path_to_xlsx, as_dict=False, index_col=0)
        assert isinstance(wb_data, list)
        assert all(isinstance(x, pd.DataFrame) for x in wb_data)


def test_parse_csr_matrix(capfd):
    data_ = [1, 2, 3, 4, 5, 6]
    indices_ = [0, 2, 2, 0, 1, 2]
    indptr_ = [0, 2, 3, 6]

    csr_mat = csr_matrix((data_, indices_, indptr_), shape=(3, 3))

    assert list(csr_mat.data) == data_
    assert list(csr_mat.indices) == indices_
    assert list(csr_mat.indptr) == indptr_

    file_path_ = os.path.join("data", "csr_mat.npz")
    path_to_csr_npz_ = importlib.resources.files(__package__).joinpath(file_path_)

    with importlib.resources.as_file(path_to_csr_npz_) as path_to_csr_npz:
        csr_mat_ = load_csr_matrix(path_to_csr_npz, verbose=True)
        out, _ = capfd.readouterr()
        assert "Loading " in out and f'{file_path_}" ... Done.\n' in out

    rslt = csr_mat != csr_mat_
    assert isinstance(rslt, csr_matrix)
    assert rslt.count_nonzero() == 0
    assert rslt.nnz == 0

    _ = load_csr_matrix("", verbose=True)
    out, _ = capfd.readouterr()
    assert "No such file or directory" in out


@pytest.mark.parametrize(
    'ext', [
        ".pickle", ".pickle.gz", ".pickle.xz", ".pickle.bz2",
        ".csv", ".xlsx", ".json", ".feather", ".joblib"])
@pytest.mark.parametrize('engine', ['ujson', 'orjson', 'rapidjson', None])
def test_load_data(ext, engine, capfd, caplog):

    file_path_ = f"data{os.path.sep}dat{ext}"
    path_to_file = importlib.resources.files(__package__).joinpath(file_path_)

    with importlib.resources.as_file(path_to_file) as f:
        if ext in {".csv", ".xlsx", ".feather"}:
            idx_arg = {'path_to_file': f, 'verbose': True, 'index': 0}
        elif ext == ".json":
            idx_arg = {'path_to_file': f, 'verbose': True, 'engine': engine}
        else:
            idx_arg = {'path_to_file': f, 'verbose': True}

        dat = load_data(**idx_arg)
        out, _ = capfd.readouterr()
        assert 'Loading ' in out and f'{file_path_}" ... ' in out and 'Done.' in out

    if ext == ".xlsx":
        assert isinstance(dat, dict)
        assert dat['TestSheet1'].set_index('City').equals(example_dataframe())
    elif ext == ".json":
        assert list(dat.keys()) == example_dataframe().index.to_list()
    elif ext == ".joblib":
        np.random.seed(0)
        assert np.array_equal(dat, np.random.rand(100, 100))
    else:  # ext in {".pickle", ".pickle.gz", ".pickle.xz", ".pickle.bz2", ".csv", ".feather"}
        assert dat.astype(float).equals(example_dataframe())

    with (importlib.resources.as_file(path_to_file) as f):
        _ = load_data(path_to_file=f, verbose=True, test_arg=True)
        out, _ = capfd.readouterr()
        assert "'test_arg'" in out
        assert "invalid keyword argument" in out or "unexpected keyword argument" in out

    # with pytest.warns(UserWarning):
    with caplog.at_level(logging.WARNING):
        dat = load_data(path_to_file='none.test', verbose=True)
        assert dat is None


# ==================================================================================================
# xfr - Manipulate or transform data in various ways.
# ==================================================================================================

def test_unzip(capfd):
    file_path_ = os.path.join("data", "zipped.zip")
    path_to_zip_file_ = importlib.resources.files(__package__).joinpath(file_path_)
    out_dir = tempfile.mkdtemp()

    with importlib.resources.as_file(path_to_zip_file_) as path_to_zip_file:
        unzip(path_to_zip_file=path_to_zip_file, output_dir=out_dir, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Extracting {_add_slashes(os.path.relpath(path_to_zip_file_.__str__()))}' in out
        assert f' to "{out_dir}' in out and "Done." in out


def test_seven_zip(capfd):
    file_path_ = os.path.join("data", "zipped.zip")
    path_to_zip_file_ = importlib.resources.files(__package__).joinpath(file_path_)
    out_dir = tempfile.mkdtemp()

    with importlib.resources.as_file(path_to_zip_file_) as path_to_zip_file:
        seven_zip(path_to_zip_file=path_to_zip_file, output_dir=out_dir, verbose=True)
        out, _ = capfd.readouterr()
        assert "Everything is Ok" in out and "Done." in out


def test_markdown_to_rst(capfd):

    rst_filename = "readme.rst"

    path_to_md_file, path_to_rst_file = map(
        importlib.resources.files(__package__).joinpath,
        [os.path.join("documents", "readme.md"), os.path.join("documents", rst_filename)])

    out_path = _check_relative_pathname(os.path.dirname(path_to_rst_file.__str__()))
    prt_info = f'Updating "{rst_filename}" at {_add_slashes(out_path)} ... Done.\n'

    markdown_to_rst(path_to_md_file, path_to_rst_file, engine='pypandoc', verbose=True)  # noqa
    out, _ = capfd.readouterr()
    assert prt_info in out

    markdown_to_rst(path_to_md_file, path_to_rst_file, verbose=True)  # noqa
    out, _ = capfd.readouterr()
    assert prt_info in out


@pytest.mark.parametrize('engine', [None, 'xlsx2csv'])
@pytest.mark.parametrize('header', [0, None])
def test_xlsx_to_csv(engine, header, capfd):
    path_to_test_xlsx_ = importlib.resources.files(__package__).joinpath(
        os.path.join("data", "dat.xlsx"))

    with importlib.resources.as_file(path_to_test_xlsx_) as path_to_test_xlsx:
        temp_csv = xlsx_to_csv(path_to_test_xlsx, engine=engine, verbose=True)
        out, _ = capfd.readouterr()
        assert out.startswith("Converting") and "Done." in out

        if engine is None:
            temp_csv_ = xlsx_to_csv(
                path_to_test_xlsx, path_to_csv=temp_csv, if_exists='replace', engine=engine,
                verbose=True)
            out, _ = capfd.readouterr()
            assert out.startswith("Converting") and "Done." in out
            assert temp_csv_ == temp_csv

            _ = xlsx_to_csv(
                path_to_test_xlsx, path_to_csv="", if_exists='pass', engine=engine, verbose=True)
            out, _ = capfd.readouterr()
            assert out.startswith("Converting") and "Cancelled." in out

        data = load_csv(temp_csv, index=0, header=header)

        if engine is None and header is None:
            data.columns = data.iloc[0]
            data = data[1:]
            data.index.name = data.columns.name
            data.columns.name = None

        assert data.astype('float16').equals(example_dataframe().astype('float16'))

        if engine is None:
            os.remove(temp_csv)


if __name__ == '__main__':
    pytest.main()
