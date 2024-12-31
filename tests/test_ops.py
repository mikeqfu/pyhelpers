"""Test the module :mod:`~pyhelpers.ops`."""

import importlib.resources
import tempfile
import time
import typing

import matplotlib.cm
import matplotlib.pyplot as plt
import pytest
from scipy.sparse import csr_matrix, save_npz

from pyhelpers._cache import example_dataframe
from pyhelpers.dbms import PostgreSQL
from pyhelpers.ops import *


# ==================================================================================================
# comp - Basic computation / converter.
# ==================================================================================================

@pytest.mark.parametrize('as_datetime', [True, False])
def test_gps_time_to_utc(as_datetime):
    utc_dt = gps_time_to_utc(gps_time=1271398985.7822514, as_datetime=as_datetime)

    if as_datetime:
        assert utc_dt == datetime.datetime(2020, 4, 20, 6, 22, 47, 782251)
    else:
        assert utc_dt == '2020-04-20T06:22:47.782251'


def test_parse_size():
    assert parse_size(size='123.45 MB') == 129446707
    assert parse_size(size='123.45 MB', binary=False) == 123450000
    assert parse_size(size='123.45 MiB', binary=True) == 129446707
    assert parse_size(size='123.45 MiB', binary=False) == 129446707
    assert parse_size(size=129446707, precision=2) == '123.45 MiB'
    assert parse_size(size=129446707, binary=False, precision=2) == '129.45 MB'


@pytest.mark.parametrize('chunk_size_limit', [0, None, 1, 0.1])
def test_get_number_of_chunks(chunk_size_limit):
    temp_file_ = tempfile.NamedTemporaryFile()
    temp_file_path = temp_file_.name + ".txt"
    with open(temp_file_path, 'w') as f:
        f.write(", ".join(map(str, range(10 ** 5))))

    number_of_chunks = get_number_of_chunks(temp_file_path, chunk_size_limit=chunk_size_limit)
    if chunk_size_limit:
        assert number_of_chunks >= 1
    else:
        assert number_of_chunks is None

    example_obj = np.zeros((1000, 1000))
    number_of_chunks = get_number_of_chunks(example_obj, chunk_size_limit=5)
    assert number_of_chunks == 2

    os.remove(temp_file_path)


def test_get_extreme_outlier_bounds():
    data = pd.DataFrame(range(100), columns=['col'])

    lo_bound, up_bound = get_extreme_outlier_bounds(data, k=1.5)
    assert (lo_bound, up_bound) == (0.0, 148.5)


def test_interquartile_range():
    data = list(range(100))

    iqr_result = interquartile_range(data)
    assert iqr_result == 49.5


def test_find_closest_date():
    example_dates = pd.date_range('2019-01-02', '2019-12-31')

    example_date = '2019-01-01'
    closest_example_date = find_closest_date(example_date, example_dates)
    assert closest_example_date == '2019-01-02 00:00:00.000000'

    example_date = pd.to_datetime('2019-01-01')
    closest_example_date = find_closest_date(example_date, example_dates, as_datetime=True)
    assert closest_example_date == pd.to_datetime('2019-01-02 00:00:00')

    example_dates = ['2019-01-02', '2019-12-31']

    example_date = '2019-01-01'
    closest_example_date = find_closest_date(example_date, example_dates, as_datetime=True)
    assert closest_example_date == pd.to_datetime('2019-01-02 00:00:00')


# ==================================================================================================
# gen - Miscellaneous operations.
# ==================================================================================================

def test_confirmed(monkeypatch):
    assert confirmed(confirmation_required=False)

    monkeypatch.setattr('builtins.input', lambda _: "Yes")
    assert confirmed()

    monkeypatch.setattr('builtins.input', lambda _: "")
    assert not confirmed()

    monkeypatch.setattr('builtins.input', lambda _: "no")
    assert not confirmed(resp=True)

    prompt = "Testing if the function works?"
    monkeypatch.setattr('builtins.input', lambda _: "Yes")
    assert confirmed(prompt=prompt, resp=False)


def test_get_obj_attr():
    res = get_obj_attr(PostgreSQL)
    assert isinstance(res, list)

    res = get_obj_attr(PostgreSQL, as_dataframe=True)
    assert isinstance(res, pd.DataFrame)
    assert res.columns.tolist() == ['attribute', 'value']
    res = get_obj_attr(PostgreSQL, col_names=['a', 'b'], as_dataframe=True)
    assert isinstance(res, pd.DataFrame)
    assert res.columns.tolist() == ['a', 'b']


