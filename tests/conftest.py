"""
Global pytest configuration, availability checks and shared test fixtures.
"""

import os
import pathlib
import shutil
import socket

import pytest


def _is_service_reachable(host, port):
    """
    Check whether a local or remote service port is reachable.

    :param host: Hostname or IP address of the target service.
    :type host: str
    :param port: Network port number.
    :type port: int
    :return: ``True`` if the socket connection succeeds, ``False`` otherwise.
    :rtype: bool

    **Examples**::

        >>> _is_service_reachable("localhost", 5432)
        False
    """

    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


# Binary executable availability
HAS_7ZIP = (
    shutil.which("7z") is not None
    or os.path.isfile(r"C:\Program Files\7-Zip\7z.exe")
)

HAS_INKSCAPE = (
    shutil.which("inkscape") is not None
    or os.path.isfile(r"C:\Program Files\Inkscape\bin\inkscape.exe")
)

HAS_PANDOC = (
    shutil.which("pandoc") is not None
    or os.path.isfile(r"C:\Program Files\Pandoc\pandoc.exe")
)

HAS_WKHTMLTOPDF = (
    shutil.which("wkhtmltopdf") is not None
    or os.path.isfile(r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
)

# Service availability
HAS_POSTGRES = _is_service_reachable("localhost", 5432)
HAS_MSSQL = _is_service_reachable("localhost", 1433)

# Reusable skip markers for tests
requires_7zip = pytest.mark.skipif(
    not HAS_7ZIP, reason="7-Zip executable is not installed"
)
requires_inkscape = pytest.mark.skipif(
    not HAS_INKSCAPE, reason="Inkscape executable is not installed"
)
requires_pandoc = pytest.mark.skipif(
    not HAS_PANDOC, reason="Pandoc executable is not installed"
)
requires_wkhtmltopdf = pytest.mark.skipif(
    not HAS_WKHTMLTOPDF, reason="wkhtmltopdf executable is not installed"
)
requires_postgres = pytest.mark.skipif(
    not HAS_POSTGRES, reason="PostgreSQL service is not reachable on localhost:5432"
)
requires_mssql = pytest.mark.skipif(
    not HAS_MSSQL, reason="MS SQL Server service is not reachable on localhost:1433"
)


@pytest.fixture(scope='session')
def dat_dir():
    """
    Return the absolute path to the test data assets directory.

    :return: Path object pointing to ``tests/data/``.
    :rtype: pathlib.Path

    **Examples**::

        >>> def test_csv_loading(dat_dir):
        ...     csv_file = dat_dir / "dat.csv"
        ...     assert csv_file.is_file()
    """

    return pathlib.Path(__file__).resolve().parent / "data"


@pytest.fixture(scope='session')
def doc_dir():
    """
    Return the absolute path to the test document assets directory.

    :return: Path object pointing to ``tests/documents/``.
    :rtype: pathlib.Path

    **Examples**::

        >>> def test_doc_printing(doc_dir):
        ...     pdf_file = doc_dir / "pyhelpers.pdf"
        ...     assert pdf_file.is_file()
    """

    return pathlib.Path(__file__).resolve().parent / "documents"


@pytest.fixture(scope='session')
def img_dir():
    """
    Return the absolute path to the test image assets directory.

    :return: Path object pointing to ``tests/images/``.
    :rtype: pathlib.Path

    **Examples**::

        >>> def test_img_saving(img_dir):
        ...     png_file = img_dir / "store-save_fig-demo.png"
        ...     assert png_file.is_file()
    """

    return pathlib.Path(__file__).resolve().parent / "images"
