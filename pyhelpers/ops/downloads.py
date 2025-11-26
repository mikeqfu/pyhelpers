"""
Utilities for file downloads from the web.
"""

import json
import os
import re
import secrets
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request

import requests.adapters

from .._cache import _add_slashes, _check_dependencies, _check_relative_pathname, _check_url_scheme, \
    _get_ansi_colour_code, _init_requests_session, _print_failure_message, _USER_AGENT_STRINGS
from ..store import _check_saving_path


def is_downloadable(url, request_field='content-type', **kwargs):
    # noinspection PyShadowingNames
    """
    Checks if a URL leads to a webpage where downloadable content is available.

    :param url: A valid URL.
    :type url: str
    :param request_field: Name of the field/header indicating the original media type of the
        resource; defaults to ``'content-type'``.
    :type request_field: str
    :param kwargs: [Optional] Additional parameters for the function `requests.head()`_.
    :return: ``True`` if the given URL leads to downloadable content, ``False`` otherwise.
    :rtype: bool

    .. _`requests.head()`: https://2.python-requests.org/en/master/api/#requests.head

    **Examples**::

        >>> from pyhelpers.ops import is_downloadable
        >>> url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> is_downloadable(url)
        True
        >>> url = 'https://www.google.co.uk/'
        >>> is_downloadable(url)
        False
    """

    kwargs.update({'allow_redirects': True})
    h = requests.head(url=url, **kwargs)

    content_type = h.headers.get(request_field).lower()

    if content_type.startswith('text/html'):
        downloadable = False
    else:
        downloadable = True

    return downloadable


def _download_file_from_url(response, path_to_file, chunk_multiplier=1, desc=None, bar_format=None,
                            colour=None, validate=True, print_wrap_limit=None, **kwargs):
    # noinspection PyShadowingNames
    """
    Downloads a file from a given HTTP response and saves it to the specified location.

    This function reads the content of the response in chunks and writes it to a file while
    displaying a progress bar using `tqdm`_.

    .. _`tqdm`: https://tqdm.github.io/

    :param response: The HTTP response object with streaming enabled
        (e.g. `requests.get(url, stream=True)`).
    :type response: requests.Response
    :param path_to_file: The destination path where the downloaded file will be saved;
        this can be either a full path including the filename,
        or just a filename, in which case it will be saved in the current working directory.
    :type path_to_file: str | os.PathLike
    :param chunk_multiplier: A factor by which the default chunk size (1MB) is multiplied;
        this can be adjusted to optimise download performance based on file size; defaults to ``1``.
    :type chunk_multiplier: int | float
    :param desc: Custom description for the progress bar;
        when ``desc=None``, it defaults to the filename.
    :type desc: str | None
    :param bar_format: Custom format for the progress bar.
    :type bar_format: str | None
    :param colour: Custom colour of the progress bar (e.g. 'green', 'yellow'); defaults to ``None``.
    :type colour: str | None
    :param validate: Whether to validate if the downloaded file size matches the expected content
        length; defaults to ``True``.
    :type validate: bool
    :param print_wrap_limit: Maximum length of the string before splitting into two lines;
        defaults to ``None``, which disables splitting. If the string exceeds this value,
        e.g. ``100``, it will be split at (before) ``state_prep`` to improve readability
        when printed.
    :type print_wrap_limit: int | None
    :param kwargs: [Optional] Additional parameters passed to `tqdm.tqdm()`_, allowing customisation
        of the progress bar (e.g. ``disable=True`` to hide the progress bar).

    :raises TypeError: If writing the downloaded data to a file fails due to encoding issues.
    :raises ValueError: If the downloaded file size does not match the expected content length.

    .. _`tqdm.tqdm()`: https://tqdm.github.io/docs/tqdm/

    **Examples**::

        >>> from pyhelpers.ops.downloads import _download_file_from_url
        >>> from pyhelpers.dirs import cd
        >>> import requests
        >>> url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> path_to_img = cd("tests", "images", "ops-download_file_from_url-demo.png")
        >>> with requests.get(url, stream=True) as response:
        ...     _download_file_from_url(response, path_to_img, colour='green')
        Downloading "ops-download_file_from_url-demo.png" 100%|██████████| 83.6k/83.6k | ...
            Updating "ops-download_file_from_url-demo.png" in ".\\tests\\images\\" ... Done.
    """

    tqdm_ = _check_dependencies('tqdm')

    file_size = int(response.headers.get('content-length', 0))  # Total size in bytes

    block_size = 1024 ** 2
    chunk_size = int(block_size * chunk_multiplier) if file_size >= block_size else block_size

    colour_code, reset_colour = _get_ansi_colour_code([colour, 'reset']) if colour else ('', '')

    pbar_args = {
        'desc': desc or f'Downloading "{os.path.basename(path_to_file)}"',
        'total': file_size,  # total_iter = file_size // chunk_size
        'unit': 'B',
        'unit_scale': True,
        'bar_format':
            bar_format or
            f'{colour_code}{{desc}} {{percentage:3.0f}}%|{{bar:10}}| '
            f'{{n_fmt}}/{{total_fmt}} | {{rate_fmt}} | ETA: {{remaining}}{reset_colour}',
    }
    kwargs.update(pbar_args)

    belated = False if os.path.isfile(path_to_file) else True

    try:
        with open(file=path_to_file, mode='wb') as file, tqdm_.tqdm(**kwargs) as progress:
            written = 0  # Track the amount downloaded in bytes

            for data in response.iter_content(chunk_size=chunk_size, decode_unicode=True):
                if data:
                    try:  # Write chunk to file
                        file.write(data)
                    except TypeError:
                        file.write(data.encode())
                    progress.update(len(data))  # Update the progress bar
                    written += len(data)

    except (IOError, TypeError) as e:
        _print_failure_message(e, prefix="Download failed:", verbose=True, raise_error=True)

    _check_saving_path(
        path_to_file, verbose=True, print_prefix="\t", print_wrap_limit=print_wrap_limit,
        belated=belated)

    if validate and (written != file_size) and (file_size > 0):
        raise ValueError(f"Download failed: expected {file_size} bytes, got {written} bytes.")
    else:
        print("Done.")


