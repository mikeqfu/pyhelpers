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

from .ops import confirmed


def get_tfdb_addr(db_cls):
    """
    Get default address of the Track Fixity database.

    :param db_cls: a class representation of a database
    :type db_cls: object
    :return: default address of database
    :rtype: str

    **Test**::

        >>> from pyhelpers.sql import get_tfdb_addr, PostgreSQL

        >>> tfdb_addr = get_tfdb_addr(db_cls=PostgreSQL)

        >>> print(tfdb_addr)
        None:***@None:None/None
    """

    args_spec = inspect.getfullargspec(db_cls)

    args_dict = dict(zip([x for x in args_spec.args if x != 'self'], args_spec.defaults))

    db_address = "{}:***@{}:{}/{}".format(args_dict['username'], args_dict['host'],
                                          args_dict['port'], args_dict['database_name'])

    return db_address


class PostgreSQL:
    """
    A class for a basic `PostgreSQL <https://www.postgresql.org/>`_ instance.

    :param host: host address,
        e.g. ``'localhost'`` or ``'127.0.0.1'`` (default by installation),
        defaults to ``None``
    :type host: str or None
    :param port: port, e.g. ``5432`` (default by installation), defaults to ``None``
    :type port: int or None
    :param username: database username, e.g. ``'postgres'`` (default by installation),
        defaults to ``None``
    :type username: str or None
    :param password: database password, defaults to ``None``
    :type password: str or int or None
    :param database_name: database name, e.g. ``'postgres'`` (default by installation),
        defaults to ``None``
    :type database_name: str
    :param confirm_new_db: whether to impose a confirmation to create a new database,
        defaults to ``False``
    :type confirm_new_db: bool
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``True``
    :type verbose: bool

    **Examples**::

        >>> from pyhelpers.sql import PostgreSQL

        >>> # Connect the default database 'postgres'
        >>> postgres = PostgreSQL(host='localhost', port=5432, username='postgres',
        ...                       database_name='postgres')
        Password (postgres@localhost:5432): ***
        Connecting postgres:***@localhost:5432/postgres ... Successfully.

        >>> # Connect a database 'testdb' (which will be created if it does not exist)
        >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
        ...                     database_name='testdb')
        Password (postgres@localhost:5432): ***
        Connecting postgres:***@localhost:5432/testdb ... Successfully.

        >>> # Define a proxy object that inherits from pyhelpers.sql.PostgreSQL
        >>> class ExampleProxyObj(PostgreSQL):
        ...
        ...     def __init__(self, host='localhost', port=5432, username='postgres',
        ...                  password=None, database_name='testdb', **kwargs):
        ...
        ...         super().__init__(host=host, port=port, username=username,
        ...                          password=password, database_name=database_name,
        ...                          **kwargs)

        >>> example_proxy_obj = ExampleProxyObj()
        Password (postgres@localhost:5432): ***
        Connecting postgres:***@localhost:5432/testdb ... Successfully.
    """

    def __init__(self, host=None, port=None, username=None, password=None,
                 database_name=None, confirm_new_db=False, verbose=True):
        """
        Constructor method.
        """
        import sqlalchemy.engine.url
        import sqlalchemy_utils

        host_ = input("PostgreSQL Host: ") if host is None else str(host)
        port_ = input("PostgreSQL Port: ") if port is None else int(port)
        username_ = input("Username: ") if username is None else str(username)
        password_ = str(password) if password \
            else getpass.getpass("Password ({}@{}:{}): ".format(username_, host_, port_))
        database_name_ = input("Database: ") if database_name is None \
            else str(database_name)

        self.database_info = {'drivername': 'postgresql+psycopg2',
                              'host': host_,
                              'port': port_,
                              'username': username_,
                              'password': password_,
                              'database': database_name_}

        # The typical form of a database URL is:
        # url = backend+driver://username:password@host:port/database
        self.url = sqlalchemy.engine.url.URL(**self.database_info)

        self.dialect = self.url.get_dialect()
        self.backend = self.url.get_backend_name()
        self.driver = self.url.get_driver_name()
        self.user, self.host, self.port = self.url.username, self.url.host, self.url.port
        self.database_name = self.database_info['database']

        self.address = "{}:***@{}:{}/{}".format(
            self.user, self.host, self.port, self.database_name)

        if not sqlalchemy_utils.database_exists(self.url):
            if confirmed("The database \"{}\" does not exist. "
                         "Proceed by creating it?".format(self.database_name),
                         confirmation_required=confirm_new_db):
                if verbose:
                    print("Connecting {} ... ".format(self.address), end="")
                sqlalchemy_utils.create_database(self.url)
        else:
            if verbose:
                print("Connecting {} ... ".format(self.address), end="")

        try:
            import sqlalchemy
            # Create a SQLAlchemy connectable
            self.engine = sqlalchemy.create_engine(self.url, isolation_level='AUTOCOMMIT')
            self.connection = self.engine.raw_connection()

            print("Successfully. ") if verbose else ""

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

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> testdb.database_exists()
            True

            >>> testdb.drop_database()
            Confirmed to drop the database "testdb"
                from postgres:***@localhost:5432/testdb?
              [No]|Yes: yes
        """

        database_name_ = str(database_name) if database_name is not None \
            else self.database_name

        result = self.engine.execute("SELECT EXISTS("
                                     "SELECT datname FROM pg_catalog.pg_database "
                                     "WHERE datname='{}');".format(database_name_))

        return result.fetchone()[0]

    def connect_database(self, database_name=None, verbose=False):
        """
        Establish a connection to a database of the PostgreSQL server being connected.

        :param database_name: name of a database;
            if ``None`` (default), the database name is input manually
        :type database_name: str or None
        :param verbose: whether to print relevant information in console
            as the function runs, defaults to ``False``
        :type verbose: bool

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> testdb.connect_database()
            >>> print(testdb.database_name)
            testdb

            >>> testdb.connect_database('postgres', verbose=True)
            Connecting postgres:***@localhost:5432/postgres ... Successfully.

            >>> print(testdb.database_name)
            postgres
        """

        import sqlalchemy.engine.url
        import sqlalchemy_utils

        if database_name:
            self.database_name = str(database_name)

            self.address = "{}:***@{}:{}/{}".format(
                self.user, self.host, self.port, self.database_name)

            print("Connecting {}".format(self.address), end=" ... ") if verbose else ""

            try:
                self.database_info['database'] = self.database_name
                self.url = sqlalchemy.engine.url.URL(**self.database_info)

                if not sqlalchemy_utils.database_exists(self.url):
                    sqlalchemy_utils.create_database(self.url)

                self.engine = sqlalchemy.create_engine(
                    self.url, isolation_level='AUTOCOMMIT')
                self.connection = self.engine.raw_connection()

                print("Successfully. ") if verbose else ""

            except Exception as e:
                print("Failed. {}.".format(e))

    def create_database(self, database_name, verbose=False):
        """
        An alternative to `sqlalchemy_utils.create_database
        <https://sqlalchemy-utils.readthedocs.io/en/latest/
        database_helpers.html#create-database>`_.

        :param database_name: name of a database
        :type database_name: str
        :param verbose: whether to print relevant information in console
            as the function runs, defaults to ``False``
        :type verbose: bool

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> testdb.create_database('testdb1', verbose=True)
            Creating a database "testdb1" ... Done.

            >>> print(testdb.database_name)
            testdb1

            >>> testdb.drop_database(verbose=True)
            Confirmed to drop the database "testdb1"
                from postgres:***@localhost:5432/testdb?
              [No]|Yes: yes
            Dropping the database "testdb1" ... Done.
        """

        if not self.database_exists(database_name):
            if verbose:
                print("Creating a database \"{}\" ... ".format(database_name), end="")

            self.disconnect_database()
            self.engine.execute('CREATE DATABASE "{}";'.format(database_name))

            print("Done.") if verbose else ""

        else:
            print("The database already exists.") if verbose else ""

        self.connect_database(database_name)

    def get_database_size(self, database_name=None):
        """
        Get the size of a database in the PostgreSQL server being connected.

        When ``database_name=None`` (default), the connected database is checked.

        :param database_name: name of a database, defaults to ``None``
        :type database_name: str or None
        :return: size of the database
        :rtype: int

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> print(testdb.get_database_size())
            7913 kB
        """

        db_name = '\'{}\''.format(database_name) if database_name \
            else 'current_database()'

        db_size = self.engine.execute(
            'SELECT pg_size_pretty(pg_database_size({})) AS size;'.format(db_name))

        return db_size.fetchone()[0]

    def disconnect_database(self, database_name=None, verbose=False):
        """
        Kill the connection to a database in the PostgreSQL server being connected.

        If ``database_name is None`` (default), disconnect the current database.

        :param database_name: name of database to disconnect from, defaults to ``None``
        :type database_name: str or None
        :param verbose: whether to print relevant information in console
            as the function runs, defaults to ``False``
        :type verbose: bool

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

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

            print("Done.") if verbose else ""

        except Exception as e:
            print("Failed. {}".format(e))

    def disconnect_other_databases(self):
        """
        Kill connections to all other databases of the PostgreSQL server being connected.
        """

        self.connect_database(database_name='postgres')

        self.engine.execute(
            'SELECT pg_terminate_backend(pid) FROM pg_stat_activity '
            'WHERE pid <> pg_backend_pid();')

    def drop_database(self, database_name=None, confirmation_required=True,
                      verbose=False):
        """
        Drop a database from the PostgreSQL server being connected.

        If ``database_name is None`` (default), drop the current database.

        :param database_name: database to be disconnected, defaults to ``None``
        :type database_name: str or None
        :param confirmation_required: whether to prompt a message
            for confirmation to proceed, defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console
            as the function runs, defaults to ``False``
        :type verbose: bool

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> testdb.drop_database(verbose=True)
            Confirmed to drop the database "testdb" from postgres:***@localhost:5432
            ? [No]|Yes: yes
            Dropping "testdb" ... Done.

            >>> testdb.database_exists(database_name='testdb')
            False

            >>> print(testdb.database_name)
            postgres
        """

        db_name = self.database_name if database_name is None else database_name

        if confirmed(
                "Confirmed to drop the database \"{}\" from {}\n?".format(
                    db_name, self.address.replace(f"/{db_name}", "")),
                confirmation_required=confirmation_required):
            self.disconnect_database(db_name)

            if verbose:
                if confirmation_required:
                    log_msg = "Dropping \"{}\"".format(db_name)
                else:
                    log_msg = "Dropping the database \"{}\"".format(db_name)
                print(log_msg, end=" ... ")

            try:
                self.engine.execute('DROP DATABASE IF EXISTS "{}"'.format(db_name))

                print("Done. ") if verbose else ""

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

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> testdb.schema_exists('public')
            True

            >>> testdb.schema_exists('test_schema')
            >>> # (if the schema 'test_schema' does not exist)
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
        :param verbose: whether to print relevant information in console
            as the function runs, defaults to ``False``
        :type verbose: bool

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> test_schema_name = 'test_schema'

            >>> testdb.create_schema(test_schema_name, verbose=True)
            Creating a schema "test_schema" ... Done.

            >>> testdb.schema_exists(test_schema_name)
            True

            >>> testdb.drop_schema(test_schema_name, verbose=True)
            Confirmed to drop the following schema:
                "test_schema"
              from postgres:***@localhost:5432/testdb?
              [No]|Yes: yes
            Dropping ...
                "test_schema" ... Done.
        """

        if not self.schema_exists(schema_name=schema_name):

            if verbose:
                print("Creating a schema \"{}\" ... ".format(schema_name), end="")

            try:
                self.engine.execute('CREATE SCHEMA IF NOT EXISTS "{}";'.format(schema_name))

                print("Done.") if verbose else ""

            except Exception as e:
                print("Failed. {}".format(e))

        else:
            print("The schema \"{}\" already exists.".format(schema_name))

    def msg_for_multi_schemas(self, schema_names, desc='schema'):
        """
        Formulate printing message for multiple schemas.

        :param schema_names: name of one table/schema, or names of several table/schemas
        :type schema_names: str or collections.abc.Iterable
        :param desc: for additional description, defaults to ``'schema'``
        :type desc: str
        :return: printing message
        :rtype: tuple

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> schema_names_ = ['points', 'lines', 'polygons']
            >>> msg = testdb.msg_for_multi_schemas(schema_names_)

            >>> for msg_ in msg:
            >>>     print(msg_)
            ['points', 'lines', 'polygons']
            schemas:
                "points",
                "lines" and
                "polygons"


        :meta private:
        """

        import sqlalchemy.engine.reflection

        if schema_names:
            names_ = [schema_names] if isinstance(schema_names, str) else schema_names
        else:
            inspector = sqlalchemy.engine.reflection.Inspector.from_engine(self.engine)
            names_ = [x for x in inspector.get_schema_names()
                      if x != 'public' and x != 'information_schema']

        print_plural = (("{}: " if len(names_) == 1 else "{}s: ").format(desc))

        if len(names_) == 1:
            print_schema = "\n\t\"{}\"\n".format(names_[0])
        elif len(names_) == 2:
            print_schema = "\n\t\"{}\" and\n\t\"{}\"\n".format(*names_)
        else:
            print_schema = ("\n\t\"{}\"," * (len(names_) - 2) +
                            "\n\t\"{}\" and\n\t\"{}\"\n").format(*names_)

        return names_, print_plural + print_schema

    def drop_schema(self, schema_names, confirmation_required=True, verbose=False):
        """
        Drop a schema in the database being connected.

        :param schema_names: name of one schema, or names of multiple schemas
        :type schema_names: str or collections.abc.Iterable
        :param confirmation_required: whether to prompt a message
            for confirmation to proceed, defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console
            as the function runs, defaults to ``False``
        :type verbose: bool

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> new_schema_names = ['points', 'lines', 'polygons']
            >>> new_schema_names_ = ['test_schema']

            >>> for new_schema in new_schema_names:
            ...     testdb.create_schema(new_schema, verbose=True)
            Creating a schema "points" ... Done.
            Creating a schema "lines" ... Done.
            Creating a schema "polygons" ... Done.

            >>> testdb.drop_schema(new_schema_names + new_schema_names_, verbose=True)
            Confirmed to drop the following schemas:
                "points",
                "lines",
                "polygons" and
                "test_schema"
              from postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Dropping ...
                "points" ... Done.
                "lines" ... Done.
                "polygons" ... Done.
        """

        schema_names_ = [schema_names] if isinstance(schema_names, str) else schema_names
        schemas, schemas_msg = self.msg_for_multi_schemas(schema_names_)

        if confirmed(
                "Confirmed to drop the following {}  from {}\n?".format(
                    schemas_msg, self.address),
                confirmation_required=confirmation_required):

            if verbose:
                if confirmation_required:
                    log_msg = "Dropping ... "
                else:
                    log_msg = "From {}, dropping the following {}".format(
                        self.address, schemas_msg.split(" ")[0])
                print(log_msg)

            for schema in schemas:
                if not self.schema_exists(schema):
                    # `schema` does not exist
                    print(f"\t\"{schema}\" does not exist. ") if verbose == 2 else ""
                else:
                    print(f"\t\"{schema}\"", end=" ... ") if verbose else ""
                    try:
                        # schema_ = ('%s, ' * (len(schemas) - 1) + '%s') % tuple(schemas)
                        self.engine.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;')

                        print("Done.") if verbose else ""

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

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> table_name_ = 'England'
            >>> schema_name_ = 'points'

            >>> testdb.table_exists(table_name_, schema_name_)
            >>> # (if 'points.England' does not exist)
            False
        """

        res = self.engine.execute("SELECT EXISTS("
                                  "SELECT * FROM information_schema.tables "
                                  "WHERE table_schema='{}' "
                                  "AND table_name='{}');".format(schema_name, table_name))

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
        :param verbose: whether to print relevant information in console
            as the function runs, defaults to ``False``
        :type verbose: bool

        .. _postgresql-create_table-example:

        **Example**::

            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> tbl_name = 'test_table'
            >>> column_specifications = 'col_name_1 INT, col_name_2 TEXT'

            >>> testdb.create_table(tbl_name, column_specifications, verbose=True)
            Creating a table '"public"."test_table"' ... Done.

            >>> res = testdb.table_exists(tbl_name)
            >>> print(f"The table 'public.\"{tbl_name}\"' exists? {res}.")
            The table 'public."test_table"' exists? True.

            >>> test_tbl_col_info = testdb.get_column_info(tbl_name, as_dict=False)
            >>> print(test_tbl_col_info.head())
                                column_0    column_1
            table_catalog         testdb      testdb
            table_schema          public      public
            table_name        test_table  test_table
            column_name       col_name_1  col_name_2
            ordinal_position           1           2

            >>> # Drop the table
            >>> testdb.drop_table(tbl_name, verbose=True)
            Confirmed to drop '"public"."test_table"'
                from postgres:***@localhost:5432/testdb
            ? [No]|Yes: >? yes
            Dropping '"public"."test_table"' ... Done.
        """

        table_name_ = '"{schema}"."{table}"'.format(schema=schema_name, table=table_name)

        if not self.schema_exists(schema_name):
            self.create_schema(schema_name, verbose=False)

        try:
            if verbose:
                print("Creating a table '{}' ... ".format(table_name_), end="")

            self.engine.execute('CREATE TABLE {} ({});'.format(table_name_, column_specs))

            print("Done.") if verbose else ""

        except Exception as e:
            print("Failed. {}".format(e))

    def get_column_info(self, table_name, schema_name='public', as_dict=True):
        """
        Get information about columns of a table.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param as_dict: whether to return the column information as a dictionary,
            defaults to ``True``
        :type as_dict: bool
        :return: information about each column of the given table
        :rtype: pandas.DataFrame or dict

        See the example for the method
        :py:meth:`.create_table()<pyhelpers.sql.PostgreSQL.create_table>`.
        """

        column_info = self.engine.execute(
            "SELECT * FROM information_schema.columns "
            "WHERE table_schema='{}' AND table_name='{}';".format(
                schema_name, table_name))

        keys, values = column_info.keys(), column_info.fetchall()
        idx = ['column_{}'.format(x) for x in range(len(values))]

        info_tbl = pd.DataFrame(values, index=idx, columns=keys).T

        if as_dict:
            info_tbl = {k: v.to_list() for k, v in info_tbl.iterrows()}

        return info_tbl

    def drop_table(self, table_name, schema_name='public', confirmation_required=True,
                   verbose=False):
        """
        Remove a table from the database being connected.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param confirmation_required: whether to prompt a message
            for confirmation to proceed, defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console
            as the function runs, defaults to ``False``
        :type verbose: bool

        See the example for the method
        :py:meth:`.create_table()<pyhelpers.sql.PostgreSQL.create_table>`.
        """

        table = '\"{}\".\"{}\"'.format(schema_name, table_name)

        if not self.table_exists(table_name=table_name, schema_name=schema_name):
            print("The table '{}' does not exist.".format(table))

        else:
            if confirmed("Confirmed to drop the table '{}'\n\tfrom {}\n?".format(
                    table, self.address), confirmation_required=confirmation_required):

                if verbose:
                    if confirmation_required:
                        log_msg = "Dropping '{}'".format(table)
                    else:
                        log_msg = "Dropping the table '{}'\n\tfrom {}".format(
                            table, self.address)
                    print(log_msg, end=" ... ")

                try:
                    self.engine.execute('DROP TABLE IF EXISTS {}.\"{}\" CASCADE;'.format(
                        schema_name, table_name))

                    if verbose:
                        print("Done.")

                except Exception as e:
                    print("Failed. {}".format(e))

    @staticmethod
    def psql_insert_copy(sql_table, sql_db_engine, column_name_list, data_iter):
        """
        A callable using PostgreSQL COPY clause for executing inserting data.

        :param sql_table: pandas.io.sql.SQLTable
        :param sql_db_engine: sqlalchemy.engine.Connection or sqlalchemy.engine.Engine
        :param column_name_list: (list of str) column names
        :param data_iter: iterable that iterates the values to be inserted

        .. note::

            This function is copied and slightly modified from the source code
            available at
            [`PIC-1 <https://pandas.pydata.org/pandas-docs/stable/user_guide/
            io.html#io-sql-method>`_].
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

    def import_data(self, data, table_name, schema_name='public', if_exists='replace',
                    force_replace=False, chunk_size=None, col_type=None, method='multi',
                    index=False, confirmation_required=True, verbose=False, **kwargs):
        """
        Import tabular data into the database being connected.

        See also
        [`DD-1 <https://pandas.pydata.org/pandas-docs/stable/user_guide/
        io.html#io-sql-method/>`_] and
        [`DD-2 <https://www.postgresql.org/docs/current/sql-copy.html/>`_].

        :param data: data frame to be dumped into a database
        :type data: pandas.DataFrame
        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param if_exists: if the table already exists,
            to ``'replace'`` (default), ``'append'`` or ``'fail'``
        :type if_exists: str
        :param force_replace: whether to force to replace existing table,
            defaults to ``False``
        :type force_replace: bool
        :param chunk_size: the number of rows in each batch to be written at a time,
            defaults to ``None``
        :type chunk_size: int or None
        :param col_type: data types for columns, defaults to ``None``
        :type col_type: dict, None
        :param method: method for SQL insertion clause, defaults to ``'multi'``

            * ``None``: uses standard SQL ``INSERT`` clause (one per row);
            * ``'multi'``: pass multiple values in a single ``INSERT`` clause;
            * callable (e.g. ``PostgreSQL.psql_insert_copy``)
              with signature ``(pd_table, conn, keys, data_iter)``.

        :type method: str or None or types.FunctionType
        :param index: whether to dump the index as a column
        :type index: bool
        :param confirmation_required: whether to prompt a message
            for confirmation to proceed, defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console
            as the function runs, defaults to ``False``
        :type verbose: bool
        :param kwargs: optional parameters of `pandas.DataFrame.to_sql`_

        .. _`pandas.DataFrame.to_sql`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/
            pandas.DataFrame.to_sql.html

        See the example for the method
        :py:meth:`.read_sql_query() <pyhelpers.sql.PostgreSQL.read_sql_query>`.
        """

        table_name_ = '"{}"."{}"'.format(schema_name, table_name)

        if confirmed("Confirmed to import the data into table '{}'\n\tat {}\n?".format(
                table_name_, self.address), confirmation_required=confirmation_required):

            import sqlalchemy.engine.reflection

            inspector = sqlalchemy.engine.reflection.Inspector.from_engine(self.engine)

            if schema_name not in inspector.get_schema_names():
                self.create_schema(schema_name, verbose=verbose)
            # if not data.empty:
            #   There may be a need to change column types

            if self.table_exists(table_name, schema_name):
                if if_exists == 'replace' and verbose:
                    print("The table {} already exists and is replaced ... ".format(
                        table_name_))

                if force_replace:
                    if verbose:
                        print("The existing table is dropped first ... ")
                    self.drop_table(table_name, schema_name, verbose=verbose)

            try:
                if verbose:
                    if confirmation_required:
                        log_msg = "Importing data into '{}'".format(table_name_)
                        log_end_msg = " ... "
                    else:
                        log_msg = "Importing the data into table '{}' ... " \
                                  "\n\tat {}".format(table_name_, self.address)
                        log_end_msg = " ... \n"
                    print(log_msg, end=log_end_msg)

                if isinstance(data, pandas.io.parsers.TextFileReader):
                    for chunk in data:
                        chunk.to_sql(table_name, self.engine, schema=schema_name,
                                     if_exists=if_exists, index=index, dtype=col_type,
                                     method=method, **kwargs)
                        del chunk
                        gc.collect()

                else:
                    data.to_sql(table_name, self.engine, schema=schema_name,
                                if_exists=if_exists, index=index, chunksize=chunk_size,
                                dtype=col_type, method=method, **kwargs)
                    gc.collect()

                print("Done. ") if verbose else ""

            except Exception as e:
                print("Failed. {}".format(e))

    def read_table(self, table_name, schema_name='public', condition=None,
                   chunk_size=None, sorted_by=None, **kwargs):
        """
        Read data from a table of the database being connected.

        See also
        [`RT-1 <https://stackoverflow.com/questions/24408557/
        pandas-read-sql-with-parameters>`_].

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param condition: defaults to ``None``
        :type condition: str or None
        :param chunk_size: number of rows to include in each chunk, defaults to ``None``
        :type chunk_size: int or None
        :param sorted_by: name(s) of a column (or columns)
            by which the retrieved data is sorted, defaults to ``None``
        :type sorted_by: str or None
        :param kwargs: optional parameters of `pandas.read_sql`_

        :return: data frame from the specified table
        :rtype: pandas.DataFrame

        .. _`pandas.read_sql`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/
            pandas.read_sql.html

        See the example for the method
        :py:meth:`.read_sql_query() <pyhelpers.sql.PostgreSQL.read_sql_query>`.
        """

        if condition:
            assert isinstance(condition, str), "'condition' must be 'str' type."
            sql_query = 'SELECT * FROM "{}"."{}" {};'.format(
                schema_name, table_name, condition)

        else:
            sql_query = 'SELECT * FROM "{}"."{}";'.format(schema_name, table_name)

        table_data = pd.read_sql(sql_query, con=self.engine, chunksize=chunk_size,
                                 **kwargs)

        if sorted_by and isinstance(sorted_by, str):
            table_data.sort_values(sorted_by, inplace=True)
            table_data.index = range(len(table_data))

        return table_data

    def read_sql_query(self, sql_query, method='spooled_tempfile', tempfile_mode='w+b',
                       max_size_spooled=1, delimiter=',', dtype=None,
                       tempfile_kwargs=None, stringio_kwargs=None, **kwargs):
        """
        Read table data by SQL query (recommended for large table).

        See also
        [`RSQ-1 <https://towardsdatascience.com/
        optimizing-pandas-read-sql-for-postgres-f31cd7f707ab>`_],
        [`RSQ-2 <https://docs.python.org/3/library/tempfile.html>`_] and
        [`RSQ-3 <https://docs.python.org/3/library/io.html>`_].

        :param sql_query: SQL query to be executed
        :type sql_query: str
        :param method: method to be used for buffering temporary data

            * `'spooled_tempfile'` (default): use `tempfile.SpooledTemporaryFile`_
            * `'tempfile'`: use `tempfile.TemporaryFile`_
            * `'stringio'`: use `io.StringIO`_

        :type method: str
        :param tempfile_mode: mode of the specified `method`, defaults to ``'w+b'``
        :type tempfile_mode: str
        :param max_size_spooled: ``max_size`` of `tempfile.SpooledTemporaryFile`_,
            defaults to ``1`` (in gigabyte)
        :type max_size_spooled: int, float
        :param delimiter: delimiter used in data, defaults to ``','``
        :type delimiter: str
        :param dtype: data type for specified data columns,
            `dtype` used by `pandas.read_csv`_, defaults to ``None``
        :type dtype: dict, None
        :param tempfile_kwargs: optional parameters of
            `tempfile.TemporaryFile`_ or `tempfile.SpooledTemporaryFile`_
        :param stringio_kwargs: optional parameters of `io.StringIO`_,
            e.g. ``initial_value`` (default: ``''``)
        :param kwargs: optional parameters of `pandas.read_csv`_
        :return: data frame as queried by the statement ``sql_query``
        :rtype: pandas.DataFrame

        .. _`pandas.read_csv`: https://pandas.pydata.org/pandas-docs/stable/reference/
            api/pandas.read_csv.html
        .. _`open`: https://docs.python.org/3/library/functions.html#open
        .. _`tempfile.TemporaryFile`: https://docs.python.org/3/library/
            tempfile.html#tempfile.TemporaryFile
        .. _`tempfile.SpooledTemporaryFile`:
            https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile
        .. _`io.StringIO`: https://docs.python.org/3/library/io.html#io.StringIO
        .. _`tempfile.mkstemp`: https://docs.python.org/3/library/
            tempfile.html#tempfile.mkstemp

        **Examples**::

            >>> import pandas as pd_
            >>> from pyhelpers.sql import PostgreSQL

            >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
            ...                     database_name='testdb', verbose=False)
            Password (postgres@localhost:5432): ***

            >>> # Create a pandas.DataFrame
            >>> xy_array = [(530034, 180381),
            ...             (406689, 286822),
            ...             (383819, 398052),
            ...             (582044, 152953)]
            >>> col_name = ['Easting', 'Northing']
            >>> dat = pd_.DataFrame(xy_array, columns=col_name)

            >>> table = 'England'
            >>> schema = 'points'

            >>> testdb.import_data(dat, table, schema, if_exists='replace',
            ...                    chunk_size=None, force_replace=False, col_type=None,
            ...                    verbose=True)
            Confirmed to import the data into table '"points"."England"'
                at postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Importing data into '"points"."England"' ... Done.

            >>> res = testdb.table_exists(table, schema)
            >>> print(f"The table '\"{schema}\".\"{table}\"' exists? {res}.")
            The table '"points"."England"' exists? True.

            >>> dat_retrieval = testdb.read_table(table, schema)
            >>> print(dat_retrieval)
               Easting  Northing
            0   530034    180381
            1   406689    286822
            2   383819    398052
            3   582044    152953

            >>> # Alternatively
            >>> sql_query_ = f'SELECT * FROM "{schema}"."{table}"'
            >>> dat_retrieval_ = testdb.read_sql_query(sql_query_)
            >>> print(dat_retrieval_)
               Easting  Northing
            0   530034    180381
            1   406689    286822
            2   383819    398052
            3   582044    152953

            >>> testdb.drop_table(table_name=table, schema_name=schema, verbose=True)
            Confirmed to drop the table '"points"."England"'
                from postgres:***@localhost:5432/testdb
            ? [No]|Yes: yes
            Dropping '"points"."England"' ... Done.

            >>> testdb.drop_schema(schema, verbose=True)
            Confirmed to drop the following schema:
                "points"
              from postgres:***@localhost:5432/testdb?
              [No]|Yes: >? yes
            Dropping ...
                "points" ... Done.

            >>> testdb.drop_database(verbose=True)
            Confirmed to drop the database "testdb"
                from postgres:***@localhost:5432/testdb?
              [No]|Yes: >? yes
            Dropping the database "testdb" ... Done.

        **Aside**: a brief example of using the parameter ``params`` for
        `pandas.read_sql <https://pandas.pydata.org/pandas-docs/stable/reference/api/
        pandas.read_sql.html>`_

        .. code-block:: python

            import datetime

            sql_query_ = 'SELECT * FROM "table_name" '
                         'WHERE "timestamp_column_name" '
                         'BETWEEN %(ts_start)s AND %(ts_end)s'

            params = {'ds_start': datetime.datetime.today(),
                      'ds_end': datetime.datetime.today()}

            data_frame = pd_.read_sql(sql_query_, testdb.engine, params=params)
        """

        methods = ('stringio', 'tempfile', 'spooled_tempfile')
        assert method in methods, \
            "The argument `method` must be one of {'%s', '%s', '%s'}" % methods

        if tempfile_kwargs is None:
            tempfile_kwargs = {'buffering': -1,
                               'encoding': None,
                               'newline': None,
                               'suffix': None,
                               'prefix': None,
                               'dir': None,
                               'errors': None}

        if method == 'spooled_tempfile':
            # Use tempfile.SpooledTemporaryFile - data would be spooled in memory until
            # its size > max_spooled_size
            csv_temp = tempfile.SpooledTemporaryFile(max_size_spooled * 10 ** 9,
                                                     tempfile_mode, **tempfile_kwargs)

        elif method == 'tempfile':
            # Use tempfile.TemporaryFile
            csv_temp = tempfile.TemporaryFile(tempfile_mode, **tempfile_kwargs)

        else:  # method == 'stringio', i.e. use io.StringIO
            if stringio_kwargs is None:
                stringio_kwargs = {'initial_value': '', 'newline': '\n'}
            csv_temp = io.StringIO(**stringio_kwargs)

        # Specify the SQL query for "COPY"
        copy_sql = \
            "COPY ({query}) TO STDOUT WITH DELIMITER '{delimiter}' CSV HEADER;".format(
                query=sql_query, delimiter=delimiter)

        # Get a cursor
        cur = self.connection.cursor()
        cur.copy_expert(copy_sql, csv_temp)
        # Rewind the file handle using seek() in order to read the data back from it
        csv_temp.seek(0)
        # Read data from temporary csv
        table_data = pandas.read_csv(csv_temp, dtype=dtype, **kwargs)

        # Close the cursor
        cur.close()

        return table_data
