"""
Tests the :mod:`~pyhelpers.store.converters` submodule.
"""

import importlib.resources
import os.path
import shutil

import pytest

from pyhelpers._cache import _add_slashes, _check_relative_pathname, _normalize_pathname, \
    example_dataframe
from pyhelpers.store.converters import *
from pyhelpers.store.loaders import load_csv


def test_unzip(capfd):
    path_to_zip_file_ = importlib.resources.files("tests").joinpath("data", "zipped.zip")
    out_dir = tempfile.mkdtemp()

    with importlib.resources.as_file(path_to_zip_file_) as path_to_zip_file:
        unzip(path_to_zip_file=path_to_zip_file, output_dir=out_dir, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Extracting {_add_slashes(os.path.relpath(path_to_zip_file_.__str__()))}' in out
        assert f' to "{_normalize_pathname(out_dir)}' in out and "Done." in out


@pytest.mark.parametrize('verbose', [True, False])
def test_seven_zip(capfd, verbose):
    path_to_zip_file_ = importlib.resources.files("tests").joinpath("data", "zipped.zip")
    output_dir = tempfile.mkdtemp()

    with importlib.resources.as_file(path_to_zip_file_) as path_to_zip_file:
        seven_zip(path_to_zip_file=path_to_zip_file, output_dir=output_dir, verbose=verbose)
        out, _ = capfd.readouterr()
        if verbose:
            assert "Everything is Ok" in out and "Done." in out
        else:
            assert os.path.isfile(os.path.join(output_dir, "zipped.txt"))

        with pytest.raises(FileNotFoundError) as exc_info:
            seven_zip(path_to_zip_file, output_dir, raise_error=True, seven_zip_exe='one_zip.exe')
            assert '"7-Zip" (https://www.7-zip.org/) is required' in exc_info.value


@pytest.mark.parametrize('engine', [None, 'pypandoc'])
def test_markdown_to_rst(capfd, engine):
    md_filename, rst_filename = "readme.md", "readme.rst"

    path_to_md_file, path_to_rst_file = map(
        importlib.resources.files("tests").joinpath,
        [os.path.join("documents", md_filename), os.path.join("documents", rst_filename)])

    temp_dir = tempfile.TemporaryDirectory()
    shutil.copy(str(path_to_md_file), temp_dir.name)
    shutil.copy(str(path_to_rst_file), temp_dir.name)

    path_to_md_file = os.path.join(temp_dir.name, md_filename)
    path_to_rst_file = os.path.join(temp_dir.name, rst_filename)

    out_path = _check_relative_pathname(os.path.dirname(path_to_rst_file.__str__()))
    prt_info = f'Updating "{rst_filename}" in {_add_slashes(out_path)} ... Done.\n'

    markdown_to_rst(path_to_md_file, path_to_rst_file, engine=engine, verbose=True)  # noqa
    out, _ = capfd.readouterr()
    assert prt_info in out

    markdown_to_rst(
        path_to_md_file, path_to_rst_file, engine='pypandoc', verbose=True, reverse=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{md_filename}" in {_add_slashes(out_path)} ... Done.\n'

    markdown_to_rst(
        path_to_md_file, path_to_rst_file, verbose=True, pandoc_exe='test_pandoc.exe')  # noqa
    out, _ = capfd.readouterr()
    assert "Failed." in out and '"Pandoc" (https://pandoc.org/) is required to proceed' in out


@pytest.mark.parametrize('engine', [None, 'xlsx2csv'])
@pytest.mark.parametrize('header', [0, None])
def test_xlsx_to_csv(engine, header, capfd):
    path_to_test_xlsx_ = importlib.resources.files("tests").joinpath("data", "dat.xlsx")

    with importlib.resources.as_file(path_to_test_xlsx_) as path_to_test_xlsx:
        with pytest.raises(Exception):
            # noinspection PyTypeChecker
            _ = xlsx_to_csv(
                path_to_test_xlsx / "123", engine=engine, sheet_name=None, raise_error=True)

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
