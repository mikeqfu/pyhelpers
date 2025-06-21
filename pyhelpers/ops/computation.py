"""
Basic computation/conversion.
"""

import copy
import datetime
import math
import os
import re
import sys

import numpy as np
import pandas as pd
import requests

from .._cache import _print_failure_message


def get_utc_tai_offset(verbose=False, raise_error=False, url=None):
    """
    Retrieves the difference between UTC (Coordinated Universal Time) and
    TAI (International Atomic Time).

    This difference increases as leap seconds are added to UTC.

    :param verbose: Whether to print additional information to the console; defaults to ``True``.
    :type verbose: bool | int
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param url: URL to the IERS (International Earth Rotation and Reference Systems Service)'s
        Bulletin C, which announces leap seconds; defaults to ``None``.
    :type url: str | None
    :return: The difference between UTC and TAI, i.e. UTC - TAI.
    :rtype: int | float | None

    **Examples**::

        >>> from pyhelpers.ops import get_utc_tai_offset
        >>> get_utc_tai_offset()
        -37
    """

    if url is None:
        url = "https://datacenter.iers.org/data/latestVersion/bulletinC.txt"

    try:
        response = requests.get(url)
        if raise_error:
            response.raise_for_status()  # Raise an error if the request was unsuccessful

        content = response.text

        desc, utc_tai_offset = None, None
        for line in content.splitlines():  # Search for the specific line containing "UTC-TAI"
            if 'UTC-TAI' in line:
                desc = line.strip()
                utc_tai_offset_ = re.search(r"UTC-TAI\s*=\s*(-?\d+)\s*s", desc)
                utc_tai_offset = int(utc_tai_offset_.group(1).strip().replace(' ', ''))
                break

        if utc_tai_offset and verbose:
            print("UTC-TAI difference not found in the bulletin.")

        return utc_tai_offset

    except requests.exceptions.RequestException as e:
        _print_failure_message(
            e=e, prefix="An error occurred while retrieving the data:", verbose=verbose,
            raise_error=raise_error)


def gps_time_to_utc(gps_time, as_datetime=True, utc_tai_offset=None):
    # noinspection PyShadowingNames
    """
    Converts GPS time to UTC time.

    :param gps_time: Standard GPS time in seconds since GPS epoch (6 January 1980).
    :type gps_time: float
    :param as_datetime: If ``True``, the function returns the UTC time as datetime type;
        otherwise string type; defaults to ``True``.
    :type as_datetime: bool
    :param utc_tai_offset: The difference between UTC (Coordinated Universal Time) and
        the TAI (International Atomic Time), i.e. UTC - TAI; defaults to ``None``.
    :type utc_tai_offset: float | int | None
    :return: UTC datetime corresponding to the GPS time.
    :rtype: datetime.datetime | str

    **Examples**::

        >>> from pyhelpers.ops import gps_time_to_utc
        >>> gps_time = 1271398985.7822514
        >>> utc_time = gps_time_to_utc(gps_time)
        >>> utc_time
        datetime.datetime(2020, 4, 20, 6, 22, 47, 782251)
        >>> utc_time = gps_time_to_utc(gps_time, as_datetime=False)
        >>> utc_time
        >>> '2020-04-20T06:22:47.782251'
    """

    gps_epoch = datetime.datetime(1980, 1, 6, 0, 0, 0)

    # GPS - TAI offset (19 seconds from the GPS epoch)
    gps_tai_offset = 19

    if utc_tai_offset is None:
        # noinspection PyBroadException
        try:
            utc_tai_offset = get_utc_tai_offset(raise_error=True)
        except Exception:
            utc_tai_offset = -37  # As of December 2024

    # Total offset: GPS to UTC
    total_offset = gps_tai_offset + utc_tai_offset

    utc_time = gps_epoch + datetime.timedelta(seconds=(gps_time + total_offset))

    if not as_datetime:
        utc_time = utc_time.isoformat()  # Alternatively, utc_time.strftime("%Y-%m-%d %H:%M:%S.%f")

    return utc_time


