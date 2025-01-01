"""
Utilities for Internet-related tasks and data manipulation from online sources.
"""

import copy
import html.parser
import importlib.resources
import json
import os
import pathlib
import random
import re
import secrets
import shutil
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

import requests
import requests.adapters
import urllib3.util

from .._cache import _add_slashes, _check_dependency, _check_relative_pathname, _check_url_scheme, \
    _format_error_message, _print_failure_message, _USER_AGENT_STRINGS


def is_network_connected():
    """
    Checks whether the current machine is connected to the Internet.

    :return: ``True`` if the Internet connection is currently working, ``False`` otherwise.
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.ops import is_network_connected
        >>> is_network_connected()  # Assuming we're currently connected to the Internet
        True
    """

    host_name = socket.gethostname()
    ip_address = socket.gethostbyname(host_name)

    if ip_address == '127.0.0.1':
        connected = False
    else:
        connected = True

    return connected


def is_url(url, partially=False):
    """
    Checks if ``url`` is a valid URL.

    See also [`OPS-IU-1 <https://stackoverflow.com/questions/7160737/>`_].

    :param url: A string representing the URL to be checked.
    :type url: str
    :param partially: Whether to consider the input as partially valid; defaults to ``False``.
    :type partially: bool
    :return: ``True`` if the given URL is a valid URL; ``False`` otherwise.
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.ops import is_url
        >>> is_url(url='https://github.com/mikeqfu/pyhelpers')
        True
        >>> is_url(url='github.com/mikeqfu/pyhelpers')
        False
        >>> is_url(url='github.com/mikeqfu/pyhelpers', partially=True)
        True
        >>> is_url(url='github.com')
        False
        >>> is_url(url='github.com', partially=True)
        True
        >>> is_url(url='github', partially=True)
        False
    """

    # noinspection PyBroadException
    try:
        parsed_url = urllib.parse.urlparse(url)
        schema_netloc = [parsed_url.scheme, parsed_url.netloc]

        rslt = all(schema_netloc)

        if rslt is False and not any(schema_netloc):
            assert re.match(r'(/\w+)+|(\w+\.\w+)', parsed_url.path.lower())
            if partially:
                rslt = True
        else:
            assert re.match(r'(ht|f)tp(s)?', parsed_url.scheme.lower())

    except Exception:  # (AssertionError, AttributeError)
        rslt = False

    return rslt


def is_url_connectable(url):
    """
    Checks if the current machine can connect to the given URL.

    :param url: A valid URL.
    :type url: str
    :return: ``True`` if the machine can currently connect to the given URL, ``False`` otherwise.
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.ops import is_url_connectable
        >>> url_0 = 'https://www.python.org/'
        >>> is_url_connectable(url_0)
        True
        >>> url_1 = 'https://www.python.org1/'
        >>> is_url_connectable(url_1)
        False
    """

    try:
        netloc = urllib.parse.urlparse(url).netloc
        host = socket.gethostbyname(netloc)
        s = socket.create_connection((host, 80))
        s.close()

        return True

    except (socket.gaierror, OSError):
        return False


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


def init_requests_session(url, max_retries=5, backoff_factor=0.1, retry_status='default', **kwargs):
    # noinspection PyShadowingNames
    """
    Instantiates a `requests <https://docs.python-requests.org/en/latest/>`_ session
    with configurable retry behaviour.

    :param url: A valid URL to establish the session.
    :type url: str
    :param max_retries: Maximum number of retry attempts; defaults to ``5``.
    :type max_retries: int
    :param backoff_factor: Backoff factor for exponential backoff in retries; defaults to ``0.1``.
    :type backoff_factor: float
    :param retry_status: HTTP status codes that trigger retries,
        derived from `urllib3.util.Retry()`_;
        defaults to ``[429, 500, 502, 503, 504]`` when ``retry_status='default'``.
    :param kwargs: [Optional] Additional parameters for the class `urllib3.util.Retry()`_.
    :return: A `requests.Session()`_ instance configured with the specified retry settings.
    :rtype: requests.Session

    .. _`requests`:
        https://docs.python-requests.org/en/latest/
    .. _`urllib3.util.Retry()`:
        https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html#urllib3.util.Retry
    .. _`requests.Session()`:
        https://2.python-requests.org/en/master/api/#request-sessions

    **Examples**::

        >>> from pyhelpers.ops import init_requests_session
        >>> url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> s = init_requests_session(url)
        >>> type(s)
        requests.sessions.Session
    """

    if retry_status == 'default':
        codes_for_retries = [429, 500, 502, 503, 504]
    else:
        codes_for_retries = copy.copy(retry_status)

    kwargs.update({'backoff_factor': backoff_factor, 'status_forcelist': codes_for_retries})
    retries = urllib3.util.Retry(total=max_retries, **kwargs)

    session = requests.Session()

    # noinspection HttpUrlsUsage
    session.mount(
        prefix='https://' if url.startswith('https:') else 'http://',
        adapter=requests.adapters.HTTPAdapter(max_retries=retries))

    return session


