"""
Tests the :mod:`~pyhelpers.ops.downloads` submodule.
"""

from unittest.mock import Mock, patch

import pytest

from pyhelpers._cache import _normalize_pathname
from pyhelpers.ops.downloads import *
from pyhelpers.ops.downloads import _download_file_from_url


def test_is_downloadable():
    logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
    assert is_downloadable(logo_url)

    google_url = 'https://www.google.co.uk/'
    assert not is_downloadable(google_url)


@pytest.mark.parametrize('verbose', [True, False])
@pytest.mark.parametrize('stream_download', [True, False])
def test_download_file_from_url(verbose, stream_download, tmp_path, capfd):
    logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'

    filename = "test_download_file_from_url.png"
    path_to_file = tmp_path / filename

    assert not os.path.isfile(path_to_file)

    download_file_from_url(
        logo_url, path_to_file, verbose=verbose, pbar_color='green', stream_download=stream_download)
    assert os.path.isfile(path_to_file)

    download_file_from_url(
        logo_url, path_to_file, if_exists='pass', verbose=verbose, stream_download=stream_download)
    out, _ = capfd.readouterr()
    if verbose:
        assert "already exists. Download skipped" in out


@pytest.mark.parametrize('total_records', [None, 2])
@pytest.mark.parametrize('validate', [True, False])
@pytest.mark.parametrize('content_length', [0, 1])
def test_mock_download_file_from_url(total_records, validate, content_length, tmp_path, capfd):
    path_to_file = tmp_path / "test.txt"

    # Mock response with Content-Length: 0
    mock_response = Mock()
    mock_response.status_code = 200  # Success!
    mock_response.headers = {'Content-Length': content_length}  # No Content-Length
    mock_response.content = b''
    mock_response.url = 'http://test_download_file_from_url.com/test.txt'
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=None)
    mock_response.iter_content = Mock(return_value=[b'col1,col2\nval1,val2\n'])

    mock_session = Mock()
    mock_session.get.return_value = mock_response

    with patch('pyhelpers._cache._init_requests_session', return_value=mock_session):
        if content_length:
            with pytest.raises(ValueError, match="Byte count mismatch."):
                _download_file_from_url(mock_response, path_to_file)
        else:
            _download_file_from_url(
                mock_response, path_to_file, total_records=total_records, validate=validate)
            out, _ = capfd.readouterr()
            if validate:
                if total_records is None:
                    assert "validation skipped" in out
                elif total_records == 2:
                    assert "validation skipped" not in out and "Warning" not in out


class TestGitHubFileDownloader:

    @staticmethod
    def test_create_url(tmp_path):
        test_url = 'https://github.com/mikeqfu/pyhelpers/blob/master/tests/data/dat.csv'
        downloader = GitHubFileDownloader(test_url, output_dir=tmp_path)
        test_api_url, test_download_path = downloader.create_url(test_url)
        assert (test_api_url ==
                'https://api.github.com/repos/mikeqfu/pyhelpers/contents/tests/data/'
                'dat.csv?ref=master')
        assert test_download_path == 'tests/data/dat.csv'

    @staticmethod
    @pytest.mark.parametrize('flatten_files', [False, True])
    def test_download(flatten_files, tmp_path, capfd):
        test_url = 'https://github.com/mikeqfu/pyhelpers/blob/master/tests/data/dat.csv'
        downloader = GitHubFileDownloader(test_url, output_dir=tmp_path)
        downloader.download()
        out, _ = capfd.readouterr()
        assert _normalize_pathname("tests/data/dat.csv") in out
        assert downloader.total_files == 1

        test_url = 'https://github.com/mikeqfu/smart-home-product-reviews-analysis/tree/master/tests'
        downloader = GitHubFileDownloader(test_url, flatten_files=flatten_files, output_dir=tmp_path)
        downloader.download()
        out, _ = capfd.readouterr()
        if flatten_files:
            assert "/tests/" not in out
        assert downloader.api_url.endswith('?ref=master')


if __name__ == '__main__':
    pytest.main()