def download_file_from_url(url, path_to_file, if_exists='replace', max_retries=5,
                           requests_session_args=None, verbose=False, print_wrap_limit=None,
                           chunk_multiplier=1, desc=None, bar_format=None, colour=None,
                           validate=True, stream_download=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Downloads a file from a valid URL.

    See also [`OPS-DFFU-1 <https://stackoverflow.com/questions/37573483/>`_] and
    [`OPS-DFFU-2 <https://stackoverflow.com/questions/15431044/>`_].

    :param url: Valid URL pointing to a web resource.
    :type url: str
    :param path_to_file: Path where the downloaded file will be saved;
        it can be either a full path with filename or just a filename,
        in which case it will be saved in the current working directory.
    :type path_to_file: str | os.PathLike[str]
    :param if_exists: Action to take if the specified file already exists;
        options include ``'replace'`` (default - download and replace the existing file) and
        ``'pass'`` (cancel the download).
    :type if_exists: str
    :param max_retries: Maximum number of retries in case of download failures; defaults to ``5``.
    :type max_retries: int
    :param verbose: Whether to print progress and relevant information to the console;
        defaults to ``False``.
    :param requests_session_args: [Optional] Additional parameters for initialising
        the requests session; defaults to ``None``.
    :type requests_session_args: dict | None
    :type verbose: bool | int
    :param print_wrap_limit: Maximum length of the string before splitting into two lines;
        defaults to ``None``, which disables splitting. If the string exceeds this value,
        e.g. ``100``, it will be split at (before) ``state_prep`` to improve readability
        when printed.
    :type print_wrap_limit: int | None
    :param chunk_multiplier: A factor by which the default chunk size (1MB) is multiplied;
        this can be adjusted to optimise download performance based on file size; defaults to ``1``.
    :type chunk_multiplier: int | float
    :param desc: Custom description for the progress bar;
        when ``desc=None``, it defaults to the filename.
    :type desc: str | None
    :param bar_format: Custom format for the progress bar.
    :type bar_format: str | None
    :param colour: Custom colour of the progress bar (e.g. 'green', 'yellow'); defaults to ``None``.
    :type colour: str | None
    :param validate: Whether to validate if the downloaded file size matches the expected content
        length; defaults to ``True``.
    :type validate: bool
    :param stream_download: When `stream_download=True`, use streaming download
        (memory-efficient, perferred for large files);
        When `stream_download=False`, not streaming (simpler/faster for small files);
        defaults to ``False``.
    :type stream_download: bool
    :param kwargs: [Optional] Additional parameters passed to the method `tqdm.tqdm()`_.

    .. _`tqdm.tqdm()`: https://tqdm.github.io/docs/tqdm/

    **Examples**::

        >>> from pyhelpers.ops import download_file_from_url
        >>> from pyhelpers.dirs import cd
        >>> from PIL import Image
        >>> import os
        >>> url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> path_to_img = cd("tests", "images", "ops-download_file_from_url-demo.png")
        >>> # Check if "python-logo.png" exists at the specified path
        >>> os.path.exists(path_to_img)
        False
        >>> # Download the .png file
        >>> download_file_from_url(url, path_to_img, verbose=True, colour='green')
        Downloading "ops-download_file_from_url-demo.png" 100%|██████████| 83.6k/83.6k | ...
            Saving "ops-download_file_from_url-demo.png" to "./tests/images/" ... Done.
        >>> # If download is successful, check again:
        >>> os.path.exists(path_to_img)
        True
        >>> img = Image.open(path_to_img)
        >>> img.show()  # as illustrated below

    .. figure:: ../_images/ops-download_file_from_url-demo.*
        :name: ops-download_file_from_url-demo
        :align: center
        :width: 65%

        The Python Logo.

    .. only:: html

        |

    .. note::

        - When ``verbose=True``, the function requires `tqdm <https://pypi.org/project/tqdm/>`_.
    """

    path_to_file_ = os.path.abspath(path_to_file)

    if os.path.isfile(path_to_file_) and if_exists != 'replace':
        if verbose:
            print(f'File "{os.path.basename(path_to_file)}" already exists. Aborting download.\n'
                  f'Set `if_exists="replace"` to update the existing file.')
        return None

    else:
        # Initialise session
        requests_session_args = requests_session_args or {}
        session = _init_requests_session(url=url, max_retries=max_retries, **requests_session_args)

        fake_headers = {
            'user-agent': secrets.choice(
                _USER_AGENT_STRINGS.get(secrets.choice(list(_USER_AGENT_STRINGS))))}

        os.makedirs(os.path.dirname(path_to_file_), exist_ok=True)  # Ensure the directory exists

        # If streaming, we can iterate over the response
        stream_download_ = verbose or stream_download

        with session.get(url=url, stream=stream_download_, headers=fake_headers) as response:
            if response.status_code != 200:
                print(f"Failed to retrieve file. HTTP Status Code: {response.status_code}.")
                return None

            if verbose:  # Handle verbose output with progress bar
                _download_file_from_url(
                    response=response,
                    path_to_file=path_to_file,
                    chunk_multiplier=chunk_multiplier,
                    desc=desc,
                    bar_format=bar_format,
                    colour=colour,
                    validate=validate,
                    print_wrap_limit=print_wrap_limit,
                    **kwargs
                )

            else:
                if stream_download_:
                    encoding = response.headers.get('Content-Encoding', '')
                    if 'gzip' in encoding or 'deflate' in encoding:
                        response.raw.decode_content = True

                    with open(path_to_file_, mode='wb') as f:  # Open the file in binary write mode
                        shutil.copyfileobj(fsrc=response.raw, fdst=f)  # type: ignore

                else:
                    with open(path_to_file_, mode='wb') as f:
                        f.write(response.content)

            # Validate download if necessary
            if validate and os.stat(path_to_file).st_size == 0:
                rel_path = _add_slashes(_check_relative_pathname(path_to_file))
                raise ValueError(
                    f"Error: The downloaded file at {rel_path} is empty. "
                    f"Check the URL or network connection.")
            # else:
            #     print(f"File successfully downloaded to {rel_path}.")
            return None


class GitHubFileDownloader:
    """
    Downloads files from GitHub repositories.

    This class facilitates downloading files from a specified GitHub repository URL.
    """

    def __init__(self, repo_url, flatten_files=False, output_dir=None):
        # noinspection PyShadowingNames
        """
        :param repo_url: URL of the GitHub repository to download from;
            it can be a path to a specific *blob* or *tree* location.
        :type repo_url: str
        :param flatten_files: Whether to flatten the directory structure by pulling
            all files into the root folder; defaults to ``False``.
        :type flatten_files: bool
        :param output_dir: Output directory where downloaded files will be saved;
            defaults to ``None``, meaning files will be saved in the current directory.
        :type output_dir: str | None

        :ivar str repo_url: URL of the GitHub repository.
        :ivar bool flatten_files: Whether to flatten the directory structure
            (i.e. pull the contents of all subdirectories into the root folder);
            defaults to ``False``.
        :ivar str | None output_dir: Output directory path; defaults to ``None``.
        :ivar str api_url: URL of the GitHub repository compatible with GitHub's REST API.
        :ivar str download_path: Pathname for downloading files.
        :ivar int total_files: Total number of files under the given directory.

        **Examples**::

            >>> from pyhelpers.ops import GitHubFileDownloader
            >>> from pyhelpers.dirs import delete_dir
            >>> output_dir = "tests/temp"
            >>> # Download a single file
            >>> repo_url = 'https://github.com/mikeqfu/pyhelpers/blob/master/tests/data/dat.csv'
            >>> downloader = GitHubFileDownloader(repo_url, output_dir=output_dir)
            >>> downloader.download()
            Downloaded to: ".\\tests\\temp\\dat.csv"
            1
            >>> # Download a directory
            >>> repo_url = 'https://github.com/mikeqfu/pyhelpers/blob/master/tests/data'
            >>> downloader = GitHubFileDownloader(repo_url, output_dir=output_dir)
            >>> downloader.download()
            Downloaded to: ".\\tests\\temp\\tests\\data\\csr_mat.npz"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.csv"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.feather"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.joblib"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.json"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.ods"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.pickle"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.pickle.bz2"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.pickle.gz"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.pickle.xz"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.txt"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.xlsx"
            Downloaded to: ".\\tests\\temp\\tests\\data\\zipped.7z"
            Downloaded to: ".\\tests\\temp\\tests\\data\\zipped.txt"
            Downloaded to: ".\\tests\\temp\\tests\\data\\zipped.zip"
            15
            >>> downloader = GitHubFileDownloader(
            ...     repo_url, flatten_files=True, output_dir=output_dir)
            >>> downloader.download()
            Downloaded to: ".\\tests\\temp\\csr_mat.npz"
            Downloaded to: ".\\tests\\temp\\dat.csv"
            Downloaded to: ".\\tests\\temp\\dat.feather"
            Downloaded to: ".\\tests\\temp\\dat.joblib"
            Downloaded to: ".\\tests\\temp\\dat.json"
            Downloaded to: ".\\tests\\temp\\dat.ods"
            Downloaded to: ".\\tests\\temp\\dat.pickle"
            Downloaded to: ".\\tests\temp\"dat.pickle.bz2"
            Downloaded to: ".\\tests\\temp\"dat.pickle.gz"
            Downloaded to: ".\\tests\\temp\\"dat.pickle.xz"
            Downloaded to: ".\\tests\\temp\\dat.txt"
            Downloaded to: ".\\tests\\temp\\dat.xlsx"
            Downloaded to: ".\\tests\\temp\\zipped.7z"
            Downloaded to: ".\\tests\\temp\\zipped.txt"
            Downloaded to: ".\\tests\\temp\\zipped.zip"
            15
            >>> delete_dir(output_dir)
            To delete the directory ".\\tests\\temp\\" (Not empty)
            ? [No]|Yes: yes
        """

        self.dir_out = ''
        self.repo_url = repo_url
        self.flatten = flatten_files
        self.output_dir = os.path.relpath(os.getcwd()) if output_dir is None else output_dir

        # Create a URL that is compatible with GitHub's REST API
        self.api_url, self.download_path = self.create_url(self.repo_url)

        # Initialize the total number of files under the given directory
        self.total_files = 0

        # Set user agent in default
        opener = urllib.request.build_opener()
        opener.addheaders = [(
            'user-agent',
            secrets.choice(_USER_AGENT_STRINGS.get(secrets.choice(list(_USER_AGENT_STRINGS)))))]

        urllib.request.install_opener(opener)

    @classmethod
    def create_url(cls, url):
        # noinspection PyShadowingNames
        """
        Creates a URL compatible with GitHub's REST API from the given URL.

        Handles *blob* or *tree* paths.

        :param url: URL.
        :type url: str
        :return: Tuple containing the URL of the GitHub repository and the pathname for downloading
            a file.
        :rtype: tuple

        **Examples**::

            >>> from pyhelpers.ops import GitHubFileDownloader
            >>> output_dir = "tests/temp"
            >>> url = 'https://github.com/mikeqfu/pyhelpers/blob/master/tests/data/dat.csv'
            >>> downloader = GitHubFileDownloader(url, output_dir=output_dir)
            >>> api_url, download_path = downloader.create_url(url)
            >>> api_url
            'https://api.github.com/repos/mikeqfu/pyhelpers/contents/tests/data/dat.csv?...
            >>> download_path
            'tests/data/dat.csv'
            >>> url = 'https://github.com/xyluo25/openNetwork/blob/main/docs'
            >>> downloader = GitHubFileDownloader(url, output_dir=output_dir)
            >>> api_url, download_path = downloader.create_url(url)
            >>> api_url
            'https://api.github.com/repos/xyluo25/openNetwork/contents/docs?ref=main'
            >>> download_path
            'docs'
        """

        repo_only_url = re.compile(
            r"https://github\.com/[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38}/[a-zA-Z0-9]+$")
        re_branch = re.compile("/(tree|blob)/(.+?)/")

        # Check if the given URL is a complete url to a GitHub repo.
        if re.match(repo_only_url, url):
            print(
                "Given url is a complete repository, "
                "please use 'git clone' to download the repository.")
            sys.exit()

        # Extract the branch name from the given url (e.g. master)
        branch = re_branch.search(url)
        download_path = url[branch.end():]

        api_url = (
            f'{url[: branch.start()].replace("github.com", "api.github.com/repos", 1)}/'
            f'contents/{download_path}?ref={branch[2]}')

        return api_url, download_path

    @classmethod
    def check_url(cls, url):
        """
        Checks if the scheme of the provided ``url`` is valid.

        :param url: The target URL.
        :type url: str

        .. seealso::

            - Examples for the method
              :meth:`GitHubFileDownloader.download()<pyhelpers.ops.GitHubFileDownloader.download>`.
        """

        parsed_url = _check_url_scheme(url, allowed_schemes=['https'])

        if 'github' not in parsed_url.netloc.lower():
            raise ValueError(
                f"Incorrect network location for GitHub repositories: '{parsed_url.netloc}'.")

    def download_single_file(self, file_url, dir_out):
        """
        Downloads a single file from the specified ``file_url`` to the ``dir_out`` directory.

        :param file_url: URL of the file to be downloaded.
        :type file_url: str
        :param dir_out: Directory path where the downloaded file will be saved.
        :type dir_out: str

        .. seealso::

            - Examples for the method
              :meth:`GitHubFileDownloader.download()<pyhelpers.ops.GitHubFileDownloader.download>`.
        """

        self.check_url(file_url)

        # Download the file
        _, _ = urllib.request.urlretrieve(file_url, dir_out)  # nosec

        if self.flatten:
            dir_out_ = os.path.basename(dir_out)
            if self.output_dir == os.path.relpath(os.getcwd()):
                print(f"Downloaded to: {_add_slashes(dir_out_)}")
            else:
                print(f"Downloaded to: {_add_slashes(self.output_dir)}{dir_out_}")

        else:
            print(f"Downloaded to: {_add_slashes(dir_out)}")

    def _get_response(self, api_url_local):
        response, _ = urllib.request.urlretrieve(api_url_local)  # nosec

        with open(response, "r") as f:  # Download files according to the response
            data = json.load(f)

        # If the data is a file, download it as one.
        if isinstance(data, dict) and data["type"] == "file":
            try:  # Download the file
                self.download_single_file(
                    data["download_url"], os.path.join(self.dir_out, data['name']))
                self.total_files += 1

                return self.total_files

            except KeyboardInterrupt as e:
                _print_failure_message(e, prefix="Error: Got interrupted for")

        # If the data is a directory, download all files in it
        for file in data:
            file_url, file_path = file["download_url"], file["path"]
            path = os.path.basename(file_path) if self.flatten else file_path
            path = os.path.join(self.output_dir, path)

            # Create a directory if it does not exist
            if os.path.dirname(path) != '':
                os.makedirs(os.path.dirname(path), exist_ok=True)

            if file_url is not None:  # Download the file if it is not a directory
                # file_name = file["name"]
                try:
                    self.download_single_file(file_url, path)
                    self.total_files += 1
                except KeyboardInterrupt:
                    print("Got interrupted.")

            else:  # If a directory, recursively download it
                try:
                    self.api_url, self.download_path = self.create_url(file["html_url"])
                    self.download(self.api_url)

                except Exception as e:
                    _print_failure_message(e, prefix="Error:")
                    print(f"{file['html_url']} may not be a file or a directory.")

        return None

    def download(self, api_url=None):
        """
        Downloads files from the specified GitHub ``api_url``.

        :param api_url: GitHub API URL for downloading files; defaults to ``None``.
        :type api_url: str | None
        :return: Total number of files downloaded under the given directory.
        :rtype: int

        .. seealso::

            >>> from pyhelpers.ops import GitHubFileDownloader
            >>> from pyhelpers.dirs import delete_dir
            >>> import tempfile
            >>> test_output_dir = tempfile.mkdtemp()
            >>> test_url = "https://github.com/mikeqfu/pyhelpers/blob/master/tests/data"
            >>> downloader = GitHubFileDownloader(test_url, output_dir=test_output_dir)
            >>> downloader.download()
            Downloaded to: "<temp_dir>/tests/data/csr_mat.npz"
            Downloaded to: "<temp_dir>/tests/data/dat.csv"
            Downloaded to: "<temp_dir>/tests/data/dat.feather"
            Downloaded to: "<temp_dir>/tests/data/dat.joblib"
            Downloaded to: "<temp_dir>/tests/data/dat.json"
            Downloaded to: "<temp_dir>/tests/data/dat.ods"
            Downloaded to: "<temp_dir>/tests/data/dat.pickle"
            Downloaded to: "<temp_dir>/tests/data/dat.pickle.bz2"
            Downloaded to: "<temp_dir>/tests/data/dat.pickle.gz"
            Downloaded to: "<temp_dir>/tests/data/dat.pickle.xz"
            Downloaded to: "<temp_dir>/tests/data/dat.txt"
            Downloaded to: "<temp_dir>/tests/data/dat.xlsx"
            Downloaded to: "<temp_dir>/tests/data/zipped.7z"
            Downloaded to: "<temp_dir>/tests/data/zipped.txt"
            Downloaded to: "<temp_dir>/tests/data/zipped.zip"
            >>> delete_dir(test_output_dir, confirmation_required=False, verbose=True)
            Deleting "<temp_dir>/" ... Done.
        """

        # Update `api_url` if it is not specified
        api_url_local = self.api_url if api_url is None else api_url

        self.check_url(api_url_local)

        # Update output directory if flatten is not specified
        if self.flatten:
            self.dir_out = self.output_dir
        elif len(self.download_path.split(".")) == 0:
            self.dir_out = os.path.join(self.output_dir, self.download_path)
        else:
            self.dir_out = os.path.join(
                self.output_dir, os.path.sep.join(self.download_path.split("/")[:-1]))

        # Make a directory with the name which is taken from the actual repo
        os.makedirs(self.dir_out, exist_ok=True)

        # Get response from GutHub response
        try:
            self._get_response(api_url_local=api_url_local)

        except urllib.error.URLError as e:
            print(f"URL error occurred: {e.reason}")
            print("Cannot get response from GitHub API. Please check the `url` or try again later.")

        except Exception as e:
            _print_failure_message(e, prefix="Error:", raise_error=True)

        return self.total_files
