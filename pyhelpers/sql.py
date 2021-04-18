"""
Basic data manipulation with SQL.

*(The current release includes* `PostgreSQL <https://www.postgresql.org/>`_ *only.)*
"""

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


def get_db_address(db_cls):
    """
    Get default address of a database instance.

    :param db_cls: a class representation of a database
    :type db_cls: object
    :return: default address of database
    :rtype: str

    **Test**::

        >>> from pyhelpers.sql import get_db_address, PostgreSQL

        >>> db_addr = get_db_address(db_cls=PostgreSQL)

        >>> print(db_addr)
        None:***@None:None/None
    """

    args_spec = inspect.getfullargspec(db_cls)

    args_dict = dict(zip([x for x in args_spec.args if x != 'self'], args_spec.defaults))

    db_address = "{}:***@{}:{}/{}".format(
        args_dict['username'], args_dict['host'], args_dict['port'], args_dict['database_name'])

    return db_address


class PostgreSQL:
    """
    A class for a basic `PostgreSQL <https://www.postgresql.org/>`_ instance.

    :param host: host address, e.g. ``'localhost'`` or ``'127.0.0.1'`` (default by installation),
        defaults to ``None``
    :type host: str or None
    :param port: port, e.g. ``5432`` (default by installation), defaults to ``None``
    :type port: int or None
    :param password: database password, defaults to ``None``
    :type password: str or int or None
    :param username: database username, e.g. ``'postgres'`` (default by installation),
        defaults to ``None``
    :type username: str or None
    :param database_name: database name, e.g. ``'postgres'`` (default by installation),
        defaults to ``None``
    :type database_name: str
    :param confirm_new_db: whether to impose a confirmation to create a new database,
        defaults to ``False``
    :type confirm_new_db: bool
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``True``
    :type verbose: bool or int

    :ivar dict database_info: basic information about the server/database being connected
    :ivar sqlalchemy.engine.URL url: PostgreSQL database URL;
        see also [`SQL-P-SP-1`_]
    :ivar type dialect: system that SQLAlchemy uses to communicate with PostgreSQL;
        see also [`SQL-P-SP-2`_]
    :ivar str backend: name of database backend
    :ivar str driver: name of database driver
    :ivar str user: username
    :ivar str host: host name
    :ivar str port: port number
    :ivar str database_name: name of a database
    :ivar str address: brief description of the database address
    :ivar sqlalchemy.engine.Engine engine: `SQLAlchemy`_ Engine class;
        see also [`SQL-P-SP-3`_]
    :ivar sqlalchemy.pool.base._ConnectionFairy connection: `SQLAlchemy`_ Connection class;
        see also [`SQL-P-SP-4`_]

    .. _`SQL-P-SP-1`:
        https://docs.sqlalchemy.org/en/13/core/engines.html#postgresql
    .. _`SQL-P-SP-2`:
        https://docs.sqlalchemy.org/en/13/dialects/postgresql.html
    .. _`SQL-P-SP-3`:
        https://docs.sqlalchemy.org/en/13/core/connections.html#sqlalchemy.engine.Engine
    .. _`SQL-P-SP-4`:
        https://docs.sqlalchemy.org/en/13/core/connections.html#sqlalchemy.engine.Connection
    .. _`SQLAlchemy`:
        https://www.sqlalchemy.org/

    **Examples**::

        >>> from pyhelpers.sql import PostgreSQL

        >>> # Connect the default database 'postgres'
        >>> postgres = PostgreSQL('localhost', 5432, username='postgres', database_name='postgres')
        Password (postgres@localhost:5432): ***
        Connecting postgres:***@localhost:5432/postgres ... Successfully.

        >>> print(postgres.address)
        postgres:***@localhost:5432/postgres

        >>> # Connect a database 'testdb' (which will be created if it does not exist)
        >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
        Password (postgres@localhost:5432): ***
        Connecting postgres:***@localhost:5432/testdb ... Successfully.

        >>> print(testdb.address)
        postgres:***@localhost:5432/testdb

        >>> # Define a proxy object that inherits from pyhelpers.sql.PostgreSQL
        >>> class ExampleProxyObj(PostgreSQL):
        ...
        ...     def __init__(self, host='localhost', port=5432, username='postgres',
        ...                  password=None, database_name='testdb', **kwargs):
        ...
        ...         super().__init__(host=host, port=port, username=username,
        ...                          password=password, database_name=database_name, **kwargs)

        >>> example_proxy_obj = ExampleProxyObj()
        Password (postgres@localhost:5432): ***
        Connecting postgres:***@localhost:5432/testdb ... Successfully.

        >>> print(example_proxy_obj.address)
        postgres:***@localhost:5432/testdb
    """

    def __init__(self, host=None, port=None, username=None, database_name=None, password=None,
                 confirm_new_db=False, verbose=True):
        """
        Constructor method.
        """
        host_ = input("PostgreSQL Host: ") if host is None else str(host)
        port_ = input("PostgreSQL Port: ") if port is None else int(port)
        username_ = input("Username: ") if username is None else str(username)
        database_name_ = input("Database: ") if database_name is None else str(database_name)

        if password:
            password_ = str(password)
        else:
            password_ = getpass.getpass("Password ({}@{}:{}): ".format(username_, host_, port_))

        self.database_info = {'drivername': 'postgresql+psycopg2',
                              'host': host_,
                              'port': port_,
                              'username': username_,
                              'password': password_,
                              'database': database_name_}

        # The typical form of the URL: backend+driver://username:password@host:port/database
        self.url = sqlalchemy.engine.URL.create(**self.database_info)

        self.dialect = self.url.get_dialect()
        self.backend = self.url.get_backend_name()
        self.driver = self.url.get_driver_name()
        self.user, self.host, self.port = self.url.username, self.url.host, self.url.port
        self.database_name = self.database_info['database']

        if self.database_name != 'postgres':
            db_info = self.database_info.copy()
            db_info['database'] = 'postgres'
            url = sqlalchemy.engine.URL.create(**db_info)
            self.engine = sqlalchemy.create_engine(url, isolation_level='AUTOCOMMIT')
            db_exists = self.engine.execute(
                "SELECT EXISTS("
                "SELECT datname FROM pg_catalog.pg_database "
                "WHERE datname='{}');".format(database_name_)).fetchone()[0]
        else:
            db_exists = True

        self.address = "{}:***@{}:{}/{}".format(self.user, self.host, self.port, self.database_name)

        if not db_exists:
            if confirmed("The database \"{}\" does not exist. "
                         "Proceed by creating it?".format(self.database_name),
                         confirmation_required=confirm_new_db):
                if verbose:
                    print("Connecting {}".format(self.address), end=" ... ")

                self.engine.execute('CREATE DATABASE "{}";'.format(self.database_name))
                self.engine.dispose()

        else:
            if verbose:
                print("Connecting {}".format(self.address), end=" ... ")

        try:  # Create a SQLAlchemy connectable
            self.engine = sqlalchemy.create_engine(self.url, isolation_level='AUTOCOMMIT')

            if verbose:
                print("Successfully.")

        except Exception as e:
            print("Failed. {}.".format(e))

    def database_exists(self, database_name=None):
        """
        Check if a database exists in the PostgreSQL server being connected.

        :param database_name: name of a database, defaults to ``None``
        :type database_name: str or None
        :return: ``True`` if the database exists, ``False``, otherwise
        :rtype: bool

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.database_exists('testdb')
            True

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.

            >>> testdb.database_exists('testdb')
            False
        """

        database_name_ = str(database_name) if database_name is not None else self.database_name

        result = self.engine.execute(
            "SELECT EXISTS("
            "SELECT datname FROM pg_catalog.pg_database WHERE datname='{}');".format(database_name_))

        return result.fetchone()[0]

    def create_database(self, database_name, verbose=False):
        """
        An alternative to `sqlalchemy_utils.create_database
        <https://sqlalchemy-utils.readthedocs.io/en/latest/database_helpers.html#create-database>`_.

        :param database_name: name of a database
        :type database_name: str
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.create_database('testdb1', verbose=True)
            Creating a database: "testdb1" ... Done.

            >>> print(testdb.database_name)
            testdb1

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb1" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb1" ... Done.
        """

        if not self.database_exists(database_name):
            if verbose:
                print("Creating a database: \"{}\" ... ".format(database_name), end="")

            self.disconnect_database()
            self.engine.execute('CREATE DATABASE "{}";'.format(database_name))

            if verbose:
                print("Done.")

        else:
            if verbose:
                print("The database already exists.")

        self.connect_database(database_name)

    def connect_database(self, database_name=None, verbose=False):
        """
        Establish a connection to a database of the PostgreSQL server being connected.

        :param database_name: name of a database;
            if ``None`` (default), the database name is input manually
        :type database_name: str or None
        :param verbose: whether to print relevant information in console as the function runs, 
            defaults to ``False``
        :type verbose: bool or int

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.connect_database()
            >>> print(testdb.database_name)
            testdb

            >>> testdb.connect_database('postgres', verbose=True)
            Connecting postgres:***@localhost:5432/postgres ... Successfully.

            >>> print(testdb.database_name)
            postgres
        """

        if database_name:
            self.database_name = str(database_name)

            self.address = "{}:***@{}:{}/{}".format(self.user, self.host, self.port, self.database_name)

            if verbose:
                print("Connecting {}".format(self.address), end=" ... ")

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
                print("Failed. {}.".format(e))

    def get_database_size(self, database_name=None):
        """
        Get the size of a database in the PostgreSQL server being connected.

        When ``database_name`` is ``None`` (default), the connected database is checked.

        :param database_name: name of a database, defaults to ``None``
        :type database_name: str or None
        :return: size of the database
        :rtype: int

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> print(testdb.get_database_size())
            7901 kB
        """

        db_name = '\'{}\''.format(database_name) if database_name else 'current_database()'

        sql_query = 'SELECT pg_size_pretty(pg_database_size({})) AS size;'.format(db_name)

        db_size = self.engine.execute(sql_query)

        return db_size.fetchone()[0]

    def disconnect_database(self, database_name=None, verbose=False):
        """
        Kill the connection to a database in the PostgreSQL server being connected.

        If ``database_name`` is ``None`` (default), disconnect the current database.

        :param database_name: name of database to disconnect from, defaults to ``None``
        :type database_name: str or None
        :param verbose: whether to print relevant information in console as the function runs, 
            defaults to ``False``
        :type verbose: bool or int

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> print(testdb.database_name)
            testdb

            >>> testdb.disconnect_database()
            >>> print(testdb.database_name)
            postgres
        """

        db_name = self.database_name if database_name is None else database_name

        if verbose:
            print("Disconnecting the database \"{}\" ... ".format(db_name), end="")
        try:
            self.connect_database(database_name='postgres')

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

    def disconnect_other_databases(self):
        """
        Kill connections to all other databases of the PostgreSQL server being connected.

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> print(testdb.database_name)
            testdb

            >>> testdb.disconnect_other_databases()
            >>> print(testdb.database_name)
            postgres
        """

        self.connect_database(database_name='postgres')

        self.engine.execute(
            'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid();')

    def drop_database(self, database_name=None, confirmation_required=True, verbose=False):
        """
        Drop a database from the PostgreSQL server being connected.

        If ``database_name`` is ``None`` (default), drop the current database.

        :param database_name: database to be disconnected, defaults to ``None``
        :type database_name: str or None
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console as the function runs, 
            defaults to ``False``
        :type verbose: bool or int

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.

            >>> testdb.database_exists(database_name='testdb')
            False

            >>> testdb.drop_database(database_name='testdb', verbose=True)
            The database "testdb" does not exist.

            >>> print(testdb.database_name)
            postgres
        """

        db_name = self.database_name if database_name is None else database_name

        if not self.database_exists(database_name=db_name):
            if verbose:
                print("The database \"{}\" does not exist.".format(db_name))

        else:
            address_ = self.address.replace(f"/{db_name}", "")
            if confirmed("To drop the database \"{}\" from {}\n?".format(db_name, address_),
                         confirmation_required=confirmation_required):
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

    def schema_exists(self, schema_name):
        """
        Check if a schema exists in the PostgreSQL server being connected.

        :param schema_name: name of a schema
        :type schema_name: str
        :return: ``True`` if the schema exists, ``False`` otherwise
        :rtype: bool

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.schema_exists('public')
            True

            >>> testdb.schema_exists('test_schema')  # (if the schema 'test_schema' does not exist)
            False
        """

        result = self.engine.execute(
            "SELECT EXISTS("
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name='{}');".format(schema_name))

        return result.fetchone()[0]

    def create_schema(self, schema_name, verbose=False):
        """
        Create a new schema in the database being connected.

        :param schema_name: name of a schema
        :type schema_name: str
        :param verbose: whether to print relevant information in console as the function runs, 
            defaults to ``False``
        :type verbose: bool or int

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> test_schema_name = 'test_schema'

            >>> testdb.create_schema(test_schema_name, verbose=True)
            Creating a schema: "test_schema" ... Done.

            >>> testdb.schema_exists(test_schema_name)
            True

            >>> testdb.drop_schema(test_schema_name, verbose=True)
            To drop the schema "test_schema" from postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Dropping "test_schema" ... Done.

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

    def _msg_for_multi_items(self, item_names, desc):
        """
        Formulate printing message for multiple items.

        :param item_names: name of one table/schema, or names of several tables/schemas
        :type item_names: str or typing.Iterable
        :param desc: for additional description
        :type desc: str
        :return: printing message
        :rtype: tuple

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> schema_name = 'points'
            >>> schemas, prt_pl, prt_name = testdb._msg_for_multi_items(schema_name, desc='schema')

            >>> print(schemas)
            ['points']
            >>> print(prt_pl, prt_name)
            schema "points"

            >>> schema_names = ['points', 'lines', 'polygons']
            >>> schemas, prt_pl, prt_name = testdb._msg_for_multi_items(schema_names, desc='schema')

            >>> print(schemas)
            ['points', 'lines', 'polygons']
            >>> print(prt_pl, prt_name)
            schemas
                "points"
                "lines"
                "polygons"

        :meta private:
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

    def drop_schema(self, schema_names, confirmation_required=True, verbose=False):
        """
        Drop a schema in the database being connected.

        :param schema_names: name of one schema, or names of multiple schemas
        :type schema_names: str or typing.Iterable
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console as the function runs, 
            defaults to ``False``
        :type verbose: bool or int

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> new_schema_names = ['points', 'lines', 'polygons']
            >>> new_schema_names_ = ['test_schema']

            >>> for new_schema in new_schema_names:
            ...     testdb.create_schema(new_schema, verbose=True)
            Creating a schema: "points" ... Done.
            Creating a schema: "lines" ... Done.
            Creating a schema: "polygons" ... Done.

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

        schemas, print_plural, print_schema = self._msg_for_multi_items(schema_names, desc='schema')

        if len(schemas) == 1:
            cfm_msg = "To drop the {} \"{}\" from {}\n?".format(print_plural, print_schema, self.address)
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

    def table_exists(self, table_name, schema_name='public'):
        """
        Check if a table exists in the database being connected.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :return: ``True`` if the table exists, ``False`` otherwise
        :rtype: bool

        **Examples**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> testdb.table_exists(table_name='England', schema_name='points')
            >>> # (if 'points.England' does not exist)
            False

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        res = self.engine.execute(
            "SELECT EXISTS("
            "SELECT * FROM information_schema.tables "
            "WHERE table_schema='{}' AND table_name='{}');".format(schema_name, table_name))

        return res.fetchone()[0]

    def create_table(self, table_name, column_specs, schema_name='public', verbose=False):
        """
        Create a new table for the database being connected.

        :param table_name: name of a table
        :type table_name: str
        :param column_specs: specifications for each column of the table
        :type column_specs: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param verbose: whether to print relevant information in console as the function runs, 
            defaults to ``False``
        :type verbose: bool or int

        .. _postgresql-create_table-example:

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> tbl_name = 'test_table'
            >>> column_specifications = 'col_name_1 INT, col_name_2 TEXT'

            >>> testdb.create_table(tbl_name, column_specifications, verbose=True)
            Creating a table "public"."test_table" ... Done.

            >>> testdb.table_exists(tbl_name)
            True

            >>> test_tbl_col_info = testdb.get_column_info(tbl_name, as_dict=False)

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

            >>> # Drop the table
            >>> testdb.drop_table(tbl_name, verbose=True)
            To drop the table "public"."test_table" from postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Dropping "public"."test_table" ... Done.

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        table_name_ = '"{schema}"."{table}"'.format(schema=schema_name, table=table_name)

        if self.table_exists(table_name=table_name, schema_name=schema_name):
            if verbose:
                print("The table {} already exists.".format(table_name_))

        else:
            if not self.schema_exists(schema_name):
                self.create_schema(schema_name, verbose=False)

            try:
                if verbose:
                    print("Creating a table: {} ... ".format(table_name_), end="")

                self.engine.execute('CREATE TABLE {} ({});'.format(table_name_, column_specs))

                if verbose:
                    print("Done.")

            except Exception as e:
                print("Failed. {}".format(e))

    def get_column_info(self, table_name, schema_name='public', as_dict=True):
        """
        Get information about columns of a table.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param as_dict: whether to return the column information as a dictionary, defaults to ``True``
        :type as_dict: bool
        :return: information about each column of the given table
        :rtype: pandas.DataFrame or dict

        See the example for the method :py:meth:`.create_table()<pyhelpers.sql.PostgreSQL.create_table>`.
        """

        column_info = self.engine.execute(
            "SELECT * FROM information_schema.columns "
            "WHERE table_schema='{}' AND table_name='{}';".format(schema_name, table_name))

        keys, values = column_info.keys(), column_info.fetchall()
        idx = ['column_{}'.format(x) for x in range(len(values))]

        info_tbl = pd.DataFrame(values, index=idx, columns=keys).T

        if as_dict:
            info_tbl = {k: v.to_list() for k, v in info_tbl.iterrows()}

        return info_tbl

    def drop_table(self, table_name, schema_name='public', confirmation_required=True, verbose=False):
        """
        Remove a table from the database being connected.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console as the function runs, 
            defaults to ``False``
        :type verbose: bool or int

        See the example for the method :py:meth:`.create_table()<pyhelpers.sql.PostgreSQL.create_table>`.
        """

        table_name_ = '"{}"."{}"'.format(schema_name, table_name)

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
                    self.engine.execute('DROP TABLE "{}"."{}" CASCADE;'.format(schema_name, table_name))

                    if verbose:
                        print("Done.")

                except Exception as e:
                    print("Failed. {}".format(e))

    def list_table_names(self, schema_name='public', verbose=False):
        """
        List the names of all tables in a schema.

        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param verbose: whether to print relevant information in console as the function runs,
            defaults to ``False``
        :type verbose: bool or int
        :return: a list of table names
        :rtype: list or None

        **Examples**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> lst_tbl_names = testdb.list_table_names()
            >>> print(lst_tbl_names)
            []

            >>> lst_tbl_names = testdb.list_table_names(schema_name='testdb', verbose=True)
            The schema "testdb" does not exist.

            >>> # Create a new table named "test_table" in the schema "testdb"
            >>> new_table_name = 'test_table'
            >>> column_specs = 'col_name_1 INT, col_name_2 TEXT'
            >>> testdb.create_table(new_table_name, column_specs, verbose=True)
            Creating a table: "public"."test_table" ... Done.

            >>> lst_tbl_names = testdb.list_table_names(schema_name='public')
            >>> print(lst_tbl_names)
            ['test_table']

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        if not self.schema_exists(schema_name=schema_name):
            if verbose:
                print("The schema \"{}\" does not exist.".format(schema_name))

        else:
            res = self.engine.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='{}' AND table_type='BASE TABLE';".format(schema_name))

            temp_list = res.fetchall()

            table_list = [x[0] for x in temp_list]

            return table_list

    def alter_table_schema(self, table_name, schema_name, new_schema_name, confirmation_required=True,
                           verbose=False):
        """
        Move a table from one schema to another within the database being connected.

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

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> # Create a new table named "test_table" in the schema "testdb"
            >>> new_table_name = 'test_table'
            >>> column_specs = 'col_name_1 INT, col_name_2 TEXT'
            >>> testdb.create_table(new_table_name, column_specs, verbose=True)
            Creating a table: "public"."test_table" ... Done.

            >>> # Create a new schema "test_schema"
            >>> testdb.create_schema(schema_name='test_schema', verbose=True)
            Creating a schema: "test_schema" ... Done.

            >>> # Move the table "public"."test_table" to the schema "test_schema"
            >>> testdb.alter_table_schema('test_table', 'public', 'test_schema', verbose=True)
            To move the table "test_table" from the schema "public" to "test_schema"
            ? [No]|Yes: yes
            Moving "public"."test_table" to "test_schema" ... Done.

            >>> lst_tbl_names = testdb.list_table_names(schema_name='test_schema')
            >>> print(lst_tbl_names)
            ['test_table']

            >>> # Delete the database "testdb"
            >>> testdb.drop_database(verbose=True)
            To drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.
        """

        table_name_ = '"{}"."{}"'.format(schema_name, table_name)

        if confirmed("To move the table \"{}\" from the schema \"{}\" to \"{}\"\n?".format(
                table_name, schema_name, new_schema_name),
                confirmation_required=confirmation_required):

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
            [`SQL-P-PIC-1
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

    def import_data(self, data, table_name, schema_name='public', if_exists='fail',
                    force_replace=False, chunk_size=None, col_type=None, method='multi',
                    index=False, confirmation_required=True, verbose=False, **kwargs):
        """
        Import tabular data into the database being connected.

        See also [`SQL-P-DD-1
        <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method/>`_]
        and [`SQL-P-DD-2
        <https://www.postgresql.org/docs/current/sql-copy.html/>`_].

        :param data: tabular data to be dumped into a database
        :type data: pandas.DataFrame or pandas.io.parsers.TextFileReader or list or tuple
        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param if_exists: if the table already exists, to ``'replace'``, ``'append'``
            or, by default, ``'fail'`` and do nothing but raise a ValueError.
        :type if_exists: str
        :param force_replace: whether to force to replace existing table, defaults to ``False``
        :type force_replace: bool
        :param chunk_size: the number of rows in each batch to be written at a time, defaults to ``None``
        :type chunk_size: int or None
        :param col_type: data types for columns, defaults to ``None``
        :type col_type: dict or None
        :param method: method for SQL insertion clause, defaults to ``'multi'``

            * ``None``: uses standard SQL ``INSERT`` clause (one per row);
            * ``'multi'``: pass multiple values in a single ``INSERT`` clause;
            * callable (e.g. ``PostgreSQL.psql_insert_copy``)
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
        :param kwargs: optional parameters of `pandas.DataFrame.to_sql`_

        .. _`pandas.DataFrame.to_sql`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html

        See the example for the method
        :py:meth:`.read_sql_query() <pyhelpers.sql.PostgreSQL.read_sql_query>`.
        """

        table_name_ = '"{}"."{}"'.format(schema_name, table_name)

        if confirmed("To import data into {} at {}\n?".format(table_name_, self.address),
                     confirmation_required=confirmation_required):

            inspector = sqlalchemy.inspect(self.engine)
            if schema_name not in inspector.get_schema_names():
                self.create_schema(schema_name, verbose=verbose)
            # if not data.empty:
            #   There may be a need to change column types

            if self.table_exists(table_name, schema_name):
                if if_exists == 'replace' and verbose:
                    print("The table {} already exists and is replaced.".format(table_name_))

                if force_replace and verbose:
                    print("The existing table is forced to be dropped", end=" ... ")
                    self.drop_table(table_name, schema_name,
                                    confirmation_required=confirmation_required, verbose=verbose)
                    print("Done.")

            if verbose == 2:
                if confirmation_required:
                    log_msg = "Importing the data into the table {}".format(table_name_)
                else:
                    log_msg = "Importing data into the table {} at {}".format(table_name_, self.address)
                print(log_msg, end=" ... ")

            if isinstance(data, (pandas.io.parsers.TextFileReader, list, tuple)):
                for chunk in data:
                    chunk.to_sql(table_name, self.engine, schema=schema_name, if_exists=if_exists,
                                 index=index, dtype=col_type, method=method, **kwargs)
                    del chunk
                    gc.collect()

            else:
                data.to_sql(table_name, self.engine, schema=schema_name, if_exists=if_exists,
                            index=index, chunksize=chunk_size, dtype=col_type, method=method,
                            **kwargs)
                gc.collect()

            print("Done.") if verbose == 2 else ""

    def read_table(self, table_name, schema_name='public', condition=None, chunk_size=None,
                   sorted_by=None, **kwargs):
        """
        Read data from a table of the database being connected.

        See also
        [`SQL-P-RT-1 <https://stackoverflow.com/questions/24408557/pandas-read-sql-with-parameters>`_].

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param condition: defaults to ``None``
        :type condition: str or None
        :param chunk_size: number of rows to include in each chunk, defaults to ``None``
        :type chunk_size: int or None
        :param sorted_by: name(s) of a column (or columns) by which the retrieved data is sorted,
            defaults to ``None``
        :type sorted_by: str or None
        :param kwargs: optional parameters of `pandas.read_sql`_
        :return: data frame from the specified table
        :rtype: pandas.DataFrame

        .. _`pandas.read_sql`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_sql.html

        See the example for the method
        :py:meth:`.read_sql_query()<pyhelpers.sql.PostgreSQL.read_sql_query>`.
        """

        if condition:
            assert isinstance(condition, str), "'condition' must be 'str' type."
            sql_query = 'SELECT * FROM "{}"."{}" {};'.format(schema_name, table_name, condition)

        else:
            sql_query = 'SELECT * FROM "{}"."{}";'.format(schema_name, table_name)

        table_data = pd.read_sql(sql_query, con=self.engine, chunksize=chunk_size, **kwargs)

        if sorted_by and isinstance(sorted_by, str):
            table_data.sort_values(sorted_by, inplace=True)
            table_data.index = range(len(table_data))

        return table_data

    def read_sql_query(self, sql_query, method='tempfile', tempfile_mode='w+b', max_size_spooled=1,
                       delimiter=',', dtype=None, tempfile_kwargs=None, stringio_kwargs=None,
                       **kwargs):
        """
        Read table data by SQL query (recommended for large table).

        See also
        [`SQL-P-RSQ-1 <https://towardsdatascience.com/
        optimizing-pandas-read-sql-for-postgres-f31cd7f707ab>`_],
        [`SQL-P-RSQ-2 <https://docs.python.org/3/library/tempfile.html>`_] and
        [`SQL-P-RSQ-3 <https://docs.python.org/3/library/io.html>`_].

        :param sql_query: SQL query to be executed
        :type sql_query: str

        :param method: method to be used for buffering temporary data

            * ``'tempfile'`` (default): use `tempfile.TemporaryFile`_
            * ``'stringio'``: use `io.StringIO`_
            * ``'spooled'``: use `tempfile.SpooledTemporaryFile`_

        :type method: str

        :param tempfile_mode: mode of the specified `method`, defaults to ``'w+b'``
        :type tempfile_mode: str
        :param max_size_spooled: ``max_size`` of `tempfile.SpooledTemporaryFile`_,
            defaults to ``1`` (in gigabyte)
        :type max_size_spooled: int or float
        :param delimiter: delimiter used in data, defaults to ``','``
        :type delimiter: str
        :param dtype: data type for specified data columns, `dtype` used by `pandas.read_csv`_,
            defaults to ``None``
        :type dtype: dict or None
        :param tempfile_kwargs: optional parameters of `tempfile.TemporaryFile`_
            or `tempfile.SpooledTemporaryFile`_
        :param stringio_kwargs: optional parameters of `io.StringIO`_,
            e.g. ``initial_value`` (default: ``''``)
        :param kwargs: optional parameters of `pandas.read_csv`_
        :return: data frame as queried by the statement ``sql_query``
        :rtype: pandas.DataFrame

        .. _`pandas.read_csv`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html
        .. _`open`:
            https://docs.python.org/3/library/functions.html#open
        .. _`tempfile.TemporaryFile`:
            https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryFile
        .. _`tempfile.SpooledTemporaryFile`:
            https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile
        .. _`io.StringIO`:
            https://docs.python.org/3/library/io.html#io.StringIO
        .. _`tempfile.mkstemp`:
            https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp

        **Examples**::

            >>> import pandas
            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL('localhost', 5432, username='postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> # Create a pandas.DataFrame
            >>> xy_array = [(530034, 180381),
            ...             (406689, 286822),
            ...             (383819, 398052),
            ...             (582044, 152953)]
            >>> idx_labels = ['London', 'Birmingham', 'Manchester', 'Leeds']
            >>> col_names = ['Easting', 'Northing']
            >>> dat = pandas.DataFrame(xy_array, index=idx_labels, columns=col_names)

            >>> print(dat)
                        Easting  Northing
            London       530034    180381
            Birmingham   406689    286822
            Manchester   383819    398052
            Leeds        582044    152953

            >>> table = 'England'
            >>> schema = 'points'

            >>> testdb.import_data(dat, table, schema, if_exists='replace', index=True,
            ...                    chunk_size=None, force_replace=False, col_type=None, verbose=2)
            To import data into "points"."England" at postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Creating a schema: "points" ... Done.
            Importing the data into the table "points"."England" ... Done.

            >>> res = testdb.table_exists(table, schema)
            >>> print("The table \"{}\".\"{}\" exists? {}.".format(schema, table, res))
            The table "points"."England" exists? True.

            >>> dat_retrieval = testdb.read_table(table, schema, index_col='index')
            >>> dat_retrieval.index.name = None
            >>> print(dat_retrieval)
                        Easting  Northing
            London       530034    180381
            Birmingham   406689    286822
            Manchester   383819    398052
            Leeds        582044    152953

            >>> # Alternatively
            >>> sql_qry = 'SELECT * FROM "{}"."{}"'.format(schema, table)

            >>> dat_retrieval_alt = testdb.read_sql_query(sql_qry, index_col='index')
            >>> dat_retrieval_alt.index.name = None
            >>> print(dat_retrieval_alt)
                        Easting  Northing
            London       530034    180381
            Birmingham   406689    286822
            Manchester   383819    398052
            Leeds        582044    152953

            >>> # Delete the table "England"
            >>> testdb.drop_table(table_name=table, schema_name=schema, verbose=True)
            To drop the table "points"."England" from postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Dropping "points"."England" ... Done.

            >>> # Delete the schema "points"
            >>> testdb.drop_schema(schema, verbose=True)
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

            sql_qry = 'SELECT * FROM "table_name" '
                      'WHERE "timestamp_column_name" BETWEEN %(ts_start)s AND %(ts_end)s'

            params = {'ds_start': datetime.datetime.today(), 'ds_end': datetime.datetime.today()}

            data_frame = pandas.read_sql(sql_qry, testdb.engine, params=params)
        """

        methods = ('tempfile', 'stringio', 'spooled')
        ast_msg = "The argument `method` must be one of {'%s', '%s', '%s'}" % methods
        assert method in methods, ast_msg

        if tempfile_kwargs is None:
            tempfile_kwargs = {'buffering': -1,
                               'encoding': None,
                               'newline': None,
                               'suffix': None,
                               'prefix': None,
                               'dir': None,
                               'errors': None}

        if method == 'tempfile':  # using tempfile.TemporaryFile
            csv_temp = tempfile.TemporaryFile(tempfile_mode, **tempfile_kwargs)

        elif method == 'stringio':  # using io.StringIO
            if stringio_kwargs is None:
                stringio_kwargs = {'initial_value': '', 'newline': '\n'}
            csv_temp = io.StringIO(**stringio_kwargs)

        else:  # method == 'spooled_tempfile': using tempfile.SpooledTemporaryFile
            # Data would be spooled in memory until its size > max_spooled_size
            csv_temp = tempfile.SpooledTemporaryFile(max_size_spooled * 10 ** 9, tempfile_mode,
                                                     **tempfile_kwargs)

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
        table_data = pandas.read_csv(csv_temp, dtype=dtype, **kwargs)

        csv_temp.close()

        # Close the cursor
        cur.close()

        connection.close()

        return table_data
