"""
Communication with databases.

*The current release includes classes for* `PostgreSQL <https://www.postgresql.org/>`_
*and* `Microsoft SQL Server <https://www.microsoft.com/en-gb/sql-server/>`_.
"""

import copy
import csv
import functools
import gc
import getpass
import inspect
import io
import itertools
import operator
import os
import re
import sys
import tempfile
import warnings

import pandas as pd
import sqlalchemy
import sqlalchemy.dialects

from ._cache import _check_dependency
from .dir import cd, validate_dir
from .ops import confirmed
from .store import save_data


def _create_db(cls, confirm_db_creation, verbose):
    """
    Create a database (if it does not exist) when creating an instance.

    :param cls: database class
    :param confirm_db_creation: whether to prompt a confirmation before creating a new database
        (if the specified database does not exist)
    :param verbose: whether to print relevant information in console
    """

    db_name = cls._database_name(cls.database_name)

    cfm_msg = f"The database {db_name} does not exist. Proceed by creating it\n?"
    if confirmed(prompt=cfm_msg, confirmation_required=confirm_db_creation):

        if verbose:
            print(f"Creating a database: {db_name}", end=" ... ")

        try:
            cls.engine.execute(f'CREATE DATABASE {db_name};')
            cls.engine.url = cls.engine.url.set(database=cls.database_name)

            if verbose:
                print("Done.")

        except Exception as e:
            if verbose:
                print("Failed. {}".format(e))


def _create_database(cls, database_name, verbose):
    """
    Create a database.

    :param cls: database class
    :param database_name: name of a database
    :param verbose: whether to print relevant information in console
    """

    if not cls.database_exists(database_name=database_name):
        db_name = cls._database_name(database_name)

        if verbose:
            print(f"Creating a database: {db_name} ... ", end="")

        cls.disconnect_database()

        cls.engine.execute(f'CREATE DATABASE {db_name};')

        if verbose:
            print("Done.")

    else:
        if verbose:
            print("The database already exists.")

    cls.connect_database(database_name=database_name)


def _drop_database(cls, database_name, confirmation_required, verbose):
    """
    Drop/delete a database.

    :param cls: database class
    :param database_name: name of a database
    :param confirmation_required: whether to prompt a message for confirmation to proceed
    :param verbose: whether to print relevant information in console
    """

    db_name = cls._database_name(database_name)

    if not cls.database_exists(database_name=database_name):
        if verbose:
            print(f"The database {db_name} does not exist.")

    else:
        # address_ = self.address.replace(f"/{db_name}", "")
        address_ = cls.address.split('/')[0]
        cfm_msg = f"To drop the database {db_name} from {address_}\n?"
        if confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):
            cls.disconnect_database(database_name=database_name)

            if verbose:
                if confirmation_required:
                    log_msg = f"Dropping {db_name}"
                else:
                    log_msg = f"Dropping the database {db_name} from {address_}"
                print(log_msg, end=" ... ")

            try:
                cls.engine.execute(f'DROP DATABASE {db_name};')

                if verbose:
                    print("Done.")

            except Exception as e:
                print("Failed. {}".format(e))


def _import_data(cls, data, table_name, schema_name=None, if_exists='fail',
                 force_replace=False, chunk_size=None, col_type=None, method='multi',
                 index=False, confirmation_required=True, verbose=False, **kwargs):
    """
    Import tabular data into a table.

    :param data: tabular data to be dumped into a database
    :type data: pandas.DataFrame or pandas.io.parsers.TextFileReader or list or tuple
    :param table_name: name of a table
    :type table_name: str
    :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
        :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
    :type schema_name: str or None
    :param if_exists: if the table already exists, to ``'replace'``, ``'append'``
        or, by default, ``'fail'`` and do nothing but raise a ValueError.
    :type if_exists: str
    :param force_replace: whether to force replacing existing table, defaults to ``False``
    :type force_replace: bool
    :param chunk_size: the number of rows in each batch to be written at a time, defaults to ``None``
    :type chunk_size: int or None
    :param col_type: data types for columns, defaults to ``None``
    :type col_type: dict or None
    :param method: method for SQL insertion clause, defaults to ``'multi'``

        - ``None``: uses standard SQL ``INSERT`` clause (one per row);
        - ``'multi'``: pass multiple values in a single ``INSERT`` clause;
        - callable (e.g. ``PostgreSQL.psql_insert_copy``)
          with signature ``(pd_table, conn, keys, data_iter)``.

    :type method: str or None or typing.Callable
    :param index: whether to dump the index as a column
    :type index: bool
    :param confirmation_required: whether to prompt a message for confirmation to proceed,
        defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.DataFrame.to_sql`_

    .. _`pandas.DataFrame.to_sql`:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html
    """

    schema_name_ = cls._schema_name(schema_name=schema_name)
    table_name_ = cls._table_name(table_name=table_name, schema_name=schema_name_)

    if confirmed("To import data into {} at {}\n?".format(table_name_, cls.address),
                 confirmation_required=confirmation_required):

        inspector = sqlalchemy.inspect(cls.engine)
        if schema_name_ not in inspector.get_schema_names():
            cls.create_schema(schema_name=schema_name_, verbose=verbose)

        if cls.table_exists(table_name=table_name, schema_name=schema_name_):
            if verbose:
                if_exists_msg = f"The table {table_name_} already exists"
                if if_exists == 'fail':
                    if not force_replace:
                        add_msg = "Use `if_exists='replace'` or `force_replace=True` to update it."
                        print(if_exists_msg + f". ({add_msg})")
                        return None
                elif if_exists == 'replace':
                    print(if_exists_msg + f" and is replaced.")

                if force_replace:
                    print("The existing table is forced to be dropped", end=" ... ")
                    cls.drop_table(
                        table_name=table_name, schema_name=schema_name_,
                        confirmation_required=confirmation_required, verbose=verbose)
                    print("Done.")

        if verbose == 2:
            if confirmation_required:
                log_msg = f"Importing the data into the table {table_name_}"
            else:
                log_msg = f"Importing data into the table {table_name_} at {cls.address}"
            print(log_msg, end=" ... ")

        to_sql_args = {
            'name': table_name,
            'con': cls.engine,
            'schema': schema_name_,
            'if_exists': if_exists,
            'index': index,
            'dtype': col_type,
            'method': method,
        }

        kwargs.update(to_sql_args)

        pd_parsers = _check_dependency(name='pandas.io.parsers')

        if isinstance(data, (pd_parsers.TextFileReader, list, tuple)):
            for chunk in data:
                chunk.to_sql(**kwargs)
                del chunk
                gc.collect()

        else:
            kwargs.update({'chunksize': chunk_size})
            data.to_sql(**kwargs)
            gc.collect()

        if verbose == 2:
            print("Done.")


""" == Databases =============================================================================== """


