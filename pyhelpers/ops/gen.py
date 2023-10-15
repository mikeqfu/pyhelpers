"""
Miscellaneous operations for general usage.
"""

import ast
import datetime
import hashlib
import inspect
import os
import re

import pandas as pd

from .._cache import _confirmed


def confirmed(prompt=None, confirmation_required=True, resp=False):
    """
    Type to confirm whether to proceed or not.

    See also [`OPS-C-1 <https://code.activestate.com/recipes/541096/>`_].

    :param prompt: a message that prompts a response (Yes/No), defaults to ``None``
    :type prompt: str | None
    :param confirmation_required: whether to require users to confirm and proceed, defaults to ``True``
    :type confirmation_required: bool
    :param resp: default response, defaults to ``False``
    :type resp: bool
    :return: a response
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.ops import confirmed

        >>> if confirmed(prompt="Testing if the function works?", resp=True):
        ...     print("Passed.")
        Testing if the function works? [Yes]|No: yes
        Passed.
    """

    return _confirmed(prompt=prompt, confirmation_required=confirmation_required, resp=resp)


def get_obj_attr(obj, col_names=None, as_dataframe=False):
    """
    Get main attributes of an object.

    :param obj: an object, e.g. a class
    :type obj: object
    :param col_names: a list of column names for renaming the returned data frame
        when ``as_dataframe=True``
    :type col_names: list | None
    :param as_dataframe: whether to return the data in tabular format, defaults to ``False``
    :type as_dataframe: bool
    :return: list or tabular data of the main attributes of the given object
    :rtype: list | pandas.DataFrame

    **Examples**::

        >>> from pyhelpers.ops import get_obj_attr
        >>> from pyhelpers.dbms import PostgreSQL

        >>> postgres = PostgreSQL()
        Password (postgres@localhost:5432): ***
        Connecting postgres:***@localhost:5432/postgres ... Successfully.

        >>> obj_attr = get_obj_attr(postgres, as_dataframe=True)
        >>> obj_attr.head()
                  attribute       value
        0  DEFAULT_DATABASE    postgres
        1   DEFAULT_DIALECT  postgresql
        2    DEFAULT_DRIVER    psycopg2
        3      DEFAULT_HOST   localhost
        4      DEFAULT_PORT        5432

        >>> obj_attr.attribute.to_list()
        ['DEFAULT_DATABASE',
         'DEFAULT_DIALECT',
         'DEFAULT_DRIVER',
         'DEFAULT_HOST',
         'DEFAULT_PORT',
         'DEFAULT_SCHEMA',
         'DEFAULT_USERNAME',
         'address',
         'database_info',
         'database_name',
         'engine',
         'host',
         'port',
         'url',
         'username']
    """

    if col_names is None:
        col_names = ['attribute', 'value']

    all_attrs = inspect.getmembers(obj, lambda x: not (inspect.isroutine(x)))

    attrs = [x for x in all_attrs if not re.match(r'^__?', x[0])]

    if as_dataframe:
        attrs = pd.DataFrame(attrs, columns=col_names)

    return attrs


def eval_dtype(str_val):
    """
    Convert a string to its intrinsic data type.

    :param str_val: a string-type variable
    :type str_val: str
    :return: converted value
    :rtype: any

    **Examples**::

        >>> from pyhelpers.ops import eval_dtype

        >>> val_1 = '1'
        >>> origin_val = eval_dtype(val_1)
        >>> origin_val
        1

        >>> val_2 = '1.1.1'
        >>> origin_val = eval_dtype(val_2)
        >>> origin_val
        '1.1.1'
    """

    try:
        val = ast.literal_eval(str_val)
    except (ValueError, SyntaxError):
        val = str_val

    return val