def find_closest_date(date, lookup_dates, as_datetime=False, fmt='%Y-%m-%d %H:%M:%S.%f'):
    # noinspection PyShadowingNames
    """
    Finds the closest date to a given date from a list of dates.

    :param date: Date to find the closest match for.
    :type date: str | datetime.datetime
    :param lookup_dates: Iterable of dates to search within.
    :type lookup_dates: typing.Iterable
    :param as_datetime: Whether to return the closest date as a datetime.datetime object;
        defaults to ``False`` which returns a string representation.
    :type as_datetime: bool
    :param fmt: Format string for datetime parsing and formatting;
        defaults to ``'%Y-%m-%d %H:%M:%S.%f'``.
    :type fmt: str
    :return: Closest date to the given `date`.
    :rtype: str | datetime.datetime

    **Examples**::

        >>> from pyhelpers.ops import find_closest_date
        >>> import pandas
        >>> lookup_dates = pandas.date_range('2019-01-02', '2019-12-31')
        >>> lookup_dates
        DatetimeIndex(['2019-01-02', '2019-01-03', '2019-01-04', '2019-01-05',
                       '2019-01-06', '2019-01-07', '2019-01-08', '2019-01-09',
                       '2019-01-10', '2019-01-11',
                       ...
                       '2019-12-22', '2019-12-23', '2019-12-24', '2019-12-25',
                       '2019-12-26', '2019-12-27', '2019-12-28', '2019-12-29',
                       '2019-12-30', '2019-12-31'],
                      dtype='datetime64[ns]', length=364, freq='D')
        >>> date = '2019-01-01'
        >>> closest_example_date = find_closest_date(date, lookup_dates)
        >>> closest_example_date
        '2019-01-02 00:00:00.000000'
        >>> date = pandas.to_datetime('2019-01-01')
        >>> closest_date = find_closest_date(date, lookup_dates, as_datetime=True)
        >>> closest_date
        Timestamp('2019-01-02 00:00:00', freq='D')
    """

    closest_date = min(lookup_dates, key=lambda x: abs(pd.to_datetime(x) - pd.to_datetime(date)))

    if as_datetime:
        if isinstance(closest_date, str):
            closest_date = pd.to_datetime(closest_date)

    else:
        if isinstance(closest_date, datetime.datetime):
            closest_date = closest_date.strftime(fmt)

    return closest_date


