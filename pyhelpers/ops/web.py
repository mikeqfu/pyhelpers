"""
Utilities for Internet-related tasks and data manipulation from online sources.
"""

import html.parser
import importlib.resources
import json
import pathlib
import random
import re
import secrets
import socket
import sys
import urllib.parse

import requests

from .._cache import _init_requests_session, _print_failure_message, _USER_AGENT_STRINGS


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

    session = _init_requests_session(
        url=url, max_retries=max_retries, backoff_factor=backoff_factor, retry_status=retry_status,
        **kwargs)

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

        >>> from pyhelpers.ops.web import _user_agent_strings
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
