""" A module for manipulation of databases. """

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


class PostgreSQL:
    """
    A class representation of a simplified PostgreSQL instance.

    :param host: host address, e.g. ``'localhost'`` or ``'127.0.0.1'`` (default by installation), defaults to ``None``
    :type host: str, None
    :param port: port, e.g. ``5432`` (default by installation), defaults to ``None``
    :type port: int, None
    :param username: database username, e.g. ``'postgres'`` (default by installation), defaults to ``None``
    :type username: str, None
    :param password: database password, defaults to ``None``
    :type password: str, int, None
    :param database_name: ``'postgres'`` (default by installation), defaults to ``None``
    :type database_name: str
    :param confirm_new_db: whether to impose a confirmation to create a new database, defaults to ``False``
    :type confirm_new_db: bool
    :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
    :type verbose: bool

    **Example**::

        from pyhelpers.sql import PostgreSQL

        # Connect the default database 'postgres'
        testdb = PostgreSQL(host='localhost', port=5432, username='postgres', database_name='postgres')
    """

    def __init__(self, host=None, port=None, username=None, password=None, database_name=None,
                 confirm_new_db=False, verbose=True):
        """
        Constructor method.
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
                         confirmation_required=confirm_new_db):
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

    def database_exists(self, database_name=None):
        """
        Check if a database exists.

        :param database_name: name of a database, defaults to ``None``
        :type database_name: str, None
        :return: ``True`` if the database exists, ``False``, otherwise
        :rtype: bool
        """

        database_name_ = str(database_name) if database_name is not None else self.database_name
        result = self.engine.execute("SELECT EXISTS("
                                     "SELECT datname FROM pg_catalog.pg_database "
                                     "WHERE datname='{}');".format(database_name_))
        return result.fetchone()[0]

    def connect_database(self, database_name=None):
        """
        Establish a connection to a database.

        :param database_name: name of a database; if ``None`` (default), the database name is input manually
        :type database_name: str, None
        """

        self.database_name = str(database_name) if database_name is not None else input("Database name: ")
        self.database_info['database'] = self.database_name
        self.url = sqlalchemy.engine.url.URL(**self.database_info)
        if not sqlalchemy_utils.database_exists(self.url):
            sqlalchemy_utils.create_database(self.url)
        self.engine = sqlalchemy.create_engine(self.url, isolation_level='AUTOCOMMIT')
        self.connection = self.engine.raw_connection()

    def create_database(self, database_name, verbose=False):
        """
        An alternative to `sqlalchemy_utils.create_database`_.

        .. _`sqlalchemy_utils.create_database`:
            https://sqlalchemy-utils.readthedocs.io/en/latest/database_helpers.html#create-database

        :param database_name: name of a database
        :type database_name: str
        :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
        :type verbose: bool
        """

        if not self.database_exists(database_name):
            print("Creating a database \"{}\" ... ".format(database_name), end="") if verbose else ""
            self.disconnect_database()
            self.engine.execute('CREATE DATABASE "{}";'.format(database_name))
            print("Done.") if verbose else ""
        else:
            print("The database already exists.") if verbose else ""
        self.connect_database(database_name)

    def get_database_size(self, database_name=None):
        """
        Get the size of a database.

        If ``database_name is None`` (default), the currently connected database is checked.

        :param database_name: name of a database, defaults to ``None``
        :type database_name: str, None
        :return: size of the database
        :rtype: int
        """

        db_name = '\'{}\''.format(database_name) if database_name else 'current_database()'
        db_size = self.engine.execute('SELECT pg_size_pretty(pg_database_size({})) AS size;'.format(db_name))
        return db_size.fetchone()[0]

    def disconnect_database(self, database_name=None, verbose=False):
        """
        Kill the connection to the specified ``database_name``.

        If ``database_name is None`` (default), disconnect the current database.

        :param database_name: name of database to disconnect from, defaults to ``None``
        :type database_name: str, None
        :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
        :type verbose: bool
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

    def disconnect_all_other_databases(self):
        """
        Kill connections to all other databases.
        """

        self.connect_database(database_name='postgres')
        self.engine.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid();')

    def drop_database(self, database_name=None, confirmation_required=True, verbose=False):
        """
        Drop the specified database.

        If ``database_name is None`` (default), drop the current database.

        :param database_name: database to be disconnected, defaults to ``None``
        :type database_name: str, None
        :param confirmation_required: whether to prompt a message for confirmation to proceed, defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
        :type verbose: bool
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

    def schema_exists(self, schema_name):
        """
        Check if a database exists.

        :param schema_name: name of a schema
        :type schema_name: str
        :return: ``True`` if the schema exists, ``False`` otherwise
        :rtype: bool
        """

        result = self.engine.execute("SELECT EXISTS("
                                     "SELECT schema_name FROM information_schema.schemata "
                                     "WHERE schema_name='{}');".format(schema_name))
        return result.fetchone()[0]

    def create_schema(self, schema_name, verbose=False):
        """
        Create a new schema in the database being currently connected.

        :param schema_name: name of a schema
        :type schema_name: str
        :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
        :type verbose: bool
        """

        try:
            print("Creating a schema \"{}\" ... ".format(schema_name), end="") if verbose else ""
            self.engine.execute('CREATE SCHEMA IF NOT EXISTS "{}";'.format(schema_name))
            print("Done.") if verbose else ""
        except Exception as e:
            print("Failed. CAUSE: \"{}\"".format(e))

    def printing_messages_for_multi_names(self, *schema_names, desc='schema'):
        """
        Formulate printing message for multiple names.

        :param schema_names: name of one schema, or names of multiple schemas
        :type schema_names: str, iterable
        :param desc: for additional description, defaults to ``'schema'``
        :type desc: str
        :return: printing message
        :rtype: tuple
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

    def drop_schema(self, *schema_names, confirmation_required=True, verbose=False):
        """
        Drop a schema in the database being currently connected.

        :param schema_names: name of one schema, or names of multiple schemas
        :type schema_names: str, iterable
        :param confirmation_required: whether to prompt a message for confirmation to proceed, defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
        :type verbose: bool
        """

        schemas, schemas_msg = self.printing_messages_for_multi_names(*schema_names)
        if confirmed("Confirmed to drop the {} from the database \"{}\"".format(schemas_msg, self.database_name),
                     confirmation_required=confirmation_required):
            try:
                print("Dropping the {} ... ".format(schemas_msg), end="") if verbose else ""
                self.engine.execute(
                    'DROP SCHEMA IF EXISTS ' + ('%s, ' * (len(schemas) - 1) + '%s') % schemas + ' CASCADE;')
                print("Done.") if verbose else ""
            except Exception as e:
                print("Failed. CAUSE: \"{}\"".format(e))

    def table_exists(self, table_name, schema_name='public'):
        """
        Check if a table exists.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :return: ``True`` if the table exists, ``False`` otherwise
        :rtype: bool

        **Examples**::

            from pyhelpers.sql import PostgreSQL

            testdb = PostgreSQL(database_name='postgres')

            table_name = 'England'
            schema_name = 'points'

            testdb.table_exists(table_name, schema_name)  # False (if 'points.England' does not exist)
        """

        res = self.engine.execute("SELECT EXISTS("
                                  "SELECT * FROM information_schema.tables "
                                  "WHERE table_schema='{}' "
                                  "AND table_name='{}');".format(schema_name, table_name))
        return res.fetchone()[0]

    def create_table(self, table_name, column_specs, schema_name='public', verbose=False):
        """
        Create a new table.

        :param table_name: name of a table
        :type table_name: str
        :param column_specs: specifications for each column of the table
        :type column_specs: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
        :type verbose: bool

        **Example**::

            from pyhelpers.sql import PostgreSQL

            postgres_db = PostgreSQL(database_name='postgres')
            table_name = 'test_tbl'
            verbose = True

            column_specs = 'col_name_1 INT, col_name_2 TEXT'
            postgres_db.create_table(table_name, column_specs, verbose=verbose)
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

    def get_column_info(self, table_name, schema_name='public', as_dict=True):
        """
        Get information about columns.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param as_dict: whether to return the column information as a dictionary, defaults to ``True``
        :type as_dict: bool
        :return: information about each column of the given table
        :rtype: pandas.DataFrame, dict
        """

        column_info = self.engine.execute(
            "SELECT * FROM information_schema.columns "
            "WHERE table_schema='{}' AND table_name='{}';".format(schema_name, table_name))
        keys, values = column_info.keys(), column_info.fetchall()
        info_tbl = pd.DataFrame(values, index=['column_{}'.format(x) for x in range(len(values))], columns=keys).T
        if as_dict:
            info_tbl = {k: v.to_list() for k, v in info_tbl.iterrows()}
        return info_tbl

    def drop_table(self, table_name, schema_name='public', confirmation_required=True, verbose=False):
        """
        Remove data from the database being currently connected.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param confirmation_required: whether to prompt a message for confirmation to proceed, defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
        :type verbose: bool
        """

        if confirmed("Confirmed to drop the table {}.\"{}\" from the database \"{}\"?".format(
                schema_name, table_name, self.database_name), confirmation_required=confirmation_required):
            try:
                self.engine.execute('DROP TABLE IF EXISTS {}.\"{}\" CASCADE;'.format(schema_name, table_name))
                print("The table \"{}\" has been dropped successfully.".format(table_name)) if verbose else ""
            except Exception as e:
                print("Failed. CAUSE: \"{}\"".format(e))

    @staticmethod
    def psql_insert_copy(pd_table, conn, keys, data_iter):
        """
        A callable using PostgreSQL COPY clause for executing inserting data.

        :param pd_table: pandas.io.sql.SQLTable
        :param conn: sqlalchemy.engine.Connection or sqlalchemy.engine.Engine
        :param keys: (list of str) column names
        :param data_iter: iterable that iterates the values to be inserted

        .. note::

            This function is copied and slightly modified from the source code available at
            [`PIC-1 <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method>`_].
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

    def dump_data(self, data, table_name, schema_name='public', if_exists='replace', force_replace=False,
                  chunk_size=None, col_type=None, method='multi', verbose=False, **kwargs):
        """
        Import data (as a pandas.DataFrame) into the database being currently connected.

        See also
        [`DD-1 <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method/>`_] and
        [`DD-2 <https://www.postgresql.org/docs/current/sql-copy.html/>`_].

        :param data: data frame to be dumped into a database
        :type data: pandas.DataFrame
        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param if_exists: if the table already exists, to ``'replace'`` (default), ``'append'`` or ``'fail'``
        :type if_exists: str
        :param force_replace: whether to force to replace existing table, defaults to ``False``
        :type force_replace: bool
        :param chunk_size: the number of rows in each batch to be written at a time, defaults to ``None``
        :type chunk_size: int, None
        :param col_type: data types for columns, defaults to ``None``
        :type col_type: dict, None
        :param method: method for SQL insertion clause, defaults to ``'multi'``

            * `None`: uses standard SQL ``INSERT`` clause (one per row);
            * `'multi'`: pass multiple values in a single ``INSERT`` clause;
            * callable (e.g. ``PostgreSQL.psql_insert_copy``) with signature ``(pd_table, conn, keys, data_iter)``.

        :type method: None, str, callable
        :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
        :type verbose: bool
        :param kwargs: optional parameters of `pandas.DataFrame.to_sql`_

        .. _`pandas.DataFrame.to_sql`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html

        **Example**::

            import pandas as pd
            from pyhelpers.sql import PostgreSQL

            testdb = PostgreSQL(database_name='postgres')

            # Create a pandas.DataFrame
            xy_array = [(530034, 180381), (406689, 286822), (383819, 398052), (582044, 152953)]
            dat = pd.DataFrame(xy_array, columns=['Easting', 'Northing'])

            table_name = 'England'
            schema_name = 'points'
            if_exists = 'replace'

            testdb.dump_data(dat, table_name, schema_name, if_exists, chunk_size=None,
                             force_replace=False, col_type=None, verbose=True)
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

    def read_table(self, table_name, schema_name='public', condition=None, chunk_size=None, sorted_by=None, **kwargs):
        """
        Read table data.

        See also [`RT-1 <https://stackoverflow.com/questions/24408557/pandas-read-sql-with-parameters>`_].

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``'public'``
        :type schema_name: str
        :param condition: defaults to ``None``
        :type condition: str, None
        :param chunk_size: number of rows to include in each chunk, defaults to ``None``
        :type chunk_size: int, None
        :param sorted_by: name(s) of a column (or columns) by which the retrieved data is sorted, defaults to ``None``
        :type sorted_by: str, None
        :param kwargs: optional parameters of `pandas.read_sql`_

        :return: data frame from the specified table
        :rtype: pandas.DataFrame

        .. _`pandas.read_sql`: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_sql.html

        **Examples**::

            from pyhelpers.sql import PostgreSQL

            testdb = PostgreSQL(database_name='postgres')

            table_name = 'England'
            schema_name = 'points'
            dat_retrieval = testdb.read_table(table_name, schema_name)

            # Aside: a brief example of using the `params` of `pandas.read_sql`

            import datetime
            import pandas as pd

            sql_query = 'SELECT * FROM "table_name" '\
                        'WHERE "timestamp_column_name" '\
                        'BETWEEN %(ts_start)s AND %(ts_end)s'
            params = {'ds_start': datetime.datetime.today(), 'ds_end': datetime.datetime.today()}

            data_frame = pd.read_sql(sql_query, testdb.engine, params=params)
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

    def read_sql_query(self, sql_query, method='spooled_tempfile', tempfile_mode='w+b', max_size_spooled=1,
                       delimiter=',', dtype=None, tempfile_kwargs=None, stringio_kwargs=None, **kwargs):
        """
        Read data by SQL query (recommended for large table).

        See also
        [`RSQ-1 <https://towardsdatascience.com/optimizing-pandas-read-sql-for-postgres-f31cd7f707ab>`_],
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
        :param max_size_spooled: ``max_size`` of `tempfile.SpooledTemporaryFile`_, defaults to ``1`` (in gigabyte)
        :type max_size_spooled: int, float
        :param delimiter: delimiter used in data, defaults to ``','``
        :type delimiter: str
        :param dtype: data type for specified data columns, `dtype` used by `pandas.read_csv`_, defaults to ``None``
        :type dtype: dict, None
        :param tempfile_kwargs: optional parameters of `tempfile.TemporaryFile`_ or `tempfile.SpooledTemporaryFile`_
        :param stringio_kwargs: optional parameters of `io.StringIO`_, e.g. ``initial_value`` (default:``''``)
        :param kwargs: optional parameters of `pandas.read_csv`_
        :return: data frame as queried by the statement ``sql_query``
        :rtype: pandas.DataFrame

        .. _`pandas.read_csv`: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html
        .. _`open`: https://docs.python.org/3/library/functions.html#open
        .. _`tempfile.TemporaryFile`: https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryFile
        .. _`tempfile.SpooledTemporaryFile`:
            https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile
        .. _`io.StringIO`: https://docs.python.org/3/library/io.html#io.StringIO
        .. _`tempfile.mkstemp`: https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp
        """

        methods = ('stringio', 'tempfile', 'spooled_tempfile')
        assert method in methods, "The argument `method` must be one of {'%s', '%s', '%s'}" % methods

        if tempfile_kwargs is None:
            tempfile_kwargs = {'buffering': -1, 'encoding': None, 'newline': None, 'suffix': None, 'prefix': None,
                               'dir': None, 'errors': None}

        if method == 'spooled_tempfile':
            # Use tempfile.SpooledTemporaryFile - data would be spooled in memory until its size > max_spooled_size
            csv_temp = tempfile.SpooledTemporaryFile(max_size_spooled * 10 ** 9, tempfile_mode, **tempfile_kwargs)
        elif method == 'tempfile':
            # Use tempfile.TemporaryFile
            csv_temp = tempfile.TemporaryFile(tempfile_mode, **tempfile_kwargs)
        else:  # method == 'stringio', i.e. use io.StringIO
            if stringio_kwargs is None:
                stringio_kwargs = {'initial_value': '', 'newline': '\n'}
            csv_temp = io.StringIO(**stringio_kwargs)

        # Specify the SQL query for "COPY"
        copy_sql = "COPY ({query}) TO STDOUT WITH DELIMITER '{delimiter}' CSV HEADER;".format(
            query=sql_query, delimiter=delimiter)

        # Get a cursor
        cur = self.connection.cursor()
        cur.copy_expert(copy_sql, csv_temp)
        csv_temp.seek(0)  # Rewind the file handle using seek() in order to read the data back from it
        # Read data from temporary csv
        table_data = pandas.read_csv(csv_temp, dtype=dtype, **kwargs)

        # Close the cursor
        cur.close()

        return table_data