def parse_size(size, binary=True, precision=1):
    """
    Parses size into human-readable format or vice versa.

    :param size: Size to be parsed, either in human-readable format (e.g. ``'10 MB'``) or
        as an integer.
    :type size: str | int | float
    :param binary: Whether to use binary (factorised by 1024) or decimal (factorised by 10 ** 3)
        representation; defaults to ``True`` for binary representation.
    :type binary: bool
    :param precision: Number of decimal places when converting ``size`` to human-readable format;
        defaults to ``1``.
    :type precision: int
    :return: Parsed size, either as an integer (for machine-readable)
        or a formatted string (for human-readable).
    :rtype: int | str

    **Examples**::

        >>> from pyhelpers.ops import parse_size
        >>> parse_size(size='123.45 MB')
        129446707
        >>> parse_size(size='123.45 MB', binary=False)
        123450000
        >>> parse_size(size='123.45 MiB', binary=True)
        129446707
        >>> # If a metric unit (e.g. 'MiB') is specified in the input,
        >>> # the function returns a result accordingly, regardless of `binary`
        >>> parse_size(size='123.45 MiB', binary=False)
        129446707
        >>> parse_size(size=129446707, precision=2)
        '123.45 MiB'
        >>> parse_size(size=129446707, binary=False, precision=2)
        '129.45 MB'
    """

    min_unit, units_prefixes = 'B', ['K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    if binary:  # Binary system
        factor, units = 2 ** 10, [x + 'i' + min_unit for x in units_prefixes]
    else:  # Decimal (or metric) system
        factor, units = 10 ** 3, [x + min_unit for x in units_prefixes]

    if isinstance(size, str):
        val, sym = [x.strip() for x in size.split()]
        if re.match(r'.*i[Bb]', sym):
            factor, units = 2 ** 10, [x + 'i' + min_unit for x in units_prefixes]
        unit = [s for s in units if s[0] == sym[0].upper()][0]

        unit_dict = dict(zip(units, [factor ** i for i in range(1, len(units) + 1)]))
        parsed_size = int(float(val) * unit_dict[unit])  # in byte

    else:
        is_negative = size < 0
        temp_size, parsed_size = map(copy.copy, (abs(size), size))

        for unit in [min_unit] + units:
            if abs(temp_size) < factor:
                parsed_size = f"{'-' if is_negative else ''}{temp_size:.{precision}f} {unit}"
                break
            if unit != units[-1]:
                temp_size /= factor

    return parsed_size


def get_number_of_chunks(file_or_obj, chunk_size_limit=50, binary=True):
    """
    Gets the total number of chunks of a data file, given a minimum chunk size limit.

    :param file_or_obj: Path to a file or an object representing the data.
    :type file_or_obj: typing.Any
    :param chunk_size_limit: Minimum limit of chunk size in megabytes (MB) or mebibytes (MiB)
        above which the function counts the number of chunks; defaults to ``50``.
    :type chunk_size_limit: int | float | None
    :param binary: Whether to use binary (factorised by 1024) or decimal (factorised by 10 ** 3)
        representation for size calculations; defaults to ``True`` for binary representation.
    :type binary: bool
    :return: Number of chunks, or ``None`` if ``file_or_obj`` is invalid
        or chunk calculation is not applicable.
    :rtype: int | None

    **Examples**::

        >>> from pyhelpers.ops import get_number_of_chunks
        >>> import numpy
        >>> example_obj = numpy.zeros((1000, 1000))
        >>> get_number_of_chunks(example_obj, chunk_size_limit=5)
        2
        >>> file_path = "C:\\Program Files\\Python310\\python310.pdb"
        >>> get_number_of_chunks(file_path, chunk_size_limit=2)
        8
    """

    factor = 2 ** 10 if binary is True else 10 ** 3

    if isinstance(file_or_obj, str) and os.path.exists(file_or_obj):
        size = os.path.getsize(file_or_obj)
    else:
        size = sys.getsizeof(file_or_obj)

    file_size_in_mb = round(size / (factor ** 2), 1)

    if chunk_size_limit:
        if file_size_in_mb > chunk_size_limit:
            number_of_chunks = math.ceil(file_size_in_mb / chunk_size_limit)
        else:
            number_of_chunks = 1
    else:
        number_of_chunks = None

    return number_of_chunks


def interquartile_range(num_dat, axis=None, rng=(25, 75), scale=1.0, outlier_fences=False, k=1.5,
                        ignore_nan=True, **kwargs):
    # noinspection PyShadowingNames
    """
    Calculates the interquartile range (IQR) of numerical data.

    This function may serve as an alternative to
    `scipy.stats.iqr <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.iqr.html>`_
    when ``scipy`` is not available.

    :param num_dat: Numerical data.
    :type num_dat: numpy.ndarray | list | tuple
    :param axis: Axis along which to calculate IQR; defaults to ``None``.
    :type axis: int | None
    :param rng: Percentile range for calculating IQR; defaults to ``(25, 75)``.
    :type rng: tuple
    :param scale: Scaling factor for the IQR; defaults to ``1.0``.
    :type scale: int | float
    :param outlier_fences: Whether to calculate and return outlier fences; defaults to ``False``.
    :type outlier_fences: bool
    :param k: Multiplier for IQR for calculating outlier fences; defaults to ``1.5``
    :type k: int | float
    :param ignore_nan: Whether to ignore NaN values; defaults to ``True``.
    :type ignore_nan: bool
    :param kwargs: [Optional] Additional parameters passed to `numpy.percentile`_.
    :return: Scaled interquartile range.
    :rtype: float
    :raises ValueError: If input has insufficient non-NaN values.

    .. _`numpy.percentile`: https://numpy.org/doc/stable/reference/generated/numpy.percentile.html

    **Examples**::

        >>> from pyhelpers.ops import interquartile_range
        >>> num_dat = [1, 2, 'nan', 3, 4]
        >>> iqr = interquartile_range(num_dat, ignore_nan=True)
        >>> iqr
        np.float64(1.5)
        >>> num_dat = list(range(100))
        >>> iqr = interquartile_range(num_dat)
        >>> iqr
        np.float64(49.5)
        >>> iqr, lower_fence, upper_fence = interquartile_range(num_dat, outlier_fences=True)
        >>> iqr, lower_fence, upper_fence
        (np.float64(49.5), np.float64(-49.5), np.float64(148.5))
    """

    if isinstance(ignore_nan, np.ndarray):
        arr = num_dat.copy()
    else:
        arr = np.array(list(map(float, num_dat)))

    if len(num_dat) < 2:
        raise ValueError("Input must contain at least 2 elements.")

    if ignore_nan and arr.dtype.kind == 'f':
        arr = arr[~np.isnan(arr)]

    q1, q3 = np.percentile(arr, q=rng, axis=axis, **kwargs)
    iqr = (q3 - q1) * scale

    if outlier_fences:
        lower_fence, upper_fence = q1 - k * iqr, q3 + k * iqr
        return iqr, lower_fence, upper_fence
    else:
        return iqr


def get_extreme_outlier_bounds(num_dat, k=1.5):
    # noinspection PyShadowingNames
    """
    Gets the upper and lower bounds for extreme outliers using the interquartile range method.

    :param num_dat: Array-like object containing numerical data.
    :type num_dat: array-like
    :param k: Scale coefficient associated with the interquartile range; defaults to ``1.5``.
    :type k: float | int
    :return: Tuple containing the lower and upper bounds for extreme outliers.
    :rtype: tuple

    **Examples**::

        >>> from pyhelpers.ops import get_extreme_outlier_bounds
        >>> import pandas as pd
        >>> data = pd.DataFrame(range(100), columns=['col'])
        >>> data
            col
        0     0
        1     1
        2     2
        3     3
        4     4
        ..  ...
        95   95
        96   96
        97   97
        98   98
        99   99
        [100 rows x 1 columns]
        >>> data.describe()
                      col
        count  100.000000
        mean    49.500000
        std     29.011492
        min      0.000000
        25%     24.750000
        50%     49.500000
        75%     74.250000
        max     99.000000
        >>> lo_bound, up_bound = get_extreme_outlier_bounds(data, k=1.5)
        >>> lo_bound, up_bound
        (0.0, 148.5)
    """

    q1, q3 = np.percentile(num_dat, 25), np.percentile(num_dat, 75)
    iqr = q3 - q1

    lower_bound = np.max([0, q1 - k * iqr])
    upper_bound = q3 + k * iqr

    return lower_bound, upper_bound
