"""
Tests the :mod:`~pyhelpers.ops.web` submodule.
"""

import pytest

from pyhelpers.ops.web import *


def test_is_network_connected():
    assert is_network_connected()  # assuming the machine is currently connected to the Internet


def test_is_url():
    assert is_url(url='https://github.com/mikeqfu/pyhelpers')
    assert not is_url(url='github.com/mikeqfu/pyhelpers')
    assert is_url(url='github.com/mikeqfu/pyhelpers', partially=True)
    assert not is_url(url='github.com')
    assert is_url(url='github.com', partially=True)
    assert not is_url(url='github', partially=True)


def test_is_url_connectable():
    url_0 = 'https://www.python.org/'
    assert is_url_connectable(url_0)

    url_1 = 'https://www.python.org1/'
    assert not is_url_connectable(url_1)


@pytest.mark.parametrize('retry_status', ['default', 123])
def test_init_requests_session(retry_status):
    logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
    s = init_requests_session(logo_url, retry_status=retry_status)
    assert isinstance(s, requests.sessions.Session)


def test__user_agent_strings():
    from pyhelpers.ops.web import _user_agent_strings

    uas = _user_agent_strings(browser_names=['Chrome'], dump_dat=False)
    assert isinstance(uas, dict)


@pytest.mark.parametrize('update', [True, False])
def test_load_user_agent_strings(capfd, update):
    uas = load_user_agent_strings(update=update, verbose=True)
    if update:
        out, _ = capfd.readouterr()
        assert "Updating the backup data of user-agent strings" in out and "Done." in out

    assert set(uas.keys()) == {'Chrome', 'Firefox', 'Safari', 'Edge', 'Internet Explorer', 'Opera'}
    assert isinstance(uas['Chrome'], list)

    uas_list = load_user_agent_strings(shuffled=True, flattened=True)
    assert isinstance(uas_list, list)


@pytest.mark.parametrize('fancy', [None, 'Chrome'])
def test_get_user_agent_string(fancy):
    # Get a random user-agent string
    uas = get_user_agent_string(fancy=fancy)
    assert isinstance(uas, str)


@pytest.mark.parametrize('randomized', [False, True])
def test_fake_requests_headers(randomized):
    fake_headers_ = fake_requests_headers(randomized=randomized)
    assert 'user-agent' in fake_headers_


if __name__ == '__main__':
    pytest.main()