def test_eval_dtype():
    from pyhelpers.ops import eval_dtype

    val_1 = '1'
    origin_val = eval_dtype(val_1)
    assert origin_val == 1

    val_2 = '1.1.1'
    origin_val = eval_dtype(val_2)
    assert origin_val == '1.1.1'


def test_hash_password():
    test_pwd = 'test%123'
    salt_size_ = 16
    sk = hash_password(password=test_pwd, salt_size=salt_size_)  # salt and key
    salt_data, key_data = sk[:salt_size_].hex(), sk[salt_size_:].hex()
    assert verify_password(password=test_pwd, salt=salt_data, key=key_data)

    test_pwd = b'test%123'
    sk = hash_password(password=test_pwd)
    salt_data, key_data = sk[:128].hex(), sk[128:].hex()
    assert verify_password(password=test_pwd, salt=salt_data, key=key_data)


def test_func_running_time(capfd):
    @func_running_time
    def test_func():
        print("Testing if the function works.")
        time.sleep(3)

    test_func()
    out, _ = capfd.readouterr()
    assert "INFO Finished running function: test_func, total: 3s" in out


# ==================================================================================================
# manip - Basic data manipulation.
# ==================================================================================================

def test_loop_in_pairs():
    res = loop_in_pairs(iterable=[1])
    assert list(res) == []

    res = loop_in_pairs(iterable=range(0, 10))
    assert list(res) == [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)]


def test_split_list_by_size():
    lst_ = list(range(0, 10))
    assert lst_ == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    lists = split_list_by_size(lst_, sub_len=3)
    assert list(lists) == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


def test_split_list():
    lst_ = list(range(0, 10))
    assert lst_ == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    lists = split_list(lst_, num_of_sub=3)
    assert list(lists) == [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]


def test_split_iterable():
    iterable_1 = list(range(0, 10))
    iterable_1_ = split_iterable(iterable_1, chunk_size=3)
    assert isinstance(iterable_1_, typing.Generator)
    assert [list(dat) for dat in iterable_1_] == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    iterable_2 = pd.Series(range(0, 20))
    iterable_2_ = split_iterable(iterable_2, chunk_size=5)

    assert [list(dat) for dat in iterable_2_] == [
        [0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11, 12, 13, 14], [15, 16, 17, 18, 19]]


def test_update_dict():
    source_dict = {'key_1': 1}
    update_data = {'key_2': 2}
    upd_dict = update_dict(source_dict, updates=update_data)
    assert upd_dict == {'key_1': 1, 'key_2': 2}
    assert source_dict == {'key_1': 1}
    update_dict(source_dict, updates=update_data, inplace=True)
    assert source_dict == {'key_1': 1, 'key_2': 2}

    source_dict = {'key': 'val_old'}
    update_data = {'key': 'val_new'}
    upd_dict = update_dict(source_dict, updates=update_data)
    assert upd_dict == {'key': 'val_new'}

    source_dict = {'key': {'k1': 'v1_old', 'k2': 'v2'}}
    update_data = {'key': {'k1': 'v1_new'}}
    upd_dict = update_dict(source_dict, updates=update_data)
    assert upd_dict == {'key': {'k1': 'v1_new', 'k2': 'v2'}}

    source_dict = {'key': {'k1': {}, 'k2': 'v2'}}
    update_data = {'key': {'k1': 'v1'}}
    upd_dict = update_dict(source_dict, updates=update_data)
    assert upd_dict == {'key': {'k1': 'v1', 'k2': 'v2'}}

    source_dict = {'key': {'k1': 'v1', 'k2': 'v2'}}
    update_data = {'key': {'k1': {}}}
    upd_dict = update_dict(source_dict, updates=update_data)
    assert upd_dict == {'key': {'k1': 'v1', 'k2': 'v2'}}


def test_update_dict_keys():
    source_dict = {'a': 1, 'b': 2, 'c': 3}

    upd_dict = update_dict_keys(source_dict, replacements=None)
    assert upd_dict == {'a': 1, 'b': 2, 'c': 3}

    repl_keys = {'a': 'd', 'c': 'e'}
    upd_dict = update_dict_keys(source_dict, replacements=repl_keys)
    assert upd_dict == {'d': 1, 'b': 2, 'e': 3}

    source_dict = {'a': 1, 'b': 2, 'c': {'d': 3, 'e': {'f': 4, 'g': 5}}}

    repl_keys = {'d': 3, 'f': 4}
    upd_dict = update_dict_keys(source_dict, replacements=repl_keys)
    assert upd_dict == {'a': 1, 'b': 2, 'c': {3: 3, 'e': {4: 4, 'g': 5}}}