def hash_password(password, salt=None, salt_size=None, iterations=None, ret_hash=True, **kwargs):
    """
    Hash a password using `hashlib.pbkdf2_hmac
    <https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac>`_.

    See also [`OPS-HP-1 <https://nitratine.net/blog/post/how-to-hash-passwords-in-python/>`_].

    :param password: input as a password
    :type password: str | int | float | bytes
    :param salt: random data; when ``salt=None`` (default), it is generated by `os.urandom()`_,
        which depends on ``salt_size``;
        see also [`OPS-HP-2 <https://en.wikipedia.org/wiki/Salt_%28cryptography%29>`_]
    :type salt: bytes | str
    :param salt_size: ``size`` of the function `os.urandom()`_, i.e. the size of a random bytestring
        for cryptographic use; when ``salt_size=None`` (default), it uses ``128``
    :type salt_size: int | None
    :param iterations: ``size`` of the function `hashlib.pbkdf2_hmac()`_,
        i.e. number of iterations of SHA-256; when ``salt_size=None`` (default), it uses ``100000``
    :type iterations: int | None
    :param ret_hash: whether to return the salt and key, defaults to ``True``
    :type ret_hash: bool
    :param kwargs: [optional] parameters of the function `hashlib.pbkdf2_hmac()`_
    :return: (only when ``ret_hash=True``) salt and key
    :rtype: bytes

    .. _`os.urandom()`: https://docs.python.org/3/library/os.html#os.urandom
    .. _`hashlib.pbkdf2_hmac()`: https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac

    **Examples**::

        >>> from pyhelpers.ops import hash_password, verify_password

        >>> test_pwd = 'test%123'
        >>> salt_size_ = 16
        >>> sk = hash_password(password=test_pwd, salt_size=salt_size_)  # salt and key
        >>> salt_data, key_data = sk[:salt_size_].hex(), sk[salt_size_:].hex()
        >>> verify_password(password=test_pwd, salt=salt_data, key=key_data)
        True

        >>> test_pwd = b'test%123'
        >>> sk = hash_password(password=test_pwd)
        >>> salt_data, key_data = sk[:128].hex(), sk[128:].hex()
        >>> verify_password(password=test_pwd, salt=salt_data, key=key_data)
        True
    """

    if not isinstance(password, (bytes, bytearray)):
        pwd = str(password).encode('UTF-8')
    else:
        pwd = password

    if salt is None:
        salt_ = os.urandom(128 if salt_size is None else salt_size)
    else:
        salt_ = salt.encode() if isinstance(salt, str) else salt

    iterations_ = 100000 if iterations is None else iterations

    key = hashlib.pbkdf2_hmac(
        hash_name='SHA256', password=pwd, salt=salt_, iterations=iterations_, **kwargs)

    if ret_hash:
        salt_and_key = salt_ + key
        return salt_and_key


def verify_password(password, salt, key, iterations=None):
    """
    Verify a password given salt and key.

    :param password: input as a password
    :type password: str | int | float | bytes
    :param salt: random data;
        see also [`OPS-HP-1 <https://en.wikipedia.org/wiki/Salt_%28cryptography%29>`_]
    :type salt: bytes | str
    :param key: PKCS#5 password-based key (produced by the function `hashlib.pbkdf2_hmac()`_)
    :type key: bytes | str
    :param iterations: ``size`` of the function `hashlib.pbkdf2_hmac()`_,
        i.e. number of iterations of SHA-256; when ``salt_size=None`` (default), it uses ``100000``
    :type iterations: int | None
    :return: whether the input password is correct
    :rtype: bool

    .. _`hashlib.pbkdf2_hmac()`: https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac

    .. seealso::

        - Examples of the function :func:`pyhelpers.ops.hash_password`
    """

    pwd = str(password).encode('UTF-8') if not isinstance(password, (bytes, bytearray)) else password
    iterations_ = 100000 if iterations is None else iterations

    def _is_hex(x):
        try:
            int(x, 16)
            return True
        except ValueError:
            return False

    key_ = hashlib.pbkdf2_hmac(
        hash_name='SHA256', password=pwd, salt=bytes.fromhex(salt) if _is_hex(salt) else salt,
        iterations=iterations_)

    rslt = True if key_ == (bytes.fromhex(key) if _is_hex(key) else key) else False

    return rslt


def func_running_time(func):
    """
    A decorator to measure the time of a function or class method.

    :param func: any function or class method
    :type func: typing.Callable
    :return: the decorated function or class method with the time of running
    :rtype: typing.Callable

    **Examples**::

        >>> from pyhelpers.ops import func_running_time
        >>> import time

        >>> @func_running_time
        >>> def test_func():
        ...     print("Testing if the function works.")
        ...     time.sleep(3)

        >>> test_func()
        INFO Begin to run function: test_func …
        Testing if the function works.
        INFO Finished running function: test_func, total: 3s
    """

    def inner(*args, **kwargs):
        print(f'INFO Begin to run function: {func.__name__} …')
        time_start = datetime.datetime.now()
        res = func(*args, **kwargs)
        time_diff = datetime.datetime.now() - time_start
        print(
            f'INFO Finished running function: {func.__name__}, total: {time_diff.seconds}s')
        print()
        return res

    return inner
