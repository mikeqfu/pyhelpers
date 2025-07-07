"""
Tests the :mod:`~pyhelpers.ops.computation` submodule.
"""

import tempfile

import pytest

from pyhelpers.ops.computation import *


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
    num_dat = [1, 2, 'nan', 3, 4]
    iqr = interquartile_range(num_dat, ignore_nan=True)
    assert iqr == 1.5

    num_dat = list(range(100))
    iqr = interquartile_range(num_dat)
    assert iqr == 49.5

    result = interquartile_range(num_dat, outlier_fences=True)
    assert result == (49.5, -49.5, 148.5)


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


if __name__ == '__main__':
    pytest.main()
