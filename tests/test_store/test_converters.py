"""
Tests the :mod:`~pyhelpers.store.converters` submodule.
"""

import importlib.resources
import os
import shutil
import subprocess

import pandas as pd
import pytest

from pyhelpers._cache import _format_display_path, _get_relative_path, _normalize_path, \
    example_dataframe
from pyhelpers.store.converters import markdown_to_rst, seven_zip, unzip, xlsx_to_csv
from pyhelpers.store.loaders import load_csv
from tests.conftest import requires_pandoc


def test_unzip(dat_dir, tmp_path, capfd):
    path_to_zip_file_ = dat_dir / "dat.zip"

    with importlib.resources.as_file(path_to_zip_file_) as path_to_zip_file:
        unzip(zip_file_path=path_to_zip_file, output_dir=tmp_path, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Extracting {_format_display_path(_get_relative_path(path_to_zip_file))}' in out
        assert f' to "{_normalize_path(tmp_path)}' in out and "Done." in out


@pytest.mark.parametrize('file_ext', [".zip", ".7z"])
@pytest.mark.parametrize('verbose', [True, False])
def test_seven_zip(dat_dir, file_ext, tmp_path, verbose, capfd):
    # import tempfile, pathlib; tmp_path = pathlib.Path(tempfile.mkdtemp())
    path_to_zip_file_ = dat_dir / f"dat{file_ext}"

    with importlib.resources.as_file(path_to_zip_file_) as path_to_zip_file:
        seven_zip(zip_file_path=path_to_zip_file, output_dir=tmp_path, verbose=verbose)
        out, _ = capfd.readouterr()
        if verbose:
            assert "Everything is Ok" in out and "Done." in out
        else:
            assert (tmp_path / "zipped.txt").is_file()

        with pytest.raises(FileNotFoundError) as exc_info:
            seven_zip(path_to_zip_file, tmp_path, raise_error=True, seven_zip_exe='one_zip.exe')
            assert '"7-Zip" (https://www.7-zip.org/) is required' in exc_info.value


@requires_pandoc
@pytest.mark.parametrize('engine', [None, 'pypandoc'])
def test_markdown_to_rst(engine, tmp_path, capfd):
    """
    Test :func:`~pyhelpers.store.markdown_to_rst`.

    :param engine: Conversion engine to test (``None`` for CLI Pandoc, ``'pypandoc'`` for module).
    :type engine: str | None
    :param tmp_path: Temporary directory fixture provided by pytest.
    :type tmp_path: pathlib.Path
    :param capfd: Capture fixture for stdout and stderr streams.
    :type capfd: pytest.CaptureFixture[str]
    """

    md_filename, rst_filename = "readme.md", "readme.rst"

    path_to_md_file = tmp_path / md_filename
    path_to_rst_file = tmp_path / rst_filename

    # Create dummy document files directly in the temporary test directory
    path_to_md_file.write_text(
        "# Sample Title\n\nSample paragraph text.\n",
        encoding="utf-8"
    )
    path_to_rst_file.write_text(
        "Sample Title\n============\n\nSample paragraph text.\n",
        encoding="utf-8"
    )

    out_path = _get_relative_path(str(tmp_path))
    display_path = _format_display_path(out_path)

    # Forward conversion: Markdown to rst
    markdown_to_rst(path_to_md_file, path_to_rst_file, engine=engine, verbose=True)
    out, _ = capfd.readouterr()
    assert f'Updating "{rst_filename}" in {display_path} ... Done.' in out

    # Reverse conversion: rst to Markdown
    markdown_to_rst(
        path_to_md_file,
        path_to_rst_file,
        engine=engine,
        verbose=True,
        reverse=True,
    )
    out, _ = capfd.readouterr()
    assert f'Updating "{md_filename}" in {display_path} ... Done.' in out

    # Verify invalid executable handling when engine=None
    invalid_exe = "test_pandoc.exe"
    markdown_to_rst(
        path_to_md_file,
        path_to_rst_file,
        verbose=True,
        pandoc_exe=invalid_exe,
    )
    out, _ = capfd.readouterr()
    assert "Failed." in out
    assert '"Pandoc" (https://pandoc.org/) is required to proceed' in out


@pytest.mark.parametrize('engine', [
    pytest.param(
        None,
        marks=pytest.mark.skipif(
            os.name != 'nt' and shutil.which('wine') is None,
            reason="VBScript engine requires Windows or wine"
        )
    ),
    'xlsx2csv'
])
@pytest.mark.parametrize('header', [0, None])
def test_xlsx_to_csv(dat_dir, engine, header, capfd):
    """
    Integration test verifying end-to-end conversion and DataFrame equality.

    :param dat_dir: Pytest fixture providing access to the test data directory.
    :type dat_dir: pathlib.Path
    :param engine: Conversion engine to test, either ``'xlsx2csv'`` or ``None``.
    :type engine: str | None
    :param header: Row number to use as column names, or ``None``.
    :type header: int | None
    :param capfd: Pytest fixture capturing standard stdout and stderr streams.
    :type capfd: _pytest.capture.CaptureFixture
    :return: ``None``
    :rtype: None
    """

    test_xlsx_path_ = dat_dir / "dat.xlsx"

    with importlib.resources.as_file(test_xlsx_path_) as test_xlsx_path:
        with pytest.raises(Exception):
            _ = xlsx_to_csv(
                test_xlsx_path / "123",
                engine=engine,
                sheet_name=None,
                raise_error=True
            )

        temp_csv = xlsx_to_csv(test_xlsx_path, engine=engine, verbose=True)
        out, _ = capfd.readouterr()
        assert out.startswith("Converting") and "Done." in out

        if engine is None:
            temp_csv_ = xlsx_to_csv(
                test_xlsx_path, temp_csv, if_exists='replace', engine=engine, verbose=True
            )
            out, _ = capfd.readouterr()
            assert out.startswith("Converting") and "Done." in out
            assert temp_csv_ == temp_csv

            _ = xlsx_to_csv(test_xlsx_path, "", if_exists='pass', engine=engine, verbose=True)
            out, _ = capfd.readouterr()
            assert out.startswith("Converting") and "Canceled." in out

        data: pd.DataFrame = load_csv(temp_csv, index_col=0, header=header)

        if header is None:
            data.columns = data.iloc[0]
            data = data[1:]
            data.index.name = data.columns.name
            data.columns.name = None

        assert data.astype(float).round(4).equals(example_dataframe().astype(float).round(4))

        if engine is None:
            os.remove(temp_csv)


def test_xlsx_to_csv_mocked(dat_dir, tmp_path, capfd, mocker):
    """
    Test edge cases, failure states and exception handling in xlsx_to_csv.

    This unit test mocks subprocess.run to safely exercise path resolution,
    return code evaluation and exception catching across all operating systems.

    :param dat_dir: Pytest fixture providing access to the test data directory.
    :type dat_dir: pathlib.Path
    :param tmp_path: Pytest fixture providing a temporary directory path.
    :type tmp_path: pathlib.Path
    :param capfd: Pytest fixture capturing standard stdout and stderr streams.
    :type capfd: _pytest.capture.CaptureFixture
    :param mocker: Pytest-mock fixture for stubbing target callables.
    :type mocker: pytest_mock.MockerFixture
    :return: ``None``
    :rtype: None
    """

    test_xlsx_path = dat_dir / "dat.xlsx"

    # Mock subprocess.run so _xlsx_to_csv executes its internal lines safely
    completed_process = subprocess.CompletedProcess(args=[], returncode=0)
    mock_run = mocker.patch('subprocess.run', return_value=completed_process)

    # Mock NamedTemporaryFile to avoid leaking unclosed tempfile wrappers
    mock_temp = mocker.patch('tempfile.NamedTemporaryFile')
    mock_temp.return_value.name = str(tmp_path / "temp.csv")

    # 1. Test path_to_csv=None (temporary file creation) and ret_null=True
    res_null = xlsx_to_csv(
        test_xlsx_path,
        path_to_csv=None,
        engine=None,
        ret_null=True,
        verbose=True
    )
    out, _ = capfd.readouterr()
    assert res_null is None
    assert "Done." in out
    assert mock_run.called

    # 2. Test VBScript failure branch (ret_code != 0)
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1)
    res_fail = xlsx_to_csv(
        test_xlsx_path,
        path_to_csv=tmp_path / "fail.csv",
        engine=None,
        verbose=True
    )
    out_fail, _ = capfd.readouterr()
    assert res_fail is None
    assert "Failed." in out_fail

    # 3. Test exception handling block with raise_error=False via side_effect
    mock_run.side_effect = ValueError("Test error")
    res_err = xlsx_to_csv(
        test_xlsx_path,
        engine=None,
        verbose=True,
        raise_error=False
    )
    out_err, _ = capfd.readouterr()
    assert res_err is None
    assert "Failed." in out_err


if __name__ == '__main__':
    pytest.main()