class _FakeUserAgentParser(html.parser.HTMLParser):

    def __init__(self, browser_name):
        super().__init__()
        self.reset()
        self.recording = 0
        self.data = []
        self.browser_name = browser_name

    def error(self, message):
        pass

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return

        if self.recording:
            self.recording += 1
            return

        if tag == 'a':
            for name, link in attrs:
                if (name == 'href' and link.startswith(f'/{self.browser_name}') and
                        link.endswith('.php')):
                    break
                else:
                    return
            self.recording = 1

    def handle_endtag(self, tag):
        if tag == 'a' and self.recording:
            self.recording -= 1

    def handle_data(self, data):
        if self.recording:
            self.data.append(data.strip())


def _user_agent_strings(browser_names=None, dump_dat=False):
    """
    Retrieves user-agent strings for popular web browsers.

    :param browser_names: Browser names to retrieve user-agent strings for;
        defaults to a predefined list of popular browsers if not provided.
    :type browser_names: list | None
    :param dump_dat: Whether to dump additional data alongside the user-agent strings;
        defaults to ``False``.
    :type dump_dat: bool
    :return: Dictionary containing user-agent strings for the specified browsers.
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.ops.webutils import _user_agent_strings
        >>> # uas = _user_agent_strings(dump_dat=True)
        >>> uas = _user_agent_strings()
        >>> list(uas.keys())
        ['Chrome', 'Firefox', 'Safari', 'Edge', 'Internet Explorer', 'Opera']
    """

    if browser_names is None:
        browser_names_ = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Internet Explorer', 'Opera']
    else:
        browser_names_ = browser_names.copy()

    resource_url = 'https://useragentstring.com/pages/useragentstring.php'

    user_agent_strings = {}
    for browser_name in browser_names_:
        # url = resource_url.replace('useragentstring.php', browser_name.replace(" ", "+") + '/')
        url = resource_url + f'?name={browser_name.replace(" ", "+")}'
        response = requests.get(url=url)
        fua_parser = _FakeUserAgentParser(browser_name=browser_name)
        fua_parser.feed(response.text)
        user_agent_strings[browser_name] = sorted(list(set(fua_parser.data)))

    if dump_dat and all(user_agent_strings.values()):
        # path_to_uas = importlib.resources.files(__package__).joinpath(
        #     "../data/user-agent-strings.json")
        path_to_uas = pathlib.Path(__file__).parent.parent / "data" / "user-agent-strings.json"
        with path_to_uas.open(mode='w') as f:
            f.write(json.dumps(user_agent_strings, indent=4))

    return user_agent_strings