def test_get_dict_values():
    key_ = 'key'
    target_dict_ = {'key': 'val'}
    val = get_dict_values(key_, target_dict_)
    assert list(val) == [['val']]

    key_ = 'k1'
    target_dict_ = {'key': {'k1': 'v1', 'k2': 'v2'}}
    val = get_dict_values(key_, target_dict_)
    assert list(val) == [['v1']]

    key_ = 'k1'
    target_dict_ = {'key': {'k1': ['v1', 'v1_1']}}
    val = get_dict_values(key_, target_dict_)
    assert list(val) == [['v1', 'v1_1']]

    key_ = 'k2'
    target_dict_ = {'key': {'k1': 'v1', 'k2': ['v2', 'v2_1']}}
    val = get_dict_values(key_, target_dict_)
    assert list(val) == [['v2', 'v2_1']]


def test_remove_dict_keys():
    target_dict_ = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'k4': 'v4', 'k5': 'v5'}
    remove_dict_keys(target_dict_, 'k1', 'k3', 'k4')
    assert target_dict_ == {'k2': 'v2', 'k5': 'v5'}


def test_compare_dicts():
    d1 = {'a': 1, 'b': 2, 'c': 3}
    d2 = {'b': 2, 'c': 4, 'd': [5, 6]}

    items_modified, k_shared, k_unchanged, k_new, k_removed = compare_dicts(d1, d2)
    assert items_modified == {'c': [3, 4]}
    assert set(k_shared) == {'b', 'c'}
    assert k_unchanged == ['b']
    assert k_new == ['d']
    assert k_removed == ['a']


def test_merge_dicts():
    dict_a = {'a': 1}
    dict_b = {'b': 2}
    dict_c = {'c': 3}

    merged_dict = merge_dicts(dict_a, dict_b, dict_c)
    assert merged_dict == {'a': 1, 'b': 2, 'c': 3}

    dict_c_ = {'c': 4}
    merged_dict = merge_dicts(merged_dict, dict_c_)
    assert merged_dict == {'a': 1, 'b': 2, 'c': [3, 4]}

    dict_1 = merged_dict
    dict_2 = {'b': 2, 'c': 4, 'd': [5, 6]}
    merged_dict = merge_dicts(dict_1, dict_2)
    assert merged_dict == {'a': 1, 'b': 2, 'c': [[3, 4], 4], 'd': [5, 6]}


def test_detect_nan_for_str_column():
    dat = example_dataframe()
    dat.loc['Leeds', 'Latitude'] = None

    nan_col_pos = detect_nan_for_str_column(data_frame=dat, column_names=None)
    assert list(nan_col_pos) == [1]


def test_create_rotation_matrix():
    rot_mat = create_rotation_matrix(theta=30)
    assert np.array_equal(
        np.round(rot_mat, 8), np.array([[-0.98803162, 0.15425145], [-0.15425145, -0.98803162]]))


def test_dict_to_dataframe():
    test_dict = {'a': 1, 'b': 2}

    dat = dict_to_dataframe(input_dict=test_dict)
    isinstance(dat, pd.DataFrame)


def test_parse_csr_matrix(capfd):
    data_ = [1, 2, 3, 4, 5, 6]
    indices_ = [0, 2, 2, 0, 1, 2]
    indptr_ = [0, 2, 3, 6]

    csr_m = csr_matrix((data_, indices_, indptr_), shape=(3, 3))

    assert list(csr_m.data) == data_
    assert list(csr_m.indices) == indices_
    assert list(csr_m.indptr) == indptr_

    path_to_csr_npz_ = importlib.resources.files(__package__).joinpath("data\\csr_mat.npz")

    with importlib.resources.as_file(path_to_csr_npz_) as path_to_csr_npz:
        save_npz(path_to_csr_npz, csr_m)
        parsed_csr_mat = parse_csr_matrix(path_to_csr_npz, verbose=True)
        out, _ = capfd.readouterr()
        assert "Loading " in out and '\\data\\csr_mat.npz" ... Done.\n' in out

    rslt = parsed_csr_mat != csr_m
    assert isinstance(rslt, csr_matrix)
    assert rslt.count_nonzero() == 0
    assert rslt.nnz == 0

    _ = parse_csr_matrix("", verbose=True)
    out, _ = capfd.readouterr()
    assert "No such file or directory" in out