class PostgreSQL:
    """
    A class for basic communication with `PostgreSQL`_ databases.

    .. _`PostgreSQL`: https://www.postgresql.org/
    """

    #: Default dialect.
    #: The dialect that SQLAlchemy uses to communicate with PostgreSQL; see also
    #: [`DBMS-PS-1 <https://docs.sqlalchemy.org/dialects/postgresql.html>`_]
    DEFAULT_DIALECT = 'postgresql'
    #: Default name of database driver.
    DEFAULT_DRIVER = 'psycopg2'
    #: Default host name/address (by installation of PostgreSQL).
    DEFAULT_HOST = 'localhost'
    #: Default listening port used by PostgreSQL.
    DEFAULT_PORT = 5432
    #: Default username.
    DEFAULT_USERNAME = 'postgres'
    #: Name of the database that is by default to connect with.
    #: The database is created by installation of PostgreSQL.
    DEFAULT_DATABASE = 'postgres'
    #: Name of the schema that is created by default for the installation of PostgreSQL.
    DEFAULT_SCHEMA = 'public'

    def __init__(self, host=None, port=None, username=None, password=None, database_name=None,
                 confirm_db_creation=False, verbose=True):
        """
        :param host: host name/address of a PostgreSQL server,
            e.g. ``'localhost'`` or ``'127.0.0.1'`` (default by installation of PostgreSQL);
            when ``host=None`` (default), it is initialized as ``'localhost'``
        :type host: str or None
        :param port: listening port used by PostgreSQL; when ``port=None`` (default),
            it is initialized as ``5432`` (default by installation of PostgreSQL)
        :type port: int or None
        :param username: username of a PostgreSQL server; when ``username=None`` (default),
            it is initialized as ``'postgres'`` (default by installation of PostgreSQL)
        :type username: str or None
        :param password: user password; when ``password=None`` (default),
            it is required to mannually type in the correct password to connect the PostgreSQL server
        :type password: str or int or None
        :param database_name: name of a database; when ``database=None`` (default),
            it is initialized as ``'postgres'`` (default by installation of PostgreSQL)
        :type database_name: str or None
        :param confirm_db_creation: whether to prompt a confirmation before creating a new database
            (if the specified database does not exist), defaults to ``False``
        :type confirm_db_creation: bool
        :param verbose: whether to print relevant information in console, defaults to ``True``
        :type verbose: bool or int

        :ivar str host: host name/address
        :ivar str port: listening port used by PostgreSQL
        :ivar str username: username
        :ivar str database_name: name of a database
        :ivar dict credentials: basic information about the server/database being connected
        :ivar str address: representation of the database address
        :ivar sqlalchemy.engine.Engine engine: `SQLAlchemy`_ connectable engine to a PostgreSQL server;
            see also [`DBMS-PS-2`_]

        .. _`DBMS-PS-1`:
            https://docs.sqlalchemy.org/en/latest/dialects/postgresql.html
        .. _`DBMS-PS-2`:
            https://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine
        .. _`SQLAlchemy`:
            https://www.sqlalchemy.org/

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> # Connect the default database 'postgres'
            >>> # postgres = PostgreSQL('localhost', 5432, 'postgres', database_name='postgres')
            >>> postgres = PostgreSQL()
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/postgres ... Successfully.

            >>> postgres.address
            'postgres:***@localhost:5432/postgres'

            >>> # Connect a database 'testdb' (which will be created if it does not exist)
            >>> testdb = PostgreSQL(database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.address
            'postgres:***@localhost:5432/testdb'

            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.

            >>> testdb.address
            'postgres:***@localhost:5432/postgres'

        **Define a proxy object that inherits from this class**::

            >>> class ExampleProxyObj(PostgreSQL):
            ...
            ...     def __init__(self, **kwargs):
            ...         super().__init__(**kwargs)

            >>> example_proxy = ExampleProxyObj(database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> example_proxy.address
            'postgres:***@localhost:5432/testdb'
            >>> example_proxy.database_name
            'testdb'

            >>> example_proxy.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.

            >>> example_proxy.database_name
            'postgres'
        """

        _ = _check_dependency(name='psycopg2')

        self.host = copy.copy(self.DEFAULT_HOST) if host is None else str(host)
        self.port = copy.copy(self.DEFAULT_PORT) if port is None else int(port)
        self.username = copy.copy(self.DEFAULT_USERNAME) if username is None else str(username)

        self.credentials = {
            'drivername': '+'.join([self.DEFAULT_DIALECT, self.DEFAULT_DRIVER]),
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'database': self.DEFAULT_DATABASE,
        }

        if password is None:
            pwd = getpass.getpass(f'Password ({self.username}@{self.host}:{self.port}): ')
        else:
            pwd = str(password)

        # The typical form of the URL: backend+driver://username:password@host:port/database
        url = sqlalchemy.engine.URL.create(**self.credentials, password=pwd)
        self.engine = sqlalchemy.create_engine(url=url, isolation_level='AUTOCOMMIT')

        if database_name is None or database_name == self.DEFAULT_DATABASE:
            self.database_name = copy.copy(self.DEFAULT_DATABASE)
            reconnect_db = False
        else:
            self.database_name = self.credentials['database'] = str(database_name)
            if database_name in self.get_database_names():
                self.engine.url = self.engine.url.set(database=self.database_name)
            else:  # the database doesn't exist
                _create_db(self, confirm_db_creation=confirm_db_creation, verbose=verbose)
            reconnect_db = True

        # self.address = make_database_address(self.host, self.port, self.username, self.database_name)
        self.address = self.engine.url.render_as_string(hide_password=True).split('//')[1]
        if verbose:
            print("Connecting {}".format(self.address), end=" ... ")

        try:  # Create a SQLAlchemy connectable
            if reconnect_db:
                self.engine = sqlalchemy.create_engine(url=self.engine.url, isolation_level='AUTOCOMMIT')
            test_conn = self.engine.connect()
            test_conn.close()
            del test_conn
            if verbose:
                print("Successfully.")
        except Exception as e:
            print("Failed. {}".format(e))

    def _database_name(self, database_name=None):
        """
        Format a database name.

        :param database_name: database name as an input, defaults to ``None``
        :type database_name: str or None
        :return: a database name
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> postgres = PostgreSQL()
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/postgres ... Successfully.

            >>> postgres._database_name()
            '"postgres"'
            >>> postgres._database_name(database_name='testdb')
            '"testdb"'
        """

        db_name = copy.copy(self.database_name) if database_name is None else str(database_name)
        database_name_ = f'"{db_name}"'

        return database_name_

    def _schema_name(self, schema_name=None):
        """
        Get a schema name.

        :param schema_name: schema name as an input, defaults to ``None``
        :type schema_name: str or None
        :return: a schema name
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> postgres = PostgreSQL()
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/postgres ... Successfully.

            >>> postgres._schema_name()
            'public'
            >>> postgres._schema_name(schema_name='test_schema')
            'test_schema'
        """

        schema_name_ = copy.copy(self.DEFAULT_SCHEMA) if schema_name is None else str(schema_name)

        return schema_name_

    def _table_name(self, table_name, schema_name=None):
        """
        Get a formatted table name.

        :param table_name: table name as an input
        :type table_name: str
        :param schema_name: schema name as an input, defaults to ``None``
        :type schema_name: str or None
        :return: a formatted table name, which is used in a SQL query statement
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> postgres = PostgreSQL()
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/postgres ... Successfully.

            >>> postgres._table_name(table_name='test_table')
            '"public"."test_table"'
            >>> postgres._table_name(table_name='test_table', schema_name='test_schema')
            '"test_schema"."test_table"'
        """

        schema_name_ = self._schema_name(schema_name=schema_name)
        table_name_ = f'"{schema_name_}"."{table_name}"'

        return table_name_

    def get_database_names(self, names_only=True):
        """
        Get names of all existing databases.

        :param names_only: whether to return only the names of the databases, defaults to ``True``
        :type names_only: bool
        :return: names of all existing databases
        :rtype: list or pandas.DataFrame

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> # Connect the default database 'postgres'
            >>> # postgres = PostgreSQL('localhost', 5432, 'postgres', database_name='postgres')
            >>> postgres = PostgreSQL()
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/postgres ... Successfully.

            >>> postgres.get_database_names()
            ['template1',
             'template0',
             'postgis_32_sample',
             'postgres']
        """

        conn = self.engine.connect(close_with_result=True)
        rslt = conn.execute('SELECT datname FROM pg_database;')

        db_names = rslt.fetchall()
        if names_only:
            database_names = list(itertools.chain(*db_names))
        else:
            database_names = pd.DataFrame(db_names)

        return database_names

    def database_exists(self, database_name=None):
        """
        Check whether a database exists.

        :param database_name: name of a database, defaults to ``None``
        :type database_name: str or None
        :return: whether the database exists
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> # Check whether the database "testdb" exists now
            >>> testdb.database_exists(database_name='testdb')  # testdb.database_exists()
            True
            >>> testdb.database_name
            'testdb'

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.

            >>> # Check again whether the database "testdb" still exists now
            >>> testdb.database_exists(database_name='testdb')
            False
            >>> testdb.database_name
            'postgres'
        """

        db_name = self.database_name if database_name is None else str(database_name)

        conn = self.engine.connect(close_with_result=True)
        rslt = conn.execute(
            f"SELECT EXISTS(SELECT datname FROM pg_catalog.pg_database WHERE datname='{db_name}');")
        db_exists = bool(rslt.fetchone()[0])

        return db_exists

    def create_database(self, database_name, verbose=False):
        """
        Create a database.

        :param database_name: name of a database
        :type database_name: str
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.
            >>> testdb.database_name
            'testdb'

            >>> testdb.create_database(database_name='testdb1', verbose=True)
            Creating a database: "testdb1" ... Done.
            >>> testdb.database_name
            'testdb1'

            >>> # Delete the database "testdb1"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb1" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb1" ... Done.
            >>> testdb.database_name
            'postgres'

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(database_name='testdb', verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
            >>> testdb.database_name
            'postgres'
        """

        _create_database(self, database_name=database_name, verbose=verbose)

    def connect_database(self, database_name=None, verbose=False):
        """
        Establish a connection to a database.

        :param database_name: name of a database;
            when ``database_name=None`` (default), the database name is input manually
        :type database_name: str or None
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.connect_database(verbose=True)
            Being connected with postgres:***@localhost:5432/testdb.

            >>> testdb.connect_database(database_name='postgres', verbose=True)
            Connecting postgres:***@localhost:5432/postgres ... Successfully.
            >>> testdb.database_name
            'postgres'

            >>> testdb.connect_database(database_name='testdb', verbose=True)
            Connecting postgres:***@localhost:5432/testdb ... Successfully.
            >>> testdb.database_name
            'testdb'

            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
            >>> testdb.database_name
            'postgres'
        """

        if database_name is not None:
            self.database_name = str(database_name)
            self.address = make_database_address(
                host=self.host, port=self.port, username=self.username,
                database_name=self.database_name)

            if verbose:
                print(f"Connecting {self.address}", end=" ... ")

            try:
                self.credentials['database'] = self.database_name
                url = self.engine.url.set(database=self.database_name)

                if not self.database_exists(database_name=self.database_name):
                    self.create_database(database_name=self.database_name)

                self.engine = sqlalchemy.create_engine(url, isolation_level='AUTOCOMMIT')

                if verbose:
                    print("Successfully.")

            except Exception as e:
                print("Failed. {}".format(e))

        else:
            if verbose:
                print(f"Being connected with {self.address}.")

    def get_database_size(self, database_name=None):
        """
        Get the size of a database.

        :param database_name: name of a database;
            if ``database_name=None`` (default), the function returns the size of the
            currently-connected database
        :type database_name: str or None
        :return: size of the database
        :rtype: int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.
            >>> testdb.get_database_size()
            '8553 kB'

            >>> testdb.DEFAULT_DATABASE
            'postgres'
            >>> testdb.get_database_size(database_name=testdb.DEFAULT_DATABASE)
            '8609 kB'

            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        db_name = 'current_database()' if database_name is None else '\'{}\''.format(database_name)

        sql_query = 'SELECT pg_size_pretty(pg_database_size({})) AS size;'.format(db_name)

        db_size = self.engine.execute(sql_query).fetchone()[0]

        return db_size

    def disconnect_database(self, database_name=None, verbose=False):
        """
        Disconnect a database.

        See also [`DBMS-PS-DD-1 <https://stackoverflow.com/questions/17449420/>`_].

        :param database_name: name of database to disconnect from;
            if ``database_name=None`` (default), disconnect the current database.
        :type database_name: str or None
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Creating a database: "testdb" ... Done.
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.database_name
            'testdb'

            >>> testdb.disconnect_database()
            >>> testdb.database_name
            'postgres'

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(database_name='testdb', verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        db_name = copy.copy(self.database_name) if database_name is None else str(database_name)

        if verbose:
            print("Disconnecting the database \"{}\" ... ".format(db_name), end="")
        try:
            self.connect_database(database_name=self.DEFAULT_DATABASE)

            self.engine.execute(f'REVOKE CONNECT ON DATABASE "{db_name}" FROM public, postgres;')

            self.engine.execute(
                f"SELECT pg_terminate_backend(pid) "
                f"FROM pg_stat_activity "
                f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid();")

            if verbose:
                print("Done.")

        except Exception as e:
            print("Failed. {}".format(e))

    def disconnect_all_others(self):
        """
        Kill connections to all databases except the currently-connected one.

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.database_name
            'testdb'

            >>> testdb.disconnect_all_others()
            >>> testdb.database_name
            'testdb'

            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        # self.connect_database(database_name='postgres')
        self.engine.execute(
            'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid();')

    def drop_database(self, database_name=None, confirmation_required=True, verbose=False):
        """
        Delete/drop a database.

        :param database_name: database to be disconnected;
            if ``database_name=None`` (default), drop the database being currently currented
        :type database_name: str or None
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.
            >>> testdb.database_name
            'testdb'

            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.

            >>> testdb.database_exists(database_name='testdb')
            False
            >>> testdb.drop_database(database_name='testdb', verbose=True)
            The database "testdb" does not exist.
            >>> testdb.database_name
            'postgres'
        """

        _drop_database(
            self, database_name=database_name, confirmation_required=confirmation_required,
            verbose=verbose)

    def _msg_for_multi_items(self, item_names, desc):
        """
        Formulate a printing message for multiple items.

        :param item_names: name of one table/schema, or names of several tables/schemas
        :type item_names: str or typing.Iterable[str] or None
        :param desc: for additional description
        :type desc: str
        :return: printing message
        :rtype: tuple

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> schema_name = 'points'
            >>> schemas, prt_pl, prt_name = testdb._msg_for_multi_items(schema_name, desc='schema')
            >>> schemas
            ['points']
            >>> prt_pl
            'schema'
            >>> prt_name
            '"points"'

            >>> schema_names = ['points', 'lines', 'polygons']
            >>> schemas, prt_pl, prt_name = testdb._msg_for_multi_items(schema_names, desc='schema')
            >>> schemas
            ['points', 'lines', 'polygons']
            >>> prt_pl
            'schemas'
            >>> prt_name
            '\n\t"points"\n\t"lines"\n\t"polygons"'
            >>> print(prt_name)

                "points"
                "lines"
                "polygons"
        """

        if item_names is None:
            item_names_ = [
                x for x in sqlalchemy.inspect(self.engine).get_schema_names()
                if x != 'public' and x != 'information_schema']
        else:
            item_names_ = [item_names] if isinstance(item_names, str) else item_names

        if len(item_names_) == 1:
            print_plural = "{}".format(desc)
            try:
                print_items = "\"{}\"".format(item_names_[0])
            except TypeError:
                print_items = "\"{}\"".format(list(item_names_)[0])
        else:
            print_plural = "{}s".format(desc)
            print_items = ("\n\t\"{}\"" * len(item_names_)).format(*item_names_)

        return item_names_, print_plural, print_items

    def schema_exists(self, schema_name):
        """
        Check whether a schema exists.

        :param schema_name: name of a schema
        :type schema_name: str
        :return: whether the schema exists
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.schema_exists('public')
            True

            >>> testdb.schema_exists('test_schema')  # (if the schema 'test_schema' does not exist)
            False

            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        result = self.engine.execute(
            "SELECT EXISTS("
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name='{}');".format(self._schema_name(schema_name=schema_name)))

        return result.fetchone()[0]

    def create_schema(self, schema_name, verbose=False):
        """
        Create a schema.

        :param schema_name: name of a schema
        :type schema_name: str
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> test_schema_name = 'test_schema'

            >>> testdb.create_schema(schema_name=test_schema_name, verbose=True)
            Creating a schema: "test_schema" ... Done.

            >>> testdb.schema_exists(schema_name=test_schema_name)
            True

            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        if not self.schema_exists(schema_name=schema_name_):
            if verbose:
                print("Creating a schema: \"{}\" ... ".format(schema_name_), end="")

            try:
                self.engine.execute('CREATE SCHEMA IF NOT EXISTS "{}";'.format(schema_name_))
                if verbose:
                    print("Done.")
            except Exception as e:
                print("Failed. {}".format(e))

        else:
            print("The schema \"{}\" already exists.".format(schema_name))

    def get_schema_names(self, include_all=False, names_only=True, verbose=False):
        """
        Get the names of existing schemas.

        :param include_all: whether to list all the available schemas, defaults to ``False``
        :type include_all: bool
        :param names_only: whether to return only the names of the schema names, defaults to ``True``
        :type names_only: bool
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int
        :return: schema names
        :rtype: list or pandas.DataFrame or None

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.get_schema_names()
            ['public']

            >>> testdb.get_schema_names(include_all=True, names_only=False)
                      schema_name  schema_id      role
            0  information_schema      13388  postgres
            1          pg_catalog         11  postgres
            2            pg_toast         99  postgres
            3              public       2200  postgres

            >>> testdb.drop_schema(schema_names='public', verbose=True)
            To drop the schema "public" from postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Dropping "public" ... Done.

            >>> testdb.get_schema_names()  # None

            >>> testdb.get_schema_names(verbose=True)
            No schema exists in the currently-connected database "testdb".

            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        condition = ""
        # Note: Use '%%' for '%' in SQL statements, as '%' in Python is used for string formatting
        if not include_all:
            condition = " WHERE nspname NOT IN ('information_schema', 'pg_catalog') " \
                        "AND nspname NOT LIKE 'pg_toast%%' " \
                        "AND nspname NOT LIKE 'pg_temp%%' "

        query = f"SELECT s.nspname, s.oid, u.usename FROM pg_catalog.pg_namespace s " \
                f"JOIN pg_catalog.pg_user u ON u.usesysid = s.nspowner" \
                f"{condition}" \
                f"ORDER BY s.nspname;"

        conn = self.engine.connect(close_with_result=True)
        rslt = conn.execute(query)

        schema_info_ = rslt.fetchall()
        if not schema_info_:
            schema_info = None
            if verbose:
                print(f"No schema exists in the currently-connected database \"{self.database_name}\".")

        else:
            if names_only:
                schema_info = [x[0] for x in schema_info_]
            else:
                schema_info = pd.DataFrame(schema_info_, columns=['schema_name', 'schema_id', 'role'])

        return schema_info

    def drop_schema(self, schema_names, confirmation_required=True, verbose=False):
        """
        Delete/drop one or multiple schemas.

        :param schema_names: name of one schema, or names of multiple schemas
        :type schema_names: str or typing.Iterable[str]
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> new_schema_names = ['points', 'lines', 'polygons']
            >>> for new_schema in new_schema_names:
            ...     testdb.create_schema(new_schema, verbose=True)
            Creating a schema: "points" ... Done.
            Creating a schema: "lines" ... Done.
            Creating a schema: "polygons" ... Done.

            >>> new_schema_names_ = ['test_schema']
            >>> testdb.drop_schema(new_schema_names + new_schema_names_, verbose=True)
            To drop the following schemas from postgres:***@localhost:5432/testdb:
                "points"
                "lines"
                "polygons"
                "test_schema"
            ? [No]|Yes: yes
            Dropping ...
                "points" ... Done.
                "lines" ... Done.
                "polygons" ... Done.
                "test_schema" (does not exist.)

            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        schemas, print_plural, print_schema = self._msg_for_multi_items(
            item_names=schema_names, desc='schema')

        if len(schemas) == 1:
            cfm_msg = "To drop the {} {} from {}\n?".format(print_plural, print_schema, self.address)
        else:
            cfm_msg = "To drop the following {} from {}: {}\n?".format(
                print_plural, self.address, print_schema)

        if confirmed(cfm_msg, confirmation_required=confirmation_required):
            if verbose:
                if len(schemas) == 1:
                    if confirmation_required:
                        log_msg = "Dropping {}".format(print_schema)
                    else:
                        log_msg = "Dropping the {}: {}".format(print_plural, print_schema)
                    print(log_msg, end=" ... ")
                else:  # len(schemas) > 1
                    if confirmation_required:
                        print("Dropping ... ")
                    else:
                        print("Dropping the following {} from {}:".format(print_plural, self.address))

            for schema in schemas:
                if not self.schema_exists(schema):  # `schema` does not exist
                    if verbose:
                        if len(schemas) == 1:
                            print("The schema \"{}\" does not exist.".format(schemas[0]))
                        else:
                            print("\t\"{}\" (does not exist.)".format(schema))

                else:
                    if len(schemas) > 1 and verbose:
                        print("\t\"{}\"".format(schema), end=" ... ")

                    try:
                        # schema_ = ('%s, ' * (len(schemas) - 1) + '%s') % tuple(schemas)
                        self.engine.execute('DROP SCHEMA "{}" CASCADE;'.format(schema))

                        if verbose:
                            print("Done.")

                    except Exception as e:
                        print("Failed. {}".format(e))

    def table_exists(self, table_name, schema_name=None):
        """
        Check whether a table exists.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :type schema_name: str
        :return: whether the table exists in the currently-connected database
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> tbl_name = 'points'

            >>> testdb.table_exists(table_name=tbl_name)  # (if 'public.points' does not exist)
            False

            >>> testdb.create_table(table_name=tbl_name, column_specs='column_0 INT', verbose=1)
            Creating a table: "public"."points" ... Done.
            >>> testdb.table_exists(table_name=tbl_name)
            True

            >>> testdb.drop_table(table_name=tbl_name, verbose=True)
            To drop the table "public"."points" from postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Dropping "public"."points" ... Done.

            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        rslt = self.engine.execute(
            f"SELECT EXISTS("
            f"SELECT * FROM information_schema.tables "
            f"WHERE table_schema='{schema_name_}' AND table_name='{table_name}');")

        result = rslt.fetchone()[0]

        return result

    def create_table(self, table_name, column_specs, schema_name=None, verbose=False):
        """
        Create a table.

        :param table_name: name of a table
        :type table_name: str
        :param column_specs: specifications for each column of the table
        :type column_specs: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :type schema_name: str or None
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int

        .. _dbms-postgresql-create_table-example:

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> tbl_name = 'test_table'
            >>> col_spec = 'col_name_1 INT, col_name_2 TEXT'

            >>> testdb.create_table(table_name=tbl_name, column_specs=col_spec, verbose=True)
            Creating a table "public"."test_table" ... Done.

            >>> testdb.table_exists(table_name=tbl_name)
            True

            >>> # Get information about all columns of the table "public"."test_table"
            >>> test_tbl_col_info = testdb.get_column_info(table_name=tbl_name, as_dict=False)
            >>> test_tbl_col_info
                                        column_0      column_1
            table_catalog                 testdb        testdb
            table_schema                  public        public
            table_name                test_table    test_table
            column_name               col_name_1    col_name_2
            ordinal_position                   1             2
            column_default                  None          None
            is_nullable                      YES           YES
            data_type                    integer          text
            character_maximum_length        None          None
            character_octet_length           NaN  1073741824.0
            numeric_precision               32.0           NaN
            numeric_precision_radix          2.0           NaN
            numeric_scale                    0.0           NaN
            datetime_precision              None          None
            interval_type                   None          None
            interval_precision              None          None
            character_set_catalog           None          None
            character_set_schema            None          None
            character_set_name              None          None
            collation_catalog               None          None
            collation_schema                None          None
            collation_name                  None          None
            domain_catalog                  None          None
            domain_schema                   None          None
            domain_name                     None          None
            udt_catalog                   testdb        testdb
            udt_schema                pg_catalog    pg_catalog
            udt_name                        int4          text
            scope_catalog                   None          None
            scope_schema                    None          None
            scope_name                      None          None
            maximum_cardinality             None          None
            dtd_identifier                     1             2
            is_self_referencing               NO            NO
            is_identity                       NO            NO
            identity_generation             None          None
            identity_start                  None          None
            identity_increment              None          None
            identity_maximum                None          None
            identity_minimum                None          None
            identity_cycle                    NO            NO
            is_generated                   NEVER         NEVER
            generation_expression           None          None
            is_updatable                     YES           YES

            >>> # Get data types of all columns of the table "public"."test_table"
            >>> test_tbl_dtypes = testdb.get_column_dtype(table_name=tbl_name)
            >>> test_tbl_dtypes
            {'col_name_1': 'integer', 'col_name_2': 'text'}

            >>> # Drop the table "public"."test_table"
            >>> testdb.drop_table(table_name=tbl_name, verbose=True)
            To drop the table "public"."test_table" from postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Dropping "public"."test_table" ... Done.

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        if self.table_exists(table_name=table_name, schema_name=schema_name):
            if verbose:
                print(f"The table {table_name_} already exists.")

        else:
            if not self.schema_exists(schema_name):
                self.create_schema(schema_name=schema_name, verbose=False)

            try:
                if verbose:
                    print(f"Creating a table: {table_name_} ... ", end="")

                self.engine.execute(f'CREATE TABLE {table_name_} ({column_specs});')

                if verbose:
                    print("Done.")

            except Exception as e:
                print("Failed. {}".format(e))

    def get_column_info(self, table_name, schema_name=None, as_dict=True):
        """
        Get information about columns of a table.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :type schema_name: str or None
        :param as_dict: whether to return the column information as a dictionary, defaults to ``True``
        :type as_dict: bool
        :return: information about all columns of the given table
        :rtype: pandas.DataFrame or dict

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.PostgreSQL.create_table`.
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        column_info = self.engine.execute(
            "SELECT * FROM information_schema.columns "
            "WHERE table_schema='{}' AND table_name='{}';".format(schema_name_, table_name))

        keys, values = column_info.keys(), column_info.fetchall()
        idx = ['column_{}'.format(x) for x in range(len(values))]

        info_tbl = pd.DataFrame(values, index=idx, columns=keys).T

        if as_dict:
            info_tbl = {k: v.to_list() for k, v in info_tbl.iterrows()}

        return info_tbl

    def get_column_dtype(self, table_name, column_names=None, schema_name=None):
        """
        Get information about data types of all or specific columns of a table.

        :param table_name: name of a table
        :type table_name: str
        :param column_names: (list of) column name(s);
            when ``column_names=None`` (default), all available columns are included
        :type column_names: str or list or None
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :return: data types of all or specific columns of a table
        :rtype: dict or None

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.PostgreSQL.create_table`.
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        col_names_query = ''  # if column_names is None (default)
        if isinstance(column_names, str):
            col_names_query = f" AND column_name = '{column_names}'"
        elif isinstance(column_names, list):
            if len(column_names) == 1:
                col_names_query = f" AND column_name = '{column_names[0]}'"
            else:
                col_names_query = f" AND column_name IN {tuple(column_names)}"

        query = \
            f"SELECT column_name, data_type FROM information_schema.columns " \
            f"WHERE table_name = '{table_name}' AND table_schema = '{schema_name_}'{col_names_query};"

        column_dtypes_ = self.engine.execute(query).fetchall()

        if len(column_dtypes_) > 0:
            column_dtypes = dict(column_dtypes_)
        else:
            column_dtypes = None

        return column_dtypes

    def get_table_names(self, schema_name=None, verbose=False):
        """
        Get the names of all tables in a schema.

        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :type schema_name: str or None
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int
        :return: a list of table names
        :rtype: list or None

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> lst_tbl_names = testdb.get_table_names()
            >>> lst_tbl_names
            []

            >>> lst_tbl_names = testdb.get_table_names(schema_name='testdb', verbose=True)
            The schema "testdb" does not exist.

            >>> # Create a new table named "test_table" in the schema "testdb"
            >>> new_tbl_name = 'test_table'
            >>> col_spec = 'col_name_1 INT, col_name_2 TEXT'
            >>> testdb.create_table(table_name=new_tbl_name, column_specs=col_spec, verbose=True)
            Creating a table: "public"."test_table" ... Done.

            >>> lst_tbl_names = testdb.get_table_names(schema_name='public')
            >>> lst_tbl_names
            ['test_table']

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        if not self.schema_exists(schema_name=schema_name_):
            if verbose:
                print("The schema \"{}\" does not exist.".format(schema_name_))

        else:
            rslt = self.engine.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='{}' AND table_type='BASE TABLE';".format(schema_name_))

            temp_list = rslt.fetchall()

            table_list = [x[0] for x in temp_list]

            return table_list

    def alter_table_schema(self, table_name, schema_name, new_schema_name, confirmation_required=True,
                           verbose=False):
        """
        Move a table from one schema to another within the currently-connected database.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema
        :type schema_name: str
        :param new_schema_name: name of a new schema
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> # Create a new table named "test_table" in the schema "testdb"
            >>> new_tbl_name = 'test_table'
            >>> col_spec = 'col_name_1 INT, col_name_2 TEXT'
            >>> testdb.create_table(table_name=new_tbl_name, column_specs=col_spec, verbose=True)
            Creating a table: "public"."test_table" ... Done.

            >>> # Create a new schema "test_schema"
            >>> testdb.create_schema(schema_name='test_schema', verbose=True)
            Creating a schema: "test_schema" ... Done.

            >>> # Move the table "public"."test_table" to the schema "test_schema"
            >>> testdb.alter_table_schema(
            ...     table_name='test_table', schema_name='public', new_schema_name='test_schema',
            ...     verbose=True)
            To move the table "test_table" from the schema "public" to "test_schema"
            ? [No]|Yes: yes
            Moving "public"."test_table" to "test_schema" ... Done.

            >>> lst_tbl_names = testdb.get_table_names(schema_name='test_schema')
            >>> lst_tbl_names
            ['test_table']

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        table_name_ = '"{}"."{}"'.format(schema_name, table_name)

        cfm_msg = f"To move the table \"{table_name}\" " \
                  f"from the schema \"{schema_name}\" to \"{new_schema_name}\"\n?"

        if confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):

            if not self.schema_exists(schema_name=new_schema_name):
                self.create_schema(schema_name=new_schema_name, verbose=verbose)

            if verbose:
                if confirmation_required:
                    log_msg = "Moving {} to \"{}\"".format(table_name_, new_schema_name)
                else:
                    log_msg = "Moving the table \"{}\" from \"{}\" to \"{}\"".format(
                        table_name, schema_name, new_schema_name)
                print(log_msg, end=" ... ")

            try:
                self.engine.execute(
                    'ALTER TABLE {} SET SCHEMA "{}";'.format(table_name_, new_schema_name))

                if verbose:
                    print("Done.")

            except Exception as e:
                print("Failed. {}".format(e))

    def null_text_to_empty_string(self, table_name, column_names=None, schema_name=None):
        """
        Convert null values (in text columns) to empty strings.

        :param table_name: name of a table
        :type table_name: str
        :param column_names: (list of) column name(s);
            when ``column_names=None`` (default), all available columns are included
        :type column_names: str or list or None
        :param schema_name: name of a schema
        :type schema_name: str

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> from pyhelpers._cache import example_dataframe

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> dat = example_dataframe()
            >>> dat.Longitude = dat.Longitude.astype(str)
            >>> dat.loc['London', 'Longitude'] = None
            >>> dat
                         Longitude   Latitude
            City
            London            None  51.507322
            Birmingham  -1.9026911  52.479699
            Manchester  -2.2451148  53.479489
            Leeds       -1.5437941  53.797418

            >>> tbl_name = 'test_table'

            >>> testdb.import_data(data=dat, table_name=tbl_name, index=True, verbose=True)
            To import data into "public"."test_table" at postgres:***@localhost:5432/postgres
            ? [No]|Yes: yes

            >>> testdb.table_exists(table_name=tbl_name)
            True

            >>> testdb.get_column_dtype(table_name=tbl_name)
            {'City': 'text', 'Longitude': 'text', 'Latitude': 'double precision'}

        .. figure:: ../_images/dbms-postgresql-null_text_to_empty_string-demo-1.*
            :name: dbms-postgresql-null_text_to_empty_string-demo-1
            :align: center
            :width: 55%

            The table "*test_table*" in the database "*testdb*".

        .. code-block:: python

            >>> # Replace the 'null' value with an empty string
            >>> testdb.null_text_to_empty_string(table_name=tbl_name)

        .. figure:: ../_images/dbms-postgresql-null_text_to_empty_string-demo-2.*
            :name: dbms-postgresql-null_text_to_empty_string-demo-2
            :align: center
            :width: 55%

            The table "*test_table*" in the database "*testdb*"
            (after converting 'null' to empty string).

        .. code-block:: python

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        column_dtypes = self.get_column_dtype(
            table_name=table_name, column_names=column_names, schema_name=schema_name)
        text_columns = [k for k, v in column_dtypes.items() if v == 'text']

        if len(text_columns) > 0:
            tbl = self._table_name(table_name=table_name, schema_name=schema_name)
            cols_query = ', '.join(f'"{x}"=COALESCE("{x}", \'\')' for x in text_columns)

            self.engine.execute(f'UPDATE {tbl} SET {cols_query};')

    def add_primary_keys(self, primary_keys, table_name, schema_name=None):
        """
        Add a primary key or multiple primary keys to a table.

        :param primary_keys: (list of) primary key(s)
        :type primary_keys: str or list or None
        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``None``
        :type schema_name: str or None

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.PostgreSQL.get_primary_keys`.
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        if primary_keys is not None:
            # If any null values in 'text' columns, replace null values with empty strings
            self.null_text_to_empty_string(
                table_name=table_name, column_names=primary_keys, schema_name=schema_name)

            pri_keys = [primary_keys] if isinstance(primary_keys, str) else copy.copy(primary_keys)

            if len(pri_keys) == 1:
                primary_keys_ = '("{}")'.format(pri_keys[0])
            else:
                primary_keys_ = str(tuple(pri_keys)).replace("'", '"')

            self.engine.execute(f'ALTER TABLE {table_name_} ADD PRIMARY KEY {primary_keys_};')

    def get_primary_keys(self, table_name, schema_name=None, names_only=True):
        """
        Get the primary keys of a table.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``None``
        :type schema_name: str or None
        :param names_only: whether to return only the names of the primary keys, defaults to ``True``
        :type names_only: bool
        :return: primary key(s) of the given table
        :rtype: list or pandas.DataFrame

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> from pyhelpers._cache import example_dataframe

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> dat = example_dataframe()
            >>> dat
                        Longitude   Latitude
            City
            London      -0.127647  51.507322
            Birmingham  -1.902691  52.479699
            Manchester  -2.245115  53.479489
            Leeds       -1.543794  53.797418

            >>> tbl_name = 'test_table'

            >>> testdb.import_data(data=dat, table_name=tbl_name, index=True, verbose=True)
            To import data into "public"."test_table" at postgres:***@localhost:5432/postgres
            ? [No]|Yes: yes

            >>> pri_keys = testdb.get_primary_keys(table_name=tbl_name)
            >>> pri_keys
            []

            >>> testdb.add_primary_keys(primary_keys='City', table_name=tbl_name)

        The "*test_table*" is illustrated in :numref:`dbms-postgresql-get_primary_keys-demo` below:

        .. figure:: ../_images/dbms-postgresql-get_primary_keys-demo.*
            :name: dbms-postgresql-get_primary_keys-demo
            :align: center
            :width: 55%

            The table "*test_table*" (with a primary key) in the database.

        .. code-block:: python

            >>> pri_keys = testdb.get_primary_keys(table_name=tbl_name)
            >>> pri_keys
            ['City']
            >>> pri_keys = testdb.get_primary_keys(table_name=tbl_name, names_only=False)
            >>> pri_keys
              key_column data_type
            0       City      text

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        postgres_query = \
            f"SELECT a.attname AS key_column, format_type(a.atttypid, a.atttypmod) AS data_type " \
            f"FROM pg_index i " \
            f"JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) " \
            f"WHERE i.indrelid = '{table_name_}'::regclass AND i.indisprimary;"

        result = self.engine.execute(postgres_query)
        primary_keys_ = result.fetchall()

        if names_only:
            primary_keys = [x[0] for x in primary_keys_]  # list(zip(*primary_keys_))[0]
        else:
            primary_keys = pd.DataFrame(primary_keys_)

        return primary_keys

    def drop_table(self, table_name, schema_name=None, confirmation_required=True, verbose=False):
        """
        Delete/drop a table.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :type schema_name: str or None
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.PostgreSQL.create_table`.
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        if not self.table_exists(table_name=table_name, schema_name=schema_name):
            if verbose:
                print("The table {} does not exist.".format(table_name_))

        else:
            if confirmed("To drop the table {} from {}\n?".format(table_name_, self.address),
                         confirmation_required=confirmation_required):

                if verbose:
                    if confirmation_required:
                        log_msg = "Dropping {}".format(table_name_)
                    else:
                        log_msg = "Dropping the table {} from {}".format(table_name_, self.address)
                    print(log_msg, end=" ... ")

                try:
                    self.engine.execute('DROP TABLE {} CASCADE;'.format(table_name_))

                    if verbose:
                        print("Done.")

                except Exception as e:
                    print("Failed. {}".format(e))

    @staticmethod
    def psql_insert_copy(sql_table, sql_db_engine, column_names, data_iter):
        """
        A callable using PostgreSQL COPY clause for executing inserting data.

        :param sql_table: pandas.io.sql.SQLTable
        :param sql_db_engine: `sqlalchemy.engine.Connection`_ or `sqlalchemy.engine.Engine`_
        :param column_names: (list of str) column names
        :param data_iter: iterable that iterates the values to be inserted

        .. _`sqlalchemy.engine.Connection`:
            https://docs.sqlalchemy.org/en/13/core/connections.html#sqlalchemy.engine.Connection
        .. _`sqlalchemy.engine.Engine`:
            https://docs.sqlalchemy.org/en/13/core/connections.html#sqlalchemy.engine.Engine

        .. note::

            This function is copied and slightly modified from the source code available at
            [`DBMS-PS-PIC-1
            <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method>`_].
        """

        con_cur = sql_db_engine.connection.cursor()
        io_buffer = io.StringIO()
        csv_writer = csv.writer(io_buffer)
        csv_writer.writerows(data_iter)
        io_buffer.seek(0)

        sql_column_names = ', '.join('"{}"'.format(k) for k in column_names)
        sql_table_name = '"{}"."{}"'.format(sql_table.schema, sql_table.name)

        sql_query = 'COPY {} ({}) FROM STDIN WITH CSV'.format(sql_table_name, sql_column_names)
        con_cur.copy_expert(sql=sql_query, file=io_buffer)

    def import_data(self, data, table_name, schema_name=None, if_exists='fail',
                    force_replace=False, chunk_size=None, col_type=None, method='multi',
                    index=False, confirmation_required=True, verbose=False, **kwargs):
        """
        Import tabular data into a table.

        See also [`DBMS-PS-ID-1
        <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method/>`_]
        and [`DBMS-PS-ID-2
        <https://www.postgresql.org/docs/current/sql-copy.html/>`_].

        :param data: tabular data to be dumped into a database
        :type data: pandas.DataFrame or pandas.io.parsers.TextFileReader or list or tuple
        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :type schema_name: str
        :param if_exists: if the table already exists, to ``'replace'``, ``'append'``
            or, by default, ``'fail'`` and do nothing but raise a ValueError.
        :type if_exists: str
        :param force_replace: whether to force replacing existing table, defaults to ``False``
        :type force_replace: bool
        :param chunk_size: the number of rows in each batch to be written at a time, defaults to ``None``
        :type chunk_size: int or None
        :param col_type: data types for columns, defaults to ``None``
        :type col_type: dict or None
        :param method: method for SQL insertion clause, defaults to ``'multi'``

            - ``None``: uses standard SQL ``INSERT`` clause (one per row);
            - ``'multi'``: pass multiple values in a single ``INSERT`` clause;
            - callable (e.g. ``PostgreSQL.psql_insert_copy``)
              with signature ``(pd_table, conn, keys, data_iter)``.

        :type method: str or None or typing.Callable
        :param index: whether to dump the index as a column
        :type index: bool
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int
        :param kwargs: [optional] parameters of `pandas.DataFrame.to_sql`_

        .. _`pandas.DataFrame.to_sql`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.PostgreSQL.read_sql_query`.
        """

        _import_data(
            self, data, table_name, schema_name=schema_name, if_exists=if_exists,
            force_replace=force_replace, chunk_size=chunk_size, col_type=col_type, method=method,
            index=index, confirmation_required=confirmation_required, verbose=verbose, **kwargs)

    def read_sql_query(self, sql_query, method='tempfile', max_size_spooled=1, delimiter=',',
                       tempfile_kwargs=None, stringio_kwargs=None, **kwargs):
        """
        Read table data by SQL query (recommended for large table).

        See also
        [`DBMS-PS-RSQ-1 <https://towardsdatascience.com/f31cd7f707ab>`_],
        [`DBMS-PS-RSQ-2 <https://docs.python.org/3/library/tempfile.html>`_] and
        [`DBMS-PS-RSQ-3 <https://docs.python.org/3/library/io.html>`_].

        :param sql_query: a SQL query to be executed
        :type sql_query: str

        :param method: method to be used for buffering temporary data

            - ``'tempfile'`` (default): use `tempfile.TemporaryFile`_
            - ``'stringio'``: use `io.StringIO`_
            - ``'spooled'``: use `tempfile.SpooledTemporaryFile`_

        :type method: str

        :param max_size_spooled: ``max_size`` of `tempfile.SpooledTemporaryFile`_,
            defaults to ``1`` (in gigabyte)
        :type max_size_spooled: int or float
        :param delimiter: delimiter used in data, defaults to ``','``
        :type delimiter: str
        :param tempfile_kwargs: [optional] parameters of `tempfile.TemporaryFile`_
            or `tempfile.SpooledTemporaryFile`_
        :type tempfile_kwargs: dict or None
        :param stringio_kwargs: [optional] parameters of `io.StringIO`_,
            e.g. ``initial_value`` (default: ``''``)
        :type stringio_kwargs: dict or None
        :param kwargs: [optional] parameters of `pandas.read_csv`_
        :return: data frame as queried by the statement ``sql_query``
        :rtype: pandas.DataFrame

        .. _`pandas.read_csv`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html
        .. _`tempfile.TemporaryFile`:
            https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryFile
        .. _`tempfile.SpooledTemporaryFile`:
            https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile
        .. _`io.StringIO`:
            https://docs.python.org/3/library/io.html#io.StringIO

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> from pyhelpers._cache import example_dataframe

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> # Create an example dataframe
            >>> example_df = example_dataframe()
            >>> example_df
                        Longitude   Latitude
            City
            London      -0.127647  51.507322
            Birmingham  -1.902691  52.479699
            Manchester  -2.245115  53.479489
            Leeds       -1.543794  53.797418

            >>> table = 'England'
            >>> schema = 'points'

            >>> # Import the data into a table named "points"."England"
            >>> testdb.import_data(example_df, table, schema, index=True, verbose=2)
            To import data into "points"."England" at postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Creating a schema: "points" ... Done.
            Importing the data into the table "points"."England" ... Done.

        The table "*points*"."*England*" is illustrated in
        :numref:`dbms-postgresql-get_primary_keys-demo` below:

        .. figure:: ../_images/dbms-postgresql-read_sql_query-demo.*
            :name: dbms-postgresql-read_sql_query-demo
            :align: center
            :width: 80%

            The table "*points*"."*England*" in the database "*testdb*".

        .. code-block:: python

            >>> rslt = testdb.table_exists(table_name=table, schema_name=schema)
            >>> print(f"The table \"{schema}\".\"{table}\" exists? {rslt}.")
            The table "points"."England" exists? True.

            >>> # Retrieve the data using the method .read_table()
            >>> example_df_ret = testdb.read_table(table, schema_name=schema, index_col='City')
            >>> example_df_ret
                        Longitude   Latitude
            City
            London      -0.127647  51.507322
            Birmingham  -1.902691  52.479699
            Manchester  -2.245115  53.479489
            Leeds       -1.543794  53.797418

            >>> # Alternatively, read the data by a SQL query statement
            >>> sql_qry = f'SELECT * FROM "{schema}"."{table}"'
            >>> example_df_ret_alt = testdb.read_sql_query(sql_query=sql_qry, index_col='City')
            >>> example_df_ret_alt
                        Longitude   Latitude
            City
            London      -0.127647  51.507322
            Birmingham  -1.902691  52.479699
            Manchester  -2.245115  53.479489
            Leeds       -1.543794  53.797418

            >>> example_df_ret.equals(example_df_ret_alt)
            True

            >>> # Delete the table "points"."England"
            >>> testdb.drop_table(table_name=table, schema_name=schema, verbose=True)
            To drop the table "points"."England" from postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Dropping "points"."England" ... Done.

            >>> # Delete the schema "points"
            >>> testdb.drop_schema(schema_names=schema, verbose=True)
            To drop the schema "points" from postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Dropping "points" ... Done.

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.

        **Aside**: a brief example of using the parameter ``params`` for `pandas.read_sql
        <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_sql.html>`_

        .. code-block:: python

            import datetime
            import pandas as pd

            sql_qry = 'SELECT * FROM "table_name" '
                      'WHERE "timestamp_column_name" BETWEEN %(ts_start)s AND %(ts_end)s'

            params = {'d_start': datetime.datetime.today(), 'd_end': datetime.datetime.today()}

            data_frame = pd.read_sql(sql=sql_qry, con=testdb.engine, params=params)
        """

        valid_methods = {'tempfile', 'stringio', 'spooled'}
        assert method in valid_methods, f"The argument `method` must be one of {valid_methods}."

        if tempfile_kwargs is None:
            tempfile_kwargs = {}
            # 'mode': 'w+b',
            # 'buffering': -1,
            # 'encoding': None,
            # 'newline': None,
            # 'suffix': None,
            # 'prefix': None,
            # 'dir': None,
            # 'errors': None,

        if method == 'tempfile':  # using tempfile.TemporaryFile
            csv_temp = tempfile.TemporaryFile(**tempfile_kwargs)

        elif method == 'stringio':  # using io.StringIO
            if stringio_kwargs is None:
                stringio_kwargs = {}

            stringio_kwargs.update({'initial_value': '', 'newline': '\n'})
            csv_temp = io.StringIO(**stringio_kwargs)

        else:  # method == 'spooled': using tempfile.SpooledTemporaryFile
            # Data would be spooled in memory until its size > max_spooled_size
            tempfile_kwargs.update({'max_size': max_size_spooled * 10 ** 9})
            csv_temp = tempfile.SpooledTemporaryFile(**tempfile_kwargs)

        # Specify the SQL query for "COPY"
        copy_sql = "COPY ({query}) TO STDOUT WITH DELIMITER '{delimiter}' CSV HEADER;".format(
            query=sql_query, delimiter=delimiter)

        # Get a cursor
        connection = self.engine.raw_connection()
        cursor = connection.cursor()
        cursor.copy_expert(copy_sql, csv_temp)

        csv_temp.seek(0)  # Rewind the file handle using seek() in order to read the data back from it

        table_data = pd.read_csv(csv_temp, **kwargs)  # Read data from temporary csv

        csv_temp.close()  # Close the temp file
        cursor.close()  # Close the cursor
        connection.close()  # Close the connection

        return table_data

    def _unique_rsq_args(self):
        """
        Get names of arguments that are exclusive to the method
        :py:meth:`~pyhelpers.dbms.PostgreSQL.read_sql_query`.

        :return: names of arguments exclusive to :py:meth:`~pyhelpers.dbms.PostgreSQL.read_sql_query`
        :rtype: dict
        """

        rsq_args = map(lambda x: inspect.getfullargspec(x).args, (self.read_sql_query, pd.read_csv))
        rsq_args_spec = set(itertools.chain(*rsq_args))

        read_sql_args = set(inspect.getfullargspec(func=pd.read_sql).args)

        return rsq_args_spec - read_sql_args

    def read_table(self, table_name, schema_name=None, conditions=None, chunk_size=None, sorted_by=None,
                   **kwargs):
        """
        Read data from a table.

        See also [`DBMS-PS-RT-1 <https://stackoverflow.com/questions/24408557/>`_].

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :type schema_name: str
        :param conditions: defaults to ``None``
        :type conditions: str or None
        :param chunk_size: number of rows to include in each chunk, defaults to ``None``
        :type chunk_size: int or None
        :param sorted_by: name(s) of a column (or columns) by which the retrieved data is sorted,
            defaults to ``None``
        :type sorted_by: str or None
        :param kwargs: [optional] parameters of the method
            :py:meth:`~pyhelpers.dbms.PostgreSQL.read_sql_query` or the function `pandas.read_sql()`_
        :return: data frame from the specified table
        :rtype: pandas.DataFrame

        .. _`pandas.read_sql()`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_sql.html

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.PostgreSQL.read_sql_query`.
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        sql_query = f'SELECT * FROM {table_name_}'
        if conditions:
            assert isinstance(conditions, str), "'condition' must be 'str' type."
            sql_query += (' ' + conditions)

        if bool(set(kwargs.keys()).intersection(self._unique_rsq_args())):
            table_data = self.read_sql_query(sql_query=sql_query, chunksize=chunk_size, **kwargs)
        else:
            table_data = pd.read_sql(sql=sql_query, con=self.engine, chunksize=chunk_size, **kwargs)

        if sorted_by:
            table_data.sort_values(sorted_by, inplace=True, ignore_index=True)

        return table_data


class MSSQL:
    """
    A class for basic communication with `Microsoft SQL Server`_ databases.

    .. _`Microsoft SQL Server`: https://www.microsoft.com/en-gb/sql-server/
    """

    #: Default dialect.
    #: The dialect that SQLAlchemy uses to communicate with Microsoft SQL Server; see also
    #: [`DBMS-MS-1 <https://docs.sqlalchemy.org/en/14/dialects/mssql.html>`_].
    DEFAULT_DIALECT = 'mssql'
    #: Default name of database driver. See also
    #: [`DBMS-MS-2
    #: <https://docs.sqlalchemy.org/dialects/mssql.html#module-sqlalchemy.dialects.mssql.pyodbc>`_].
    DEFAULT_DRIVER = 'pyodbc'
    #: Default ODBC driver.
    DEFAULT_ODBC_DRIVER = 'ODBC Driver 17 for SQL Server'
    #: Default host (server name). Alternatively, ``os.environ['COMPUTERNAME']``
    DEFAULT_HOST = 'localhost'
    #: Default listening port used by Microsoft SQL Server.
    DEFAULT_PORT = 1433
    #: Default username.
    DEFAULT_USERNAME = 'sa'
    #: Default database name.
    DEFAULT_DATABASE = 'master'
    #: Default schema name.
    DEFAULT_SCHEMA = 'dbo'

    def __init__(self, host=None, port=None, username=None, password=None, database_name=None,
                 confirm_db_creation=False, verbose=True):
        """
        :param host: name of the server running the SQL Server, e.g. ``'localhost'`` or ``'127.0.0.1'``;
            when ``host=None`` (default), it is initialized as ``'localhost'``
        :type host: str or None
        :param port: listening port; when ``port=None`` (default),
            it is initialized as ``1433`` (default by installation of the SQL Server)
        :type port: int or None
        :param username: name of the user or login used to connect; when ``username=None`` (default),
            the instantiation relies on Windows Authentication
        :type username: str or None
        :param password: user's password; when ``password=None`` (default),
            it is required to mannually type in the correct password to connect the PostgreSQL server
        :type password: str or int or None
        :param database_name: name of a database; when ``database=None`` (default),
            it is initialized as ``'master'``
        :type database_name: str or None
        :param confirm_db_creation: whether to prompt a confirmation before creating a new database
            (if the specified database does not exist), defaults to ``False``
        :type confirm_db_creation: bool
        :param verbose: whether to print relevant information in console, defaults to ``True``
        :type verbose: bool or int

        :ivar str host: host name/address
        :ivar str port: listening port used by PostgreSQL
        :ivar str username: username
        :ivar str database_name: name of a database
        :ivar dict credentials: basic information about the server/database being connected
        :ivar str or None auth: authentication method (used for establish the connection)
        :ivar str address: representation of the database address
        :ivar sqlalchemy.engine.Engine engine: a `SQLAlchemy`_ connectable engine to a SQL Server;
            see also [`DBMS-MS-3
            <https://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine>`_]

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.address
            '<server_name>@localhost:1433/master'

            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.

            >>> testdb.database_name
            'testdb'

            >>> testdb.drop_database(verbose=True)
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.
        """

        pyodbc_ = _check_dependency(name='pyodbc')

        self.host = copy.copy(self.DEFAULT_HOST) if host is None else str(host)
        self.port = copy.copy(self.DEFAULT_PORT) if port is None else int(port)

        if username is None:
            self.auth = 'Windows Authentication'
            self.username = os.environ['USERDOMAIN'] + '\\' + os.environ['USERNAME']
            pwd = None
        else:
            self.auth = 'SQL Server Authentication'
            self.username = str(username)  # copy.copy(self.DEFAULT_USERNAME)
            if password is None:
                pwd = getpass.getpass(f'Password ({self.username}@{self.host}:{self.port}): ')
            else:
                pwd = str(password)

        self.credentials = {
            'drivername': '+'.join([self.DEFAULT_DIALECT, self.DEFAULT_DRIVER]),
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'database': self.DEFAULT_DATABASE,
        }

        if self.DEFAULT_ODBC_DRIVER not in pyodbc_.drivers():
            self.odbc_driver = [x for x in pyodbc_.drivers() if 'ODBC' in x and 'SQL Server' in x][0]
        else:
            self.odbc_driver = self.DEFAULT_ODBC_DRIVER

        url_query = {'driver': self.odbc_driver}
        if pwd is None:
            url_query.update({'trusted_connection': 'yes'})
            url = sqlalchemy.engine.URL.create(**self.credentials, query=url_query)
        else:
            url = sqlalchemy.engine.URL.create(**self.credentials, password=pwd, query=url_query)

        self.engine = sqlalchemy.create_engine(url=url, isolation_level='AUTOCOMMIT')

        if database_name is None or database_name == self.DEFAULT_DATABASE:
            self.database_name = copy.copy(self.DEFAULT_DATABASE)
            reconnect_db = False
        else:
            self.database_name = self.credentials['database'] = copy.copy(database_name)
            if database_name in self.get_database_names():
                self.engine.url = self.engine.url.set(database=self.database_name)
            else:  # the database doesn't exist
                _create_db(self, confirm_db_creation=confirm_db_creation, verbose=verbose)
            reconnect_db = True

        self.address = re.split(r'://|\?', self.engine.url.render_as_string(hide_password=True))[1]
        if verbose:
            print("Connecting {}".format(self.address), end=" ... ")

        try:
            if reconnect_db:
                self.engine = sqlalchemy.create_engine(url=self.engine.url, isolation_level='AUTOCOMMIT')
            test_conn = self.engine.connect()
            test_conn.close()
            del test_conn
            if verbose:
                print("Successfully.")
        except Exception as e:
            print("Failed. {}".format(e))

    def _database_name(self, database_name=None):
        """
        Format a database name.

        :param database_name: database name as an input, defaults to ``None``
        :type database_name: str or None
        :return: a database name
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql._database_name()
            '[master]'
            >>> mssql._database_name(database_name='testdb')
            '[testdb]'
        """

        db_name = copy.copy(self.database_name) if database_name is None else str(database_name)
        database_name_ = f'[{db_name}]'

        return database_name_

    def _schema_name(self, schema_name=None):
        """
        Get a schema name.

        :param schema_name: schema name as an input, defaults to ``None``
        :type schema_name: str or list or tuple or None
        :return: a schema name
        :rtype: str or list

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql._schema_name()
            'dbo'
            >>> mssql._schema_name(schema_name=('test_schema1', 'test_schema2'))
            ['test_schema1', 'test_schema2']
        """

        if schema_name is None:
            schema_name_ = copy.copy(self.DEFAULT_SCHEMA)
        elif isinstance(schema_name, (list, tuple)):
            schema_name_ = [str(x) for x in schema_name]
        else:
            schema_name_ = str(schema_name)

        return schema_name_

    def _table_name(self, table_name, schema_name=None):
        """
        Get a formatted table name.

        :param table_name: table name as an input
        :type table_name: str
        :param schema_name: schema name as an input, defaults to ``None``
        :type schema_name: str or None
        :return: a formatted table name, which is used in a SQL query statement
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql._table_name(table_name='test_table')
            '[dbo].[test_table]'
            >>> mssql._table_name(table_name='test_table', schema_name='test_schema')
            '[test_schema].[test_table]'
        """

        schema_name_ = self._schema_name(schema_name=schema_name)
        table_name_ = f'[{schema_name_}].[{table_name}]'

        return table_name_

    def specify_conn_str(self, database_name=None, auth=None, password=None):
        """
        Specify a string used for establishing a connection.

        :param database_name: name of a database,
            defaults to the name of the currently-connected database when ``database=None``
        :type database_name: str or None
        :param auth: authentication method (used for establish the connection),
            defaults to the current authentication method when ``auth=None``
        :type auth: str or None
        :param password: user's password; when ``password=None`` (default),
            it is required to mannually type in the correct password to connect the PostgreSQL server
        :type password: str or int or None
        :return: connection string
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> conn_str = mssql.specify_conn_str()
            >>> conn_str
            'DRIVER={ODBC Driver 17 for SQL Server};SERVER={localhost};DATABASE={master};Trusted_...
        """

        # mssql+pyodbc://<username>:<password>@<dsnname>
        db_name = copy.copy(self.database_name) if database_name is None else copy.copy(database_name)

        conn_string = f'DRIVER={{{self.odbc_driver}}};SERVER={{{self.host}}};DATABASE={{{db_name}}};'

        if auth in {None, 'Windows Authentication'}:
            # The trusted_connection setting indicates whether to use Windows Authentication Mode for
            # login validation or not. This specifies the user used to establish this connection.
            # In Microsoft implementations, this user account is a Windows user account.
            conn_string += 'Trusted_Connection=yes;'
        else:  # e.g. auth = 'SQL Server Authentication'
            if password is None:
                pwd = getpass.getpass(f'Password ({self.username}@{self.host}): ')
            else:
                pwd = str(password)
            conn_string += f'UID={{{self.username}}};PWD={{{pwd}}};'

        return conn_string

    def create_engine(self, database_name=None, auth=None, password=None):
        """
        Create a `SQLAlchemy <https://www.sqlalchemy.org/>`_ connectable engine.

        Connect string format: '*mssql+pyodbc://<username>:<password>@<dsn_name>*'

        :param database_name: name of a database,
            defaults to the name of the currently-connected database when ``database=None``
        :type database_name: str or None
        :param auth: authentication method (used for establish the connection),
            defaults to the current authentication method when ``auth=None``
        :type auth: str or None
        :param password: user's password; when ``password=None`` (default),
            it is required to manually type in the correct password to connect the PostgreSQL server
        :type password: str or int or None
        :return: a SQLAlchemy connectable engine
        :rtype: sqlalchemy.engine.Engine

        1. Use `pyodbc <https://pypi.org/project/pyodbc/>`_ (or
           `pypyodbc <https://pypi.org/project/pypyodbc/>`_)::

            connect_string = 'driver={...};server=...;database=...;uid=username;pwd=...'
            conn = pyodbc.connect(connect_string)  # conn = pypyodbc.connect(connect_string)

        2. Use `SQLAlchemy`_::

            conn_string = 'mssql+pyodbc:///?odbc_connect=%s' % quote_plus(connect_string)
            engine = sqlalchemy.create_engine(conn_string)
            conn = engine.connect()

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> db_engine = mssql.create_engine()
            >>> db_engine.name
            'mssql'

            >>> db_engine.dispose()
        """

        conn_string = self.specify_conn_str(database_name=database_name, auth=auth, password=password)

        url = sqlalchemy.engine.URL.create(
            drivername=f'{self.DEFAULT_DIALECT}+{self.DEFAULT_DRIVER}',
            query={'odbc_connect': conn_string})

        engine = sqlalchemy.create_engine(url=url, isolation_level='AUTOCOMMIT')

        return engine

    def create_connection(self, database_name=None, close_with_result=False, mode=None):
        """
        Create a SQLAlchemy connection.

        :param database_name: name of a database,
            defaults to the name of the currently-connected database when ``database=None``
        :type database_name: str or None
        :param close_with_result: parameter of the method `sqlalchemy.engine.Engine.connect()`_,
            defaults to ``False``
        :type close_with_result: bool
        :param mode: when ``mode=None`` (default), the method uses the existing engine;
            when ``mode='pyodbc'`` (optional), it uses `pyodbc.connect()`_
        :type mode: None or str
        :return: a SQLAlchemy connection to a Microsoft SQL Server
        :rtype: sqlalchemy.engine.Connection or pyodbc.Connection

        .. _`sqlalchemy.engine.Engine.connect()`:
            https://docs.sqlalchemy.org/en/14/core/connections.html#sqlalchemy.engine.Engine.connect
        .. _`pyodbc.connect()`: https://github.com/mkleehammer/pyodbc/wiki/The-pyodbc-Module#connect

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> db_conn = mssql.create_connection()
            >>> db_conn.should_close_with_result
            False
            >>> db_conn.closed
            False
            >>> rslt = db_conn.execute('SELECT 1')
            >>> rslt.fetchall()
            [(1,)]
            >>> db_conn.closed
            False
            >>> db_conn.close()
            >>> db_conn.closed
            True

            >>> db_conn = mssql.create_connection(close_with_result=True)
            >>> db_conn.should_close_with_result
            True
            >>> db_conn.closed
            False
            >>> rslt = db_conn.execute('SELECT 1')
            >>> rslt.fetchall()
            [(1,)]
            >>> db_conn.closed
            True
        """

        if mode is None:  # (default)
            engine = self.create_engine(database_name=database_name)
            conn = engine.connect(close_with_result=close_with_result)

        else:  # use 'pyodbc'
            pyodbc_ = _check_dependency(name='pyodbc')

            conn_str = self.specify_conn_str(database_name=self.database_name, auth=self.auth)

            conn = pyodbc_.connect(conn_str)

        return conn

    def create_cursor(self, database_name=None):
        """
        Create a `pyodbc <https://pypi.org/project/pyodbc/>`_ cursor.

        :param database_name: name of a database,
            defaults to the name of the currently-connected database when ``database=None``
        :type database_name: str or None
        :return: a `pyodbc`_ cursor
        :rtype: pyodbc.Cursor

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> db_cur = mssql.create_cursor()

            >>> # Get information about all tables in the database [master]
            >>> tables_in_db = db_cur.tables(schema='dbo', tableType='TABLE')
            >>> list(tables_in_db)
            [('master', 'dbo', 'MSreplication_options', 'TABLE', None),
             ('master', 'dbo', 'spt_fallback_db', 'TABLE', None),
             ('master', 'dbo', 'spt_fallback_dev', 'TABLE', None),
             ('master', 'dbo', 'spt_fallback_usg', 'TABLE', None),
             ('master', 'dbo', 'spt_monitor', 'TABLE', None)]

            >>> db_cur.close()
        """

        # noinspection PyBroadException
        try:
            conn = self.create_connection(database_name=database_name, mode='pyodbc')
            cursor = conn.cursor()
        except Exception:
            cursor = self.engine.raw_connection().cursor()

        return cursor

    def get_database_names(self, names_only=True):
        """
        Get names of all existing databases.

        :param names_only: whether to return only the names of the databases, defaults to ``True``
        :type names_only: bool
        :return: names of all existing databases
        :rtype: list or pandas.DataFrame

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_database_names()
            ['master',
             'tempdb',
             'model',
             'msdb']
        """

        conn = self.engine.connect(close_with_result=True)
        rslt = conn.execute('SELECT name, database_id, create_date FROM sys.databases;')

        db_names = rslt.fetchall()
        if names_only:
            database_names = [x[0] for x in db_names]
        else:
            database_names = pd.DataFrame(db_names)

        return database_names

    def database_exists(self, database_name=None):
        """
        Check whether a database exists.

        :param database_name: name of a database, defaults to ``None``
        :type database_name: str or None
        :return: whether the database exists
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.

            >>> # Check whether the database [testdb] exists now
            >>> testdb.database_name
            'testdb'
            >>> testdb.database_exists(database_name='testdb')
            True

            >>> # Delete the database [testdb]
            >>> testdb.drop_database(verbose=True)
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.

            >>> # Check again whether the database [testdb] still exists now
            >>> testdb.database_exists(database_name='testdb')
            False
            >>> testdb.database_name
            'master'
        """

        db_name = copy.copy(self.database_name) if database_name is None else str(database_name)

        # noinspection PyBroadException
        try:
            rslt = self.engine.execute(
                f"IF (EXISTS (SELECT name FROM master.sys.databases WHERE name='{db_name}')) "
                f"SELECT 1 ELSE SELECT 0")
        except Exception:
            rslt = self.engine.execute(
                f"SELECT COUNT(*) FROM master.sys.databases "
                f"WHERE '[' + name + ']' = '{db_name}' OR name = '{db_name}';")

        result = bool(rslt.fetchone()[0])

        return result

    def connect_database(self, database_name=None, verbose=False):
        """
        Establish a connection to a database.

        :param database_name: name of a database;
            when ``database_name=None`` (default), the database name is input manually
        :type database_name: str or None
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.

            >>> testdb.connect_database(verbose=True)
            Being connected with <server_name>@localhost:1433/testdb.

            >>> testdb.connect_database(database_name='master', verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> testdb.database_name
            'master'

            >>> testdb.connect_database(database_name='testdb', verbose=True)
            Connecting <server_name>@localhost:1433/testdb ... Successfully.
            >>> testdb.database_name
            'testdb'

            >>> testdb.drop_database(verbose=True)  # Delete the database [testdb]
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.
            >>> testdb.database_name
            'master'
        """

        if database_name is not None:
            self.database_name = str(database_name)

            self.credentials.update({'database': self.database_name})

            url_query = {'driver': self.odbc_driver}
            if self.auth == 'Windows Authentication':
                url_query.update({'Trusted_Connection': 'yes'})

            url = sqlalchemy.engine.URL.create(**self.credentials, query=url_query)
            self.address = re.split(r'://|\?', url.render_as_string(hide_password=True))[1]

            if verbose:
                print(f"Connecting {self.address}", end=" ... ")

            try:
                if not self.database_exists(self.database_name):
                    self.create_database(database_name=self.database_name)

                self.engine = sqlalchemy.create_engine(url=url, isolation_level='AUTOCOMMIT')

                if verbose:
                    print("Successfully.")

            except Exception as e:
                print("Failed. {}".format(e))

        else:
            if verbose:
                print(f"Being connected with {self.address}.")

    def create_database(self, database_name, verbose=False):
        """
        Create a database.

        :param database_name: name of a database
        :type database_name: str
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.

            >>> testdb.database_name
            'testdb'

            >>> testdb.create_database(database_name='testdb1', verbose=True)
            Creating a database: [testdb1] ... Done.
            >>> testdb.database_name
            'testdb1'

            >>> # Delete the database [testdb1]
            >>> testdb.drop_database(verbose=True)
            To drop the database [testdb1] from <server_name>@localhost:5432
            ? [No]|Yes: yes
            Dropping [testdb1] ... Done.
            >>> testdb.database_name
            'master'

            >>> # Delete the database [testdb]
            >>> testdb.drop_database(database_name='testdb', verbose=True)
            To drop the database [testdb] from <server_name>@localhost:5432
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.
            >>> testdb.database_name
            'master'
        """

        _create_database(self, database_name=database_name, verbose=verbose)

    def disconnect_database(self, database_name=None, verbose=False):
        """
        Disconnect a database.

        :param database_name: name of database to disconnect from;
            if ``database_name=None`` (default), disconnect the current database.
        :type database_name: str or None
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.

            >>> testdb.database_name
            'testdb'

            >>> testdb.disconnect_database()
            >>> testdb.database_name
            'master'

            >>> # Delete the database [testdb]
            >>> testdb.drop_database(database_name='testdb', verbose=True)
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.

            >>> testdb.drop_database(database_name='testdb', verbose=True)
            The database [testdb] does not exist.
        """

        db_name = copy.copy(self.database_name) if database_name is None else str(database_name)

        if verbose:
            print("Disconnecting the database \"{}\" ... ".format(db_name), end="")

        try:
            # self.engine.execute(
            #     f'ALTER DATABASE {db_name} SET SINGLE_USER WITH ROLLBACK IMMEDIATE;'
            #     f'ALTER DATABASE {db_name} SET MULTI_USER;')

            self.connect_database(database_name=self.DEFAULT_DATABASE)

            self.engine.execute(
                f"DECLARE @kill varchar(8000) = ''; "
                f"SELECT @kill = @kill + 'kill ' + CONVERT(varchar(5), session_id) + ';' "
                f"FROM sys.dm_exec_sessions WHERE database_id  = db_id('{db_name}') "
                f"EXEC(@kill);")

            if verbose:
                print("Done.")

        except Exception as e:
            print("Failed. {}".format(e))

    def drop_database(self, database_name=None, confirmation_required=True, verbose=False):
        """
        Delete/drop a database.

        :param database_name: database to be disconnected;
            if ``database_name=None`` (default), drop the database being currently currented
        :type database_name: str or None
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.
            >>> testdb.database_name
            'testdb'

            >>> testdb.drop_database(verbose=True)  # Delete the database [testdb]
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.

            >>> testdb.database_exists(database_name='testdb')
            False
            >>> testdb.drop_database(database_name='testdb', verbose=True)
            The database [testdb] does not exist.
            >>> testdb.database_name
            'master'
        """

        _drop_database(
            self, database_name=database_name, confirmation_required=confirmation_required,
            verbose=verbose)

    def schema_exists(self, schema_name):
        """
        Check whether a schema exists.

        :param schema_name: name of a schema in the currently-connected database
        :type schema_name: str
        :return: whether the schema exists
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.

            >>> testdb.schema_exists('dbo')
            True

            >>> testdb.schema_exists('test_schema')  # (if the schema [test_schema] does not exist)
            False

            >>> testdb.drop_database(verbose=True)  # Delete the database [testdb]
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        rslt = self.engine.execute(
            f"IF EXISTS (SELECT name FROM sys.schemas WHERE name='{schema_name_}') "
            f"SELECT 1 ELSE SELECT 0")

        result = bool(rslt.fetchone()[0])

        return result

    def create_schema(self, schema_name, verbose=False):
        """
        Create a schema.

        :param schema_name: name of a schema in the currently-connected database
        :type schema_name: str
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.

            >>> test_schema_name = 'test_schema'

            >>> testdb.create_schema(schema_name=test_schema_name, verbose=True)
            Creating a schema: [test_schema] ... Done.

            >>> testdb.schema_exists(schema_name=test_schema_name)
            True

            >>> testdb.drop_database(verbose=True)  # Delete the database [testdb]
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.
        """

        schema_name_ = self._schema_name(schema_name=schema_name)
        s_name = f'[{schema_name_}]'

        if not self.schema_exists(schema_name=schema_name_):
            if verbose:
                print(f"Creating a schema: {s_name} ... ", end="")

            try:
                self.engine.execute(f'CREATE SCHEMA {s_name};')
                if verbose:
                    print("Done.")
            except Exception as e:
                print("Failed. {}".format(e))

        else:
            print(f"The schema {s_name} already exists.")

    def get_table_names(self, schema_name=None):
        """
        Get names of all tables stored in a schema.

        :param schema_name: name of a schema,
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``
        :type schema_name: str or list or None
        :return: names of tables in the given schema ``mssql_schema_name``
        :rtype: list

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_table_names()
            ['MSreplication_options',
             'spt_fallback_db',
             'spt_fallback_dev',
             'spt_fallback_usg',
             'spt_monitor']

            >>> mssql.get_table_names(schema_name=['dbo', 'sys'])
        """

        inspector = sqlalchemy.inspection.inspect(self.engine)

        schema_name_ = self._schema_name(schema_name=schema_name)
        if isinstance(schema_name_, str):
            table_names = inspector.get_table_names(schema=schema_name_)
        else:
            table_names = [
                (schema, inspector.get_table_names(schema=schema)) for schema in schema_name_]
        return table_names

    def create_table(self, table_name, column_specs, schema_name=None, verbose=False):
        """
        Create a table.

        :param table_name: name of a table
        :type table_name: str
        :param column_specs: specifications for each column of the table
        :type column_specs: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'dbo'``)
        :type schema_name: str or None
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.

            >>> tbl_name = 'test_table'
            >>> col_spec = 'col_name_1 INT, col_name_2 varchar(255)'

            >>> testdb.create_table(table_name=tbl_name, column_specs=col_spec, verbose=True)
            Creating a table: [dbo].[test_table] ... Done.

            >>> testdb.table_exists(table_name=tbl_name)
            True

            >>> testdb.get_column_names(table_name=tbl_name)
            ['col_name_1', 'col_name_2']

            >>> # Drop the table [dbo].[test_table]
            >>> testdb.drop_table(table_name=tbl_name, verbose=True)
            To drop the table [dbo].[test_table] from <server_name>@localhost:1433/testdb
            ? [No]|Yes: yes
            Dropping [dbo].[test_table] ... Done.

            >>> # Delete the database [testdb]
            >>> testdb.drop_database(verbose=True)
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        if self.table_exists(table_name=table_name, schema_name=schema_name):
            if verbose:
                print(f"The table {table_name_} already exists.")

        else:
            if not self.schema_exists(schema_name):
                self.create_schema(schema_name=schema_name, verbose=False)

            try:
                if verbose:
                    print(f"Creating a table: {table_name_} ... ", end="")

                self.engine.execute(f'CREATE TABLE {table_name_} ({column_specs});')

                if verbose:
                    print("Done.")

            except Exception as e:
                print("Failed. {}".format(e))

    def table_exists(self, table_name, schema_name=None):
        """
        Check whether a table exists.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema,
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``
        :type schema_name: str or None
        :return: whether the table exists in the currently-connected database
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.table_exists(table_name='test_table')
            False

            >>> mssql.get_table_names()
            ['MSreplication_options',
             'spt_fallback_db',
             'spt_fallback_dev',
             'spt_fallback_usg',
             'spt_monitor']

            >>> mssql.table_exists(table_name='MSreplication_options')
            True
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        rslt = self.engine.execute(
            f"IF (EXISTS ("
            f"SELECT * FROM INFORMATION_SCHEMA.TABLES "
            f"WHERE TABLE_SCHEMA = '{schema_name_}' AND TABLE_NAME = '{table_name}'))"
            f"SELECT 1 ELSE SELECT 0")

        result = bool(rslt.fetchone()[0])

        return result

    def get_file_tables(self, names_only=True):
        """
        Get information about *FileTables* (if available).

        :param names_only: whether to return *FileTables* names only, defaults to ``True``
        :type names_only: bool
        :return: information about *FileTables* (if available)
        :rtype: list or pandas.DataFrame

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_file_tables()
            []
        """

        result = self.engine.execute('SELECT * FROM sys.tables WHERE is_filetable = 1;')

        file_tables_ = result.fetchall()
        if names_only:
            file_tables = [x[0] for x in file_tables_]
        else:
            file_tables = pd.DataFrame(file_tables_)

        return file_tables

    def get_row_count(self, table_name, schema_name=None):
        """
        Get row count of a table in a database.

        :param table_name: name of a table in the currently-connected database
        :type table_name: str
        :param schema_name: schema name of the given table, defaults to ``None``
        :type schema_name: str or None
        :return: count of rows in the given table
        :rtype: int

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_table_names()
            ['MSreplication_options',
             'spt_fallback_db',
             'spt_fallback_dev',
             'spt_fallback_usg',
             'spt_monitor']

            >>> mssql.get_row_count(table_name='MSreplication_options')
            3
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        conn = self.engine.connect(close_with_result=True)
        rslt = conn.execute(f'SELECT COUNT(*) FROM {table_name_};')

        row_count = rslt.fetchone()[0]

        return row_count

    def get_column_names(self, table_name, schema_name=None):
        """
        Get column names of a table.

        :param table_name: name of a table in the currently-connected database
        :type table_name: str
        :param schema_name: defaults to ``None``
        :type schema_name: str or None
        :return: a list of column names
        :rtype: list

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_table_names()
            ['MSreplication_options',
             'spt_fallback_db',
             'spt_fallback_dev',
             'spt_fallback_usg',
             'spt_monitor']

            >>> mssql.get_column_names(table_name='MSreplication_options')
            ['optname',
             'value',
             'major_version',
             'minor_version',
             'revision',
             'install_failures']
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        cursor = self.engine.raw_connection().cursor()

        col_names = [x.column_name for x in cursor.columns(table=table_name, schema=schema_name_)]

        cursor.close()

        return col_names

    def get_primary_keys(self, table_name=None, schema_name=None, table_type='TABLE'):
        """
        Get the primary keys of table(s).

        :param table_name: name of a table in the currently-connected database;
             when ``table_name=None`` (default), get the primary keys of all existing tables
        :type table_name: str or None
        :param schema_name: name of a schema,
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``
        :type schema_name: str or None
        :param table_type: table type, defaults to ``'TABLE'``
        :type table_type: str
        :return: a list of primary keys
        :rtype: list

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_primary_keys()
            {}
        """

        try:
            cursor = self.create_cursor(self.database_name)

            schema_name_ = self._schema_name(schema_name=schema_name)
            # noinspection PyArgumentList
            table_names_ = cursor.tables(schema=schema_name_, tableType=table_type)
            table_names = [table.table_name for table in table_names_]  # Get all table names

            # noinspection PyArgumentList
            tbl_pks = [  # Get primary keys for each table
                {k.table_name: k.column_name} for tbl_name in table_names
                for k in cursor.primaryKeys(table=tbl_name)]

            # Close the cursor
            cursor.close()

            # ( Each element of 'tbl_pks' (as a dict) is in the format of {'table_name':'primary key'} )
            tbl_names_set = functools.reduce(operator.or_, (set(d.keys()) for d in tbl_pks), set())
            # Find all primary keys for each table
            tbl_pk_dict = dict((tbl, [d[tbl] for d in tbl_pks if tbl in d]) for tbl in tbl_names_set)

            if table_name:
                tbl_pk_dict = tbl_pk_dict[table_name]

        except KeyError:  # Most likely that the table (i.e. 'table_name') does not have any primary key
            tbl_pk_dict = None

        return tbl_pk_dict

    def _has_dtypes(self, table_name, dtypes, schema_name=None):
        """
        Check whether a table contains data of a certain type.

        :param table_name: name of a table in the currently-connected database
        :type table_name: str
        :param dtypes: data type(s), such as ``'geometry'``, ``'hierarchyid'``, ``'varbinary'``
        :type dtypes: str or list
        :param schema_name: name of a schema,
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``
        :type schema_name: str or None
        :return: whether the table contains any of the given data types, and the names of those tables
        :rtype: tuple[bool, list]

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_table_names()
            ['MSreplication_options',
             'spt_fallback_db',
             'spt_fallback_dev',
             'spt_fallback_usg',
             'spt_monitor']

            >>> mssql._has_dtypes(table_name='MSreplication_options', dtypes='varbinary')
            (False, [])

            >>> mssql._has_dtypes(table_name='MSreplication_options', dtypes=['varbinary', 'int'])
            (True, ['major_version', 'minor_version', 'revision', 'install_failures'])
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        dtype_query = (f"= '{dtypes}'" if isinstance(dtypes, str) else f"IN {tuple(dtypes)}")
        sql_query_geom_col = \
            f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS " \
            f"WHERE TABLE_NAME='{table_name}' AND TABLE_SCHEMA='{schema_name_}' " \
            f"AND DATA_TYPE {dtype_query};"

        col_names = self.engine.execute(sql_query_geom_col).fetchall()

        if len(col_names) > 0:
            has_the_dtypes = True
            col_names = list(itertools.chain.from_iterable(col_names))
        else:
            has_the_dtypes = False

        return has_the_dtypes, col_names

    def has_dtypes(self, table_name, dtypes, schema_name=None):
        """
        Check whether a table contains data of a certain data type or data types.

        :param table_name: name of a table in the currently-connected database
        :type table_name: str
        :param dtypes: data types, such as ``'geometry'``, ``'hierarchyid'``, ``'varbinary'``
        :type dtypes: str or typing.Sequence[str]
        :param schema_name: name of a schema,
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``
        :type schema_name: str or None
        :return: data type, whether the table has this data type and the corresponding column names
        :rtype: typing.Generator[str, bool, list]

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_table_names()
            ['MSreplication_options',
             'spt_fallback_db',
             'spt_fallback_dev',
             'spt_fallback_usg',
             'spt_monitor']

            >>> rslt = mssql.has_dtypes(table_name='spt_monitor', dtypes='varbinary')
            >>> list(rslt)
            [('varbinary', False, [])]

            >>> rslt = mssql.has_dtypes(table_name='spt_monitor', dtypes=['geometry', 'int'])
            >>> list(rslt)
            [('geometry', False, []),
             ('int',
              True,
              ['cpu_busy',
               'io_busy',
               'idle',
               'pack_received',
               'pack_sent',
               'connections',
               'pack_errors',
               'total_read',
               'total_write',
               'total_errors'])]
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        dtypes_ = [dtypes] if isinstance(dtypes, str) else copy.copy(dtypes)

        for data_type in dtypes_:
            sql_query_geom_col = \
                f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS " \
                f"WHERE TABLE_NAME='{table_name}' " \
                f"AND TABLE_SCHEMA='{schema_name_}' " \
                f"AND DATA_TYPE='{data_type}'"

            col_names = self.engine.execute(sql_query_geom_col).fetchall()

            if len(col_names) > 0:
                has_the_dtypes = True
                col_names = list(itertools.chain.from_iterable(col_names))
            else:
                has_the_dtypes = False

            yield data_type, has_the_dtypes, col_names

    def _column_names_in_query(self, table_name, column_names=None, schema_name=None, exclude=None):
        """
        Format column names in a SQL query statement.

        :param table_name: name of a table in the currently-connected database
        :type table_name: str
        :param column_names: a list of column names of the specified table, defaults to ``None``
        :type column_names: list or None
        :param schema_name: name of a schema,
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``
        :type schema_name: str or None
        :param exclude: name(s) of column(s) to be excluded from the specifying the query statement
        :return: formatted column names in a SQL query statement, and a list of target column names
        :rtype: tuple[str, list]

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_table_names()
            ['MSreplication_options',
             'spt_fallback_db',
             'spt_fallback_dev',
             'spt_fallback_usg',
             'spt_monitor']

            >>> mssql._column_names_in_query('MSreplication_options', column_names=['optname'])
            ('[dbo].[optname]',
             ['optname',
              'value',
              'major_version',
              'minor_version',
              'revision',
              'install_failures'])
        """

        if exclude is None:
            exclude = []

        schema_name_ = self._schema_name(schema_name=schema_name)

        # Get a list of column names, excluding the `other_col_names` if any
        column_name_list = self.get_column_names(table_name, schema_name=schema_name_)
        column_names_ = [x for x in column_name_list if x not in exclude]

        # Specify SQL query - read all selected columns
        if column_names is not None:
            col_names_ = [x for x in column_names if x not in exclude]
        else:
            col_names_ = column_names_.copy()

        column_names_in_query = ', '.join(
            f'[{schema_name_}].[{tbl_col_name}]' for tbl_col_name in col_names_)

        return column_names_in_query, column_name_list

    def import_data(self, data, table_name, schema_name=None, if_exists='fail',
                    force_replace=False, chunk_size=None, col_type=None, method='multi',
                    index=False, confirmation_required=True, verbose=False, **kwargs):
        """
        Import tabular data into a table.

        See also [`DBMS-MS-ID-1
        <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method/>`_].

        :param data: tabular data to be dumped into a database
        :type data: pandas.DataFrame or pandas.io.parsers.TextFileReader or list or tuple
        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :type schema_name: str or None
        :param if_exists: if the table already exists, to ``'replace'``, ``'append'``
            or, by default, ``'fail'`` and do nothing but raise a ValueError.
        :type if_exists: str
        :param force_replace: whether to force replacing existing table, defaults to ``False``
        :type force_replace: bool
        :param chunk_size: the number of rows in each batch to be written at a time, defaults to ``None``
        :type chunk_size: int or None
        :param col_type: data types for columns, defaults to ``None``
        :type col_type: dict or None
        :param method: method for SQL insertion clause, defaults to ``'multi'``

            - ``None``: uses standard SQL ``INSERT`` clause (one per row);
            - ``'multi'``: pass multiple values in a single ``INSERT`` clause;
            - callable (e.g. ``PostgreSQL.psql_insert_copy``)
              with signature ``(pd_table, conn, keys, data_iter)``.

        :type method: str or None or typing.Callable
        :param index: whether to dump the index as a column
        :type index: bool
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int
        :param kwargs: [optional] parameters of `pandas.DataFrame.to_sql`_

        .. _`pandas.DataFrame.to_sql`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> from pyhelpers._cache import example_dataframe

            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.

            >>> example_df = example_dataframe()
            >>> example_df
                        Longitude   Latitude
            City
            London      -0.127647  51.507322
            Birmingham  -1.902691  52.479699
            Manchester  -2.245115  53.479489
            Leeds       -1.543794  53.797418

            >>> test_table_name = 'example_df'

            >>> testdb.import_data(example_df, table_name=test_table_name, index=True, verbose=2)
            To import data into [dbo].[example_df] at <server_name>@localhost:1433/testdb
            ? [No]|Yes: yes
            Importing the data into the table [dbo].[example_df] ... Done.

        The imported example data can also be viewed using Microsoft SQL Server Management Studio
        (as illustrated in :numref:`dbms-mssql-import_data-demo` below):

        .. figure:: ../_images/dbms-mssql-import_data-demo.*
            :name: dbms-mssql-import_data-demo
            :align: center
            :width: 90%

            The table *[dbo].[example_df]* in the database *[testdb]*.

        .. code-block:: python

            >>> # Drop/delete the table [dbo].[example_df]
            >>> testdb.drop_table(table_name=test_table_name, verbose=True)
            To drop the table [dbo].[example_df] from <server_name>@localhost:1433/testdb
            ? [No]|Yes: yes
            Dropping [dbo].[example_df] ... Done.

            >>> # Drop/delete the database [testdb]
            >>> testdb.drop_database(verbose=True)
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.MSSQL.read_table`.
        """

        if index is True:
            data.reset_index(inplace=True)

        _import_data(
            self, data=data, table_name=table_name, schema_name=schema_name, if_exists=if_exists,
            force_replace=force_replace, chunk_size=chunk_size, col_type=col_type, method=method,
            index=False, confirmation_required=confirmation_required, verbose=verbose, **kwargs)

    def read_columns(self, table_name, column_names, dtype=None, schema_name=None, chunk_size=None,
                     **kwargs):
        """
        Read data of specific columns of a table.

        :param table_name: name of a table in the currently-connected database
        :type table_name: str
        :param column_names: column name(s) of the specified table
        :type column_names: list or tuple
        :param dtype: data type, defaults to ``None``;
            options include ``'hierarchyid'``, ``'varbinary'`` and ``'geometry'``
        :type dtype: str or None
        :param schema_name: name of a schema,
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``
        :type schema_name: str or None
        :param chunk_size: number of rows to include in each chunk (if specified),
            defaults to ``None``
        :type chunk_size: int or None
        :param kwargs: [optional] parameters of `pandas.read_sql`_
        :return: data of specific columns of the queried table
        :rtype: pandas.DataFrame

        .. _`pandas.read_sql`: https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> from pyhelpers._cache import example_dataframe

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_table_names()
            ['MSreplication_options',
             'spt_fallback_db',
             'spt_fallback_dev',
             'spt_fallback_usg',
             'spt_monitor']

            >>> mssql.read_columns('MSreplication_options', column_names=['optname', 'value'])
                      optname  value
            0   transactional   True
            1           merge   True
            2  security_model   True

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.MSSQL.read_table`.
        """

        col_names = [column_names] if isinstance(column_names, str) else copy.copy(column_names)

        if dtype == 'hierarchyid':
            fmt = 'CONVERT(NVARCHAR(max), CONVERT(VARBINARY(max), [{x}], 1), 1) AS [{x}]'
        elif dtype == 'varbinary':
            fmt = 'CONVERT(VARCHAR(max), [{x}], 2) AS [{x}]'
        elif dtype == 'geometry':
            fmt = '[{x}].STAsText() AS [{x}]'
        else:
            fmt = '[{x}]'
        col_names_ = ', '.join(fmt.format(x=x) for x in col_names)

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        sql_query = f'SELECT {col_names_} FROM {table_name_};'
        data = pd.read_sql(sql=sql_query, con=self.engine, chunksize=chunk_size, **kwargs)

        if chunk_size:
            data = pd.concat(data, ignore_index=True)

        if dtype == 'geometry':
            shapely_wkt = _check_dependency(name='shapely.wkt')

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=DeprecationWarning)
                data.loc[:, col_names] = data[col_names].applymap(shapely_wkt.loads)

        return data

    def read_table(self, table_name, schema_name=None, column_names=None, conditions=None,
                   chunk_size=None, save_as=None, data_dir=None, **kwargs):
        """
        Read data from a table.

        :param table_name: name of a table in the currently-connected database
        :type table_name: str
        :param schema_name: name of a schema,
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``
        :type schema_name: str or None
        :param column_names: column name(s), defaults to all columns when ``column_names=None``
        :type column_names: list or tuple or None
        :param conditions: conditions in a SQL query statement, defaults to ``None``
        :type conditions: str or None
        :param chunk_size: number of rows to include in each chunk (if specified),
            defaults to ``None``
        :type chunk_size: int or None
        :param save_as: file extension (if specified) for saving table data locally, defaults to ``None``
        :type save_as: str or None
        :param data_dir: directory where the table data is to be saved, defaults to ``None``
        :type data_dir: str or None
        :param kwargs: [optional] parameters of `pandas.read_sql`_
        :return: data of the queried table
        :rtype: pandas.DataFrame

        .. _`pandas.read_sql`: https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> from pyhelpers._cache import example_dataframe

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.

            >>> mssql.get_table_names()
            ['MSreplication_options',
             'spt_fallback_db',
             'spt_fallback_dev',
             'spt_fallback_usg',
             'spt_monitor']

            >>> mssql.read_table(table_name='MSreplication_options')
                      optname  value  ...  revision  install_failures
            0   transactional   True  ...         0                 0
            1           merge   True  ...         0                 0
            2  security_model   True  ...         0                 0

            [3 rows x 6 columns]

            >>> mssql.read_table(table_name='MSreplication_options', column_names=['optname'])
                      optname
            0   transactional
            1           merge
            2  security_model

            >>> # Create a new database for testing
            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.

            >>> example_df = example_dataframe()
            >>> example_df
                        Longitude   Latitude
            City
            London      -0.127647  51.507322
            Birmingham  -1.902691  52.479699
            Manchester  -2.245115  53.479489
            Leeds       -1.543794  53.797418

            >>> test_table_name = 'example_df'
            >>> testdb.import_data(example_df, table_name=test_table_name, index=True, verbose=2)
            To import data into [dbo].[example_df] at <server_name>@localhost:1433/testdb
            ? [No]|Yes: yes
            Importing the data into the table [dbo].[example_df] ... Done.

            >>> # Retrieve the imported data
            >>> example_df_ret = testdb.read_table(table_name=test_table_name, index_col='City')
            >>> example_df_ret
                        Longitude   Latitude
            City
            London      -0.127647  51.507322
            Birmingham  -1.902691  52.479699
            Manchester  -2.245115  53.479489
            Leeds       -1.543794  53.797418

            >>> # Drop/Delete the testing database [testdb]
            >>> testdb.drop_database(verbose=True)
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.MSSQL.import_data`.
        """

        if column_names is None:
            column_names_ = self.get_column_names(table_name=table_name, schema_name=schema_name)
        else:
            column_names_ = list(column_names)

        check_dtypes = ['hierarchyid', 'varbinary', 'geometry']
        check_dtypes_rslt = self.has_dtypes(table_name, dtypes=check_dtypes)

        solo_column_names = []
        column_names_in_query = column_names_.copy()
        for dtype, if_exists, col_names in check_dtypes_rslt:
            if if_exists:
                if dtype == 'hierarchyid':
                    fmt = 'CONVERT(NVARCHAR(max), CONVERT(VARBINARY(max), [{x}], 1), 1) AS [{x}]'
                elif dtype == 'varbinary':
                    fmt = 'CONVERT(VARCHAR(max), [{x}], 2) AS [{x}]'
                elif dtype == 'geometry':
                    fmt = '[{x}].STAsText() AS [{x}]'
                else:
                    fmt = '[{x}]'
                col_names_ = ', '.join(fmt.format(x=x) for x in col_names)

                solo_column_names.append(col_names_)
                column_names_in_query = list(set(column_names_in_query) - set(col_names))

        column_names_in_query = ', '.join([f'[{x}]' for x in column_names_in_query] + solo_column_names)

        # Specify a SQL query statement
        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)
        sql_query = f'SELECT {column_names_in_query} FROM {table_name_};'

        if conditions:
            sql_query = sql_query.replace(';', ' ') + conditions + ';'

        data = pd.read_sql(sql=sql_query, con=self.engine, chunksize=chunk_size, **kwargs)

        if chunk_size:
            data = pd.concat(objs=data, axis=0, ignore_index=True)

        # Sort the order of columns
        data = data[[x for x in column_names_ if x not in data.index.names]]

        if save_as:
            data_dir_ = validate_dir(data_dir)
            path_to_file = cd(data_dir_, table_name + save_as)
            save_data(data, path_to_file)

        return data

    def drop_table(self, table_name, schema_name=None, confirmation_required=True, verbose=False):
        """
        Delete/drop a table.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'dbo'``)
        :type schema_name: str or None
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool or int

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.MSSQL.create_table`.
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        if not self.table_exists(table_name=table_name, schema_name=schema_name):
            if verbose:
                print("The table {} does not exist.".format(table_name_))

        else:
            if confirmed("To drop the table {} from {}\n?".format(table_name_, self.address),
                         confirmation_required=confirmation_required):

                if verbose:
                    if confirmation_required:
                        log_msg = "Dropping {}".format(table_name_)
                    else:
                        log_msg = "Dropping the table {} from {}".format(table_name_, self.address)
                    print(log_msg, end=" ... ")

                try:
                    self.engine.execute(f'DROP TABLE {table_name_};')

                    if verbose:
                        print("Done.")

                except Exception as e:
                    print("Failed. {}".format(e))


""" == Database tools/utilities ================================================================ """


def make_database_address(host, port, username, database_name=""):
    """
    Make a string of a database address.

    :param host: host name/address of a PostgreSQL server
    :type host: str
    :param port: listening port used by PostgreSQL
    :type port: int or str
    :param username: username of a PostgreSQL server
    :type username: str
    :param database_name: name of a database, defaults to ``""``
    :type database_name: str or None
    :return: address of a database
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dbms import make_database_address

        >>> db_addr = make_database_address('localhost', 5432, 'postgres', 'postgres')
        >>> db_addr
        'postgres:***@localhost:5432/postgres'
    """

    database_address = f"{username}:***@{host}:{port}"

    if database_name:
        database_address += f"/{database_name}"

    return database_address


def get_default_database_address(db_cls):
    """
    Get default database address of a given class in the current module.

    :param db_cls: a class representation of a database
    :type db_cls: object
    :return: default address of database
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dbms import get_default_database_address, PostgreSQL

        >>> db_addr = get_default_database_address(db_cls=PostgreSQL)
        >>> db_addr
        'None:***@None:None'
    """

    args_spec = inspect.getfullargspec(func=db_cls)

    args_dict = dict(zip([x for x in args_spec.args if x != 'self'], args_spec.defaults))

    database_address = make_database_address(
        args_dict['host'], args_dict['port'], args_dict['username'], args_dict['database_name'])

    return database_address


def mssql_to_postgresql(mssql, postgres, mssql_schema=None, postgres_schema=None, chunk_size=None,
                        excluded_tables=None, file_tables=False, memory_threshold=2., update=False,
                        confirmation_required=True, verbose=True):
    """
    Copy tables of a database from a Microsoft SQL server to a PostgreSQL server.

    :param mssql: name of a Microsoft SQL (source) database
    :type mssql: pyhelpers.dbms.MSSQL
    :param postgres: name of a PostgreSQL (destination) database
    :type postgres: pyhelpers.dbms.PostgreSQL
    :param mssql_schema: name of a schema to be migrated from the SQl Server
    :type mssql_schema: str or None
    :param postgres_schema: name of a schema to store the migrated data in the PostgreSQL server
    :type postgres_schema: str or None
    :param chunk_size: number of rows in each batch to be read/written at a time, defaults to ``None``
    :type chunk_size: int or None
    :param excluded_tables: names of tables that are excluded from the data migration
    :type excluded_tables: list or None
    :param file_tables: whether to include FileTables, defaults to ``False``
    :type file_tables: bool
    :param memory_threshold: threshold (in GiB) beyond which the data is migrated by partitions,
        defaults to ``2.``
    :type memory_threshold: float or int
    :param update: whether to redo the transfer between the database servers, defaults to ``False``
    :type update: bool
    :param confirmation_required: whether asking for confirmation to proceed, defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information, defaults to ``True``
    :type verbose: bool or int

    **Examples**::

        >>> from pyhelpers.dbms import mssql_to_postgresql, PostgreSQL, MSSQL
        >>> from pyhelpers._cache import example_dataframe

        >>> # Connect/create a PostgreSQL database, which is named [testdb]
        >>> mssql_testdb = MSSQL(database_name='testdb')
        Creating a database: [testdb] ... Done.
        Connecting <server_name>@localhost:1433/testdb ... Successfully.

        >>> mssql_testdb.database_name
        'testdb'

        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> test_table_name = 'example_df'

        >>> # Import the example dataframe into a table named [example_df]
        >>> mssql_testdb.import_data(example_df, table_name=test_table_name, index=True, verbose=2)
        To import data into [dbo].[example_df] at <server_name>@localhost:1433/testdb
        ? [No]|Yes: yes
        Importing the data into the table [dbo].[example_df] ... Done.

        >>> mssql_testdb.get_column_names(table_name=test_table_name)
        ['City', 'Longitude', 'Latitude']

    .. figure:: ../_images/dbms-mssql_to_postgresql-demo-1.*
        :name: dbms-mssql_to_postgresql-demo-1
        :align: center
        :width: 90%

        The table *[dbo].[example_df]* in the Microsoft SQL Server database *[testdb]*.

    .. code-block:: python

        >>> # Create an instance for a PostgreSQL database, which is also named "testdb"
        >>> postgres_testdb = PostgreSQL(database_name='testdb')
        Password (postgres@localhost:5432): ***
        Creating a database: "testdb" ... Done.
        Connecting postgres:***@localhost:5432/testdb ... Successfully.

        >>> # For now, the newly-created database doesn't contain any tables
        >>> postgres_testdb.get_table_names()
        []

        >>> # Copy the example data from the SQL Server to the PostgreSQL "testdb" (under "public")
        >>> mssql_to_postgresql(mssql=mssql_testdb, postgres=postgres_testdb)
        To copy tables from [testdb] (MSSQL) to "testdb" (PostgreSQL)
        ? [No]|Yes: yes
        Processing tables ...
            (1/1) Copying [dbo].[example_df] to "public"."example_df" ... Done.
        Completed.

        >>> postgres_testdb.get_table_names()
        ['example_df']

    .. figure:: ../_images/dbms-mssql_to_postgresql-demo-2.*
        :name: dbms-mssql_to_postgresql-demo-2
        :align: center
        :width: 90%

        The table *"dbo"."example_df"* in the PostgreSQL database *"testdb"*.

    .. code-block:: python

        >>> # Drop/delete the created databases
        >>> mssql_testdb.drop_database(verbose=True)
        To drop the database [testdb] from <server_name>@localhost:1433
        ? [No]|Yes: yes
        Dropping [testdb] ... Done.

        >>> postgres_testdb.drop_database(verbose=True)
        To drop the database "testdb" from postgres:***@localhost:5432
        ? [No]|Yes: yes
        Dropping "testdb" ... Done.
    """

    task_msg = f'from [{mssql.database_name}] (MSSQL) to "{postgres.database_name}" (PostgreSQL)'

    if confirmed(f'To copy tables {task_msg}\n?', confirmation_required=confirmation_required):

        # MSSQL
        mssql_schema_name = mssql._schema_name(schema_name=mssql_schema)
        mssql_table_names = mssql.get_table_names(schema_name=mssql_schema_name)

        # PostgreSQL
        postgres_schema_name = postgres.DEFAULT_SCHEMA if postgres_schema is None else postgres_schema

        if verbose:
            if confirmation_required:
                print("Processing tables ... ")
            else:
                print(f"Copying tables {task_msg} ... ")

        excl_tbl_names = [] if excluded_tables is None else copy.copy(excluded_tables)

        if not file_tables:
            file_table_names = mssql.get_file_tables()
            excl_tbl_names += file_table_names

        mssql_table_names = [x for x in mssql_table_names if x not in excl_tbl_names]

        table_counter, table_total = 1, len(mssql_table_names)
        error_log = {}
        for mssql_table_name in mssql_table_names:
            counter_msg = f"({table_counter}/{table_total})"

            postgres_table_exists = postgres.table_exists(
                table_name=mssql_table_name, schema_name=postgres_schema_name)

            if not postgres_table_exists or update:
                try:
                    if verbose:
                        postgresql_tbl = postgres._table_name(
                            table_name=mssql_table_name, schema_name=postgres_schema_name)
                        if postgres_table_exists:
                            msg = f"Updating {postgresql_tbl}"
                        else:
                            mssql_tbl = mssql._table_name(
                                table_name=mssql_table_name, schema_name=mssql_schema_name)
                            msg = f"Copying {mssql_tbl} to {postgresql_tbl}"
                        print(f'\t{counter_msg} ' + msg, end=" ... ")

                    row_count = mssql.get_row_count(mssql_table_name)

                    if row_count >= 1000000:

                        if chunk_size is None:
                            chunk_size = 1000000

                    source_data = mssql.read_table(table_name=mssql_table_name, chunk_size=chunk_size)

                    col_type = {}

                    check_dtypes = ['hierarchyid', 'varbinary']
                    check_dtypes_rslt = mssql.has_dtypes(mssql_table_name, dtypes=check_dtypes)

                    for dtype, if_exists, col_names in check_dtypes_rslt:
                        if if_exists:
                            if dtype == 'hierarchyid':
                                source_data.loc[:, col_names] = source_data[col_names].applymap(
                                    lambda x: str(x).replace('\\', '\\\\'))

                            bytea_list = [sqlalchemy.dialects.postgresql.BYTEA] * len(col_names)
                            col_type.update(dict(zip(col_names, bytea_list)))

                    memory_usage = sys.getsizeof(source_data) / 1024 ** 3
                    if memory_usage > memory_threshold:
                        np_ = _check_dependency(name='numpy')

                        source_data = np_.array_split(source_data, memory_usage // memory_threshold)

                        i = 0
                        while i < len(source_data):
                            postgres.import_data(
                                source_data[i], table_name=mssql_table_name,
                                schema_name=postgres_schema_name,
                                if_exists='replace' if i == 0 else 'append',
                                method=postgres.psql_insert_copy, chunk_size=chunk_size,
                                col_type=col_type, confirmation_required=False, verbose=False)

                            gc.collect()
                            i += 1

                    else:
                        postgres.import_data(
                            source_data, table_name=mssql_table_name, schema_name=postgres_schema_name,
                            if_exists='replace', method=postgres.psql_insert_copy,
                            chunk_size=chunk_size, col_type=col_type, confirmation_required=False,
                            verbose=False)

                    # Get primary keys from MSSQL
                    primary_keys = mssql.get_primary_keys(mssql_table_name, table_type='TABLE')

                    # Specify primary keys in PostgreSQL
                    postgres_pkey = postgres.get_primary_keys(
                        table_name=mssql_table_name, schema_name=postgres_schema_name)
                    if not postgres_pkey:
                        postgres.add_primary_keys(primary_keys, mssql_table_name, postgres_schema_name)

                    del source_data
                    gc.collect()

                    if verbose:
                        print("Done.")

                except Exception as e:
                    print("Failed.")

                    error_log.update({mssql_table_name: "{}".format(e)})

            else:
                if verbose:
                    postgresql_tbl = f'"{postgres_schema_name}"."{mssql_table_name}"'
                    print(f"\t{counter_msg} {postgresql_tbl} already exists.")

            table_counter += 1

        if verbose:
            print(f"Completed.")

        if bool(error_log):
            return error_log
