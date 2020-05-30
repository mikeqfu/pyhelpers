""" PostgreSQL """

import csv
import gc
import getpass
import io
import tempfile

import pandas as pd
import pandas.io.parsers
import sqlalchemy
import sqlalchemy.engine.reflection
import sqlalchemy.engine.url
import sqlalchemy_utils

from pyhelpers.ops import confirmed


# PostgreSQL
class PostgreSQL:
    def __init__(self, host=None, port=None, username=None, password=None, database_name=None,
                 cfm_reqd_cndb=False, verbose=True):
        """
        :param host: [str; None (default)] ('localhost' or '127.0.0.1' - default by installation)
        :param port: [int; None (default)] (5432 - default by installation)
        :param username: [str] (default: 'postgres')
        :param password: [str; None (default)]
        :param database_name: [str] (default: 'postgres')
        :param cfm_reqd_cndb: [bool] (default: False) confirmation required to create a new database (if absent)
        :param verbose: [bool] (default: True)
        """
        host_ = input("PostgreSQL Host: ") if host is None else str(host)
        port_ = input("PostgreSQL Port: ") if port is None else int(port)
        username_ = input("Username: ") if username is None else str(username)
        password_ = str(password) if password else getpass.getpass("Password ({}@{}:{}): ".format(
            username_, host_, port_))
        database_name_ = input("Database: ") if database_name is None else str(database_name)

        self.database_info = {'drivername': 'postgresql+psycopg2',
                              'host': host_,
                              'port': port_,
                              'username': username_,
                              'password': password_,
                              'database': database_name_}

        # The typical form of a database URL is: url = backend+driver://username:password@host:port/database
        self.url = sqlalchemy.engine.url.URL(**self.database_info)

        self.dialect = self.url.get_dialect()
        self.backend = self.url.get_backend_name()
        self.driver = self.url.get_driver_name()
        self.user, self.host, self.port = self.url.username, self.url.host, self.url.port
        self.database_name = self.database_info['database']

        if not sqlalchemy_utils.database_exists(self.url):
            if confirmed("The database \"{}\" does not exist. Proceed by creating it?".format(self.database_name),
                         confirmation_required=cfm_reqd_cndb):
                if verbose:
                    print("Connecting to PostgreSQL database: {}@{}:{} ... ".format(
                        self.database_name, self.host, self.port), end="")
                sqlalchemy_utils.create_database(self.url)
        else:
            if verbose:
                print("Connecting to PostgreSQL database: {}@{}:{} ... ".format(
                    self.database_name, self.host, self.port), end="")
        try:
            # Create a SQLAlchemy connectable
            self.engine = sqlalchemy.create_engine(self.url, isolation_level='AUTOCOMMIT')
            self.connection = self.engine.raw_connection()
            print("Successfully.") if verbose else ""
        except Exception as e:
            print("Failed. CAUSE: \"{}\".".format(e))

    # Check if a database exists
    def database_exists(self, database_name=None):
        """
        :param database_name: [str; None (default)] name of a database
        :return: [bool] True if the database exists; otherwise, False
        """
        database_name_ = str(database_name) if database_name is not None else self.database_name
        result = self.engine.execute("SELECT EXISTS("
                                     "SELECT datname FROM pg_catalog.pg_database "
                                     "WHERE datname='{}');".format(database_name_))
        return result.fetchone()[0]

    # Establish a connection to the specified database_name
    def connect_database(self, database_name=None):
        """
        :param database_name: [str; None (default)] name of a database; if None, the database name is input manually
        """
        self.database_name = str(database_name) if database_name is not None else input("Database name: ")
        self.database_info['database'] = self.database_name
        self.url = sqlalchemy.engine.url.URL(**self.database_info)
        if not sqlalchemy_utils.database_exists(self.url):
            sqlalchemy_utils.create_database(self.url)
        self.engine = sqlalchemy.create_engine(self.url, isolation_level='AUTOCOMMIT')
        self.connection = self.engine.raw_connection()

    # An alternative to sqlalchemy_utils.create_database()
    def create_database(self, database_name, verbose=False):
        """
        :param database_name: [str] name of a database
        :param verbose: [bool] (default: False)
        """
        if not self.database_exists(database_name):
            print("Creating a database \"{}\" ... ".format(database_name), end="") if verbose else ""
            self.disconnect_database()
            self.engine.execute('CREATE DATABASE "{}";'.format(database_name))
            print("Done.") if verbose else ""
        else:
            print("The database already exists.") if verbose else ""
        self.connect_database(database_name)

    # Get size of a database
    def get_database_size(self, database_name=None):
        """
        :param database_name: [str; None (default)] name of a database; if None, the current connected database is used
        :return: [int] size of the database
        """
        db_name = '\'{}\''.format(database_name) if database_name else 'current_database()'
        db_size = self.engine.execute('SELECT pg_size_pretty(pg_database_size({})) AS size;'.format(db_name))
        return db_size.fetchone()[0]

    # Kill the connection to the specified database_name
    def disconnect_database(self, database_name=None, verbose=False):
        """
        :param database_name: [str; None (default)] name of database to disconnect from; if None, current database
        :param verbose: [bool] (default: False)
        """
        db_name = self.database_name if database_name is None else database_name
        print("Disconnecting the database \"{}\" ... ".format(db_name), end="") if verbose else ""
        try:
            self.connect_database(database_name='postgres')
            self.engine.execute('REVOKE CONNECT ON DATABASE "{}" FROM PUBLIC, postgres;'.format(db_name))
            self.engine.execute(
                'SELECT pg_terminate_backend(pid) '
                'FROM pg_stat_activity '
                'WHERE datname = \'{}\' AND pid <> pg_backend_pid();'.format(db_name))
            print("Done.") if verbose else ""
        except Exception as e:
            print("Failed. CAUSE: \"{}\"".format(e))

    # Kill connections to all other databases
    def disconnect_all_other_databases(self):
        self.connect_database(database_name='postgres')
        self.engine.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid();')

    # Drop the specified database
    def drop_database(self, database_name=None, confirmation_required=True, verbose=False):
        """
        :param database_name: [str; None (default)] database to be disconnected; if None, to disconnect the current one
        :param confirmation_required: [bool] (default: True)
        :param verbose: [bool] (default: False)
        """
        db_name = self.database_name if database_name is None else database_name
        if confirmed("Confirmed to drop the database \"{}\" for {}@{}?".format(db_name, self.user, self.host),
                     confirmation_required=confirmation_required):
            self.disconnect_database(db_name)
            try:
                print("Dropping the database \"{}\" ... ".format(db_name), end="") if verbose else ""
                self.engine.execute('DROP DATABASE IF EXISTS "{}"'.format(db_name))
                print("Done.") if verbose else ""
            except Exception as e:
                print("Failed. CAUSE: \"{}\"".format(e))

    # Check if a database exists
    def schema_exists(self, schema_name):
        """
        :param schema_name: [str] name of a schema
        :return: [bool] True if the schema exists; otherwise, False
        """
        result = self.engine.execute("SELECT EXISTS("
                                     "SELECT schema_name FROM information_schema.schemata "
                                     "WHERE schema_name='{}');".format(schema_name))
        return result.fetchone()[0]

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

    # Formulate printing message for multiple names
    def printing_messages_for_multi_names(self, *schema_names, desc='schema'):
        """
        :param schema_names: [str; iterable]
        :param desc: [str] (default: 'schema')
        :return: [tuple] ([tuple, str])
        """
        if schema_names:
            schemas = tuple(schema_name for schema_name in schema_names)
        else:
            schemas = tuple(
                x for x in sqlalchemy.engine.reflection.Inspector.from_engine(self.engine).get_schema_names()
                if x != 'public' and x != 'information_schema')
        print_plural = (("{} " if len(schemas) == 1 else "{}s ").format(desc))
        print_schema = ("\"{}\", " * (len(schemas) - 1) + "\"{}\"").format(*schemas)
        return schemas, print_plural + print_schema

    # Drop a schema in the database being currently connected
    def drop_schema(self, *schema_names, confirmation_required=True, verbose=False):
        """
        :param schema_names: [str] name of one schema, or names of multiple schemas
        :param confirmation_required: [bool] (default: True)
        :param verbose: [bool] (default: False)
        """
        schemas, schemas_msg = self.printing_messages_for_multi_names(*schema_names)
        if confirmed("Confirmed to drop the {} from the database \"{}\"".format(schemas_msg, self.database_name),
                     confirmation_required=confirmation_required):
            try:
                print("Dropping the {} ... ".format(schemas_msg), end="") if verbose else ""
                self.engine.execute('DROP SCHEMA IF EXISTS ' + ('%s, '*(len(schemas)-1) + '%s') % schemas + ' CASCADE;')
                print("Done.") if verbose else ""
            except Exception as e:
                print("Failed. CAUSE: \"{}\"".format(e))

    # Check if a table exists
    def table_exists(self, table_name, schema_name='public'):
        """
        :param table_name: [str] name of a table
        :param schema_name: [str] name of a schema (default: 'public')
        :return: [bool] True if the table exists; otherwise, False
        """
        res = self.engine.execute("SELECT EXISTS("
                                  "SELECT * FROM information_schema.tables "
                                  "WHERE table_schema='{}' "
                                  "AND table_name='{}');".format(schema_name, table_name))
        return res.fetchone()[0]

    # Create a new table
    def create_table(self, table_name, column_specs, schema_name='public', verbose=False):
        """
        :param table_name: [str] name of a table
        :param schema_name: [str] name of a schema (default: 'public')
        :param column_specs: [str; None (default)] 
        :param verbose: [bool] (default: False)

        e.g.
            CREATE TABLE table_name(
               column1 datatype column1_constraint,
               column2 datatype column2_constraint,
               ...
               columnN datatype columnN_constraint,
               PRIMARY KEY( one or more columns )
            );
            # column_specs = 'column_name TYPE column_constraint, ..., table_constraint table_constraint'
            column_specs = 'col_name_1 INT, col_name_2 TEXT'
        """
        table_name_ = '{schema}.\"{table}\"'.format(schema=schema_name, table=table_name)

        if not self.schema_exists(schema_name):
            self.create_schema(schema_name, verbose=False)

        try:
            print("Creating a table '{}' ... ".format(table_name_), end="") if verbose else ""
            self.engine.execute('CREATE TABLE {} ({});'.format(table_name_, column_specs))
            print("Done.") if verbose else ""
        except Exception as e:
            print("Failed. CAUSE: \"{}\"".format(e))

    # Get information about columns
    def get_column_info(self, table_name, schema_name='public', as_dict=True):
        """
        :param table_name: [str] name of a table
        :param schema_name: [str] name of a schema (default: 'public')
        :param as_dict: [bool] (default: True)
        :return: [pd.DataFrame; dict]
        """
        column_info = self.engine.execute(
            "SELECT * FROM information_schema.columns "
            "WHERE table_schema='{}' AND table_name='{}';".format(schema_name, table_name))
        keys, values = column_info.keys(), column_info.fetchall()
        info_tbl = pd.DataFrame(values, index=['column_{}'.format(x) for x in range(len(values))], columns=keys).T
        if as_dict:
            info_tbl = {k: v.to_list() for k, v in info_tbl.iterrows()}
        return info_tbl

    # Remove data from the database being currently connected
    def drop_table(self, table_name, schema_name='public', confirmation_required=True, verbose=False):
        """
        :param table_name: [str] name of a table
        :param schema_name: [str] name of a schema (default: 'public')
        :param confirmation_required: [bool] (default: True)
        :param verbose: [bool] (default: False)
        """
        if confirmed("Confirmed to drop the table {}.\"{}\" from the database \"{}\"?".format(
                schema_name, table_name, self.database_name), confirmation_required=confirmation_required):
            try:
                self.engine.execute('DROP TABLE IF EXISTS {}.\"{}\" CASCADE;'.format(schema_name, table_name))
                print("The table \"{}\" has been dropped successfully.".format(table_name)) if verbose else ""
            except Exception as e:
                print("Failed. CAUSE: \"{}\"".format(e))

    # A callable using PostgreSQL COPY clause for executing inserting data
    @staticmethod
    def psql_insert_copy(pd_table, conn, keys, data_iter):
        """
        :param pd_table: [pandas.io.sql.SQLTable]
        :param conn: [sqlalchemy.engine.Engine; sqlalchemy.engine.Connection]
        :param keys: [list of str] column names
        :param data_iter: iterable that iterates the values to be inserted

        Source: https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method
        """
        cur = conn.connection.cursor()
        s_buf = io.StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)

        columns = ', '.join('"{}"'.format(k) for k in keys)
        table_name = '{}."{}"'.format(pd_table.schema, pd_table.name)

        sql = 'COPY {} ({}) FROM STDIN WITH CSV'.format(table_name, columns)
        cur.copy_expert(sql=sql, file=s_buf)

    # Import data (as a pandas.DataFrame) into the database being currently connected
    def dump_data(self, data, table_name, schema_name='public', if_exists='replace', force_replace=False,
                  chunk_size=None, col_type=None, method='multi', verbose=False, **kwargs):
        """
        :param data: [pd.DataFrame]
        :param schema_name: [str]
        :param table_name: [str] name of the targeted table
        :param if_exists: [str] 'fail', 'replace' (default), 'append'
        :param force_replace: [bool] (default: False)
        :param chunk_size: [int; None (default)]
        :param col_type: [dict; None (default)]
        :param method: [None; str; callable] (default: 'multi' - pass multiple values in a single INSERT clause)
        :param kwargs: optional arguments used by `pd.DataFrame.to_sql()`
        :param verbose: [bool] (default: False)

        References:
        https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method
        https://www.postgresql.org/docs/current/sql-copy.html
        """
        if schema_name not in sqlalchemy.engine.reflection.Inspector.from_engine(self.engine).get_schema_names():
            self.create_schema(schema_name, verbose=verbose)
        # if not data.empty:
        #   There may be a need to change column types

        table_name_ = '{}."{}"'.format(schema_name, table_name)

        if self.table_exists(table_name, schema_name):
            if if_exists == 'replace' and verbose:
                print("The table \"{}\" already exists and will be replaced ... ".format(table_name_))
            if force_replace:
                if verbose:
                    print("The existing table \"{}\" will be dropped first ... ".format(table_name_))
                self.drop_table(table_name, schema_name, verbose=verbose)

        try:
            print("Dumping the data as a table \"{}\" into {}.\"{}\"@{} ... ".format(
                table_name, schema_name, self.database_name, self.host), end="") if verbose else ""
            if isinstance(data, pandas.io.parsers.TextFileReader):
                for chunk in data:
                    chunk.to_sql(table_name, self.engine, schema_name, if_exists, index=False, dtype=col_type,
                                 method=method, **kwargs)
                    del chunk
                    gc.collect()
            else:
                data.to_sql(table_name, self.engine, schema_name, if_exists=if_exists, index=False,
                            chunksize=chunk_size, dtype=col_type, method=method, **kwargs)
                gc.collect()
            print("Done.") if verbose else ""
        except Exception as e:
            print("Failed. CAUSE: \"{}\"".format(e))

    # Read table data
    def read_table(self, table_name, schema_name='public', condition=None, chunk_size=None, sorted_by=None, **kwargs):
        """
        :param table_name: [str] name of a table
        :param schema_name: [str] name of a schema
        :param condition: [str; None (default)]
        :param chunk_size: [int; None (default)] number of rows to include in each chunk
        :param sorted_by: [str; None (default)]
        :param kwargs: optional arguments used by `pd.read_sql()`
        :return: [pd.DataFrame]

        Example for the use of 'params' parameter for pd.read_sql():

            sql_query = 'SELECT * FROM "table_name" WHERE "timestamp_column_name" BETWEEN %(ts_start)s AND %(ts_end)s'
            params = {'ds_start': datetime.datetime.today(), 'ds_end': datetime.datetime.today()}
            data_frame = pd.read_sql(sql_query, con, params=params)

            Reference:
            https://stackoverflow.com/questions/24408557/pandas-read-sql-with-parameters
        """
        if condition:
            assert isinstance(condition, str), "'condition' must be 'str' type."
            sql_query = 'SELECT * FROM {}."{}" {};'.format(schema_name, table_name, condition)
        else:
            sql_query = 'SELECT * FROM {}."{}";'.format(schema_name, table_name)
        table_data = pd.read_sql(sql_query, con=self.engine, chunksize=chunk_size, **kwargs)
        if sorted_by and isinstance(sorted_by, str):
            table_data.sort_values(sorted_by, inplace=True)
            table_data.index = range(len(table_data))
        return table_data

    # Read data by SQL query (recommended for large table)
    def read_sql_query(self, sql_query, method='spooled_tempfile', mode='w+b', max_size_spooled=1, delimiter=',',
                       csv_dtype=None, buffering=None, encoding=None, newline=None, suffix=None, prefix=None,
                       directory=None, errors=None, initial_value='', io_newline='\n', **kwargs):
        """
        :param sql_query: [str]
        :param method: [str] {'spooled_tempfile', 'tempfile', 'stringio'} (default: 'spooled_tempfile')
        :param mode: [str] (default: 'w+b')
        :param max_size_spooled: [int] (default: 10000, in Gigabyte)
        :param delimiter: [str]
        :param csv_dtype: [dict; None (default)]
        :param buffering: [None (default)]
        :param encoding: [None (default)]
        :param newline: [None (default)]
        :param suffix: [None (default)]
        :param prefix: [None (default)]
        :param directory: [None (default)]
        :param errors: [None (default)]
        :param initial_value: [int] (default: '')
        :param io_newline: [int] (default: '\n')
        :param kwargs: optional arguments used by `pd.read_csv()`
        :return: [pd.DataFrame]

        References:
        https://towardsdatascience.com/optimizing-pandas-read-sql-for-postgres-f31cd7f707ab
        https://docs.python.org/3/library/tempfile.html
        https://docs.python.org/3/library/io.html
        """
        methods = ('stringio', 'tempfile', 'spooled_tempfile')
        assert method in methods, "\"method\" must be one of {\"%s\", \"%s\", \"%s\"}" % methods

        if method == 'stringio':  # Use io.StringIO
            csv_temp = io.StringIO(initial_value=initial_value, newline=io_newline)
        elif method == 'tempfile':  # Use tempfile.TemporaryFile
            csv_temp = tempfile.TemporaryFile(mode, buffering=buffering, encoding=encoding, newline=newline,
                                              suffix=suffix, prefix=prefix, dir=directory, errors=errors)
        else:  # Use tempfile.SpooledTemporaryFile - data would be spooled in memory until its size > max_spooled_size
            csv_temp = tempfile.SpooledTemporaryFile(max_size_spooled * 10 ** 9, mode, buffering=buffering,
                                                     encoding=encoding, newline=newline, suffix=suffix, prefix=prefix,
                                                     dir=directory, errors=errors)

        # Specify the SQL query for "COPY"
        copy_sql = "COPY ({query}) TO STDOUT WITH DELIMITER '{delimiter}' CSV HEADER;".format(
            query=sql_query, delimiter=delimiter)

        # Get a cursor
        cur = self.connection.cursor()
        cur.copy_expert(copy_sql, csv_temp)
        csv_temp.seek(0)  # Rewind the file handle using seek() in order to read the data back from it
        # Read data from temporary csv
        table_data = pandas.read_csv(csv_temp, dtype=csv_dtype, **kwargs)

        # Close the cursor
        cur.close()

        return table_data