def load_user_agent_strings(shuffled=False, flattened=False, update=False, verbose=False,
                            raise_error=False):
    """
    Loads user-agent strings for popular web browsers.

    This function retrieves a partially comprehensive list of user-agent strings for
    `Chrome`_, `Firefox`_, `Safari`_, `Edge`_, `Internet Explorer`_, and `Opera`_.

    :param shuffled: Whether to randomly shuffle the user-agent strings; defaults to ``False``.
    :type shuffled: bool
    :param flattened: Whether to return a flattened list of all user-agent strings;
        defaults to ``False``.
    :type flattened: bool
    :param update: Whether to update the backup data of user-agent strings; defaults to ``False``.
    :type update: bool
    :param verbose: Whether to print relevant information in the console; defaults to ``False``.
    :type verbose: bool | int
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :return: Dictionary or list of user-agent strings, depending on the `flattened` parameter.
    :rtype: dict | list

    .. _`Chrome`:
        https://useragentstring.com/pages/useragentstring.php?name=Chrome
    .. _`Firefox`:
        https://useragentstring.com/pages/useragentstring.php?name=Firefox
    .. _`Safari`:
        https://useragentstring.com/pages/useragentstring.php?name=Safari
    .. _`Edge`:
        https://useragentstring.com/pages/useragentstring.php?name=Edge
    .. _`Internet Explorer`:
        https://useragentstring.com/pages/useragentstring.php?name=Internet+Explorer
    .. _`Opera`:
        https://useragentstring.com/pages/useragentstring.php?name=Opera

    **Examples**::

        >>> from pyhelpers.ops import load_user_agent_strings
        >>> uas = load_user_agent_strings()
        >>> list(uas.keys())
        ['Chrome', 'Firefox', 'Safari', 'Edge', 'Internet Explorer', 'Opera']
        >>> type(uas['Chrome'])
        list
        >>> uas['Chrome'][0]
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)...
        >>> uas_list = load_user_agent_strings(shuffled=True, flattened=True)
        >>> type(uas_list)
        list
        >>> uas_list[0]  # a random one
        'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.7...

    .. note::

        The order of the elements in ``uas_list`` may be different every time we run the example
        as ``shuffled=True``.
    """

    if not update:
        user_agent_strings = _USER_AGENT_STRINGS.copy()

    else:
        if verbose:
            print("Updating the backup data of user-agent strings", end=" ... ")

        try:
            user_agent_strings = _user_agent_strings(dump_dat=True)

            importlib.reload(sys.modules.get('pyhelpers._cache'))

            if verbose:
                print("Done.")

        except Exception as e:
            _print_failure_message(e, prefix="Failed.", verbose=verbose, raise_error=raise_error)
            user_agent_strings = load_user_agent_strings(update=False, verbose=False)

    if shuffled:
        for browser_name, ua_str in user_agent_strings.items():
            random.shuffle(ua_str)
            user_agent_strings.update({browser_name: ua_str})

    if flattened:
        user_agent_strings = [x for v in user_agent_strings.values() for x in v]

    return user_agent_strings


def get_user_agent_string(fancy=None, **kwargs):
    """
    Gets a random user-agent string for a specified browser.

    :param fancy: Name of the preferred browser; options include ``'Chrome'``, ``'Firefox'``,
        ``'Safari'``, ``'Edge'``, ``'Internet Explorer'`` and ``'Opera'``.
        If ``fancy=None`` (default), the function returns a user-agent string
        from a randomly-selected browser among all available options.
    :type fancy: None | str
    :param kwargs: [Optional] Additional parameters for the function
        :func:`~pyhelpers.ops.get_user_agent_strings`.
    :return: A user-agent string for the specified browser.
    :rtype: str

    **Examples**::

        >>> from pyhelpers.ops import get_user_agent_string
        >>> # Get a random user-agent string
        >>> uas_0 = get_user_agent_string()
        >>> uas_0
        'Opera/7.01 (Windows 98; U)  [en]'
        >>> # Get a random Chrome user-agent string
        >>> uas_1 = get_user_agent_string(fancy='Chrome')
        >>> uas_1
        'Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrom...

    .. note::

        In the above examples, the returned user-agent string is random and may be different
        every time of running the function.
    """

    if fancy is not None:
        browser_names = {'Chrome', 'Firefox', 'Safari', 'Edge', 'Internet Explorer', 'Opera'}
        assert fancy in browser_names, f"`fancy` must be one of {browser_names}."

        kwargs.update({'flattened': False})
        user_agent_strings_ = load_user_agent_strings(**kwargs)

        user_agent_strings = user_agent_strings_[fancy]

    else:
        kwargs.update({'flattened': True})
        user_agent_strings = load_user_agent_strings(**kwargs)

    user_agent_string = secrets.choice(user_agent_strings)

    return user_agent_string


