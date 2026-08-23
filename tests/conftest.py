"""
Global pytest configuration and shared test fixtures.
"""

import pathlib

import pytest


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
