"""
Communication with databases.

*(The current release includes* `PostgreSQL <https://www.postgresql.org/>`_ *only.)*
"""

import copy
import csv
import gc
import getpass
import inspect
import io
import tempfile

import pandas as pd
import pandas.io.parsers
import sqlalchemy
import sqlalchemy.engine

from .ops import confirmed


def _make_database_address(host, port, username, database_name=""):
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

    **Test**::

        >>> from pyhelpers.dbms import _make_database_address

        >>> db_addr = _make_database_address('localhost', 5432, 'postgres', 'postgres')
        >>> db_addr
        'postgres:***@localhost:5432/postgres'
    """

    database_address = f"{username}:***@{host}:{port}"

    if database_name:
        database_address += f"/{database_name}"

    return database_address


def _get_database_address(db_cls):
    """
    Get default database address of a given class in the current module.

    :param db_cls: a class representation of a database
    :type db_cls: object
    :return: default address of database
    :rtype: str

    **Test**::

        >>> from pyhelpers.dbms import _get_database_address, PostgreSQL

        >>> db_addr = _get_database_address(db_cls=PostgreSQL)
        >>> db_addr
        'None:***@None:None'
    """

    args_spec = inspect.getfullargspec(func=db_cls)

    args_dict = dict(zip([x for x in args_spec.args if x != 'self'], args_spec.defaults))

    database_address = _make_database_address(
        args_dict['host'], args_dict['port'], args_dict['username'], args_dict['database_name'])

    return database_address


class PostgreSQL:
    """
    A class for basic communication with a `PostgreSQL`_ server.

    .. _`PostgreSQL`: https://www.postgresql.org/
    """

    #: Default dialect.
    #: The system that SQLAlchemy uses to communicate with PostgreSQL; see also
    #: [`DBMS-P-SP-1 <https://docs.sqlalchemy.org/en/13/dialects/postgresql.html>`_]
    DEFAULT_DIALECT = 'postgresql'
    #: Default name of database driver
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
            if ``host=None`` (default), it is initialized as ``'localhost'``
        :type host: str or None
        :param port: listening port used by PostgreSQL;
            if ``port=None`` (default), initialized as ``5432`` (default by installation of PostgreSQL)
        :type port: int or None
        :param username: username of a PostgreSQL server; if ``username=None`` (default),
            initialized as ``'postgres'`` (default by installation of PostgreSQL)
        :type username: str or None
        :param password: user password; if ``password=None`` (default),
            it is required to mannually type in the correct password to connect the PostgreSQL server
        :type password: str or int or None
        :param database_name: name of a database; if ``database=None`` (default),
            initialized as ``'postgres'`` (default by installation of PostgreSQL)
        :type database_name: str or None
        :param confirm_db_creation: whether to prompt a confirmation before creating a new database
            (if the specified database does not exist), defaults to ``False``
        :type confirm_db_creation: bool
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``True``
        :type verbose: bool or int

        :ivar str host: host name/address
        :ivar str port: listening port used by PostgreSQL
        :ivar str username: username
        :ivar str database_name: name of a database
        :ivar dict database_info: basic information about the server/database being connected
        :ivar sqlalchemy.engine.URL url: PostgreSQL database URL; see also [`DBMS-P-SP-2`_]
        :ivar str address: representation of the database address
        :ivar sqlalchemy.engine.Engine engine: `SQLAlchemy`_ engine class; see also [`DBMS-P-SP-3`_]

        .. _`DBMS-P-SP-1`:
            https://docs.sqlalchemy.org/en/latest/dialects/postgresql.html
        .. _`DBMS-P-SP-2`:
            https://docs.sqlalchemy.org/en/latest/core/engines.html#postgresql
        .. _`DBMS-P-SP-3`:
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

        self.host = self.DEFAULT_HOST if host is None else str(host)
        self.port = self.DEFAULT_PORT if port is None else int(port)
        self.username = self.DEFAULT_USERNAME if username is None else str(username)

        if password is None:
            pwd = getpass.getpass(f'Password ({self.username}@{self.host}:{self.port}): ')
        else:
            pwd = str(password)

        self.database_name = self.DEFAULT_DATABASE if database_name is None else str(database_name)

        self.database_info = {
            'drivername': '+'.join([self.DEFAULT_DIALECT, self.DEFAULT_DRIVER]),
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': pwd,
            'database': self.database_name,
        }
        # The typical form of the URL: backend+driver://username:password@host:port/database
        self.url = sqlalchemy.engine.URL.create(**self.database_info)

        if self.database_name != self.DEFAULT_DATABASE:
            self.engine = sqlalchemy.create_engine(
                url=self.url.set(database=self.DEFAULT_DATABASE), isolation_level='AUTOCOMMIT')
            db_exists = self.engine.execute(
                f"SELECT EXISTS("
                f"SELECT datname FROM pg_catalog.pg_database "
                f"WHERE datname='{self.database_name}');").fetchone()[0]
        else:
            db_exists = True

        if not db_exists:  # The database doesn't exist
            cfm_msg = f"The database \"{self.database_name}\" does not exist. Proceed by creating it\n?"
            if confirmed(prompt=cfm_msg, confirmation_required=confirm_db_creation):
                if verbose:
                    print(f"Creating a database: \"{self.database_name}\"", end=" ... ")
                try:
                    self.engine.execute(f'CREATE DATABASE "{self.database_name}";')
                    self.engine.dispose()
                    if verbose:
                        print("Done.")
                except Exception as e:
                    if verbose:
                        print("Failed. {}".format(e))

        # self.address = _make_database_address(host_, port_, username_, database_name_)
        self.address = self.url.render_as_string(hide_password=True).split('//')[1]
        if verbose:
            print("Connecting {}".format(self.address), end=" ... ")

        try:  # Create a SQLAlchemy connectable
            self.engine = sqlalchemy.create_engine(url=self.url, isolation_level='AUTOCOMMIT')
            if verbose:
                print("Successfully.")
        except Exception as e:
            print("Failed. {}".format(e))
        # self.connection = self.engine.raw_connection()

    def database_exists(self, database_name=None):
        """
        Check whether a database exists in the currently-connected server.

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
            >>> testdb.database_exists('testdb')
            True
            >>> testdb.database_name
            'testdb'

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.

            >>> # Check again whether the database "testdb" still exists now
            >>> testdb.database_exists('testdb')
            False
            >>> testdb.database_name
            'postgres'
        """

        db_name = copy.copy(self.database_name) if database_name is None else str(database_name)

        result = self.engine.execute(
            f"SELECT EXISTS(SELECT datname FROM pg_catalog.pg_database WHERE datname='{db_name}');")

        return result.fetchone()[0]

    def create_database(self, database_name, verbose=False):
        """
        Create a database in the currently-connected server.

        :param database_name: name of a database
        :type database_name: str
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
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

        if not self.database_exists(database_name=database_name):
            if verbose:
                print("Creating a database: \"{}\" ... ".format(database_name), end="")

            self.disconnect_database()
            self.engine.execute('CREATE DATABASE "{}";'.format(database_name))

            if verbose:
                print("Done.")

        else:
            if verbose:
                print("The database already exists.")

        self.connect_database(database_name=database_name)

    def connect_database(self, database_name=None, verbose=False):
        """
        Establish a connection to a database in the currently-connected server.

        :param database_name: name of a database;
            if ``database_name=None`` (default), the database name is input manually
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

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
            >>> testdb.database_name
            'postgres'
        """

        if database_name is not None:
            self.database_name = str(database_name)
            self.address = _make_database_address(
                self.host, self.port, self.username, self.database_name)

            if verbose:
                print(f"Connecting {self.address}", end=" ... ")

            try:
                self.database_info['database'] = self.database_name
                self.url = sqlalchemy.engine.URL.create(**self.database_info)

                if not self.database_exists(self.database_name):
                    self.create_database(database_name=self.database_name)

                self.engine = sqlalchemy.create_engine(self.url, isolation_level='AUTOCOMMIT')
                # self.connection = self.engine.raw_connection()

                if verbose:
                    print("Successfully.")

            except Exception as e:
                print("Failed. {}".format(e))

        else:
            if verbose:
                print(f"Being connected with {self.address}.")

    def get_database_size(self, database_name=None):
        """
        Get the size of a database in the currently-connected server.

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
            '8577 kB'

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
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
        Kill the connection to a database in the currently-connected server.

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

            self.engine.execute(
                'REVOKE CONNECT ON DATABASE "{}" FROM PUBLIC, postgres;'.format(db_name))

            self.engine.execute(
                'SELECT pg_terminate_backend(pid) '
                'FROM pg_stat_activity '
                'WHERE datname = \'{}\' AND pid <> pg_backend_pid();'.format(db_name))

            if verbose:
                print("Done.")

        except Exception as e:
            print("Failed. {}".format(e))

    def disconnect_all_others(self):
        """
        Kill connections to all other databases in the currently-connected server.

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

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        # self.connect_database(database_name='postgres')
        self.engine.execute(
            'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid();')

    def drop_database(self, database_name=None, confirmation_required=True, verbose=False):
        """
        Delete/drop a database from the currently-connected server.

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

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
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

        db_name = copy.copy(self.database_name) if database_name is None else str(database_name)

        if not self.database_exists(database_name=db_name):
            if verbose:
                print("The database \"{}\" does not exist.".format(db_name))

        else:
            # address_ = self.address.replace(f"/{db_name}", "")
            address_ = self.address.split('/')[0]
            cfm_msg = "To drop the database \"{}\" from {}\n?".format(db_name, address_)
            if confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):
                self.disconnect_database(db_name)

                if verbose:
                    if confirmation_required:
                        log_msg = "Dropping \"{}\"".format(db_name)
                    else:
                        log_msg = "Dropping the database \"{}\" from {}".format(db_name, address_)
                    print(log_msg, end=" ... ")

                try:
                    self.engine.execute('DROP DATABASE "{}"'.format(db_name))

                    if verbose:
                        print("Done.")

                except Exception as e:
                    print("Failed. {}".format(e))

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
        Check whether a schema exists in the currently-connected database.

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

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        result = self.engine.execute(
            "SELECT EXISTS("
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name='{}');".format(schema_name))

        return result.fetchone()[0]

    def create_schema(self, schema_name, verbose=False):
        """
        Create a schema in the currently-connected database.

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

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        if not self.schema_exists(schema_name=schema_name):
            if verbose:
                print("Creating a schema: \"{}\" ... ".format(schema_name), end="")

            try:
                self.engine.execute('CREATE SCHEMA IF NOT EXISTS "{}";'.format(schema_name))
                if verbose:
                    print("Done.")
            except Exception as e:
                print("Failed. {}".format(e))

        else:
            print("The schema \"{}\" already exists.".format(schema_name))

    def list_schema_names(self, include_all=False, names_only=True, verbose=False):
        """
        List the names of schemas in the currently-connected database.

        :param include_all: whether to list all the available schemas, defaults to ``False``
        :type include_all: bool
        :param names_only: whether to return a list of schema names only, defaults to ``True``
        :type names_only: bool
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int
        :return: schema names
        :rtype: list or pandas.DataFrame or None

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.list_schema_names()
            ['public']

            >>> testdb.list_schema_names(include_all=True, names_only=False)
                      schema_name  schema_id      role
            0  information_schema      13388  postgres
            1          pg_catalog         11  postgres
            2            pg_toast         99  postgres
            3              public       2200  postgres

            >>> testdb.drop_schema(schema_names='public', verbose=True)
            To drop the schema "public" from postgres:***@localhost:5432/testdb
            ? [No]|Yes: >? yes
            Dropping "public" ... Done.

            >>> testdb.list_schema_names()  # None

            >>> testdb.list_schema_names(verbose=True)
            No schema exists in the currently-connected database "testdb".
        """

        condition = ""
        # Note: Use '%%' for '%' in SQL statements, as '%' in Python is used for string formatting
        if not include_all:
            condition = "WHERE nspname NOT IN ('information_schema', 'pg_catalog') " \
                        "AND nspname NOT LIKE 'pg_toast%%' " \
                        "AND nspname NOT LIKE 'pg_temp%%' "

        query = f"SELECT s.nspname, s.oid, u.usename FROM pg_catalog.pg_namespace s " \
                f"JOIN pg_catalog.pg_user u ON u.usesysid = s.nspowner " \
                f"{condition}" \
                f"ORDER BY s.nspname;"

        rslt = self.engine.execute(query)

        schema_info_ = rslt.fetchall()
        if not schema_info_:
            schema_info = None
            if verbose:
                print(f"No schema exists in the currently-connected database \"{self.database_name}\".")

        else:
            schema_info = pd.DataFrame(schema_info_, columns=['schema_name', 'schema_id', 'role'])

            if names_only:
                schema_info = schema_info['schema_name'].to_list()

        return schema_info

    def drop_schema(self, schema_names, confirmation_required=True, verbose=False):
        """
        Delete/drop one or multiple schemas from the currently-connected database.

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

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
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
                        log_msg = "Dropping the {}: ".format(print_plural, print_schema)
                    print(log_msg, end=" ... ")
                else:  # len(schemas) > 1
                    if confirmation_required:
                        print("Dropping ... ")
                    else:
                        print("Dropping the following {} from {}:".format(print_plural, self.address))

            for schema in schemas:
                if not self.schema_exists(schema):
                    # `schema` does not exist
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
        Check whether a table exists in the currently-connected database.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``None``;
            when ``schema_name=None``, consider
            :py:attr:`PostgreSQL.DEFAULT_SCHEMA<pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA>`
            (i.e. ``'public'``)
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

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        schema_name_ = copy.copy(self.DEFAULT_SCHEMA) if schema_name is None else str(schema_name)

        res = self.engine.execute(
            "SELECT EXISTS("
            "SELECT * FROM information_schema.tables "
            "WHERE table_schema='{}' AND table_name='{}');".format(schema_name_, table_name))

        return res.fetchone()[0]

    def create_table(self, table_name, column_specs, schema_name=None, verbose=False):
        """
        Create a table in the currently-connected database.

        :param table_name: name of a table
        :type table_name: str
        :param column_specs: specifications for each column of the table
        :type column_specs: str
        :param schema_name: name of a schema, defaults to ``None``;
            when ``schema_name=None``, consider
            :py:attr:`PostgreSQL.DEFAULT_SCHEMA<pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA>`
            (i.e. ``'public'``)
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

        schema_name_ = copy.copy(self.DEFAULT_SCHEMA) if schema_name is None else str(schema_name)
        table_ = '"{schema}"."{table}"'.format(schema=schema_name_, table=table_name)

        if self.table_exists(table_name=table_name, schema_name=schema_name_):
            if verbose:
                print("The table {} already exists.".format(table_))

        else:
            if not self.schema_exists(schema_name_):
                self.create_schema(schema_name=schema_name_, verbose=False)

            try:
                if verbose:
                    print("Creating a table: {} ... ".format(table_), end="")

                self.engine.execute('CREATE TABLE {} ({});'.format(table_, column_specs))

                if verbose:
                    print("Done.")

            except Exception as e:
                print("Failed. {}".format(e))

    def get_column_info(self, table_name, schema_name=None, as_dict=True):
        """
        Get information about columns of a table in the currently-connected database.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``None``;
            when ``schema_name=None``, consider
            :py:attr:`PostgreSQL.DEFAULT_SCHEMA<pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA>`
            (i.e. ``'public'``)
        :type schema_name: str or None
        :param as_dict: whether to return the column information as a dictionary, defaults to ``True``
        :type as_dict: bool
        :return: information about all columns of the given table
        :rtype: pandas.DataFrame or dict

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.PostgreSQL.create_table`.
        """

        schema_name_ = copy.copy(self.DEFAULT_SCHEMA) if schema_name is None else str(schema_name)

        column_info = self.engine.execute(
            "SELECT * FROM information_schema.columns "
            "WHERE table_schema='{}' AND table_name='{}';".format(schema_name_, table_name))

        keys, values = column_info.keys(), column_info.fetchall()
        idx = ['column_{}'.format(x) for x in range(len(values))]

        info_tbl = pd.DataFrame(values, index=idx, columns=keys).T

        if as_dict:
            info_tbl = {k: v.to_list() for k, v in info_tbl.iterrows()}

        return info_tbl

    def list_table_names(self, schema_name=None, verbose=False):
        """
        List the names of all tables in a schema in the currently-connected database.

        :param schema_name: name of a schema, defaults to ``None``;
            when ``schema_name=None``, it defaults to
            :py:attr:`PostgreSQL.DEFAULT_SCHEMA<pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA>`
            (i.e. ``'public'``)
        :type schema_name: str or None
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int
        :return: a list of table names
        :rtype: list or None

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> lst_tbl_names = testdb.list_table_names()
            >>> lst_tbl_names
            []

            >>> lst_tbl_names = testdb.list_table_names(schema_name='testdb', verbose=True)
            The schema "testdb" does not exist.

            >>> # Create a new table named "test_table" in the schema "testdb"
            >>> new_tbl_name = 'test_table'
            >>> col_spec = 'col_name_1 INT, col_name_2 TEXT'
            >>> testdb.create_table(table_name=new_tbl_name, column_specs=col_spec, verbose=True)
            Creating a table: "public"."test_table" ... Done.

            >>> lst_tbl_names = testdb.list_table_names(schema_name='public')
            >>> lst_tbl_names
            ['test_table']

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        schema_name_ = copy.copy(self.DEFAULT_SCHEMA) if schema_name is None else str(schema_name)

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
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
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

            >>> lst_tbl_names = testdb.list_table_names(schema_name='test_schema')
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

    def drop_table(self, table_name, schema_name=None, confirmation_required=True, verbose=False):
        """
        Delete/drop a table from the currently-connected database.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``None``;
            when ``schema_name=None``, it defaults to
            :py:attr:`PostgreSQL.DEFAULT_SCHEMA<pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA>`
            (i.e. ``'public'``)
        :type schema_name: str or None
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.PostgreSQL.create_table`.
        """

        schema_name_ = copy.copy(self.DEFAULT_SCHEMA) if schema_name is None else str(schema_name)
        table_name_ = '"{}"."{}"'.format(schema_name_, table_name)

        if not self.table_exists(table_name=table_name, schema_name=schema_name_):
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
                    self.engine.execute('DROP TABLE "{}"."{}" CASCADE;'.format(schema_name_, table_name))

                    if verbose:
                        print("Done.")

                except Exception as e:
                    print("Failed. {}".format(e))

    @staticmethod
    def psql_insert_copy(sql_table, sql_db_engine, column_name_list, data_iter):
        """
        A callable using PostgreSQL COPY clause for executing inserting data.

        :param sql_table: pandas.io.sql.SQLTable
        :param sql_db_engine: `sqlalchemy.engine.Connection`_ or `sqlalchemy.engine.Engine`_
        :param column_name_list: (list of str) column names
        :param data_iter: iterable that iterates the values to be inserted

        .. _`sqlalchemy.engine.Connection`:
            https://docs.sqlalchemy.org/en/13/core/connections.html#sqlalchemy.engine.Connection
        .. _`sqlalchemy.engine.Engine`:
            https://docs.sqlalchemy.org/en/13/core/connections.html#sqlalchemy.engine.Engine

        .. note::

            This function is copied and slightly modified from the source code available at
            [`DBMS-P-PIC-1
            <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method>`_].
        """

        con_cur = sql_db_engine.connection.cursor()
        io_buffer = io.StringIO()
        csv_writer = csv.writer(io_buffer)
        csv_writer.writerows(data_iter)
        io_buffer.seek(0)

        sql_column_names = ', '.join('"{}"'.format(k) for k in column_name_list)
        sql_table_name = '"{}"."{}"'.format(sql_table.schema, sql_table.name)

        sql_query = 'COPY {} ({}) FROM STDIN WITH CSV'.format(sql_table_name, sql_column_names)
        con_cur.copy_expert(sql=sql_query, file=io_buffer)

    def import_data(self, data, table_name, schema_name=None, if_exists='fail',
                    force_replace=False, chunk_size=None, col_type=None, method='multi',
                    index=False, confirmation_required=True, verbose=False, **kwargs):
        """
        Import tabular data into a table in the currently-connected database.

        See also [`DBMS-P-DD-1
        <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method/>`_]
        and [`DBMS-P-DD-2
        <https://www.postgresql.org/docs/current/sql-copy.html/>`_].

        :param data: tabular data to be dumped into a database
        :type data: pandas.DataFrame or pandas.io.parsers.TextFileReader or list or tuple
        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``None``;
            when ``schema_name=None``, it defaults to
            :py:attr:`PostgreSQL.DEFAULT_SCHEMA<pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA>`
            (i.e. ``'public'``)
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

        schema_name_ = copy.copy(self.DEFAULT_SCHEMA) if schema_name is None else str(schema_name)
        table_ = '"{}"."{}"'.format(schema_name_, table_name)

        if confirmed("To import data into {} at {}\n?".format(table_, self.address),
                     confirmation_required=confirmation_required):

            inspector = sqlalchemy.inspect(self.engine)
            if schema_name_ not in inspector.get_schema_names():
                self.create_schema(schema_name=schema_name_, verbose=verbose)
            # if not data.empty:
            #   There may be a need to change column types

            if self.table_exists(table_name=table_name, schema_name=schema_name_):
                if if_exists == 'replace' and verbose:
                    print("The table {} already exists and is replaced.".format(table_))

                if force_replace and verbose:
                    print("The existing table is forced to be dropped", end=" ... ")
                    self.drop_table(
                        table_name=table_name, schema_name=schema_name_,
                        confirmation_required=confirmation_required, verbose=verbose)
                    print("Done.")

            if verbose == 2:
                if confirmation_required:
                    log_msg = "Importing the data into the table {}".format(table_)
                else:
                    log_msg = "Importing data into the table {} at {}".format(table_, self.address)
                print(log_msg, end=" ... ")

            to_sql_args = {
                'name': table_name,
                'con': self.engine,
                'schema': schema_name_,
                'if_exists': if_exists,
                'index': index,
                'dtype': col_type,
                'method': method,
            }

            kwargs.update(to_sql_args)

            if isinstance(data, (pandas.io.parsers.TextFileReader, list, tuple)):
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

    def read_table(self, table_name, schema_name=None, condition=None, chunk_size=None, sorted_by=None,
                   **kwargs):
        """
        Read data from a table in the currently-connected database.

        See also [`DBMS-P-RT-1 <https://stackoverflow.com/questions/24408557/>`_].

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``None``;
            when ``schema_name=None``, it defaults to
            :py:attr:`PostgreSQL.DEFAULT_SCHEMA<pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA>`
            (i.e. ``'public'``)
        :type schema_name: str
        :param condition: defaults to ``None``
        :type condition: str or None
        :param chunk_size: number of rows to include in each chunk, defaults to ``None``
        :type chunk_size: int or None
        :param sorted_by: name(s) of a column (or columns) by which the retrieved data is sorted,
            defaults to ``None``
        :type sorted_by: str or None
        :param kwargs: [optional] parameters of `pandas.read_sql`_
        :return: data frame from the specified table
        :rtype: pandas.DataFrame

        .. _`pandas.read_sql`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_sql.html

        .. seealso::

            - Examples for the method :py:meth:`pyhelpers.dbms.PostgreSQL.read_sql_query`.
        """

        schema_name_ = copy.copy(self.DEFAULT_SCHEMA) if schema_name is None else str(schema_name)

        if condition:
            assert isinstance(condition, str), "'condition' must be 'str' type."
            sql_query = 'SELECT * FROM "{}"."{}" {};'.format(schema_name_, table_name, condition)
        else:
            sql_query = 'SELECT * FROM "{}"."{}";'.format(schema_name_, table_name)

        table_data = pd.read_sql(sql=sql_query, con=self.engine, chunksize=chunk_size, **kwargs)

        if sorted_by and isinstance(sorted_by, str):
            table_data.sort_values(sorted_by, inplace=True, ignore_index=True)

        return table_data

    def read_sql_query(self, sql_query, method='tempfile', max_size_spooled=1, delimiter=',',
                       tempfile_kwargs=None, stringio_kwargs=None, **kwargs):
        """
        Read table data by SQL query (recommended for large table).

        See also
        [`DBMS-P-RSQ-1 <https://towardsdatascience.com/f31cd7f707ab>`_],
        [`DBMS-P-RSQ-2 <https://docs.python.org/3/library/tempfile.html>`_] and
        [`DBMS-P-RSQ-3 <https://docs.python.org/3/library/io.html>`_].

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
            >>> dat = example_dataframe()
            >>> dat
                        Easting  Northing
            London       530034    180381
            Birmingham   406689    286822
            Manchester   383819    398052
            Leeds        582044    152953

            >>> table = 'England'
            >>> schema = 'points'

            >>> # Import the data into a table named "points"."England"
            >>> testdb.import_data(dat, table, schema, if_exists='replace', index=True, verbose=2)
            To import data into "points"."England" at postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Creating a schema: "points" ... Done.
            Importing the data into the table "points"."England" ... Done.

            >>> rslt = testdb.table_exists(table_name=table, schema_name=schema)
            >>> print("The table \"{}\".\"{}\" exists? {}.".format(schema, table, rslt))
            The table "points"."England" exists? True.

            >>> dat_ret = testdb.read_table(table_name=table, schema_name=schema, index_col='index')
            >>> dat_ret
                        Easting  Northing
            index
            London       530034    180381
            Birmingham   406689    286822
            Manchester   383819    398052
            Leeds        582044    152953

            >>> dat_ret.index.name = None
            >>> dat_ret
                        Easting  Northing
            London       530034    180381
            Birmingham   406689    286822
            Manchester   383819    398052
            Leeds        582044    152953

            >>> # Alternatively, read the data by a SQL query statement
            >>> sql_qry = f'SELECT * FROM "{schema}"."{table}"'
            >>> dat_ret_alt = testdb.read_sql_query(sql_query=sql_qry, index_col='index')
            >>> dat_ret_alt.index.name = None
            >>> dat_ret_alt
                        Easting  Northing
            London       530034    180381
            Birmingham   406689    286822
            Manchester   383819    398052
            Leeds        582044    152953

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

            >>> import datetime

            >>> sql_qry = 'SELECT * FROM "table_name" '
            ...           'WHERE "timestamp_column_name" BETWEEN %(ts_start)s AND %(ts_end)s'

            >>> params = {'d_start': datetime.datetime.today(), 'd_end': datetime.datetime.today()}

            >>> data_frame = pandas.read_sql(sql=sql_qry, con=testdb.engine, params=params)
        """

        methods = ('tempfile', 'stringio', 'spooled')
        ast_msg = "The argument `method` must be one of {'%s', '%s', '%s'}" % methods
        assert method in methods, ast_msg

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

        else:  # method == 'spooled_tempfile': using tempfile.SpooledTemporaryFile
            # Data would be spooled in memory until its size > max_spooled_size
            tempfile_kwargs.update({'max_size': max_size_spooled * 10 ** 9})
            csv_temp = tempfile.SpooledTemporaryFile(**tempfile_kwargs)

        # Specify the SQL query for "COPY"
        copy_sql = "COPY ({query}) TO STDOUT WITH DELIMITER '{delimiter}' CSV HEADER;".format(
            query=sql_query, delimiter=delimiter)

        # Get a cursor
        connection = self.engine.raw_connection()
        cur = connection.cursor()
        cur.copy_expert(copy_sql, csv_temp)
        # Rewind the file handle using seek() in order to read the data back from it
        csv_temp.seek(0)
        # Read data from temporary csv
        table_data = pandas.read_csv(csv_temp, **kwargs)
        # Close the temp file
        csv_temp.close()

        cur.close()  # Close the cursor
        connection.close()  # Close the connection

        return table_data
