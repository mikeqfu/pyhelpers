"""
Global pytest configuration, availability checks and shared test fixtures.
"""

import os
import pathlib
import shutil
import socket

import pytest

try:  # local development: read settings from an untracked .env file (never overrides real env vars)
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is a dev-only dependency
    # noinspection unused-parameter
    def load_dotenv(*args, **kwargs):
        """No-op fallback used when python-dotenv is not installed."""
        return False

# Read settings from an untracked .env file for local development;
# never overrides variables already set in the environment (e.g. by CI)
load_dotenv()

IN_CI = os.environ.get("CI", "").lower() == "true"


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
HAS_7ZIP = shutil.which("7z") is not None or os.path.isfile(r"C:\Program Files\7-Zip\7z.exe")
HAS_INKSCAPE = (shutil.which("inkscape") is not None
                or os.path.isfile(r"C:\Program Files\Inkscape\bin\inkscape.exe"))
HAS_PANDOC = (shutil.which("pandoc") is not None
              or os.path.isfile(r"C:\Program Files\Pandoc\pandoc.exe"))
HAS_WKHTMLTOPDF = (shutil.which("wkhtmltopdf") is not None
                   or os.path.isfile(r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"))

# Service availability
_POSTGRES_HOST = os.environ.get("POSTGRES_SERVER", "localhost")
_POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
_MSSQL_HOST = os.environ.get("MSSQL_SERVER", "localhost")
_MSSQL_PORT = int(os.environ.get("MSSQL_PORT", 1433))

HAS_POSTGRES = _is_service_reachable(_POSTGRES_HOST, _POSTGRES_PORT)
HAS_MSSQL = _is_service_reachable(_MSSQL_HOST, _MSSQL_PORT)

# Reusable skip markers for tests
requires_7zip = pytest.mark.skipif(
    not (HAS_7ZIP or IN_CI),
    reason="7-Zip executable is not installed"
)
requires_inkscape = pytest.mark.skipif(
    not (HAS_INKSCAPE or IN_CI),
    reason="Inkscape executable is not installed"
)
requires_pandoc = pytest.mark.skipif(
    not (HAS_PANDOC or IN_CI),
    reason="Pandoc executable is not installed"
)
requires_wkhtmltopdf = pytest.mark.skipif(
    not (HAS_WKHTMLTOPDF or IN_CI),
    reason="wkhtmltopdf executable is not installed"
)
requires_postgres = pytest.mark.skipif(
    not (HAS_POSTGRES or IN_CI),
    reason=f"PostgreSQL service is not reachable on {_POSTGRES_HOST}:{_POSTGRES_PORT}",
)
requires_mssql = pytest.mark.skipif(
    not (HAS_MSSQL or IN_CI),
    reason=f"MS SQL Server service is not reachable on {_MSSQL_HOST}:{_MSSQL_PORT}",
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


@pytest.fixture(scope="session")
def mssql_kwargs():
    return {
        "host": os.environ.get("MSSQL_SERVER"),
        "port": os.environ.get("MSSQL_PORT"),
        "username": os.environ.get("MSSQL_USER"),
        "password": os.environ.get("MSSQL_PASSWORD"),
    }


@pytest.fixture(scope="session")
def postgres_kwargs():
    return {
        "host": os.environ.get("POSTGRES_SERVER"),
        "port": os.environ.get("POSTGRES_PORT"),
        "username": os.environ.get("POSTGRES_USER"),
        "password": os.environ.get("POSTGRES_PASSWORD"),
    }
