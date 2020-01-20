""" PostgreSQL """

import gc
import getpass

import pandas as pd
import pandas.io.parsers
import sqlalchemy
import sqlalchemy.engine.reflection
import sqlalchemy.engine.url
import sqlalchemy_utils

from pyhelpers.ops import confirmed


# PostgreSQL
class PostgreSQL:
    def __init__(self, host='localhost', port=5432, username='postgres', password=None, database_name='postgres',
                 verbose=True):
        """
        :param host: [str] (default: 'localhost'; or '127.0.0.1')
        :param port: [int] (default: 5432)
        :param username: [str] (default: 'postgres')
        :param password: [str; None (default)]
        :param database_name: [str] (default: 'postgres')
        """
        self.database_info = {'drivername': 'postgresql+psycopg2',
                              'host': host if host else input("PostgreSQL Host: "),  # default: 'localhost'
                              'port': port if port else input("PostgreSQL Port: "),  # 5432 (default by installation).
                              'username': username if username else input("Username: "),
                              'password': password if password else getpass.getpass("Password: "),
                              'database': database_name}

        # The typical form of a database URL is: url = backend+driver://username:password@host:port/database
        self.url = sqlalchemy.engine.url.URL(**self.database_info)

        self.dialect = self.url.get_dialect()
        self.backend = self.url.get_backend_name()
        self.driver = self.url.get_driver_name()
        self.user, self.host, self.port = self.url.username, self.url.host, self.url.port
        self.database_name = self.database_info['database']

        if verbose:
            print("Connecting to PostgreSQL database: {}@{} ... ".format(self.database_name, self.host), end="")
        try:
            if not sqlalchemy_utils.database_exists(self.url):
                sqlalchemy_utils.create_database(self.url)

            # Create a SQLAlchemy connectable
            self.engine = sqlalchemy.create_engine(self.url, isolation_level='AUTOCOMMIT')
            self.connection = self.engine.connect()
            print("Successfully.") if verbose else ""
        except Exception as e:
            print("Failed. CAUSE: \"{}\".".format(e))

    # Establish a connection to the specified database_name
    def connect_db(self, database_name=None):
        """
        :param database_name: [str; None (default)] name of a database
        """
        self.database_name = 'postgres' if database_name is None else database_name
        self.database_info['database'] = self.database_name
        self.url = sqlalchemy.engine.url.URL(**self.database_info)
        if not sqlalchemy_utils.database_exists(self.url):
            sqlalchemy_utils.create_database(self.url)
        self.engine = sqlalchemy.create_engine(self.url, isolation_level='AUTOCOMMIT')
        self.connection = self.engine.connect()

    # Check if a database exists
    def db_exists(self, database_name):
        result = self.engine.execute("SELECT EXISTS("
                                     "SELECT datname FROM pg_catalog.pg_database "
                                     "WHERE datname='{}');".format(database_name))
        return result.fetchone()[0]

    # An alternative to sqlalchemy_utils.create_database()
    def create_db(self, database_name, verbose=False):
        if not self.db_exists(database_name):
            print("Creating a database \"{}\" ... ".format(database_name), end="") if verbose else ""
            self.disconnect()
            self.engine.execute('CREATE DATABASE "{}";'.format(database_name))
            self.connect_db(database_name)
            print("Done.") if verbose else ""
        else:
            print("The database already exists.") if verbose else ""

    # Get size of a database
    def get_db_size(self, database_name=None):
        db_name = '\'{}\''.format(database_name) if database_name else 'current_database()'
        db_size = self.engine.execute('SELECT pg_size_pretty(pg_database_size({})) AS size;'.format(db_name))
        print(db_size.fetchone()[0])

    # Kill the connection to the specified database_name
    def disconnect(self, database_name=None, verbose=False):
        """
        :param database_name: [str; None (default)] name of database to disconnect from
        :param verbose: [bool] (default: False)
        """
        db_name = self.database_name if database_name is None else database_name
        print("Disconnecting the database \"{}\" ... ".format(db_name), end="") if verbose else ""
        try:
            self.connect_db()
            self.engine.execute('REVOKE CONNECT ON DATABASE "{}" FROM PUBLIC, postgres;'.format(db_name))
            self.engine.execute(
                'SELECT pg_terminate_backend(pid) '
                'FROM pg_stat_activity '
                'WHERE datname = \'{}\' AND pid <> pg_backend_pid();'.format(db_name))
            print("Done.") if verbose else ""
        except Exception as e:
            print("Failed. CAUSE: \"{}\"".format(e))

    # Kill connections to all other databases
    def disconnect_all_other_dbs(self):
        self.connect_db('postgres')
        self.engine.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid();')

    # Drop the specified database
    def drop(self, database_name=None, confirmation_required=True, verbose=False):
        """
        :param database_name: [str; None (default)] database to be disconnected; None to disconnect the current one
        :param confirmation_required: [bool] (default: True)
        :param verbose: [bool] (default: False)
        """
        db_name = self.database_name if database_name is None else database_name
        if confirmed("Confirmed to drop the database \"{}\" for {}@{}?".format(db_name, self.user, self.host),
                     confirmation_required=confirmation_required):
            self.disconnect(db_name)
            try:
                print("Dropping the database \"{}\" ... ".format(db_name), end="") if verbose else ""
                self.engine.execute('DROP DATABASE IF EXISTS "{}"'.format(db_name))
                print("Done.") if verbose else ""
            except Exception as e:
                print("Failed. CAUSE: \"{}\"".format(e))

    # Create a new schema in the database being currently connected
    def create_schema(self, schema_name, verbose=False):
        """
        :param schema_name: [str] name of a schema
        :param verbose: [bool] (default: False)
        """
        try:
            print("Creating a schema \"{}\" ... ".format(schema_name), end="") if verbose else ""
            self.engine.execute('CREATE SCHEMA IF NOT EXISTS "{}";'.format(schema_name))
            print("Done.") if verbose else ""
        except Exception as e:
            print("Failed. CAUSE: \"{}\"".format(e))

    # Drop a schema in the database being currently connected
    def drop_schema(self, *schema_names, confirmation_required=True, verbose=False):
        """
        :param schema_names: [str] name of one schema, or names of multiple schemas
        :param confirmation_required: [bool] (default: True)
        :param verbose: [bool] (default: False)
        """
        if schema_names:
            schemas = tuple(schema_name for schema_name in schema_names)
        else:
            schemas = tuple(
                x for x in sqlalchemy.engine.reflection.Inspector.from_engine(self.engine).get_schema_names()
                if x != 'public' and x != 'information_schema')
        print_plural = ("schema " if len(schemas) == 1 else "schemas ")
        print_schema = ("\"{}\", " * (len(schemas) - 1) + "\"{}\"").format(*schemas)
        if confirmed("Confirmed to drop the {}{} from the database \"{}\"".format(
                print_plural, print_schema, self.database_name), confirmation_required=confirmation_required):
            try:
                print("Dropping the {}{} ... ".format(print_plural, print_schema), end="") if verbose else ""
                self.engine.execute('DROP SCHEMA IF EXISTS ' + ('%s, '*(len(schemas)-1) + '%s') % schemas + ' CASCADE;')
                print("Done.") if verbose else ""
            except Exception as e:
                print("Failed. CAUSE: \"{}\"".format(e))

    # Check if a table exists
    def table_exists(self, table_name, schema_name='public'):
        """
        :param table_name: [str] name of a table
        :param schema_name: [str] name of a schema (default: 'public')
        :return: [bool] whether the table already exists
        """
        res = self.engine.execute("SELECT EXISTS("
                                  "SELECT * FROM information_schema.tables "
                                  "WHERE table_schema='{}' "
                                  "AND table_name='{}');".format(schema_name, table_name))
        return res.fetchone()[0]

    # Import data (as a pandas.DataFrame) into the database being currently connected
    def dump_data(self, data, table_name, schema_name='public', if_exists='replace', chunk_size=None,
                  force_replace=False, col_type=None, verbose=False):
        """
        :param data: [pandas.DataFrame]
        :param schema_name: [str]
        :param table_name: [str] name of the targeted table
        :param if_exists: [str] 'fail', 'replace' (default), 'append'
        :param force_replace: [bool] (default: False)
        :param col_type: [dict; None (default)]
        :param chunk_size: [int; None (default)]
        :param verbose: [bool] (default: False)
        """
        if schema_name not in sqlalchemy.engine.reflection.Inspector.from_engine(self.engine).get_schema_names():
            self.create_schema(schema_name, verbose=verbose)
        # if not data.empty:
        #   There may be a need to change column types

        if self.table_exists(table_name, schema_name):
            if if_exists == 'replace' and verbose:
                print("The table {}.\"{}\" already exists and will be replaced ... ".format(schema_name, table_name))
            if force_replace:
                if verbose:
                    print("The existing table {}.\"{}\" will be dropped first ... ".format(schema_name, table_name))
                self.drop_table(table_name, verbose=verbose)

        try:
            print("Dumping the data as a table \"{}\" into {}.\"{}\"@{} ... ".format(
                table_name, schema_name, self.database_name, self.host), end="") if verbose else ""
            if isinstance(data, pandas.io.parsers.TextFileReader):
                for chunk in data:
                    chunk.to_sql(table_name, self.engine, schema_name, if_exists=if_exists, index=False, dtype=col_type)
            else:
                data.to_sql(table_name, self.engine, schema_name, if_exists=if_exists, index=False,
                            chunksize=chunk_size, dtype=col_type)
            gc.collect()
            print("Done.") if verbose else ""
        except Exception as e:
            print("Failed. CAUSE: \"{}\"".format(e))

    # Read data and schema (geom type, e.g. points, lines, ...)
    def read_table(self, table_name, schema_name='public', chunk_size=None, sorted_by=None):
        """
        :param table_name: [str] name of a table
        :param schema_name: [str] name of a schema
        :param chunk_size: [int; None (default)] number of rows to include in each chunk
        :param sorted_by: [str; None (default)]
        :return: [pd.DataFrame]
        """
        sql_query = 'SELECT * FROM {}."{}";'.format(schema_name, table_name)
        table_data = pd.read_sql(sql=sql_query, con=self.engine, chunksize=chunk_size)
        if sorted_by:
            table_data.sort_values('id', inplace=True)
            table_data.index = range(len(table_data))
        return table_data

    # Remove data from the database being currently connected
    def drop_table(self, table_name, schema_name='public', confirmation_required=True, verbose=False):
        """
        :param table_name: [str] name of a table
        :param schema_name: [str] name of a schema
        :param confirmation_required: [bool] (default: True)
        :param verbose: [bool] (default: False)
        """
        if confirmed("Confirmed to drop the table \"{}\" from the database \"{}\"?".format(
                table_name, self.database_name), confirmation_required=confirmation_required):
            try:
                self.engine.execute('DROP TABLE IF EXISTS {}.\"{}\" CASCADE;'.format(schema_name, table_name))
                print("The table \"{}\" has been dropped successfully.".format(table_name)) if verbose else ""
            except Exception as e:
                print("Failed. CAUSE: \"{}\"".format(e))
