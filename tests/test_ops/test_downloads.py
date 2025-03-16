"""
Tests the :mod:`~pyhelpers.ops.downloads` submodule.
"""

import tempfile

import pytest

from pyhelpers._cache import _normalize_pathname
from pyhelpers.ops.downloads import *


def test_is_downloadable():
    logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
    assert is_downloadable(logo_url)

    google_url = 'https://www.google.co.uk/'
    assert not is_downloadable(google_url)


@pytest.mark.parametrize('verbose', [True, False])
def test_download_file_from_url(capfd, verbose):
    logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'

    path_to_img = "ops-download_file_from_url-demo.png"
    download_file_from_url(logo_url, path_to_img, verbose=verbose, colour='green')
    assert os.path.isfile(path_to_img)

    download_file_from_url(logo_url, path_to_img, if_exists='pass', verbose=verbose)
    out, _ = capfd.readouterr()
    if verbose:
        assert "Aborting download." in out

    os.remove(path_to_img)

    path_to_img_ = tempfile.NamedTemporaryFile()
    path_to_img = path_to_img_.name + ".png"
    download_file_from_url(logo_url, path_to_img, verbose=verbose)
    assert os.path.isfile(path_to_img)

    os.remove(path_to_img_.name)
    os.remove(path_to_img)


class TestGitHubFileDownloader:

    @staticmethod
    def test_create_url():
        test_output_dir = tempfile.mkdtemp()

        test_url = "https://github.com/mikeqfu/pyhelpers/blob/master/tests/data/dat.csv"
        downloader = GitHubFileDownloader(test_url, output_dir=test_output_dir)
        test_api_url, test_download_path = downloader.create_url(test_url)
        assert (test_api_url ==
                'https://api.github.com/repos/mikeqfu/pyhelpers/contents/tests/data/'
                'dat.csv?ref=master')
        assert test_download_path == 'tests/data/dat.csv'

        test_url = "https://github.com/xyluo25/openNetwork/blob/main/docs"
        gd = GitHubFileDownloader(test_url, output_dir=test_output_dir)
        test_api_url, test_download_path = gd.create_url(test_url)
        assert (test_api_url ==
                'https://api.github.com/repos/xyluo25/openNetwork/contents/docs?ref=main')
        assert test_download_path == 'docs'

        shutil.rmtree(test_output_dir)

    @staticmethod
    def test_download(capfd):
        test_output_dir = tempfile.mkdtemp()

        test_url = "https://github.com/mikeqfu/pyhelpers/blob/master/tests/data/dat.csv"
        downloader = GitHubFileDownloader(test_url, output_dir=test_output_dir)
        downloader.download()
        out, _ = capfd.readouterr()
        assert _normalize_pathname("tests/data/dat.csv") in out
        assert downloader.total_files == 1

        test_url = "https://github.com/mikeqfu/pyhelpers/blob/master/tests/data"
        downloader = GitHubFileDownloader(test_url, output_dir=test_output_dir)
        downloader.download()
        out, _ = capfd.readouterr()
        assert downloader.total_files >= 15

        downloader = GitHubFileDownloader(test_url, flatten_files=True, output_dir=test_output_dir)
        downloader.download()
        out, _ = capfd.readouterr()
        assert "zipped.txt" in out
        assert downloader.total_files >= 15

        shutil.rmtree(test_output_dir)


if __name__ == '__main__':
    pytest.main()