def test_swap_cols():
    example_arr = example_dataframe(osgb36=True).to_numpy(dtype=int)

    # Swap the 0th and 1st columns
    new_arr = swap_cols(example_arr, c1=0, c2=1)
    assert np.array_equal(new_arr, np.array([[180371, 530039],
                                             [286868, 406705],
                                             [398113, 383830],
                                             [433553, 430147]]))

    new_list = swap_cols(example_arr, c1=0, c2=1, as_list=True)
    assert new_list == [[180371, 530039], [286868, 406705], [398113, 383830], [433553, 430147]]


def test_swap_rows():
    example_arr = example_dataframe(osgb36=True).to_numpy(dtype=int)

    # Swap the 0th and 1st rows
    new_arr = swap_rows(example_arr, r1=0, r2=1)
    assert np.array_equal(new_arr, np.array([[406705, 286868],
                                             [530039, 180371],
                                             [383830, 398113],
                                             [430147, 433553]]))

    new_list = swap_rows(example_arr, r1=0, r2=1, as_list=True)
    assert new_list == [[406705, 286868], [530039, 180371], [383830, 398113], [430147, 433553]]


def test_np_shift():
    arr = example_dataframe(osgb36=True).to_numpy()

    rslt1 = np_shift(arr, step=-1)
    assert np.array_equal(rslt1, np.array([[406705.8870136, 286868.1666422],
                                           [383830.0390357, 398113.0558309],
                                           [430147.4473539, 433553.3271173],
                                           [np.nan, np.nan]]),
                          equal_nan=True)

    rslt2 = np_shift(arr, step=1, fill_value=0)
    assert np.array_equal(rslt2, np.array([[0, 0],
                                           [530039, 180371],
                                           [406705, 286868],
                                           [383830, 398113]]))

    rslt3 = np_shift(arr, step=0)
    assert np.array_equal(rslt3, arr)


def test_cmap_discretisation():
    cm_accent = cmap_discretisation(matplotlib.colormaps['Accent'], n_colours=5)
    assert cm_accent.name == 'Accent_5'


def test_colour_bar_index():
    plt.figure(figsize=(2, 6))

    cbar = colour_bar_index(cmap=matplotlib.colormaps['Accent'], n_colours=5, labels=list('abcde'))
    cbar.ax.tick_params(labelsize=14)

    plt.close(fig='all')


# ==================================================================================================
# webutils - Utilities for Internet-related tasks and manipulating data from online sources.
# ==================================================================================================

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


def test_is_downloadable():
    logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
    assert is_downloadable(logo_url)

    google_url = 'https://www.google.co.uk/'
    assert not is_downloadable(google_url)


@pytest.mark.parametrize('retry_status', ['default', 123])
def test_init_requests_session(retry_status):
    logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
    s = init_requests_session(logo_url, retry_status=retry_status)
    assert isinstance(s, requests.sessions.Session)


def test__user_agent_strings():
    from pyhelpers.ops.webutils import _user_agent_strings

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


@pytest.mark.parametrize('verbose', [True, False])
def test_download_file_from_url(capfd, verbose):
    logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'

    path_to_img = "ops-download_file_from_url-demo.png"
    download_file_from_url(logo_url, path_to_img, verbose=verbose)
    assert os.path.isfile(path_to_img)

    download_file_from_url(logo_url, path_to_img, if_exists='pass', verbose=verbose)
    out, _ = capfd.readouterr()
    if verbose:
        assert "The download is cancelled." in out

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
        assert os.path.join("tests", "data", "dat.csv") in out
        assert downloader.total_files == 1

        test_url = "https://github.com/mikeqfu/pyhelpers/blob/master/tests/data"
        downloader = GitHubFileDownloader(test_url, output_dir=test_output_dir)
        downloader.download()
        out, _ = capfd.readouterr()
        assert os.path.join("tests", "data", "zipped", "zipped.txt") in out
        assert downloader.total_files == 13

        downloader = GitHubFileDownloader(test_url, flatten_files=True, output_dir=test_output_dir)
        downloader.download()
        out, _ = capfd.readouterr()
        assert "zipped.txt" in out
        assert downloader.total_files == 13

        shutil.rmtree(test_output_dir)


if __name__ == '__main__':
    pytest.main()