def fake_requests_headers(randomized=True, **kwargs):
    """
    Generates fake HTTP headers.

    This function creates HTTP headers suitable for use with `requests.get
    <https://requests.readthedocs.io/en/master/user/advanced/#request-and-response-objects>`_.
    By default, it includes a randomly selected user-agent string from various popular browsers.

    :param randomized: Whether to use a randomly selected user-agent string from available
        browser data; defaults to ``True``;
        if ``randomized=False``, a random Chrome user-agent string is used.
    :type randomized: bool
    :param kwargs: [Optional] Additional parameters for the function
        :func:`~pyhelpers.ops.get_user_agent_string`.
    :return: Fake HTTP headers.
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.ops import fake_requests_headers
        >>> fake_headers_1 = fake_requests_headers()
        >>> fake_headers_1
        {'user-agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it-IT) AppleWebKit/525.1...
        >>> fake_headers_2 = fake_requests_headers(randomized=False)
        >>> fake_headers_2  # using a random Chrome user-agent string
        {'user-agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.1...

    .. note::

        - ``fake_headers_1`` may also be different every time we run the example.
          This is because the returned result is randomly chosen from a limited set of candidate
          user-agent strings, even though ``randomized`` is (by default) set to be ``False``.
        - By setting ``randomized=True``, the function returns a random result from among
          all available user-agent strings of several popular browsers.
    """

    if not randomized:
        kwargs.update({'fancy': 'Chrome'})

    user_agent_string = get_user_agent_string(**kwargs)

    fake_headers = {'user-agent': user_agent_string}

    return fake_headers


def _download_file_from_url(response, path_to_file):
    """
    Downloads a file from a valid URL (and saves it).

    :param response: Server's response to an HTTP request containing the file to download.
    :type response: requests.Response
    :param path_to_file: Path where the downloaded file will be saved;
        it can be either a path with filename or just a filename,
        in which case it will be saved in the current working directory.
    :type path_to_file: str | os.PathLike[str]
    """

    tqdm_ = _check_dependency(name='tqdm')

    file_size = int(response.headers.get('content-length'))  # Total size in bytes

    unit_divisor = 1024
    block_size = unit_divisor ** 2
    chunk_size = block_size if file_size >= block_size else unit_divisor

    total_iter = file_size // chunk_size

    pg_args = {
        'desc': f'"{_check_relative_pathname(path_to_file)}"',
        'total': total_iter,
        'unit': 'B',
        'unit_scale': True,
        'unit_divisor': unit_divisor,
    }
    with tqdm_.tqdm(**pg_args) as progress:

        contents = response.iter_content(chunk_size=chunk_size, decode_unicode=True)

        with open(file=path_to_file, mode='wb') as f:
            written = 0
            for data in contents:
                if data:
                    try:
                        f.write(data)
                    except TypeError:
                        f.write(data.encode())
                    progress.update(len(data))
                    written += len(data)

    if file_size != 0 and written != file_size:
        print("ERROR! Something went wrong!")


