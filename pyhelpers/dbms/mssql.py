"""
Communication with `Microsoft SQL Server <https://www.microsoft.com/en-gb/sql-server/>`_ databases.
"""

import copy
import functools
import getpass
import itertools
import operator
import os
import re
import warnings

import pandas as pd
import sqlalchemy
import sqlalchemy.dialects
import sqlalchemy.exc

from ._base import _Base
from .._cache import _check_dependency, _confirmed, _print_failure_msg


class MSSQL(_Base):
    """
    A class for basic communication with `Microsoft SQL Server`_ databases.

    .. _`Microsoft SQL Server`: https://www.microsoft.com/en-gb/sql-server/
    """

    #: Default dialect.
    #: The dialect that SQLAlchemy uses to communicate with Microsoft SQL Server; see also
    #: [`DBMS-MS-1 <https://docs.sqlalchemy.org/en/14/dialects/mssql.html>`_].
    DEFAULT_DIALECT: str = 'mssql'
    #: Default name of database driver. See also
    #: [`DBMS-MS-2
    #: <https://docs.sqlalchemy.org/dialects/mssql.html#module-sqlalchemy.dialects.mssql.pyodbc>`_].
    DEFAULT_DRIVER: str = 'pyodbc'
    #: Default ODBC driver.
    DEFAULT_ODBC_DRIVER: str = 'ODBC Driver 17 for SQL Server'
    #: Default host (server name). Alternatively, ``os.environ['COMPUTERNAME']``.
    DEFAULT_HOST: str = 'localhost'
    #: Default listening port used by Microsoft SQL Server.
    DEFAULT_PORT: str | int = 1433
    #: Default username.
    DEFAULT_USERNAME: str = 'sa'
    #: Default database name.
    DEFAULT_DATABASE: str = 'master'
    #: Default schema name.
    DEFAULT_SCHEMA: str = 'dbo'
    #: Names of built-in schemas of Microsoft SQL Server.
    BUILTIN_SCHEMAS: set = {
        'db_accessadmin',
        'db_backupoperator',
        'db_datareader',
        'db_datawriter',
        'db_ddladmin',
        'db_denydatareader',
        'db_denydatawriter',
        'db_owner',
        'db_securityadmin',
        'dbo',
        'guest',
        'INFORMATION_SCHEMA',
        'sys',
    }

    def __init__(self, host=None, port=None, username=None, password=None, database_name=None,
                 confirm_db_creation=False, verbose=False):
        """
        :param host: Name or IP address of the SQL Server, e.g. ``'localhost'`` or ``'127.0.0.1'``;
            defaults to ``'localhost'`` if not specified.
        :type host: str | None
        :param port: Listening port of the SQL Server;
            defaults to ``1433`` if not specified (default by installation of the SQL Server).
        :type port: int | None
        :param username: Username for authentication;
            if not provided, Windows Authentication is used.
        :type username: str | None
        :param password: Password for the specified username;
            required for non-Windows Authentication.
        :type password: str | int | None
        :param database_name: Name of the initial database to connect to;
            defaults to ``'master'`` if not specified.
        :type database_name: str | None
        :param confirm_db_creation: Whether to prompt for confirmation
            before creating a new database (if the specified database does not exist);
            defaults to ``False``.
        :type confirm_db_creation: bool
        :param verbose: Whether to print connection and operation details to the console;
            defaults to ``False``.
        :type verbose: bool | int

        :ivar str host: Name or IP address of the SQL Server.
        :ivar str port: Listening port of the SQL Server.
        :ivar str username: Username used for authentication.
        :ivar str database_name: Name of the connected database.
        :ivar dict credentials: Contains basic information about the server and database.
        :ivar str | None auth: Authentication method used for connection.
        :ivar str address: String representation of the database connection address.
        :ivar sqlalchemy.engine.Engine engine: SQLAlchemy engine connected to the SQL Server;
            see also [`DBMS-MS-3`_].

        .. _`DBMS-MS-3`:
            https://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.address
            '<server_name>@localhost:1433/master'
            >>> testdb = MSSQL(database_name='testdb', verbose=True)
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.
            >>> testdb.database_name
            'testdb'
            >>> testdb.drop_database(verbose=True)
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.
        """

        super().__init__()

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
            self.odbc_driver = [
                x for x in pyodbc_.drivers() if 'ODBC' in x and 'SQL Server' in x][0]
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
            else:  # The database doesn't exist
                self._create_db(
                    confirm_db_creation=confirm_db_creation, verbose=verbose, fmt='[{}]')
            reconnect_db = True

        self.address = re.split(
            r'://|\?', self.engine.url.render_as_string(hide_password=True))[1].replace('%5C', '\\')
        if verbose:
            print(f"Connecting {self.address}", end=" ... ")

        try:
            if reconnect_db:
                self.engine = sqlalchemy.create_engine(
                    url=self.engine.url, isolation_level='AUTOCOMMIT')

            with self.engine.connect() as test_conn:
                test_conn.close()

            if verbose:
                print("Successfully.")

        except Exception as e:
            _print_failure_msg(e=e, msg="Failed.")

    def specify_conn_str(self, database_name=None, auth=None, password=None):
        """
        Specify the connection string for establishing a connection to a database.

        :param database_name: Name of the database to connect to;
            defaults to the currently-connected database if ``database_name=None``.
        :type database_name: str | None
        :param auth: Authentication method used for the connection;
            defaults to the current authentication method if ``auth=None``.
        :type auth: str | None
        :param password: User's password;
            if ``password=None`` (default), manual input of the correct password is required to
            establish the connection.
        :type password: str | int | None
        :return: Connection string formatted for establishing a connection.
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
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
        Create a SQLAlchemy connectable engine for connecting to a SQL Server database.

        This method generates and returns a *SQLAlchemy* engine configured to connect to a
        SQL Server database using the provided or default database name, authentication method and
        password. The returned engine can be used to execute SQL queries and interact with the
        database.

        :param database_name: Name of the database to connect to;
            defaults to the currently-connected database if ``database_name=None``.
        :type database_name: str | None
        :param auth: Authentication method used to establish the connection;
            defaults to the current authentication method if ``auth=None``.
        :type auth: str | None
        :param password: User's password;
            if ``password=None`` (default), manual input of the correct password is required
            to establish the connection.
        :type password: str | int | None
        :return: A SQLAlchemy connectable engine.
        :rtype: sqlalchemy.engine.Engine

        1. Use `pyodbc <https://pypi.org/project/pyodbc/>`_ (or
           `pypyodbc <https://pypi.org/project/pypyodbc/>`_)::

            connect_string = 'driver={...};server=...;database=...;uid=username;pwd=...'
            conn = pyodbc.connect(connect_string)  # conn = pypyodbc.connect(connect_string)

        2. Use `SQLAlchemy <https://www.sqlalchemy.org/>`_::

            conn_string = 'mssql+pyodbc:///?odbc_connect=%s' % quote_plus(connect_string)
            engine = sqlalchemy.create_engine(conn_string)
            conn = engine.connect()

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
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

    def create_connection(self, database_name=None, mode=None):
        # noinspection PyTypeChecker
        """
        Create a SQLAlchemy connection to a Microsoft SQL Server database.

        This method establishes and returns a connection to the specified database using either
        SQLAlchemy or pyodbc, depending on the specified ``mode``.

        :param database_name: Name of the database to connect to; defaults to the name of the
            currently-connected database if ``database_name=None``.
        :type database_name: str | None
        :param mode: Connection mode; defaults to using the existing engine if ``mode=None``.
            When ``mode='pyodbc'``, it uses `pyodbc.connect()`_.
        :type mode: None | str
        :return: A SQLAlchemy connection or a pyodbc connection to the database.
        :rtype: sqlalchemy.engine.Connection | pyodbc.Connection

        .. _`pyodbc.connect()`:
            https://github.com/mkleehammer/pyodbc/wiki/The-pyodbc-Module#connect

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> import sqlalchemy
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> db_conn = mssql.create_connection()
            >>> db_conn.should_close_with_result
            False
            >>> db_conn.closed
            False
            >>> res = db_conn.execute(sqlalchemy.text('SELECT 1'))
            >>> res.fetchall()
            [(1,)]
            >>> db_conn.closed
            False
            >>> db_conn.close()
            >>> db_conn.closed
            True
        """

        if mode is None:  # (default)
            engine = self.create_engine(database_name=database_name)
            conn = engine.connect()

        else:  # use 'pyodbc'
            pyodbc_ = _check_dependency(name='pyodbc')

            conn_str = self.specify_conn_str(database_name=self.database_name, auth=self.auth)

            conn = pyodbc_.connect(conn_str)

        return conn

    def create_cursor(self, database_name=None):
        """
        Create a `pyodbc <https://pypi.org/project/pyodbc/>`_ cursor.

        :param database_name: Name of the database to connect to;
            defaults to the name of the currently-connected database if ``database_name=None``.
        :type database_name: str | None
        :return: A `pyodbc <https://pypi.org/project/pyodbc/>`_ cursor.
        :rtype: pyodbc.Cursor

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
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

    # == Database ==================================================================================

    def get_database_names(self, names_only=True):
        """
        Get names of all existing databases.

        :param names_only: Whether to return only the names of the databases; defaults to ``True``.
        :type names_only: bool
        :return: Names of all existing databases.
        :rtype: list | pandas.DataFrame

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_database_names()
            ['master', 'tempdb', 'model', 'msdb']
        """

        with self.engine.connect() as connection:
            query = sqlalchemy.text('SELECT name, database_id, create_date FROM sys.databases;')
            result = connection.execute(query)

        db_names = result.fetchall()
        if names_only:
            database_names = [x[0] for x in db_names]
        else:
            database_names = pd.DataFrame(db_names)

        return database_names

    def database_exists(self, database_name=None):
        """
        Check whether a database exists.

        :param database_name: Name of the database to check; defaults to ``None``.
        :type database_name: str | None
        :return: Whether the database exists.
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

        db_name = self.database_name if database_name is None else str(database_name)

        with self.engine.connect() as connection:
            # noinspection PyBroadException
            try:
                query = sqlalchemy.text(
                    f"IF (EXISTS (SELECT name FROM master.sys.databases WHERE name='{db_name}')) "
                    f"SELECT 1 ELSE SELECT 0")
                result_ = connection.execute(query)
            except Exception:
                query = sqlalchemy.text(
                    f"SELECT COUNT(*) FROM master.sys.databases "
                    f"WHERE '[' + name + ']' = '{db_name}' OR name = '{db_name}';")
                result_ = connection.execute(query)

        result = bool(result_.fetchone()[0])

        return result

    def create_database(self, database_name, verbose=False):
        """
        Create a database.

        :param database_name: Name of the database to be created.
        :type database_name: str
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int

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

        self._create_database(database_name=database_name, verbose=verbose, fmt='[{}]')

    def connect_database(self, database_name=None, verbose=False):
        """
        Establish a connection to a database.

        :param database_name: Name of the database to connect to;
            if ``database_name=None`` (default), the database name is input manually.
        :type database_name: str | None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int

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
            db_name = str(database_name)  # self.database_name = str(database_name)

            self.credentials.update({'database': db_name})

            url_query = {'driver': self.odbc_driver}
            if self.auth == 'Windows Authentication':
                url_query.update({'Trusted_Connection': 'yes'})

            url = sqlalchemy.engine.URL.create(**self.credentials, query=url_query)
            self.address = re.split(
                r'://|\?', url.render_as_string(hide_password=True))[1].replace('%5C', '\\')

            if verbose:
                print(f"Connecting {self.address}", end=" ... ")

            try:
                if not self.database_exists(database_name=db_name):
                    self.create_database(database_name=db_name)

                self.engine = sqlalchemy.create_engine(url=url, isolation_level='AUTOCOMMIT')

                if verbose:
                    print("Successfully.")

                self.database_name = self.credentials['database']

            except Exception as e:
                _print_failure_msg(e=e, msg="Failed.")

        else:
            if verbose:
                print(f"Being connected with {self.address}.")

    def disconnect_database(self, database_name=None, verbose=False):
        """
        Disconnect from a database.

        :param database_name: Name of the database to disconnect from;
            if ``database_name=None`` (default), disconnects from the current database.
        :type database_name: str | None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int

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

        db_name = self.database_name if database_name is None else str(database_name)

        if db_name != self.DEFAULT_DATABASE:
            if verbose:
                print(f'Disconnecting the database "{db_name}" ... ', end="")

            try:
                # with self.engine.connect() as connection:
                #     query = sqlalchemy.text(
                #         f'ALTER DATABASE {db_name} SET SINGLE_USER WITH ROLLBACK IMMEDIATE;'
                #         f'ALTER DATABASE {db_name} SET MULTI_USER;')
                #     connection.execute(query)

                with self.engine.connect() as connection:
                    query = sqlalchemy.text(
                        f"USE [master]; "
                        f"DECLARE @kill varchar(8000) = ''; "
                        f"SELECT @kill = @kill + 'kill ' + CONVERT(varchar(5), session_id) + ';' "
                        f"FROM sys.dm_exec_sessions WHERE database_id  = db_id('{db_name}') "
                        f"EXEC(@kill);")
                    connection.execute(query)

                if verbose:
                    print("Done.")

                self.connect_database(database_name=self.DEFAULT_DATABASE)

            except Exception as e:
                _print_failure_msg(e=e, msg="Failed.")

        else:
            if verbose:
                print(f"Being connected with {self.address}.")

    def drop_database(self, database_name=None, confirmation_required=True, verbose=False):
        """
        Delete/drop a database.

        :param database_name: Name of the database to be dropped;
            if ``database_name=None`` (default), drops the currently-connected database.
        :type database_name: str | None
        :param confirmation_required: Whether to prompt a confirmation message before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int

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

        self._drop_database(
            database_name=database_name, fmt='[{}]', confirmation_required=confirmation_required,
            verbose=verbose)

    # == Schema ====================================================================================

    def schema_exists(self, schema_name):
        """
        Check whether a schema exists.

        :param schema_name: Name of the schema to check.
        :type schema_name: str
        :return: Whether the schema exists.
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

        query = (f"IF EXISTS (SELECT name FROM sys.schemas WHERE name='{schema_name_}') "
                 f"SELECT 1 ELSE SELECT 0")

        result = bool(self._execute(query)[0])

        return result

    def create_schema(self, schema_name, verbose=False):
        """
        Create a schema.

        :param schema_name: Name of the schema to be created.
        :type schema_name: str
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int

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
                with self.engine.connect() as connection:
                    query = sqlalchemy.text(f'CREATE SCHEMA {s_name};')
                    connection.execute(query)
                if verbose:
                    print("Done.")
            except Exception as e:
                _print_failure_msg(e=e, msg="Failed.")

        else:
            print(f"The schema {s_name} already exists.")

    def get_schema_info(self, names_only=True, include_all=False, column_names=None, verbose=False):
        """
        Retrieve information about existing schemas.

        :param names_only: Whether to return only the names of the schemas; defaults to ``True``.
        :type names_only: bool
        :param include_all: Whether to include all available schemas; defaults to ``False``.
        :type include_all: bool
        :param column_names: Column names of the returned dataframe if ``names_only=False``;
            defaults to ``['schema_name', 'schema_id', 'role']`` if ``column_names=None``.
        :type column_names: list | None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :return: Names of schemas, a dataframe with schema information,
            or ``None`` if no information is retrieved.
        :rtype: list | pandas.DataFrame | None

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.
            >>> testdb.get_schema_info()
            ['dbo']
            >>> test_schema_name = 'test_schema'
            >>> testdb.create_schema(schema_name=test_schema_name, verbose=True)
            Creating a schema: [test_schema] ... Done.
            >>> testdb.get_schema_info()
            ['dbo', 'test_schema']
            >>> testdb.get_schema_info(names_only=False, include_all=True)
                       schema_name        schema_owner  schema_id
            0       db_accessadmin      db_accessadmin      16385
            1    db_backupoperator   db_backupoperator      16389
            2        db_datareader       db_datareader      16390
            3        db_datawriter       db_datawriter      16391
            4          db_ddladmin         db_ddladmin      16387
            5    db_denydatareader   db_denydatareader      16392
            6    db_denydatawriter   db_denydatawriter      16393
            7             db_owner            db_owner      16384
            8     db_securityadmin    db_securityadmin      16386
            9                  dbo                 dbo          1
            10               guest               guest          2
            11  INFORMATION_SCHEMA  INFORMATION_SCHEMA          3
            12                 sys                 sys          4
            13         test_schema                 dbo          5
            >>> testdb.drop_schema(schema_names='test_schema', verbose=True)
            To drop the schema "test_schema" from <server_name>@localhost:1433/testdb
            ? [No]|Yes: yes
            Dropping "test_schema" ... Done.
            >>> testdb.get_schema_info()  # None
            ['dbo']
            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database [testdb] from <server_name>@localhost:1433
            ? [No]|Yes: yes
            Dropping [testdb] ... Done.
        """

        if not include_all:
            condition = (
                "WHERE SUBSTRING(s.name, 1, 3) NOT IN ('db_') "
                "AND u.name NOT IN ('sys', 'guest', 'INFORMATION_SCHEMA') ")
        else:
            condition = ""

        if names_only:  # query = "SELECT name FROM sys.schemas ORDER BY name;"
            query = sqlalchemy.text(
                f"SELECT s.name FROM sys.schemas s "
                f"INNER JOIN sys.sysusers u ON u.uid = s.principal_id "
                f"{condition}"
                f"ORDER BY s.name;")
        else:
            query = sqlalchemy.text(
                f"SELECT s.name as schema_name, u.name as schema_owner, s.schema_id "
                f"FROM sys.schemas s "
                f"INNER JOIN sys.sysusers u ON u.uid = s.principal_id "
                f"{condition}"
                f"ORDER BY s.name;")

        with self.engine.connect() as connection:
            result = connection.execute(query)

        schema_info_ = result.fetchall()
        if not schema_info_:
            schema_info = None
            if verbose:
                print(f"No schema exists in the currently-connected database "
                      f"\"{self.database_name}\".")

        else:
            if names_only:
                schema_info = [x[0] for x in schema_info_]
            else:
                if column_names is None:
                    column_names = ['schema_name', 'schema_owner', 'schema_id']
                else:
                    assert len(column_names) == len(schema_info_[0]), \
                        f"`column_names` must be a list of strings and " \
                        f"its length must equal {len(schema_info_[0])}."
                schema_info = pd.DataFrame(schema_info_, columns=column_names)

        return schema_info

    def drop_schema(self, schema_names, confirmation_required=True, verbose=False):
        """
        Delete/drop one or multiple schemas.

        :param schema_names: Name of a single schema or names of multiple schemas to be dropped.
        :type schema_names: str | typing.Iterable[str]
        :param confirmation_required: Whether to prompt a confirmation message before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.
            >>> new_schema_names = ['points', 'lines', 'polygons']
            >>> for new_schema in new_schema_names:
            ...     testdb.create_schema(new_schema, verbose=True)
            Creating a schema: [points] ... Done.
            Creating a schema: [lines] ... Done.
            Creating a schema: [polygons] ... Done.
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

        declare_statement = \
            ("DECLARE @sql_statement1 NVARCHAR(MAX); "
             "DECLARE @sql_statement2 NVARCHAR(MAX); "
             "DECLARE @db_schema NVARCHAR(200); "
             "SET @db_schema = '{}'; ")

        alter_table_statement = \
            ("COALESCE(@sql_statement1, N'') + "
             "N'ALTER TABLE ' + tc.TABLE_NAME + ' DROP CONSTRAINT ' + tc.constraint_name + ';' + "
             "CHAR(13)")
        select1 = \
            "SELECT @sql_statement1 = " + alter_table_statement + \
            "FROM INFORMATION_SCHEMA.TABLES t, INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc " \
            "WHERE " \
            "t.TABLE_NAME = tc.TABLE_NAME AND " \
            "tc.CONSTRAINT_NAME NOT LIKE '%%_pk' AND " \
            "CONSTRAINT_TYPE <> 'PRIMARY KEY' AND " \
            "t.TABLE_CATALOG='{}'; " \
            "EXEC sp_executesql @sql_statement1; "

        drop_tables_statement = \
            ("COALESCE(@sql_statement2, N'') + "
             "N'DROP TABLE ' +'[' + @db_schema +']' + '.' + QUOTENAME(TABLE_NAME) + N';' + "
             "CHAR(13)")
        select2 = \
            "SELECT @sql_statement2 = " + drop_tables_statement + \
            "FROM INFORMATION_SCHEMA.TABLES " \
            "WHERE TABLE_SCHEMA = @db_schema AND TABLE_TYPE = 'BASE TABLE' " \
            "EXEC sp_executesql @sql_statement2; "

        query_ = declare_statement + select1 + select2 + 'DROP SCHEMA IF EXISTS [{}];'

        self._drop_schema(
            schema_names=schema_names, fmt='[{}]', query_=query_,
            confirmation_required=confirmation_required, verbose=verbose)

    # == Table =====================================================================================

    def get_table_names(self, schema_name=None, verbose=False):
        """
        Get names of all tables stored in one or multiple schemas.

        :param schema_name: Name of a single schema, or names of multiple schemas;
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``.
        :type schema_name: str | list | None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :return: Dictionary containing table names grouped by schema(s)
            specified in ``schema_name``.
        :rtype: dict

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_table_names()
            {'dbo': ['MSreplication_options',
              'spt_fallback_db',
              'spt_fallback_dev',
              'spt_fallback_usg',
              'spt_monitor',
              'test_table']}
            >>> mssql.get_table_names(schema_name=['dbo', 'sys'])
            {'dbo': ['MSreplication_options',
              'spt_fallback_db',
              'spt_fallback_dev',
              'spt_fallback_usg',
              'spt_monitor',
              'test_table'],
             'sys': []}
        """

        table_names = super().get_table_names(schema_name=schema_name, verbose=verbose)

        return table_names

    def _table_name(self, table_name, schema_name=None, fmt='[{}].[{}]'):
        """
        Format a table name optionally including a schema name.

        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema; defaults to ``None``.
        :type schema_name: str | None
        :param fmt: Format string for formatting the schema and table names;
            defaults to ``'[{}].[{}]'``.
        :type fmt: str
        :return: Formatted table name.
        :rtype: str
        """

        table_name_ = super()._table_name(table_name=table_name, schema_name=schema_name, fmt=fmt)

        return table_name_

    def create_table(self, table_name, column_specs, schema_name=None, verbose=False):
        """
        Create a table with specified columns.

        :param table_name: Name of the table to be created.
        :type table_name: str
        :param column_specs: Specifications for each column of the table.
        :type column_specs: str
        :param schema_name: Name of the schema where the table will be created;
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'dbo'``)
            if ``schema_name=None``.
        :type schema_name: str | None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> testdb = MSSQL(database_name='testdb')
            Creating a database: [testdb] ... Done.
            Connecting <server_name>@localhost:1433/testdb ... Successfully.
            >>> # Create a new table named 'test_table'
            >>> tbl_name = 'test_table'
            >>> col_spec = 'col_name_1 INT, col_name_2 varchar(255)'
            >>> testdb.create_table(table_name=tbl_name, column_specs=col_spec, verbose=True)
            Creating a table: [dbo].[test_table] ... Done.
            >>> testdb.table_exists(table_name=tbl_name)
            True
            >>> testdb.get_column_names(table_name=tbl_name)
            ['col_name_1', 'col_name_2']
            >>> test_tbl_col_info = testdb.get_column_info(table_name=tbl_name, as_dict=False)
            >>> test_tbl_col_info.head()
                                column_0    column_1
            TABLE_CATALOG         testdb      testdb
            TABLE_SCHEMA             dbo         dbo
            TABLE_NAME        test_table  test_table
            COLUMN_NAME       col_name_1  col_name_2
            ORDINAL_POSITION           1           2
            >>> testdb.validate_column_names(table_name=tbl_name)
            '"col_name_1", "col_name_2"'
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

                with self.engine.connect() as connection:
                    query = sqlalchemy.text(f'CREATE TABLE {table_name_} ({column_specs});')
                    connection.execute(query)

                if verbose:
                    print("Done.")

            except Exception as e:
                _print_failure_msg(e=e, msg="Failed.")

    def table_exists(self, table_name, schema_name=None):
        """
        Check whether a table exists.

        :param table_name: Name of the table to check.
        :type table_name: str
        :param schema_name: Name of the schema where the table is located;
            defaults to :attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'dbo'``)
            if ``schema_name=None``.
        :type schema_name: str | None
        :return: Whether the table exists in the currently-connected database.
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.table_exists(table_name='test_table')
            False
            >>> mssql.get_table_names()
            {'dbo': ['MSreplication_options',
              'spt_fallback_db',
              'spt_fallback_dev',
              'spt_fallback_usg',
              'spt_monitor']}
            >>> mssql.table_exists(table_name='MSreplication_options')
            True
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        with self.engine.connect() as connection:
            query = sqlalchemy.text(
                f"IF (EXISTS ("
                f"SELECT * FROM INFORMATION_SCHEMA.TABLES "
                f"WHERE TABLE_SCHEMA = '{schema_name_}' AND TABLE_NAME = '{table_name}')) "
                f"SELECT 1 ELSE SELECT 0")
            result_ = connection.execute(query)

        result = bool(result_.fetchone()[0])

        return result

    def get_file_tables(self, names_only=True):
        """
        Retrieve information about *FileTables* from the database (if available).

        :param names_only: Whether to return only the names of *FileTables*; defaults to ``True``.
        :type names_only: bool
        :return: Information about *FileTables* (if available).
        :rtype: list | pandas.DataFrame

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_file_tables()
            []
        """

        with self.engine.connect() as connection:
            query = sqlalchemy.text('SELECT * FROM sys.tables WHERE is_filetable = 1;')
            result = connection.execute(query)

        file_tables_ = result.fetchall()
        if names_only:
            file_tables = [x[0] for x in file_tables_]
        else:
            file_tables = pd.DataFrame(file_tables_)

        return file_tables

    def get_row_count(self, table_name, schema_name=None):
        """
        Get the row count of a table.

        :param table_name: Name of the table to get row count from.
        :type table_name: str
        :param schema_name: Name of the schema where the table is located; defaults to ``None``.
        :type schema_name: str | None
        :return: Number of rows in the specified table in the currently-connected database.
        :rtype: int

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_table_names()
            {'dbo': ['MSreplication_options',
              'spt_fallback_db',
              'spt_fallback_dev',
              'spt_fallback_usg',
              'spt_monitor']}
            >>> mssql.get_row_count(table_name='MSreplication_options')
            3
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        with self.engine.connect() as connection:
            query = sqlalchemy.text(f'SELECT COUNT(*) FROM {table_name_};')
            result = connection.execute(query)

        row_count = result.fetchone()[0]

        return row_count

    def get_column_names(self, table_name, schema_name=None):
        """
        Retrieve column names of a table.

        :param table_name: Name of the table to retrieve column names from.
        :type table_name: str
        :param schema_name: Name of the schema where the table is located; defaults to ``None``.
        :type schema_name: str | None
        :return: List of column names in the specified table in the currently-connected database.
        :rtype: list

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_table_names()
            {'dbo': ['MSreplication_options',
              'spt_fallback_db',
              'spt_fallback_dev',
              'spt_fallback_usg',
              'spt_monitor']}
            >>> mssql.get_column_names(table_name='MSreplication_options')
            ['optname',
             'value',
             'major_version',
             'minor_version',
             'revision',
             'install_failures']
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        connection = self.engine.raw_connection()
        try:
            cursor = connection.cursor()
            col_names = [x.column_name for x in cursor.columns(table=table_name, schema=schema_name_)]
            cursor.close()
        finally:
            connection.close()

        return col_names

    def get_column_info(self, table_name, schema_name=None, as_dict=True):
        """
        Retrieve information about columns of a table.

        :param table_name: Name of the table to retrieve column information from.
        :type table_name: str
        :param schema_name: Name of the schema where the table is located;
            defaults to :py:attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'master'``)
            if ``schema_name=None``.
        :type schema_name: str | None
        :param as_dict: Whether to return the column information as a dictionary;
            defaults to ``True``.
        :type as_dict: bool
        :return: Information about all columns of the specified table in the currently-connected
            database.
        :rtype: pandas.DataFrame | dict

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.MSSQL.create_table`.
        """

        column_info = super().get_column_info(
            table_name=table_name, schema_name=schema_name, as_dict=as_dict)

        return column_info

    def validate_column_names(self, table_name, schema_name=None, column_names=None):
        """
        Validate column names for use in a SQL query statement.

        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema where the table is located; defaults to ``None``.
        :type schema_name: str | None
        :param column_names: Column name(s) to validate for a dataframe.
        :type column_names: str | list | tuple | None
        :return: Validated column names formatted for a SQL query statement.
        :rtype: str

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.MSSQL.create_table`.
        """

        column_names_ = super().validate_column_names(
            schema_name=schema_name, table_name=table_name, column_names=column_names)

        return column_names_

    def _has_dtypes(self, table_name, dtypes, schema_name=None):
        """
        Check whether a table contains columns of specified data types.

        :param table_name: Name of the table in the currently-connected database.
        :type table_name: str
        :param dtypes: Data type(s) to check for,
            e.g. ``'geometry'``, ``'hierarchyid'``, ``'varbinary'``.
        :type dtypes: str | list
        :param schema_name: Name of the schema where the table is located;
            defaults to :attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'master'``)
            if ``schema_name=None``.
        :type schema_name: str | None
        :return: Whether the table contains any of the specified data types,
                 and a list of tables that contain those data types.
        :rtype: tuple[bool, list]

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_table_names()
            {'dbo': ['MSreplication_options',
              'spt_fallback_db',
              'spt_fallback_dev',
              'spt_fallback_usg',
              'spt_monitor']}
            >>> mssql._has_dtypes(table_name='MSreplication_options', dtypes='varbinary')
            (False, [])
            >>> mssql._has_dtypes(table_name='MSreplication_options', dtypes=['varbinary', 'int'])
            (True, ['major_version', 'minor_version', 'revision', 'install_failures'])
        """

        with self.engine.connect() as connection:
            schema_name_ = self._schema_name(schema_name=schema_name)

            dtype_query = (f"= '{dtypes}'" if isinstance(dtypes, str) else f"IN {tuple(dtypes)}")
            sql_query_geom_col = \
                f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS " \
                f"WHERE TABLE_NAME='{table_name}' AND TABLE_SCHEMA='{schema_name_}' " \
                f"AND DATA_TYPE {dtype_query};"

            query = sqlalchemy.text(sql_query_geom_col)
            result = connection.execute(query)

        col_names = result.fetchall()

        if len(col_names) > 0:
            has_the_dtypes = True
            col_names = list(itertools.chain.from_iterable(col_names))
        else:
            has_the_dtypes = False

        return has_the_dtypes, col_names

    def has_dtypes(self, table_name, dtypes, schema_name=None):
        """
        Check whether a table contains columns of specified data types.

        :param table_name: Name of the table in the currently-connected database.
        :type table_name: str
        :param dtypes: Data type(s) to check for,
            e.g. ``'geometry'``, ``'hierarchyid'``, ``'varbinary'``.
        :type dtypes: str | list
        :param schema_name: Name of the schema where the table is located;
            defaults to :attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'master'``)
            if ``schema_name=None``.
        :type schema_name: str | None
        :return: Data type, whether the table has this data type and the corresponding column names.
        :rtype: typing.Generator[str, bool, list]

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_table_names()
            {'dbo': ['MSreplication_options',
              'spt_fallback_db',
              'spt_fallback_dev',
              'spt_fallback_usg',
              'spt_monitor']}
            >>> res = mssql.has_dtypes(table_name='spt_monitor', dtypes='varbinary')
            >>> list(res)
            [('varbinary', False, [])]
            >>> res = mssql.has_dtypes(table_name='spt_monitor', dtypes=['geometry', 'int'])
            >>> list(res)
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

        with self.engine.connect() as connection:
            for data_type in dtypes_:
                sql_query_geom_col = \
                    f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS " \
                    f"WHERE TABLE_NAME='{table_name}' " \
                    f"AND TABLE_SCHEMA='{schema_name_}' " \
                    f"AND DATA_TYPE='{data_type}'"
                query = sqlalchemy.text(sql_query_geom_col)
                result = connection.execute(query)

                col_names = result.fetchall()

                if len(col_names) > 0:
                    has_the_dtypes = True
                    col_names = list(itertools.chain.from_iterable(col_names))
                else:
                    has_the_dtypes = False

                yield data_type, has_the_dtypes, col_names

    def _column_names_in_query(self, table_name, column_names=None, schema_name=None, exclude=None):
        """
        Format column names for use in a SQL query statement.

        :param table_name: Name of the table in the currently-connected database.
        :type table_name: str
        :param column_names: List of column names from the specified table; defaults to ``None``.
        :type column_names: list | None
        :param schema_name: Name of the schema where the table is located;
            defaults to :attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'master'``)
            if ``schema_name=None``.
        :type schema_name: str | None
        :param exclude: Column name(s) to exclude from the formatted query statement.
        :type exclude: str | list | None
        :return: Formatted column names for a SQL query statement and a list of target column names.
        :rtype: tuple[str, list]

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_table_names()
            {'dbo': ['MSreplication_options',
              'spt_fallback_db',
              'spt_fallback_dev',
              'spt_fallback_usg',
              'spt_monitor']}
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

    def get_primary_keys(self, table_name=None, schema_name=None, table_type='TABLE'):
        """
        Retrieve the primary keys of table(s) from the currently-connected database.

        :param table_name: Name of a specific table to retrieve primary keys from;
            when ``table_name=None`` (default), retrieves primary keys for all tables.
        :type table_name: str | None
        :param schema_name: Name of the schema where the table(s) are located;
            defaults to :attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'master'``)
            if ``schema_name=None``.
        :type schema_name: str | None
        :param table_type: Type of table to consider; defaults to ``'TABLE'``.
        :type table_type: str
        :return: The primary keys for the specified table(s).
        :rtype: list

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> mssql = MSSQL(verbose=True)
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

            # Each element of 'tbl_pks' (as a dict) is in the format of {'table_name': 'primary key'}
            # noinspection PyTypeChecker
            tbl_names_set = functools.reduce(operator.or_, (set(d.keys()) for d in tbl_pks), set())
            # Find all primary keys for each table
            tbl_pk_dict = dict((tbl, [d[tbl] for d in tbl_pks if tbl in d]) for tbl in tbl_names_set)

            if table_name:
                tbl_pk_dict = tbl_pk_dict[table_name]

        except KeyError:  # Most likely that the table (i.e. 'table_name') does not have any primary key
            tbl_pk_dict = None

        return tbl_pk_dict

    def add_primary_key(self, column_name, table_name, schema_name=None):
        """
        Add a primary key constraint to a table.

        :param column_name: Name of the column to set as the primary key.
        :type column_name: str
        :param table_name: Name of the table where the primary key constraint will be added.
        :type table_name: str
        :param schema_name: Name of the schema where the table is located; defaults to ``None``.
        :type schema_name: str | None
        """

        schema_name_ = self.DEFAULT_SCHEMA if schema_name is None else schema_name
        column_type_query = \
            f"SELECT DATA_TYPE, CHARACTER_OCTET_LENGTH AS OCTET_LENGTH " \
            f"FROM INFORMATION_SCHEMA.COLUMNS " \
            f"WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = '{schema_name_}' " \
            f"AND COLUMN_NAME = '{column_name}';"

        with self.engine.connect() as connection:
            col_typ_ = connection.execute(sqlalchemy.text(column_type_query))
            data_type, octet_len = col_typ_.fetchone()

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name_)

        with self.engine.connect() as connection:
            if data_type == 'varchar' and (octet_len == -1 or octet_len > 900):
                alter_column_query = \
                    f"ALTER TABLE {table_name_} ALTER COLUMN {column_name} VARCHAR(500) NOT NULL;"
                connection.execute(sqlalchemy.text(alter_column_query))

            query = f'ALTER TABLE {table_name_} ADD PRIMARY KEY ({column_name});'
            connection.execute(sqlalchemy.text(query))

    def varchar_to_geometry_dtype(self, table_name, geom_column_name, srid=None, schema_name=None):
        """
        Alter a ``VARCHAR`` column containing geometry data to a geometry data type.

        :param table_name: Name of the table where the column exists.
        :type table_name: str
        :param geom_column_name: Name of the VARCHAR column to convert to geometry data type.
        :type geom_column_name: str
        :param srid: Spatial Reference Identifier (SRID) associated with the coordinate system,
            tolerance and resolution; defaults to ``None``.
        :type srid: int | None
        :param schema_name: Name of the schema where the table is located;
            defaults to :attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'master'``)
            if ``schema_name=None``.
        :type schema_name: str | None
        """

        if geom_column_name:
            table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

            temp_col_name = 'temp_geom'
            srid_ = srid if srid else 0

            # Reference: https://stackoverflow.com/questions/64257958/

            add_temp_col = f"ALTER TABLE {table_name_} ADD [{temp_col_name}] GEOMETRY;"

            update_dtype = \
                f"UPDATE {table_name_} " \
                f"SET [{temp_col_name}] = " \
                f"geometry::STGeomFromText(CONVERT(varchar(max), [{geom_column_name}]), {srid_}) " \
                f"FROM {table_name_};"

            alter_column = \
                f"ALTER TABLE {table_name_} DROP COLUMN [{geom_column_name}]; " \
                f"EXEC sp_rename '{table_name_}.{temp_col_name}', '{geom_column_name}', 'COLUMN';"

            with self.engine.connect() as connection:
                for query in [add_temp_col, update_dtype, alter_column]:
                    connection.execute(sqlalchemy.text(query))

    def import_data(self, data, table_name, schema_name=None, if_exists='fail',
                    force_replace=False, chunk_size=None, col_type=None, method='multi',
                    index=False, geom_column_name=None, srid=None, confirmation_required=True,
                    verbose=False, **kwargs):
        """
        Import tabular data into a table.

        See also [`DBMS-MS-ID-1
        <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method/>`_].

        :param data: Tabular data to be imported into the database.
                     It can be a dataframe, a ``TextFileReader`` or a list/tuple of tuples.
        :type data: pandas.DataFrame | pandas.io.parsers.TextFileReader | list | tuple
        :param table_name: Name of the table where the data will be imported.
        :type table_name: str
        :param schema_name: Name of the schema where the table is located;
            defaults to :attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'master'``)
            if ``schema_name=None``.
        :type schema_name: str | None
        :param if_exists: Action to take if the table already exists:

            - ``'replace'``: Drop the table before inserting new data.
            - ``'append'``: Insert new data to the existing table.
            - ``'fail'``: Raise a ValueError if the table already exists (default).

        :type if_exists: str
        :param force_replace: Whether to force replace the existing table; defaults to ``False``.
        :type force_replace: bool
        :param chunk_size: Number of rows to insert at a time; defaults to ``None`` (all at once).
        :type chunk_size: int | None
        :param col_type: Dictionary specifying column data types; defaults to ``None``.
        :type col_type: dict | None
        :param method: Method for SQL insertion clause:

            - ``None``: Uses standard SQL ``INSERT`` clause (one per row).
            - ``'multi'``: Passes multiple values in a single ``INSERT`` clause (default).

        :type method: str | None | typing.Callable
        :param index: Whether to include the DataFrame index as a column in the database table.
        :type index: bool
        :param geom_column_name: Name of the geometry column if importing spatial data;
            defaults to ``None``.
        :type geom_column_name: str | None
        :param srid: Spatial Reference Identifier (SRID) associated with the coordinate system,
            tolerance and resolution; defaults to ``None``.
        :type srid: int | None
        :param confirmation_required: Whether to prompt a confirmation message before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print detailed information during the import process;
            defaults to ``False``.
        :type verbose: bool | int
        :param kwargs: [Optional] Additional parameters for the method `pandas.DataFrame.to_sql()`_.

        .. _`pandas.DataFrame.to_sql()`:
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

            - Examples for the method :meth:`~pyhelpers.dbms.MSSQL.read_table`.
        """

        dat = data.reset_index() if index is True else data

        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=sqlalchemy.exc.SAWarning)

            self._import_data(
                data=dat, table_name=table_name, schema_name=schema_name, if_exists=if_exists,
                force_replace=force_replace, chunk_size=chunk_size, col_type=col_type, method=method,
                index=False, confirmation_required=confirmation_required, verbose=verbose, **kwargs)

        self.varchar_to_geometry_dtype(
            table_name=table_name, schema_name=schema_name, geom_column_name=geom_column_name,
            srid=srid)

    @staticmethod
    def _dtype_read_fmt(dtype):
        """
        Generate SQL format string based on data type.

        :param dtype: Data type identifier, e.g. ``'hierarchyid'``, ``'varbinary'``, ``'geometry'``,
            or others.
        :type dtype: str
        :return: SQL format string for reading data of the specified type.
        :rtype: str
        """

        if dtype == 'hierarchyid':
            fmt = 'CONVERT(NVARCHAR(max), CONVERT(VARBINARY(max), [{x}], 1), 1) AS [{x}]'
        elif dtype == 'varbinary':
            fmt = 'CONVERT(VARCHAR(max), [{x}], 2) AS [{x}]'
        elif dtype == 'geometry':
            fmt = '[{x}].STAsText() AS [{x}]'
        else:
            fmt = '[{x}]'

        return fmt

    def _read_column_names(self, table_name, schema_name, column_names):
        """
        Generate formatted column names for a SQL query statement.

        :param table_name: Name of the table in the currently-connected database.
        :type table_name: str
        :param schema_name: Name of the schema containing the table.
        :type schema_name: str
        :param column_names: Name(s) of the column(s) to be included in the SQL query.
        :type column_names: str | list
        :return: Original column names and formatted column names for SQL query.
        :rtype: tuple[list, str]
        """
        
        col_names = [column_names] if isinstance(column_names, str) else column_names.copy()

        column_info = self.get_column_info(table_name=table_name, schema_name=schema_name)
        # column_info_col_names = list(map(str.lower, column_info['COLUMN_NAME']))
        column_info_col_names = [x.lower() for x in column_info['COLUMN_NAME']]

        # col_idx = [column_info_col_names.index(x) for x in map(str.lower, col_names)]
        col_idx = [column_info_col_names.index(x) for x in (y.lower() for y in col_names)]
        dtypes = [column_info['DATA_TYPE'][i] for i in col_idx]

        fmts = [self._dtype_read_fmt(dtype) for dtype in dtypes]
        col_names_ = ', '.join(fmt.format(x=x) for fmt, x in zip(fmts, col_names))

        return col_names, col_names_

    def read_columns(self, table_name, column_names, dtype=None, schema_name=None, chunk_size=None,
                     **kwargs):
        """
        Read data of specific columns of a table.

        :param table_name: Name of a table in the currently-connected database.
        :type table_name: str
        :param column_names: Column name(s) of the specified table.
        :type column_names: list | tuple
        :param dtype: data type; options are ``{'hierarchyid', 'varbinary', 'geometry'}``;
            defaults to ``None``.
        :type dtype: str | None
        :param schema_name: Name of a schema,
            defaults to :attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``.
        :type schema_name: str | None
        :param chunk_size: Number of rows to include in each chunk (if specified);
            defaults to ``None``
        :type chunk_size: int | None
        :param kwargs: [Optional] Additional parameters for the function `pandas.read_sql()`_.
        :return: Data of specific columns of the queried table.
        :rtype: pandas.DataFrame

        .. _`pandas.read_sql()`: https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> from pyhelpers._cache import example_dataframe
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_table_names()
            {'dbo': ['MSreplication_options',
              'spt_fallback_db',
              'spt_fallback_dev',
              'spt_fallback_usg',
              'spt_monitor']}
            >>> mssql.read_columns('MSreplication_options', column_names=['optname', 'value'])
                      optname  value
            0   transactional   True
            1           merge   True
            2  security_model   True

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.MSSQL.read_table`.
        """

        col_names, col_names_ = self._read_column_names(
            table_name=table_name, schema_name=schema_name, column_names=column_names)
        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        with self.engine.connect() as connection:
            query = sqlalchemy.text(f'SELECT {col_names_} FROM {table_name_};')
            data = pd.read_sql(sql=query, con=connection, chunksize=chunk_size, **kwargs)

        if chunk_size:
            data = pd.concat(data, ignore_index=True)

        if dtype == 'geometry':
            shapely_wkt = _check_dependency(name='shapely.wkt')
            data[col_names] = data[col_names].map(shapely_wkt.loads)

        return data

    def read_table(self, table_name, schema_name=None, column_names=None, conditions=None,
                   chunk_size=None, save_as=None, data_dir=None, save_args=None, verbose=False,
                   **kwargs):
        """
        Read data from a specified table.

        :param table_name: Name of the table to read data from in the currently-connected database.
        :type table_name: str
        :param schema_name: Name of the schema where the table resides;
            defaults to :attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` when ``schema_name=None``.
        :type schema_name: str | None
        :param column_names: Names of columns to retrieve data from;
            defaults to all columns when ``column_names=None``.
        :type column_names: list | tuple | None
        :param conditions: Conditions to apply in the SQL query statement; defaults to ``None``.
        :type conditions: str | None
        :param chunk_size: Number of rows to retrieve in each chunk (if specified);
            defaults to ``None``.
        :type chunk_size: int | None
        :param save_as: File extension (if specified) for saving table data locally;
            defaults to ``None``.
        :type save_as: str | None
        :param data_dir: Directory path where the table data should be saved; defaults to ``None``.
        :type data_dir: str | None
        :param save_args: Optional parameters for the function :func:`pyhelpers.store.save_data`;
            defaults to ``None``.
        :type save_args: dict | None
        :param verbose: Whether to print relevant information in the console; defaults to ``False``.
        :type verbose: bool | int
        :param kwargs: [Optional] Additional parameters for the function `pandas.read_sql()`_.
        :return: Data of the queried table from the currently-connected database.
        :rtype: pandas.DataFrame

        .. _`pandas.read_sql()`: https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html

        **Examples**::

            >>> from pyhelpers.dbms import MSSQL
            >>> from pyhelpers._cache import example_dataframe
            >>> mssql = MSSQL(verbose=True)
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_table_names()
            {'dbo': ['MSreplication_options',
              'spt_fallback_db',
              'spt_fallback_dev',
              'spt_fallback_usg',
              'spt_monitor']}
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

            - Examples for the method :meth:`~pyhelpers.dbms.MSSQL.import_data`.
        """

        if column_names is None:
            column_names_ = self.get_column_names(table_name=table_name, schema_name=schema_name)
        else:
            column_names_ = list(column_names)

        check_dtypes = self.has_dtypes(table_name, dtypes=['hierarchyid', 'varbinary', 'geometry'])

        solo_column_names = []
        column_names_in_query = column_names_.copy()
        for dtype, if_exists, col_names in check_dtypes:
            if if_exists:
                fmt = self._dtype_read_fmt(dtype)
                col_names_ = ', '.join(fmt.format(x=x) for x in col_names)
                solo_column_names.append(col_names_)
                column_names_in_query = list(set(column_names_in_query) - set(col_names))

        column_names_in_query = ', '.join(
            [f'[{x}]' for x in column_names_in_query] + solo_column_names)

        # Specify a SQL query statement
        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)
        sql_query = f'SELECT {column_names_in_query} FROM {table_name_};'

        if conditions:
            sql_query = sql_query.replace(';', ' ') + conditions + ';'

        with self.engine.connect() as connection:
            query = sqlalchemy.text(sql_query)
            data = pd.read_sql(sql=query, con=connection, chunksize=chunk_size, **kwargs)

        if chunk_size:
            data = pd.concat(objs=data, axis=0, ignore_index=True)

        # Sort the order of columns
        data = data[[x for x in column_names_ if x not in data.index.names]]

        if save_as:
            from pyhelpers.dirs import validate_dir
            from pyhelpers.store import save_data

            data_dir_ = validate_dir(data_dir)
            path_to_file = os.path.join(data_dir_, table_name + save_as)

            save_args_ = {} if save_args is None else save_args
            save_args_.update({'data': data, 'path_to_file': path_to_file, 'verbose': verbose})
            save_data(**save_args_)

        return data

    def drop_table(self, table_name, schema_name=None, confirmation_required=True, verbose=False):
        """
        Delete/drop a table.

        :param table_name: Name of the table to be deleted.
        :type table_name: str
        :param schema_name: Name of the schema where the table resides;
            defaults to :attr:`~pyhelpers.dbms.MSSQL.DEFAULT_SCHEMA` (i.e. ``'dbo'``)
            if ``schema_name=None``.
        :type schema_name: str | None
        :param confirmation_required: Whether to prompt for confirmation before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information in the console; defaults to ``False``.
        :type verbose: bool | int

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.MSSQL.create_table`.
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        if not self.table_exists(table_name=table_name, schema_name=schema_name):
            if verbose:
                print(f"The table {table_name_} does not exist.")

        else:
            if _confirmed(f"To drop the table {table_name_} from {self.address}\n?",
                          confirmation_required=confirmation_required):

                if verbose:
                    if confirmation_required:
                        log_msg = f"Dropping {table_name_}"
                    else:
                        log_msg = f"Dropping the table {table_name_} from {self.address}"
                    print(log_msg, end=" ... ")

                try:
                    with self.engine.connect() as connection:
                        connection.execute(sqlalchemy.text(f'DROP TABLE {table_name_};'))

                    if verbose:
                        print("Done.")

                except Exception as e:
                    _print_failure_msg(e=e, msg="Failed.")
