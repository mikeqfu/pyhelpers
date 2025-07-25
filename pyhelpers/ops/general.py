"""
Miscellaneous operations for general usage.
"""

import ast
import datetime
import hashlib
import inspect
import os
import re
import subprocess  # nosec

import pandas as pd

from .._cache import _confirmed, _get_ansi_colour_code


def confirmed(prompt=None, confirmation_required=True, resp=False):
    """
    Prompts user for confirmation to proceed.

    See also [`OPS-C-1 <https://code.activestate.com/recipes/541096/>`_].

    :param prompt: Message prompting a response (Yes/No); defaults to ``None``.
    :type prompt: str | None
    :param confirmation_required: Whether to require user confirmation to proceed;
        defaults to ``True``.
    :type confirmation_required: bool
    :param resp: Default response if no user input; defaults to ``False`` (No).
    :type resp: bool
    :return: User response indicating confirmation (``True``) or denial (``False``).
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
    Retrieves main attributes of an object.

    :param obj: Object from which to retrieve attributes, e.g. an instance of a class.
    :type obj: object
    :param col_names: List of column names for renaming the returned dataframe
        when ``as_dataframe=True``; defaults to ``None``.
    :type col_names: list | None
    :param as_dataframe: Whether to return the data in tabular format (dataframe);
        defaults to ``False``.
    :type as_dataframe: bool
    :return: The main attributes of the given ``obj``.
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
    Converts a string representation to its intrinsic data type.

    :param str_val: String representation of a value.
    :type str_val: str
    :return: Value converted to its intrinsic data type.
    :rtype: typing.Any

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
    Hashes a password using `hashlib.pbkdf2_hmac
    <https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac>`_
    (PBKDF2 algorithm with HMAC-SHA256).

    See also [`OPS-HP-1 <https://nitratine.net/blog/post/how-to-hash-passwords-in-python/>`_].

    :param password: Password to be hashed.
    :type password: str | int | float | bytes
    :param salt: Optional salt data for hashing;
        if ``salt=None`` (default), it is generated by `os.urandom()`_,
        which depends on ``salt_size``;
        see also [`OPS-HP-2 <https://en.wikipedia.org/wiki/Salt_%28cryptography%29>`_].
    :type salt: bytes | str | None
    :param salt_size: Size of the ``salt`` in bytes,
        which is equivalent to ``size`` of the function `os.urandom()`_;
        defaults to ``128`` if not specified.
    :type salt_size: int | None
    :param iterations: Number of iterations for PBKDF2,
        which is equivalent to ``size`` of the function `hashlib.pbkdf2_hmac()`_;
        defaults to ``100000`` if not specified.
    :type iterations: int | None
    :param ret_hash: Whether to return the salt and key; defaults to ``True``.
    :type ret_hash: bool
    :param kwargs: [Optional] Additional parameters for the function `hashlib.pbkdf2_hmac()`_.
    :return: Hashed password and salt as bytes (returned only if ``ret_hash=True``).
    :rtype: bytes | None

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

    return None


def verify_password(password, salt, key, iterations=None):
    """
    Verifies if a password matches the provided salt and key.

    :param password: Password to be verified.
    :type password: str | int | float | bytes
    :param salt: Salt used during hashing to enhance security;
        see also [`OPS-HP-1 <https://en.wikipedia.org/wiki/Salt_%28cryptography%29>`_].
    :type salt: bytes | str
    :param key: Hashed key generated using PBKDF2 algorithm (produced by `hashlib.pbkdf2_hmac()`_).
    :type key: bytes | str
    :param iterations: Number of iterations used in PBKDF2; defaults to ``100000`` if not specified.
    :type iterations: int | None
    :return: ``True`` if the input password matches the hashed key and salt, ``False`` otherwise.
    :rtype: bool

    .. _`hashlib.pbkdf2_hmac()`: https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac

    .. seealso::

        - Examples of the function :func:`pyhelpers.ops.hash_password`.
    """

    if not isinstance(password, (bytes, bytearray)):
        pwd = str(password).encode('UTF-8')
    else:
        pwd = password
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
    Decorator to measure the execution time of a function or class method.

    :param func: Function or class method to be decorated.
    :type func: typing.Callable
    :return: Decorated function or class method that measures its own execution time.
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
        print(f'INFO Finished running function: {func.__name__}, total: {time_diff.seconds}s\n')
        return res

    return inner


def get_git_branch(verbose=False):
    """
    Gets the current Git branch name.

    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :return: The name of the currently checked-out Git branch.
    :rtype: str

    **Examples**::

        >>> from pyhelpers.ops import get_git_branch
        >>> get_git_branch()
        'master'
    """

    try:  # Run the git command to get the current branch name
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            check=True,
            text=True,
            capture_output=True
        )  # nosec
        branch_name = result.stdout.strip()

        return branch_name

    except subprocess.CalledProcessError:
        if verbose:
            print("Not in a Git repository")


def get_ansi_colour_code(colours, show_valid_colours=False):
    """
    Returns the ANSI escape code(s) for the given colour name(s).

    :param colours: A single colour name (str) or a sequence of colour names
        (e.g. 'red', ['red', 'green']).
    :type colours: str | list[str] | tuple[str]
    :param show_valid_colours: If ``True``, returns a tuple containing the ANSI code(s) and
        a set of valid colour names.
    :type show_valid_colours: bool
    :return: The ANSI escape code(s) for the given colour(s), or an error message
        if an invalid colour is provided.
    :rtype: str | list[str] | tuple[str | list[str], set[str]]

    **Examples**::

        >>> from pyhelpers.ops import get_ansi_colour_code
        >>> get_ansi_colour_code('red')
        '\\033[31m'
        >>> get_ansi_colour_code(['red', 'blue'])
        ['\\033[31m', '\\033[34m']
        >>> get_ansi_colour_code('invalid_colour')
        Traceback (most recent call last):
            ...
        ValueError: 'invalid_colour' is not a valid colour name.
        >>> get_ansi_colour_code('red', show_valid_colours=True)
        ('\\033[31m', {'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', ...})
    """

    return _get_ansi_colour_code(colours=colours, show_valid_colours=show_valid_colours)
