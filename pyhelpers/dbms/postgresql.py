"""
Communication with `PostgreSQL <https://www.postgresql.org/>`_ databases.
"""

import copy
import csv
import getpass
import io
import itertools
import tempfile

import pandas as pd
import sqlalchemy.dialects

from ._base import _Base
from .utils import make_database_address
from .._cache import _check_dependencies, _confirmed, _print_failure_message


class PostgreSQL(_Base):
    """
    A class for basic communication with `PostgreSQL`_ databases.

    .. _`PostgreSQL`: https://www.postgresql.org/
    """

    #: Default dialect used by SQLAlchemy to communicate with PostgreSQL;
    #: see also [`DBMS-PS-1 <https://docs.sqlalchemy.org/dialects/postgresql.html>`_].
    DEFAULT_DIALECT: str = 'postgresql'
    #: Default name of the database driver.
    DEFAULT_DRIVER: str = 'psycopg2'
    #: Default host name/address (typically `localhost`).
    DEFAULT_HOST: str = 'localhost'
    #: Default listening port used by PostgreSQL.
    DEFAULT_PORT: str = 5432
    #: Default username.
    DEFAULT_USERNAME: str = 'postgres'
    #: Default database name (usually created during PostgreSQL installation).
    DEFAULT_DATABASE: str = 'postgres'
    #: Default schema name created during PostgreSQL installation.
    DEFAULT_SCHEMA: str = 'public'
    #: Built-in schemas of PostgreSQL.
    BUILTIN_SCHEMAS: set = {
        'information_schema',
        # 'public',
    }

    def __init__(self, host=None, port=None, username=None, password=None, database_name=None,
                 confirm_db_creation=False, verbose=False, raise_error=False):
        """
        :param host: Host name/address of a PostgreSQL server,
            e.g. ``'localhost'`` or ``'127.0.0.1'``.
            If ``host=None``, it defaults to ``'localhost'``.
        :type host: str | None
        :param port: Listening port used by PostgreSQL.
            If ``port=None``, it defaults to ``5432``.
        :type port: int | None
        :param username: Username of the PostgreSQL server.
            If ``username=None``, it defaults to ``'postgres'``.
        :type username: str | None
        :param password: User password.
            If ``password=None``, it must be manually entered to connect to the PostgreSQL server.
        :type password: str | int | None
        :param database_name: Name of the database.
            If ``database_name=None``, it defaults to ``'postgres'``.
        :type database_name: str | None
        :param confirm_db_creation: Whether to prompt for confirmation
            before creating a new database if the specified database does not exist;
            defaults to ``False``.
        :type confirm_db_creation: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool

        :ivar str host: Host name/address.
        :ivar int port: Listening port used by PostgreSQL.
        :ivar str username: Username.
        :ivar str database_name: Name of the database.
        :ivar dict credentials: Basic information about the server/database being connected.
        :ivar str address: Representation of the database address.
        :ivar sqlalchemy.engine.Engine engine: `SQLAlchemy`_ connectable engine
            to a PostgreSQL server; see also [`DBMS-PS-2`_].

        .. _`DBMS-PS-2`:
            https://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine
        .. _`SQLAlchemy`:
            https://www.sqlalchemy.org/

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> # Connect the default database 'postgres'
            >>> postgres = PostgreSQL(verbose=True)
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/postgres ... Successfully.
            >>> postgres.address
            'postgres:***@localhost:5432/postgres'
            >>> # Connect a database 'testdb' (which will be created if it does not exist)
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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
            ...     def __init__(self, **kwargs):
            ...         super().__init__(**kwargs)
            >>> example_proxy = ExampleProxyObj(database_name='testdb', verbose=True)
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

        super().__init__()

        _ = _check_dependencies('psycopg2')

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
                self._create_db(
                    confirm_db_creation=confirm_db_creation, fmt='"{}"', verbose=verbose,
                    raise_error=raise_error)
            reconnect_db = True

        # make_database_address(self.host, self.port, self.username, self.database_name)
        self.address = self.engine.url.render_as_string(hide_password=True).split('//')[1]

        if verbose:
            print(f"Connecting {self.address}", end=" ... ")

        try:  # Create a SQLAlchemy connectable
            if reconnect_db:
                self.engine = sqlalchemy.create_engine(
                    url=self.engine.url, isolation_level='AUTOCOMMIT')

            test_conn = self.engine.connect()
            test_conn.close()
            del test_conn

            if verbose:
                print("Successfully.")

        except Exception as e:
            _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

    # == Database ==================================================================================

    def get_database_names(self, names_only=True):
        """
        Retrieves the names of all existing databases.

        :param names_only: Whether to return only the names of the databases; defaults to ``True``.
        :type names_only: bool
        :return: A list of database names if ``names_only`` is ``True``;
            otherwise, a dataframe containing detailed information.
        :rtype: list | pandas.DataFrame

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> # Connect the default database 'postgres'
            >>> postgres = PostgreSQL(verbose=True)
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/postgres ... Successfully.
            >>> isinstance(postgres.get_database_names(), list)
            True
            >>> 'postgres' in postgres.get_database_names()
            True
        """

        with self.engine.connect() as connection:
            query = sqlalchemy.text('SELECT datname FROM pg_database;')
            result = connection.execute(query)

        db_names = result.fetchall()
        if names_only:
            database_names = list(itertools.chain(*db_names))
        else:
            database_names = pd.DataFrame(db_names)

        return database_names

    def database_exists(self, database_name=None):
        """
        Checks if a specified database exists.

        :param database_name: Name of the database to check; defaults to ``None``.
        :type database_name: str | None
        :return: ``True`` if the database exists, otherwise ``False``.
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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

        query = \
            f"SELECT EXISTS(SELECT datname FROM pg_catalog.pg_database " \
            f"WHERE datname='{db_name}');"

        result = bool(self._execute(query)[0])

        return result

    def create_database(self, database_name, verbose=False):
        """
        Creates a database.

        :param database_name: Name of the database to be created.
        :type database_name: str
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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

        self._create_database(database_name=database_name, verbose=verbose, fmt='"{}"')

    def connect_database(self, database_name=None, verbose=False, raise_error=False):
        """
        Establishes a connection to a database.

        :param database_name: Name of the database.
            If ``database_name=None`` (default), the database name must be input manually.
        :type database_name: str | None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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
            db_name = str(database_name)  # self.database_name = str(database_name)

            self.address = make_database_address(
                host=self.host, port=self.port, username=self.username,
                database_name=db_name)

            if verbose:
                print(f"Connecting {self.address}", end=" ... ")

            try:
                self.credentials['database'] = db_name
                url = self.engine.url.set(database=db_name)

                if not self.database_exists(database_name=db_name):
                    self.create_database(database_name=db_name)

                self.engine = sqlalchemy.create_engine(url, isolation_level='AUTOCOMMIT')

                if verbose:
                    print("Successfully.")

                self.database_name = self.credentials['database']

            except Exception as e:
                _print_failure_message(
                    e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

        else:
            if verbose:
                print(f"Being connected with {self.address}.")

    def get_database_size(self, database_name=None):
        """
        Retrieves the size of a database.

        :param database_name: Name of the database.
            If ``database_name=None`` (default), it retrieves the size of the currently-connected
            database.
        :type database_name: str | None
        :return: Size of the database.
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.
            >>> testdb.get_database_size()
            '7900 kB'
            >>> testdb.DEFAULT_DATABASE
            'postgres'
            >>> testdb.get_database_size(database_name=testdb.DEFAULT_DATABASE)
            '7828 kB'
            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        db_name = 'current_database()' if database_name is None else f'\'{database_name}\''

        with self.engine.connect() as connection:
            query = sqlalchemy.text(f'SELECT pg_size_pretty(pg_database_size({db_name})) AS size;')
            result = connection.execute(query)

        db_size = result.fetchone()[0]

        return db_size

    def disconnect_database(self, database_name=None, verbose=False, raise_error=False):
        """
        Disconnects from a database.


        See also [`DBMS-PS-DD-1 <https://stackoverflow.com/questions/17449420/>`_].

        :param database_name: Name of the database to disconnect from.
            If ``database_name=None`` (default), disconnect from the current database.
        :type database_name: str | None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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
            print(f"Disconnecting the database \"{db_name}\" ... ", end="")

        try:
            self.connect_database(database_name=self.DEFAULT_DATABASE)

            with self.engine.connect() as connection:
                s1 = sqlalchemy.text(
                    f'REVOKE CONNECT ON DATABASE "{db_name}" FROM public, postgres;')
                connection.execute(s1)

                s2 = sqlalchemy.text(
                    f"SELECT pg_terminate_backend(pid) "
                    f"FROM pg_stat_activity "
                    f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid();")
                connection.execute(s2)

            if verbose:
                print("Done.")

        except Exception as e:
            _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

    def disconnect_all_others(self):
        """
        Terminates connections to all databases except the currently-connected one.

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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
        with self.engine.connect() as connection:
            query = sqlalchemy.text(
                'SELECT pg_terminate_backend(pid) FROM pg_stat_activity '
                'WHERE pid <> pg_backend_pid();')
            connection.execute(query)

    def drop_database(self, database_name=None, confirmation_required=True, verbose=False):
        """
        Deletes/drops a database.

        :param database_name: Name of the database to be dropped.
            If ``database_name=None`` (default), drop the currently connected database.
        :type database_name: str | None
        :param confirmation_required: Whether to prompt for confirmation before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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

        self._drop_database(
            database_name=database_name, fmt='"{}"', confirmation_required=confirmation_required,
            verbose=verbose)

    # == Schema ====================================================================================

    def schema_exists(self, schema_name):
        """
        Checks if a schema exists.

        :param schema_name: Name of the schema to check.
        :type schema_name: str
        :return: ``True`` if the schema exists, otherwise ``False``.
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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

        schema_name_ = self._schema_name(schema_name=schema_name)

        query = \
            f"SELECT EXISTS(" \
            f"SELECT schema_name FROM information_schema.schemata " \
            f"WHERE schema_name='{schema_name_}');"

        result = bool(self._execute(query)[0])

        return result

    def create_schema(self, schema_name, verbose=False, raise_error=False):
        """
        Creates a schema.

        :param schema_name: Name of the schema to be created.
        :type schema_name: str
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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
                with self.engine.connect() as connection:
                    query = sqlalchemy.text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name_}";')
                    connection.execute(query)
                if verbose:
                    print("Done.")
            except Exception as e:
                _print_failure_message(
                    e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

        else:
            print("The schema \"{}\" already exists.".format(schema_name))

    def get_schema_info(self, names_only=True, include_all=False, column_names=None, verbose=False):
        """
        Retrieves information about existing schemas.

        :param names_only: Whether to return only the names of the schemas; defaults to ``True``.
        :type names_only: bool
        :param include_all: Whether to list all available schemas; defaults to ``False``.
        :type include_all: bool
        :param column_names: Column names for the returned dataframe if ``names_only=False``;
            defaults to ``['schema_name', 'schema_id', 'role']`` if ``column_names=None``.
        :type column_names: list | None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :return: Names of schemas or a dataframe with schema information if requested.
        :rtype: list | pandas.DataFrame | None

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.
            >>> testdb.get_schema_info()
            ['public']
            >>> testdb.get_schema_info(names_only=False, include_all=True)
                      schema_name       schema_owner    oid  nspowner
            0              public  pg_database_owner   2200      6171
            1            pg_toast           postgres     99        10
            2          pg_catalog           postgres     11        10
            3  information_schema           postgres  13183        10
            >>> testdb.create_schema(schema_name='test_schema', verbose=True)
            Creating a schema: "test_schema" ... Done.
            >>> testdb.get_schema_info()
            ['public', 'test_schema']
            >>> testdb.drop_schema(schema_names=['public', 'test_schema'], verbose=True)
            To drop the following schemas from postgres:***@localhost:5432/testdb:
                "public"
                "test_schema"
            ? [No]|Yes: yes
            Dropping ...
                "public" ... Done.
                "test_schema" ... Done.
            >>> testdb.get_schema_info() is None
            True
            >>> testdb.get_schema_info(verbose=True)
            No schema exists in the currently-connected database "testdb".
            >>> testdb.drop_database(verbose=True)  # Delete the database "testdb"
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        condition = ""
        # Note: Use '%%' for '%' in SQL statements, as '%' in Python is used for string formatting
        if not include_all:
            condition = "WHERE nspname NOT IN ('information_schema', 'pg_catalog') " \
                        "AND nspname NOT LIKE 'pg_toast%%' " \
                        "AND nspname NOT LIKE 'pg_temp%%' "

        with self.engine.connect() as connection:
            query = sqlalchemy.text(
                f"SELECT s.schema_name, s.schema_owner, c.oid, c.nspowner "
                f"FROM pg_catalog.pg_namespace c "
                f"JOIN information_schema.schemata s ON c.nspname = s.schema_name "
                f"{condition}"
                f"ORDER BY s.schema_owner;")
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
                    column_names = ['schema_name', 'schema_owner', 'oid', 'nspowner']
                else:
                    assert len(column_names) == len(schema_info_[0]), \
                        f"`column_names` must be a list of strings and " \
                        f"its length must equal {len(schema_info_[0])}."
                schema_info = pd.DataFrame(schema_info_, columns=column_names)

        return schema_info

    def drop_schema(self, schema_names, confirmation_required=True, verbose=False):
        """
        Deletes/drops one or multiple schemas.

        :param schema_names: Name of one schema or names of multiple schemas to be dropped.
        :type schema_names: str | typing.Iterable[str]
        :param confirmation_required: Whether to prompt for confirmation before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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

        self._drop_schema(
            schema_names=schema_names, fmt='"{}"', query_='DROP SCHEMA "{}" CASCADE;',
            confirmation_required=confirmation_required, verbose=verbose)

    # == Table =====================================================================================

    def table_exists(self, table_name, schema_name=None):
        """
        Checks if a table exists.

        :param table_name: Name of the table to check.
        :type table_name: str
        :param schema_name: Name of the schema;
            if ``schema_name=None`` (default),
            it defaults to :attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``).
        :type schema_name: str | None
        :return: ``True`` if the table exists in the currently-connected database,
            otherwise ``False``.
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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

        query = \
            f"SELECT EXISTS(" \
            f"SELECT * FROM information_schema.tables " \
            f"WHERE table_schema='{schema_name_}' AND table_name='{table_name}');"

        result = bool(self._execute(query)[0])

        return result

    def create_table(self, table_name, column_specs, schema_name=None, verbose=False,
                     raise_error=False):
        """
        Creates a table.

        :param table_name: Name of the table to be created.
        :type table_name: str
        :param column_specs: Specifications for each column of the table.
        :type column_specs: str
        :param schema_name: Name of the schema;
            if ``schema_name=None`` (default),
            it defaults to :attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``).
        :type schema_name: str | None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool

        .. _dbms-postgresql-create_table-example:

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.
            >>> # Create a new table named 'test_table'
            >>> tbl_name = 'test_table'
            >>> col_spec = 'col_name_1 INT, col_name_2 TEXT'
            >>> testdb.create_table(table_name=tbl_name, column_specs=col_spec, verbose=True)
            Creating a table "public"."test_table" ... Done.
            >>> testdb.table_exists(table_name=tbl_name)
            True
            >>> # Get information about all columns of the table "public"."test_table"
            >>> test_tbl_col_info = testdb.get_column_info(table_name=tbl_name, as_dict=False)
            >>> test_tbl_col_info.head()
                                        column_0      column_1
            table_catalog                 testdb        testdb
            table_schema                  public        public
            table_name                test_table    test_table
            column_name               col_name_1    col_name_2
            ordinal_position                   1             2
            >>> # Get data types of all columns of the table "public"."test_table"
            >>> test_tbl_dtypes = testdb.get_column_dtype(table_name=tbl_name)
            >>> test_tbl_dtypes
            {'col_name_1': 'integer', 'col_name_2': 'text'}
            >>> testdb.validate_column_names(table_name=tbl_name)
            '"col_name_1", "col_name_2"'
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

        super()._create_table(
            table_name=table_name, column_specs=column_specs, schema_name=schema_name,
            verbose=verbose, raise_error=raise_error)

    def get_column_info(self, table_name, schema_name=None, as_dict=True):
        """
        Retrieves information about columns of a table.

        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema;
            if ``schema_name=None`` (default),
            it defaults to :attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``).
        :type schema_name: str | None
        :param as_dict: Whether to return the column information as a dictionary;
            defaults to ``True``.
        :type as_dict: bool
        :return: Information about all columns of the given table.
        :rtype: pandas.DataFrame | dict

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.PostgreSQL.create_table`.
        """

        column_info = super().get_column_info(
            table_name=table_name, schema_name=schema_name, as_dict=as_dict)

        return column_info

    def get_column_dtype(self, table_name, column_names=None, schema_name=None):
        """
        Retrieves information about data types of all or specific columns of a table.

        :param table_name: Name of the table.
        :type table_name: str
        :param column_names: (List of) column name(s);
            if ``column_names=None`` (default), data types of all available columns are retrieved.
        :type column_names: str | list | None
        :param schema_name: Name of the schema;
            if ``schema_name=None`` (default),
            it defaults to :attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``).
        :return: Data types of all or specific columns of a table.
        :rtype: dict | None

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.PostgreSQL.create_table`.
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

        with self.engine.connect() as connection:
            query = sqlalchemy.text(
                f"SELECT column_name, data_type FROM information_schema.columns "
                f"WHERE table_name = '{table_name}' "
                f"AND table_schema = '{schema_name_}'{col_names_query};")
            result = connection.execute(query)

        column_dtypes_ = result.fetchall()

        if len(column_dtypes_) > 0:
            # noinspection PyTypeChecker
            column_dtypes = dict(column_dtypes_)
        else:
            column_dtypes = None

        return column_dtypes

    def validate_column_names(self, table_name, schema_name=None, column_names=None):
        """
        Validates column names for a query statement.

        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema; defaults to ``None``.
        :type schema_name: str | None
        :param column_names: Column name(s) for a dataframe.
        :type column_names: str | list | tuple | None
        :return: Validated column names formatted for a PostgreSQL query statement.
        :rtype: str

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.PostgreSQL.create_table`.
        """

        column_names_ = super().validate_column_names(
            schema_name=schema_name, table_name=table_name, column_names=column_names)

        return column_names_

    def get_table_names(self, schema_name=None, verbose=False):
        """
        Retrieves the names of all tables in a schema.

        :param schema_name: Name of the schema;
            if ``schema_name=None`` (default),
            it defaults to :attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``).
        :type schema_name: str | list | None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :return: Table names of the specified schema(s) ``schema_name``.
        :rtype: dict

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.
            >>> tbl_names = testdb.get_table_names()
            >>> tbl_names
            {'public': []}
            >>> tbl_names = testdb.get_table_names(schema_name='testdb', verbose=True)
            The schema "testdb" does not exist.
            >>> tbl_names
            {'testdb': []}
            >>> # Create a new table named "test_table" in the schema "testdb"
            >>> new_tbl_name = 'test_table'
            >>> col_spec = 'col_name_1 INT, col_name_2 TEXT'
            >>> testdb.create_table(table_name=new_tbl_name, column_specs=col_spec, verbose=True)
            Creating a table: "public"."test_table" ... Done.
            >>> tbl_names = testdb.get_table_names(schema_name='public')
            >>> tbl_names
            {'public': ['test_table']}
            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        table_names = super().get_table_names(schema_name=schema_name, verbose=verbose)

        return table_names

    def alter_table_schema(self, table_name, schema_name, new_schema_name,
                           confirmation_required=True, verbose=False, raise_error=False):
        """
        Moves a table from one schema to another within the currently-connected database.

        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the current schema containing the table.
        :type schema_name: str
        :param new_schema_name: Name of the new schema to move the table to.
        :type new_schema_name: str
        :param confirmation_required: Whether to prompt for confirmation before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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
            >>> tbl_names = testdb.get_table_names(schema_name='test_schema')
            >>> tbl_names
            {'test_schema': ['test_table']}
            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        if self.table_exists(table_name=table_name, schema_name=schema_name):

            cfm_msg = f"To move the table \"{table_name}\" " \
                      f"from the schema \"{schema_name}\" to \"{new_schema_name}\"\n?"
            if _confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):

                if not self.schema_exists(schema_name=new_schema_name):
                    self.create_schema(schema_name=new_schema_name, verbose=verbose)

                table_name_ = f'"{schema_name}"."{table_name}"'

                if verbose:
                    if confirmation_required:
                        log_msg = f'Moving {table_name_} to "{new_schema_name}"'
                    else:
                        log_msg = (f'Moving the table "{table_name}" '
                                   f'from "{schema_name}" to "{new_schema_name}"')
                    print(log_msg, end=" ... ")

                try:
                    with self.engine.connect() as connection:
                        query = sqlalchemy.text(
                            f'ALTER TABLE {table_name_} SET SCHEMA "{new_schema_name}";')
                        connection.execute(query)

                    if verbose:
                        print("Done.")

                except Exception as e:
                    _print_failure_message(
                        e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

        else:
            print(f'The table "{schema_name}"."{table_name}" does not exist.')

    def add_primary_keys(self, primary_keys, table_name, schema_name=None):
        """
        Adds a primary key or multiple primary keys to a table.

        :param primary_keys: (List of) primary key(s) to be added.
        :type primary_keys: str | list | None
        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema; defaults to ``None``.
        :type schema_name: str | None

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.PostgreSQL.get_primary_keys`.
        """

        if primary_keys is not None:
            # If any null values in 'text' columns, replace null values with empty strings
            self.null_text_to_empty_string(
                table_name=table_name, column_names=primary_keys, schema_name=schema_name)

            pri_keys = [primary_keys] if isinstance(primary_keys, str) else copy.copy(primary_keys)

            if len(pri_keys) == 1:
                primary_keys_ = '("{}")'.format(pri_keys[0])
            else:
                primary_keys_ = str(tuple(pri_keys)).replace("'", '"')

            with self.engine.connect() as connection:
                table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)
                query = f'ALTER TABLE {table_name_} ADD PRIMARY KEY {primary_keys_};'
                query_ = sqlalchemy.text(query)
                connection.execute(query_)

    def get_primary_keys(self, table_name, schema_name=None, names_only=True):
        """
        Retrieves the primary keys of a table.

        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema; defaults to ``None``.
        :type schema_name: str | None
        :param names_only: Whether to return only the names of the primary keys;
            defaults to ``True``.
        :type names_only: bool
        :return: Primary key(s) of the given table.
        :rtype: list | pandas.DataFrame

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> from pyhelpers._cache import example_dataframe
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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

        query_ = \
            f"SELECT a.attname AS key_column, format_type(a.atttypid, a.atttypmod) AS data_type " \
            f"FROM pg_index i " \
            f"JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) " \
            f"WHERE i.indrelid = '{table_name_}'::regclass AND i.indisprimary;"

        with self.engine.connect() as connection:
            query = sqlalchemy.text(query_)
            result = connection.execute(query)

        primary_keys_ = result.fetchall()

        if names_only:
            primary_keys = [x[0] for x in primary_keys_]  # list(zip(*primary_keys_))[0]
        else:
            primary_keys = pd.DataFrame(primary_keys_)

        return primary_keys

    def null_text_to_empty_string(self, table_name, column_names=None, schema_name=None):
        """
        Converts null values (in text columns) to empty strings.

        :param table_name: Name of the table.
        :type table_name: str
        :param column_names: (List of) column name(s) to convert null values to empty strings;
            if ``column_names=None`` (default), all available columns are included.
        :type column_names: str | list | None
        :param schema_name: Name of the schema; defaults to ``None``.
        :type schema_name: str | None

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> from pyhelpers._cache import example_dataframe
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.
            >>> dat = example_dataframe()
            >>> dat['Longitude'] = dat['Longitude'].astype(str)
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
            >>> dat_ = testdb.read_table(tbl_name)
            >>> dat_.loc[0, 'Longitude'] is None
            True

        .. figure:: ../_images/dbms-postgresql-null_text_to_empty_string-demo-1.*
            :name: dbms-postgresql-null_text_to_empty_string-demo-1
            :align: center
            :width: 55%

            The table "*test_table*" in the database "*testdb*".

        .. code-block:: python

            >>> # Replace the 'null' value with an empty string
            >>> testdb.null_text_to_empty_string(table_name=tbl_name)
            >>> dat_ = testdb.read_table(tbl_name)
            >>> dat_.loc[0, 'Longitude']
            ''

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
            cols_query = ', '.join(f'"{x}"=COALESCE("{x}", \'\')' for x in text_columns)
            table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

            with self.engine.connect() as connection:
                query = sqlalchemy.text(f'UPDATE {table_name_} SET {cols_query};')
                connection.execute(query)

    @staticmethod
    def psql_insert_copy(sql_table, sql_db_engine, column_names, data_iter):
        """
        Callable function using *PostgreSQL* ``COPY`` clause for executing data insertion.

        :param sql_table: Object that represents the table to insert into.
        :type sql_table: pandas.io.sql.SQLTable
        :param sql_db_engine: Object that represents the database engine or connection.
        :type sql_db_engine: sqlalchemy.engine.Connection | sqlalchemy.engine.Engine
        :param column_names: List of column names to insert data into.
        :type column_names: list[str]
        :param data_iter: Iterable that iterates over the values to be inserted.
        :type data_iter: typing.Iterable

        .. _`sqlalchemy.engine.Connection`:
            https://docs.sqlalchemy.org/en/13/core/connections.html#sqlalchemy.engine.Connection
        .. _`sqlalchemy.engine.Engine`:
            https://docs.sqlalchemy.org/en/13/core/connections.html#sqlalchemy.engine.Engine

        .. note::

            This function is modified from the source code available at
            [`DBMS-PS-PIC-1
            <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method>`_].
        """

        con_cur = sql_db_engine.connection.cursor()
        io_buffer = io.StringIO()
        csv_writer = csv.writer(io_buffer)
        csv_writer.writerows(data_iter)
        io_buffer.seek(0)

        sql_column_names = ', '.join(f'"{k}"' for k in column_names)
        sql_table_name = f'"{sql_table.schema}"."{sql_table.name}"'

        sql_query = f'COPY {sql_table_name} ({sql_column_names}) FROM STDIN WITH CSV'
        con_cur.copy_expert(sql=sql_query, file=io_buffer)

    def import_data(self, data, table_name, schema_name=None, if_exists='fail', force_replace=False,
                    chunk_size=None, col_type=None, method='multi', index=False,
                    confirmation_required=True, verbose=False, **kwargs):
        """
        Imports tabular data into a table.

        See also [`DBMS-PS-ID-1
        <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method>`_]
        and [`DBMS-PS-ID-2
        <https://www.postgresql.org/docs/current/sql-copy.html>`_].

        :param data: Tabular data to be imported into the database.
        :type data: pandas.DataFrame | pandas.io.parsers.TextFileReader | list | tuple
        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema;
            if ``schema_name=None`` (default),
            it defaults to :attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``).
        :type schema_name: str | None
        :param if_exists: Action to take if the table already exists. Options are ``'replace'``,
            ``'append'`` or ``'fail'`` (default).
        :type if_exists: str
        :param force_replace: Whether to force replace an existing table; defaults to ``False``.
        :type force_replace: bool
        :param chunk_size: Number of rows in each batch to be written at a time;
            defaults to ``None``.
        :type chunk_size: int | None
        :param col_type: Data types for columns; defaults to ``None``.
        :type col_type: dict | None
        :param method: Method for SQL insertion clause; defaults to ``'multi'``.

            - ``None``: Uses standard SQL ``INSERT`` clause (one per row).
            - ``'multi'``: Passes multiple values in a single ``INSERT`` clause.
            - Callable (e.g. ``PostgreSQL.psql_insert_copy``) with signature
              ``(pd_table, conn, keys, data_iter)``.

        :type method: str | None | typing.Callable
        :param index: Whether to include the index as a column in the table.
        :type index: bool
        :param confirmation_required: Whether to prompt for confirmation before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param kwargs: [Optional] Additional parameters for the method `pandas.DataFrame.to_sql()`_.

        .. _`pandas.DataFrame.to_sql()`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.PostgreSQL.read_sql_query`.
        """

        self._import_data(
            data, table_name, schema_name=schema_name, if_exists=if_exists,
            force_replace=force_replace, chunk_size=chunk_size, col_type=col_type, method=method,
            index=index, confirmation_required=confirmation_required, verbose=verbose,
            **kwargs)

    def read_sql_query(self, sql_query, method='tempfile', max_size_spooled=1, delimiter=',',
                       tempfile_kwargs=None, stringio_kwargs=None, **kwargs):
        # noinspection PyShadowingNames
        """
        Reads table data by executing a SQL query (recommended for large tables).

        See also
        [`DBMS-PS-RSQ-1 <https://towardsdatascience.com/f31cd7f707ab>`_],
        [`DBMS-PS-RSQ-2 <https://docs.python.org/3/library/tempfile.html>`_] and
        [`DBMS-PS-RSQ-3 <https://docs.python.org/3/library/io.html>`_].

        :param sql_query: SQL query to be executed.
        :type sql_query: str
        :param method: Method to be used for buffering temporary data.

            - ``'tempfile'`` (default): Uses `tempfile.TemporaryFile()`_.
            - ``'stringio'``: Uses `io.StringIO()`_.
            - ``'spooled'``: Uses `tempfile.SpooledTemporaryFile()`_.

        :type method: str
        :param max_size_spooled: Maximum size of the file generated via
            `tempfile.SpooledTemporaryFile()`_; defaults to ``1`` (in gigabyte).
        :type max_size_spooled: int | float
        :param delimiter: Delimiter used in data; defaults to ``','``.
        :type delimiter: str
        :param tempfile_kwargs: [Optional] Additional parameters for `tempfile.TemporaryFile()`_ or
            `tempfile.SpooledTemporaryFile()`_; defaults to ``None``.
        :param stringio_kwargs: [Optional] Additional parameters for `io.StringIO()`_,
            e.g. ``initial_value``; defaults to ``None``.
        :param kwargs: [Optional] Additional parameters for the function `pandas.read_csv()`_.
        :return: Data queried by the statement ``sql_query``.
        :rtype: pandas.DataFrame

        .. _`pandas.read_csv()`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html
        .. _`tempfile.TemporaryFile()`:
            https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryFile
        .. _`tempfile.SpooledTemporaryFile()`:
            https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile
        .. _`io.StringIO()`:
            https://docs.python.org/3/library/io.html#io.StringIO

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> from pyhelpers._cache import example_dataframe
            >>> testdb = PostgreSQL(database_name='testdb', verbose=True)
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

            >>> res = testdb.table_exists(table_name=table, schema_name=schema)
            >>> print(f"The table \"{schema}\".\"{table}\" exists? {res}.")
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

        **Aside:** a brief example of using the parameter ``params`` for `pandas.read_sql
        <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_sql.html>`_

        .. code-block:: python

            >>> import datetime
            >>> import pandas as pd
            >>> sql_qry = 'SELECT * FROM "table_name" '
            ...           'WHERE "timestamp_column_name" BETWEEN %(ts_start)s AND %(ts_end)s'
            >>> params = {'d_start': datetime.datetime.today(), 'd_end': datetime.datetime.today()}
            >>> data_frame = pd.read_sql(sql=sql_qry, con=testdb.engine, params=params)
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

        connection = self.engine.raw_connection()
        try:
            # Get a cursor
            cursor = connection.cursor()
            cursor.copy_expert(copy_sql, csv_temp)

            # Rewind the file handle using seek() in order to read the data back from it
            csv_temp.seek(0)

            table_data = pd.read_csv(csv_temp, **kwargs)  # Read data from temporary csv

            csv_temp.close()  # Close the temp file
            cursor.close()  # Close the cursor
        finally:
            connection.close()  # Close the connection

        return table_data

    def read_table(self, table_name, schema_name=None, conditions=None, chunk_size=None,
                   sorted_by=None, **kwargs):
        """
        Reads data from a specified table.

        See also [`DBMS-PS-RT-1 <https://stackoverflow.com/questions/24408557/>`_].

        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema;
            if ``schema_name=None``,
            it defaults to :attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e., ``'public'``).
        :type schema_name: str | None
        :param conditions: SQL conditions to filter rows; defaults to ``None``.
        :type conditions: str | None
        :param chunk_size: Number of rows to fetch per iteration; defaults to ``None``.
        :type chunk_size: int | None
        :param sorted_by: Name(s) of column(s) by which the retrieved data is sorted;
            defaults to ``None``.
        :type sorted_by: str | None
        :param kwargs: [Optional] Additional parameters for the method
            :meth:`~pyhelpers.dbms.PostgreSQL.read_sql_query` or the function `pandas.read_sql()`_.
        :return: Data of the specified table.
        :rtype: pandas.DataFrame

        .. _`pandas.read_sql()`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_sql.html

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.PostgreSQL.read_sql_query`.
        """

        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name)

        sql_query = f'SELECT * FROM {table_name_}'
        if conditions:
            assert isinstance(conditions, str), "`conditions` must be in 'str' type."
            sql_query += (' ' + conditions)

        if bool(set(kwargs.keys()).intersection(self._read_sql_query_args())):
            data = self.read_sql_query(sql_query=sql_query, chunksize=chunk_size, **kwargs)
        else:
            with self.engine.connect() as connection:
                sql_query_ = sqlalchemy.text(sql_query)
                data = pd.read_sql(sql=sql_query_, con=connection, chunksize=chunk_size, **kwargs)

        if sorted_by:
            # noinspection PyUnboundLocalVariable
            data.sort_values(sorted_by, inplace=True, ignore_index=True)

        return data

    def drop_table(self, table_name, schema_name=None, confirmation_required=True, verbose=False,
                   raise_error=False):
        """
        Deletes/drops a specified table.

        :param table_name: Name of the table to be deleted.
        :type table_name: str
        :param schema_name: Name of the schema;
            if ``schema_name=None``,
            it defaults to :attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e., ``'public'``).
        :type schema_name: str | None
        :param confirmation_required: Whether to prompt for confirmation before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool

        .. seealso::

            - Examples for the method :meth:`~pyhelpers.dbms.PostgreSQL.create_table`.
        """

        self._drop_table(
            table_name, query_fmt='DROP TABLE {} CASCADE;', schema_name=schema_name,
            confirmation_required=confirmation_required, verbose=verbose, raise_error=raise_error)
