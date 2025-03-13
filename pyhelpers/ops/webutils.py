"""
Utilities for Internet-related tasks and data manipulation from online sources.
"""

import copy
import datetime
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
import string
import sys
import urllib.error
import urllib.parse
import urllib.request

import requests
import requests.adapters
import urllib3.util

from .._cache import _add_slashes, _check_dependency, _check_relative_pathname, _check_url_scheme, \
    _confirmed, _format_error_message, _print_failure_message, _USER_AGENT_STRINGS
from ..ops import get_ansi_colour_code
from ..store import _check_saving_path


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


def _download_file_from_url(response, path_to_file, chunk_multiplier=1, desc=None, bar_format=None,
                            colour=None, validate=True, **kwargs):
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
    :param kwargs: [Optional] Additional parameters passed to `tqdm.tqdm()`_, allowing customisation
        of the progress bar (e.g. ``disable=True`` to hide the progress bar).

    :raises TypeError: If writing the downloaded data to a file fails due to encoding issues.
    :raises ValueError: If the downloaded file size does not match the expected content length.

    .. _`tqdm.tqdm()`: https://tqdm.github.io/docs/tqdm/

    **Examples**::

        >>> from pyhelpers.ops.webutils import _download_file_from_url
        >>> from pyhelpers.dirs import cd
        >>> import requests
        >>> url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> path_to_img = cd("tests", "images", "ops-download_file_from_url-demo.png")
        >>> with requests.get(url, stream=True) as response:
        ...     _download_file_from_url(response, path_to_img, colour='green')
        Downloading "ops-download_file_from_url-demo.png" 100%|██████████| 83.6k/83.6k | ...
            Updating "ops-download_file_from_url-demo.png" in ".\\tests\\images\\" ... Done.
    """

    tqdm_ = _check_dependency(name='tqdm')

    file_size = int(response.headers.get('content-length', 0))  # Total size in bytes

    block_size = 1024 ** 2
    chunk_size = int(block_size * chunk_multiplier) if file_size >= block_size else block_size

    colour_code, reset_colour = get_ansi_colour_code([colour, 'reset']) if colour else ('', '')

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

    _check_saving_path(path_to_file, verbose=True, print_prefix="\t", belated=belated)
    if validate and (written != file_size) and (file_size > 0):
        raise ValueError(f"Download failed: expected {file_size} bytes, got {written} bytes.")
    else:
        print("Done.")


def download_file_from_url(url, path_to_file, if_exists='replace', max_retries=5,
                           random_header=True, requests_session_args=None, fake_headers_args=None,
                           verbose=False, chunk_multiplier=1, desc=None, bar_format=None,
                           colour=None, validate=True, **kwargs):
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
    :param requests_session_args: [Optional] Additional parameters for initialising
        the requests session; defaults to ``None``.
    :type requests_session_args: dict | None
    :param fake_headers_args: [Optional] Additional parameters for generating fake HTTP headers;
        defaults to ``None``.
    :type fake_headers_args: dict | None
    :type verbose: bool | int
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
            print(f'File "{os.path.basename(path_to_file)}" already exists. Aborting download. '
                  f'Set `if_exists="replace"` to update the existing file.')

    else:
        # Initialise session
        requests_session_args = requests_session_args or {}
        session = init_requests_session(url=url, max_retries=max_retries, **requests_session_args)

        fake_headers_args = fake_headers_args or {}
        fake_headers = fake_requests_headers(randomized=random_header, **fake_headers_args)

        os.makedirs(os.path.dirname(path_to_file_), exist_ok=True)  # Ensure the directory exists

        # Streaming, so we can iterate over the response
        with session.get(url=url, stream=True, headers=fake_headers) as response:
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
                    **kwargs
                )

            else:
                with open(path_to_file_, mode='wb') as f:  # Open the file in binary write mode
                    shutil.copyfileobj(fsrc=response.raw, fdst=f)  # type: ignore

            # Validate download if necessary
            if validate and os.stat(path_to_file).st_size == 0:
                rel_path = _add_slashes(_check_relative_pathname(path_to_file))
                raise ValueError(
                    f"Error: The downloaded file at {rel_path} is empty. "
                    f"Check the URL or network connection.")
            # else:
            #     print(f"File successfully downloaded to {rel_path}.")


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


class CrossRefOrcid:
    """
    A class to interact with the ORCID Public API and CrossRef API
    to retrieve metadata about academic publications.

    :var ORCID_PUBLIC_API_ENDPOINT: The ORCID environment for the Public API
        on the production ORCID Registry.
    :type ORCID_PUBLIC_API_ENDPOINT: str
    :var CROSSREF_REST_API_ENDPOINT: The CrossRef REST API endpoint
        for querying metadata about published works.
    :type CROSSREF_REST_API_ENDPOINT: str
    :var ZENODO_REST_API_ENDPOINT: The Zenodo REST API endpoint
        for access to records stored in Zenodo.
    :type ZENODO_REST_API_ENDPOINT: str
    :var CITATION_STYLES: Templates of various styles of citations.
    :type CITATION_STYLES: dict
    :ivar my_name: My name to be bolded in the author list; defaults to ``"Fu, Qian"``.
    :type my_name: str
    :ivar requests_headers: HTTP headers used for making requests to external APIs;
        defaults to ``{"Accept": "application/json"}``.
    :type requests_headers: dict
    """

    ORCID_PUBLIC_API_ENDPOINT = 'https://pub.orcid.org/v3.0'

    CROSSREF_REST_API_ENDPOINT = 'https://api.crossref.org/works'

    ZENODO_REST_API_ENDPOINT = 'https://zenodo.org/api/records'

    CITATION_STYLES = {
        "APA": "{author} ({year}). {title}. {publication}, {pages}. https://doi.org/{doi}",
        "MLA": "{author} \"{title}.\" {publication}, {year}, pp. {pages}.",
        "Chicago": "{author} {year}. \"{title}.\" {publication}, {pages}. https://doi.org/{doi}",
        "Harvard": "{author} ({year}) '{title}', {publication}, pp. {pages}. "
                   "Available at: https://doi.org/{doi} [Accessed {accessed}].",
        "IEEE": "[{index}] {author}, \"{title},\" {publication}, pp. {pages}, {year}, doi:{doi}.",
        "Vancouver": "{author} {title}. {publication}. {year};{pages}. doi:{doi}.",
    }

    def __init__(self, my_name=""):
        """
        :ivar self.my_name: My name to be bolded in the author list; defaults to ``""``.
        :type self.my_name: str
        :ivar self.requests_headers: HTTP headers used for making requests to external APIs;
            defaults to ``{"Accept": "application/json"}``.
        :type self.requests_headers: dict

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> co.ORCID_PUBLIC_API_ENDPOINT
            'https://pub.orcid.org/v3.0'
            >>> co.CROSSREF_REST_API_ENDPOINT
            'https://api.crossref.org/works'
        """

        self.my_name = my_name
        self.requests_headers = {"Accept": "application/json"}

    def get_orcid_profile(self, orcid_id, section=None):
        # noinspection PyShadowingNames
        """
        Fetches the ORCID profile for a given ORCID ID.

        :param orcid_id: ORCID iD of the researcher.
        :type orcid_id: str
        :param section: Specific section of the profile (e.g. 'works'); defaults to ``None``.
        :type section: str | None
        :return: A dictionary containing profile data, or ``None`` if an error occurs.
        :rtype: dict | None

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> profile_data = co.get_orcid_profile(orcid_id)
            >>> list(profile_data.keys())
            ['orcid-identifier',
             'preferences',
             'history',
             'person',
             'activities-summary',
             'path']
        """

        url = f"{self.ORCID_PUBLIC_API_ENDPOINT}/{orcid_id}/{section.lower() if section else ''}"

        response = requests.get(url, headers=self.requests_headers)

        if response.status_code == 200:
            profile_data = response.json()  # Returns ORCID profile data as a dictionary

            return profile_data

        else:
            print(f"Error: {response.status_code} - {response.text}")

    def get_list_of_works(self, orcid_id):
        # noinspection PyShadowingNames
        """
        Fetches a list of works from an ORCID profile.

        :param orcid_id: ORCID ID of the researcher.
        :type orcid_id: str
        :return: A list of works with titles and years.
        :rtype: list[str]

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> list_of_works = co.get_list_of_works(orcid_id)
            >>> list_of_works[-1]
            'A Review on Transit Assignment Modelling Approaches to Congested Networks: A New...
        """

        profile_data = self.get_orcid_profile(orcid_id=orcid_id)

        try:
            works = profile_data["activities-summary"]["works"]["group"]
            list_of_works = []
            for work in works:
                title = work["work-summary"][0]["title"]["title"]["value"]
                year = work["work-summary"][0].\
                    get("publication-date", {}).\
                    get("year", {}).\
                    get("value", "N/A")
                list_of_works.append(f"{title} ({year})")

            return list_of_works

        except KeyError:
            print("No works available.")

    def get_metadata_from_doi(self, doi):
        # noinspection PyShadowingNames
        """
        Fetch full metadata from CrossRef using DOI.

        :param doi: The DOI of the publication.
        :type doi: str
        :return: A dictionary containing metadata.
        :rtype: dict

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> doi = 'https://doi.org/10.1016/j.jii.2024.100729'
            >>> co.get_metadata_from_doi(doi)
            {'journal': 'Journal of Industrial Information Integration',
             'conference': '',
             'volume': '42',
             'issue': '',
             'pages': '100729',
             'authors': 'Fu, Qian, Nicholson, Gemma L., Easton, John M.'}
        """

        response = requests.get(
            url=f"{self.CROSSREF_REST_API_ENDPOINT}/{doi}", headers=self.requests_headers)

        if response.status_code == 200:
            data = response.json().get("message", {})
            metadata = {
                "journal": data.get("container-title", [""])[0],  # Journal Name
                "conference": data.get("event", {}).get("name", ""),  # Conference Name
                "volume": data.get("volume", ""),
                "issue": data.get("issue", ""),
                "pages": data.get("page", ""),
                "authors": ", ".join(
                    [author.get("family", "") + ", " + author.get("given", "")
                     for author in
                     data.get("author", []) if "family" in author]) or "Unknown Author",
            }

            return metadata

        else:  # If no metadata found in CrossRef, try Zenodo
            zenodo_record_id = doi.split('.')[-1]
            response = requests.get(
                url=f"{self.ZENODO_REST_API_ENDPOINT}/{zenodo_record_id}",
                headers=self.requests_headers)

            if response.status_code == 200:
                data = response.json().get("metadata", {})
                metadata = {
                    "journal": data.get("resource_type", {}).get("title", ""),
                    "conference": data.get("meeting", {}).get("title", ""),
                    "volume": data.get("volume", ""),
                    "issue": data.get("issue", ""),
                    "pages": data.get("pages", ""),
                    "publisher": "Zenodo",
                    "authors": ", ".join([author.get("name", "") for author in
                                          data.get("creators", [])]) or "Unknown Author",
                }

                return metadata

        return {}

    def fetch_orcid_works(self, orcid_id, work_types=None, recent_years=2):
        # noinspection PyShadowingNames
        """
        Fetch recent works from ORCID and enrich with metadata from DOI.

        :param orcid_id: ORCID iD of the researcher.
        :type orcid_id: str
        :param work_types: Work type(s) to include
            (e.g. 'journal-article' or ['book', 'conference-paper']); defaults to ``None``.
        :type work_types: str | list | None
        :param recent_years: Number of recent years to include; defaults to ``2``.
        :type recent_years: int
        :return: A list of extracted reference dictionaries.
        :rtype: list[dict]

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> ref_data = co.fetch_orcid_works(orcid_id)  # Past two years
            >>> type(ref_data)
            list
            >>> # ref_data = co.fetch_orcid_works(orcid_id, recent_years=5)  # Past five years
            >>> # for ref_dat in ref_data:
            ... #     print(ref_dat)
        """

        data = self.get_orcid_profile(orcid_id, section='works')
        works = data.get("group", [])  # ORCID stores works in "group"

        ref_data = []
        current_year = datetime.datetime.now().year  # Get the current year
        recent_years_ = {
            str(current_year - x) for x in range(recent_years if recent_years else 100)}

        if work_types:
            work_types = [
                wt.lower() for wt in ([work_types] if isinstance(work_types, str) else work_types)]

        for work in works:
            summary = work.get("work-summary", [{}])[0]
            work_type = summary.get("type", "").replace("-", " ").title()  # Normalize work type

            # Skip if work type does not match the filter (when work_types is set)
            if work_types:
                if not any(wt in work_type.lower() for wt in work_types):
                    continue

            # Extract publication year
            year = summary.get("publication-date", {}).get("year", {}).get("value", "")
            if year not in recent_years_:  # Skip if not in the last two years
                continue

            # Extract details of journal papers:
            title = summary.get("title", {}).get("title", {}).get("value", "")
            doi = None

            # Extract DOI or other external IDs
            external_ids = summary.get("external-ids", {}).get("external-id", [])
            for ext_id in external_ids:
                if ext_id.get("external-id-type") == "doi":
                    doi = ext_id.get("external-id-value")
                    break

            metadata = self.get_metadata_from_doi(doi) if doi else {}

            # Build reference dictionary, excluding empty fields
            ref_dat = {
                "author": metadata.get("authors", "Unknown Author"),
                "year": year if year else None,
                "title": title if title else None,
                "work_type": work_type if work_type else "Other",
                "journal": metadata.get("journal", None),
                "conference": metadata.get("conference", None),
                "volume": metadata.get("volume", None),
                "issue": metadata.get("issue", None),
                "pages": metadata.get("pages", None),
                "publisher": metadata.get("publisher", None),
                "doi": f"https://doi.org/{doi}" if doi else None,
            }

            ref_dat = {k: v for k, v in ref_dat.items() if v}  # Remove None values
            ref_data.append(ref_dat)

        return ref_data

    def _format_author_names(self, author_str, corresponding_author=None):
        """
        Converts full author names to "Surname, F." format.

        :param author_str: A string of author names.
        :type author_str: str
        :return: Formatted author names.
        :rtype: str
        """

        authors = author_str.split(", ")  # Split by ", " to separate surname and given names
        formatted_authors = []

        for i in range(0, len(authors) - 1, 2):
            surname = authors[i]  # Last name
            given_names = authors[i + 1].split()  # First & middle names

            # Convert given names to initials, removing spaces between consecutive initials
            initials = "".join([name[0] + "." for name in given_names])

            # Format the author name
            author_name = f"{surname}, {initials}"

            # Bold your name
            if self.my_name in {author_name, f"{surname}, {' '.join(given_names)}"}:
                author_name = f"**{author_name}**"

            # Add an asterisk (*) as a superscript to the corresponding author
            if corresponding_author and author_name == corresponding_author:
                author_name = f"{author_name}<sup>*</sup>"

            formatted_authors.append(author_name)

        return ", ".join(formatted_authors)

    @staticmethod
    def _preprocess_doi(doi):
        """
        Ensures the DOI is formatted correctly with ``'https://doi.org/'``.

        :param doi: The DOI to preprocess.
        :type doi: str
        :return: Formatted DOI.
        :rtype: str
        """

        doi = doi.strip()  # Remove any surrounding whitespace
        return doi if doi.startswith("https://doi.org/") else f"https://doi.org/{doi}"

    @staticmethod
    def _clean_punctuation(text):
        """
        Cleans up extra punctuation, spaces, and unnecessary symbols left by missing placeholders.

        :param text: The text to clean.
        :type text: str
        :return: Cleaned text.
        :rtype: str
        """

        text = re.sub(r'\(\s*[,;]*\s*\)', '', text)  # Empty parentheses
        text = re.sub(r'\s*,\s*([.)])', r'\1', text)  # Commas before closing brackets or periods
        text = re.sub(r'\s*\(\s*\)', '', text)  # Empty parentheses again
        text = re.sub(r'\s*[,;]\s*$', '', text)  # Trailing commas/semicolons
        text = re.sub(r'\s+', ' ', text).strip()  # Spaces

        text = re.sub(r"Available at: \s*\[Accessed \s*]", "", text)  # Remove empty "Available at"
        text = re.sub(r"Available at: \s*[\[\]]?", "", text)  # Remove "Available at" if empty URL
        text = re.sub(r"\[Accessed \s*]", "", text)  # Remove empty "Accessed" brackets

        return text

    def _format_reference(self, ref_dat, style='APA', index=1):
        # noinspection PyShadowingNames
        """
        Formats a citation string (without missing placeholders).

        :param ref_dat: The reference data to format.
        :type ref_dat: dict
        :param style: The citation style to use; defaults to ``'APA'``.
        :type style: str
        :param index: The index for IEEE style; defaults to ``1``.
        :type index: int
        :return: Formatted citation string.
        :rtype: str

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> ref_data = co.fetch_orcid_works(orcid_id)  # Past two years
            >>> ref_dat = ref_data[0]
            >>> reference = co._format_reference(ref_dat, style="APA")
            >>> reference

        """

        if style in self.CITATION_STYLES:
            formatter = string.Formatter()
            formatted_parts = []

            # Determine the publication field based on work_type
            publication = ref_dat.get("journal", "")

            for literal_text, field_name, _, _ in formatter.parse(self.CITATION_STYLES[style]):
                if field_name is None:  # Keep literal text
                    formatted_parts.append(literal_text)

                elif field_name == "author" and field_name in ref_dat:  # Format authors
                    corresponding_author = ref_dat.get("corresponding_author", None)
                    author_names = self._format_author_names(
                        author_str=ref_dat[field_name], corresponding_author=corresponding_author)
                    formatted_parts.append(literal_text + author_names)

                elif field_name == "doi" and field_name in ref_dat:  # Ensure DOI format
                    literal_text_ = literal_text.replace('https://doi.org/', '')
                    doi = self._preprocess_doi(ref_dat[field_name])
                    if 'doi:' in literal_text:
                        doi = doi.replace('https://doi.org/', '')
                    formatted_parts.append(f"{literal_text_}{doi}")

                elif field_name == "index":  # Ensure IEEE gets an index
                    formatted_parts.append(literal_text + str(index))

                elif field_name == "publication":  # Use the determined publication field
                    formatted_parts.append(literal_text + html.unescape(publication))

                elif field_name in ref_dat and ref_dat[field_name]:  # Add field value
                    formatted_parts.append(literal_text + str(ref_dat[field_name]))

                else:
                    formatted_parts.append(literal_text)  # Remove missing placeholders

            reference = self._clean_punctuation("".join(formatted_parts))

            return reference

        else:
            print("Style not found!")

    def format_references(self, ref_data, style="APA"):
        # noinspection PyShadowingNames
        """
        Formats multiple references in a given citation style.

        :param ref_data: A collection of reference dictionaries or a single reference.
        :type ref_data: list | dict | typing.Iterable
        :param style: The citation style to use; defaults to ``'APA'``.
        :type style: str
        :return: A list of formatted citation strings.
        :rtype: list[str]

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> ref_data = co.fetch_orcid_works(orcid_id)  # Past two years
            >>> references = co.format_references(ref_data, style="APA")
            >>> references[-1]
            'Fu, Q., Easton, J.M., Burrow, M.P.N. (2024). Development of an Integrated Computing...
        """

        if isinstance(ref_data, dict):
            ref_data = [ref_data]  # Convert single dictionary to list

        references = [
            self._format_reference(ref_dat, style, index=i + 1)
            for i, ref_dat in enumerate(ref_data)]

        # # Add a footnote for the corresponding author
        # footnote = "\n\n<sup>*</sup> Corresponding author"
        # references.append(footnote)

        return references

    def fetch_references(self, orcid_id, work_types=None, recent_years=2, style='APA'):
        # noinspection PyShadowingNames
        """
        Fetches and formats references from an ORCID profile.

        :param orcid_id: ORCID iD of the researcher.
        :type orcid_id: str
        :param work_types: Work type(s) to include; defaults to ``None``.
        :type work_types: str | list | None
        :param recent_years: Number of recent years to include; defaults to ``2``.
        :type recent_years: int
        :param style: The citation style to use; defaults to ``'APA'``.
        :type style: str
        :return: A list of formatted citation strings.
        :rtype: list[str]

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> references = co.fetch_references(orcid_id)
            >>> references[-1]
            'Fu, Q., Easton, J.M., Burrow, M.P.N. (2024). Development of an Integrated Computing...
        """

        ref_data = self.fetch_orcid_works(
            orcid_id=orcid_id, work_types=work_types, recent_years=recent_years)

        if isinstance(ref_data, dict):
            ref_data = [ref_data]  # Convert single dictionary to list

        references = self.format_references(ref_data, style=style)

        return references

    @classmethod
    def _update_references(cls, references, limit=3, file_path="README.md", heading_level=3,
                           heading="Recent publications", heading_suffix=":"):
        # noinspection PyShadowingNames
        """
        Updates the "Recent publications" section in a Markdown file with a new list of citations.

        :param references: A list of reference strings to add to the
            ``"Recent publications"`` section.
        :type references: list[str]
        :param limit: The maximum number of the references to be included; defaults to ``3``.
        :type limit: int | None
        :param file_path: Path to the Markdown file; defaults to ``"README.md"``.
        :type file_path: str
        :param heading_level: The level of the heading under which the contents are to be updated;
            defaults to ``3``.
        :type heading_level: int
        :param heading: The Markdown heading for the references section;
            defaults to ``"Recent publications"``.
        :param heading_suffix: Suffix to the ``heading``; defaults to ``":"``.
        :type heading_suffix: str | None
        :type heading: str

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> references = co.fetch_references(orcid_id)
            >>> co._update_references(references, verbose=True)
            Updating "Recent publications" in README.md ... Done.
            >>> references = co.fetch_references(orcid_id, recent_years=5)
            >>> co._update_references(references, verbose=True)
            Updating "Recent publications" in README.md ... Done.
        """

        heading_ = f"{'#' * heading_level} {heading}{heading_suffix or ''}"

        with open(file_path, "r") as file:  # Read the existing content of the file
            content = file.read()

        if heading_ in content:  # Remove the existing "References" section (if it exists)
            content = content.split(heading_)[0].strip()

        # Write the updated content (excluding the old "References" section)
        with open(file_path, "w") as file:
            file.write(content)

            file.write(f"\n\n{heading_}\n\n")  # Add the new "Recent publications" section
            for reference in references[:(limit if limit else len(references))]:
                file.write(f"- {reference}\n")

    def update_references(self, orcid_id, work_types=None, recent_years=2, style='APA',
                          file_path="README.md", heading="Recent publications", heading_level=3,
                          heading_suffix=":", confirmation_required=True, verbose=False):
        # noinspection PyShadowingNames
        """
        Updates the "Recent publications" section in a Markdown file with a new list of citations.

        :param orcid_id: ORCID iD of the researcher.
        :type orcid_id: str
        :param work_types: Work type(s) to include; defaults to ``None``.
        :type work_types: str | list | None
        :param recent_years: Number of recent years to include; defaults to ``2``.
        :type recent_years: int
        :param style: The citation style to use; defaults to ``'APA'``.
        :type style: str
        :param file_path: Path to the Markdown file; defaults to ``"README.md"``.
        :type file_path: str
        :param heading_level: The level of the heading under which the contents are to be updated;
            defaults to ``3``.
        :type heading_level: int
        :param heading: The Markdown heading for the references section;
            defaults to ``"Recent publications"``.
        :type heading: str
        :param heading_suffix: Suffix to the ``heading``; defaults to ``":"``.
        :type heading_suffix: str | None
        :param confirmation_required: Whether to prompt for confirmation before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: If ``True``, prints status messages; defaults to ``False``.
        :type verbose: bool

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> co.update_references(orcid_id, verbose=True)
            To write/update references in README.md
            ? [No]|Yes: yes
            Updating "Recent publications" in README.md ... Done.
            >>> co.update_references(orcid_id, recent_years=5, verbose=True)
            To write/update references in README.md
            ? [No]|Yes: yes
            Updating "Recent publications" in README.md ... Done.
        """

        if _confirmed(f"To write/update references in {file_path}\n?", confirmation_required):
            if verbose:
                print(f'Updating "{heading}" in {file_path}', end=" ... ")

            try:
                references = self.fetch_references(
                    orcid_id=orcid_id, work_types=work_types, recent_years=recent_years,
                    style=style)

                if not os.path.exists(file_path):
                    with open(file_path, "w"):  # Create the file if it doesn't exist
                        pass

                self._update_references(
                    references=references, file_path=file_path, heading=heading,
                    heading_level=heading_level, heading_suffix=heading_suffix)

                if verbose:
                    print("Done.")

            except FileNotFoundError:
                print(f'Failed. Error: File "{file_path}" not found.')

            except IOError as e:
                print(f'Failed. Error: Unable to read/write file "{file_path}". {e}')