def download_file_from_url(url, path_to_file, if_exists='replace', max_retries=5,
                           random_header=True, verbose=False, requests_session_args=None,
                           fake_headers_args=None, **kwargs):
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
    :param random_header: Whether to use a random user-agent header; defaults to ``True``.
    :type random_header: bool
    :param verbose: Whether to print progress and relevant information to the console;
        defaults to ``False``.
    :type verbose: bool | int
    :param requests_session_args: [Optional] Additional parameters for initialising
        the requests session; defaults to ``None``.
    :type requests_session_args: dict | None
    :param fake_headers_args: [Optional] Additional parameters for generating fake HTTP headers;
        defaults to ``None``.
    :type fake_headers_args: dict | None
    :param kwargs: [Optional] Additional parameters for the method `requests.Session.get()`_.

    .. _`requests.Session.get()`:
        https://docs.python-requests.org/en/master/_modules/requests/sessions/#Session.get

    **Examples**::

        >>> from pyhelpers.ops import download_file_from_url
        >>> from pyhelpers.dirs import cd
        >>> from PIL import Image
        >>> import os
        >>> url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> path_to_img = cd("tests\\images", "ops-download_file_from_url-demo.png")
        >>> # Check if "python-logo.png" exists at the specified path
        >>> os.path.exists(path_to_img)
        False
        >>> # Download the .png file
        >>> download_file_from_url(url, path_to_img)
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

    path_to_dir = os.path.dirname(path_to_file)
    if path_to_dir == "":
        path_to_file_ = os.path.join(os.getcwd(), path_to_file)
        path_to_dir = os.path.dirname(path_to_file_)
    else:
        path_to_file_ = copy.copy(path_to_file)

    if os.path.exists(path_to_file_) and if_exists != 'replace':
        if verbose:
            print(f"The destination already has a file named "
                  f"\"{os.path.basename(path_to_file_)}\". "
                  f"The download is cancelled.")

    else:
        if requests_session_args is None:
            requests_session_args = {}
        session = init_requests_session(url=url, max_retries=max_retries, **requests_session_args)

        if fake_headers_args is None:
            fake_headers_args = {}
        fake_headers = fake_requests_headers(randomized=random_header, **fake_headers_args)

        # Streaming, so we can iterate over the response
        with session.get(url=url, stream=True, headers=fake_headers, **kwargs) as response:
            os.makedirs(path_to_dir, exist_ok=True)  # Ensure the directory exists

            if verbose:
                _download_file_from_url(response=response, path_to_file=path_to_file_)

            else:
                with open(file=path_to_file_, mode='wb') as f:  # Open the file in binary write mode
                    shutil.copyfileobj(fsrc=response.raw, fdst=f)  # type: ignore

                if os.stat(path=path_to_file_).st_size == 0:
                    print("ERROR! Something went wrong! Check if the URL is downloadable.")


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
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.txt"
            Downloaded to: ".\\tests\\temp\\tests\\data\\dat.xlsx"
            Downloaded to: ".\\tests\\temp\\tests\\data\\zipped.7z"
            Downloaded to: ".\\tests\\temp\\tests\\data\\zipped.txt"
            Downloaded to: ".\\tests\\temp\\tests\\data\\zipped.zip"
            Downloaded to: ".\\tests\\temp\\tests\\data\\zipped\\zipped.txt"
            13
            >>> downloader = GitHubFileDownloader(
            ...     repo_url, flatten_files=True, output_dir=output_dir)
            >>> downloader.download()
            Downloaded to: .\\tests\\temp\\csr_mat.npz
            Downloaded to: .\\tests\\temp\\dat.csv
            Downloaded to: .\\tests\\temp\\dat.feather
            Downloaded to: .\\tests\\temp\\dat.joblib
            Downloaded to: .\\tests\\temp\\dat.json
            Downloaded to: .\\tests\\temp\\dat.ods
            Downloaded to: .\\tests\\temp\\dat.pickle
            Downloaded to: .\\tests\\temp\\dat.txt
            Downloaded to: .\\tests\\temp\\dat.xlsx
            Downloaded to: .\\tests\\temp\\zipped.7z
            Downloaded to: .\\tests\\temp\\zipped.txt
            Downloaded to: .\\tests\\temp\\zipped.zip
            Downloaded to: .\\tests\\temp\\zipped.txt
            13
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
        opener.addheaders = list(fake_requests_headers().items())
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

    def download(self, api_url=None):
        """
        Downloads files from the specified GitHub ``api_url``.

        :param api_url: GitHub API URL for downloading files; defaults to ``None``.
        :type api_url: str | None
        :return: Total number of files downloaded under the given directory.
        :rtype: int

        .. seealso::

            - Examples for the method
              :meth:`GitHubFileDownloader.download()<pyhelpers.ops.GitHubFileDownloader.download>`.
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
                    print(f"Error: Got interrupted for {_format_error_message(e)}")

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

        except urllib.error.URLError as e:
            print(f"URL error occurred: {e.reason}")
            print("Cannot get response from GitHub API. Please check the `url` or try again later.")

        except Exception as e:
            _print_failure_message(e, prefix="Error:", raise_error=True)

        return self.total_files
