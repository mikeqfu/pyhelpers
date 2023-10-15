"""
Communication with database servers.
"""

import copy
import gc
import inspect
import itertools
import typing

import pandas as pd
import sqlalchemy

from .._cache import _check_dependency, _confirmed, _print_failure_msg


class _Base:
    """
    A base class for communication with database servers.
    """

    #: str: Default schema name.
    DEFAULT_SCHEMA = ''
    #: set: Names of built-in schemas.
    BUILTIN_SCHEMAS = set()

    def __init__(self):
        self.database_name = ''
        self.address = ''
        self.engine = None
        self.builtin_schema_names = {}

    def _execute(self, query):
        """
        Check whether an item exists.

        :return: whether an item exists
        :rtype: any

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

        if isinstance(query, str):
            query_ = sqlalchemy.text(query)
        else:
            assert isinstance(query, sqlalchemy.TextClause)
            query_ = query

        with self.engine.connect() as connection:
            result_ = connection.execute(query_)

        result = result_.fetchone()

        return result

    def _database_name(self, database_name=None, fmt='"{}"'):
        """
        Format a database name.

        :param database_name: database name as an input, defaults to ``None``
        :type database_name: str | None
        :param fmt: string format of database name, defaults to ``'"{}"'``
        :type fmt: str
        :return: a database name
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL, MSSQL

            >>> postgres = PostgreSQL()
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/postgres ... Successfully.
            >>> postgres._database_name()
            '"postgres"'
            >>> postgres._database_name(database_name='testdb')
            '"testdb"'

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql._database_name(fmt='[{}]')
            '[master]'
            >>> mssql._database_name(database_name='testdb', fmt='[{}]')
            '[testdb]'
        """

        db_name = copy.copy(self.database_name) if database_name is None else str(database_name)
        if '%s' in fmt:
            database_name_ = fmt % db_name
        else:
            assert '{}' in fmt
            database_name_ = fmt.format(db_name)  # e.g. f'"{db_name}"'

        return database_name_

    def _create_db(self, confirm_db_creation, verbose, fmt='"{}"'):
        """
        Create a database (if it does not exist) when creating an instance.

        :param confirm_db_creation: whether to prompt a confirmation before creating a new database
            (if the specified database does not exist)
        :type confirm_db_creation: bool
        :param verbose: whether to print relevant information in console
        :type verbose: bool | int
        :param fmt: string format of database name, defaults to ``'"{}"'``
        :type fmt: str
        """

        db_name = self._database_name(database_name=self.database_name, fmt=fmt)

        cfm_msg = f"The database {db_name} does not exist. Proceed by creating it\n?"
        if _confirmed(prompt=cfm_msg, confirmation_required=confirm_db_creation):

            if verbose:
                print(f"Creating a database: {db_name}", end=" ... ")

            try:
                with self.engine.connect() as connection:
                    connection.execute(sqlalchemy.text(f'CREATE DATABASE {db_name};'))
                    self.engine.url = self.engine.url.set(database=self.database_name)

                if verbose:
                    print("Done.")

            except Exception as e:
                _print_failure_msg(e=e)

    def database_exists(self, database_name):
        pass

    def connect_database(self, database_name, verbose=False):
        pass

    def disconnect_database(self, database_name=None, verbose=False):
        pass

    def _create_database(self, database_name, verbose, fmt):
        """
        Create a database.

        :param database_name: name of a database
        :param verbose: whether to print relevant information in console
        """

        if not self.database_exists(database_name=database_name):
            db_name = self._database_name(database_name=database_name, fmt=fmt)

            if verbose:
                print(f"Creating a database: {db_name} ... ", end="")

            self.disconnect_database()

            with self.engine.connect() as connection:
                query = sqlalchemy.text(f'CREATE DATABASE {db_name};')
                connection.execute(query)

            if verbose:
                print("Done.")

        else:
            if verbose:
                print("The database already exists.")

        self.connect_database(database_name=database_name, verbose=False)

    def _drop_database(self, database_name, fmt, confirmation_required, verbose):
        """
        Drop/delete a database.

        :param database_name: name of a database
        :param confirmation_required: whether to prompt a message for confirmation to proceed
        :param verbose: whether to print relevant information in console
        """

        db_name = self._database_name(database_name, fmt=fmt)

        if not self.database_exists(database_name=database_name):
            if verbose:
                print(f"The database {db_name} does not exist.")

        else:
            # address_ = self.address.replace(f"/{db_name}", "")
            address_ = self.address.split('/')[0]
            cfm_msg = f"To drop the database {db_name} from {address_}\n?"
            if _confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):
                self.disconnect_database(database_name=database_name)

                if verbose:
                    if confirmation_required:
                        log_msg = f"Dropping {db_name}"
                    else:
                        log_msg = f"Dropping the database {db_name} from {address_}"
                    print(log_msg, end=" ... ")

                try:
                    with self.engine.connect() as connection:
                        query = sqlalchemy.text(f'DROP DATABASE {db_name};')
                        connection.execute(query)

                    if verbose:
                        print("Done.")

                except Exception as e:
                    _print_failure_msg(e=e)

    def _schema_name(self, schema_name=None):
        """
        Get a schema name.

        :param schema_name: schema name as an input, defaults to ``None``
        :type schema_name: str | list | tuple | None
        :return: a schema name
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL, MSSQL

            >>> postgres = PostgreSQL()
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/postgres ... Successfully.
            >>> postgres._schema_name()
            'public'
            >>> postgres._schema_name(schema_name='test_schema')
            'test_schema'

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

    def _table_name(self, table_name, schema_name=None, fmt='"{}"."{}"'):
        """
        Get a formatted table name.

        :param table_name: table name as an input
        :type table_name: str
        :param schema_name: schema name as an input
        :type schema_name: str | None
        :param fmt: string format of full table name, defaults to ``'"{}"."{}"'``
        :type fmt: str
        :return: a formatted table name, which is used in a SQL query statement
        :rtype: str

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL, MSSQL

            >>> postgres = PostgreSQL()
            Password (postgres@localhost:5432): ***
            Connecting postgres:***@localhost:5432/postgres ... Successfully.
            >>> postgres._table_name(table_name='test_table')
            '"public"."test_table"'
            >>> postgres._table_name(table_name='test_table', schema_name='test_schema')
            '"test_schema"."test_table"'

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql._table_name(table_name='test_table')
            '[dbo].[test_table]'
            >>> mssql._table_name(table_name='test_table', schema_name='test_schema')
            '[test_schema].[test_table]'
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        if '%s' in fmt:
            table_name_ = fmt % (schema_name_, table_name)
        else:
            assert '{}' in fmt  # e.g. f'"{schema_name_}"."{table_name}"'
            table_name_ = fmt.format(schema_name_, table_name)

        return table_name_

    def _msg_for_multi_items(self, item_names, desc, fmt='"{}"'):
        """
        Formulate a printing message for multiple items.

        :param item_names: name of one table/schema, or names of several tables/schemas
        :type item_names: str | typing.Iterable[str] | None
        :param desc: for additional description
        :type desc: str
        :param fmt: printing format of each item, defaults to ``'"{}"'``
        :type fmt: str
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
            item_names_ = [x for x in sqlalchemy.inspect(self.engine).get_schema_names()]
        else:
            item_names_ = [item_names] if isinstance(item_names, str) else item_names

        if len(item_names_) == 1:
            print_plural = "{}".format(desc)
            try:
                print_items = fmt.format(item_names_[0])
            except TypeError:
                print_items = fmt.format(list(item_names_)[0])
        else:
            print_plural = "{}s".format(desc)
            print_items = (f'\n\t{fmt}' * len(item_names_)).format(*item_names_)

        return item_names_, print_plural, print_items

    def create_schema(self, schema_name, verbose=False):
        pass

    def schema_exists(self, schema_name):
        pass

    def _drop_schema(self, schema_names, fmt, query_, confirmation_required=True, verbose=False):
        schema_names_, print_plural, print_schema = self._msg_for_multi_items(
            item_names=schema_names, desc='schema', fmt=fmt)

        if len(schema_names_) == 1:
            cfm_msg = f"To drop the {print_plural} {print_schema} from {self.address}\n?"
        else:
            cfm_msg = f"To drop the following {print_plural} from {self.address}: {print_schema}\n?"

        if _confirmed(cfm_msg, confirmation_required=confirmation_required):
            if verbose:
                if len(schema_names_) == 1:
                    if confirmation_required:
                        log_msg = f"Dropping {print_schema}"
                    else:
                        log_msg = f"Dropping the {print_plural}: {print_schema}"
                    print(log_msg, end=" ... ")
                else:  # len(schema_names_) > 1
                    if confirmation_required:
                        print("Dropping ... ")
                    else:
                        print(f"Dropping the following {print_plural} from {self.address}:")

            for schema_name in schema_names_:
                if not self.schema_exists(schema_name):  # `schema` does not exist
                    if verbose:
                        if len(schema_names_) == 1:
                            print(f"The schema \"{schema_names_[0]}\" does not exist.")
                        else:
                            print(f"\t\"{schema_name}\" (does not exist.)")

                else:
                    if len(schema_names_) > 1 and verbose:
                        print(f"\t\"{schema_name}\"", end=" ... ")

                    if schema_name in self.BUILTIN_SCHEMAS:
                        if verbose:
                            print("(Built-in schemas which cannot be deleted.)")

                    else:
                        try:  # e.g. query_ = 'DROP SCHEMA "{}" CASCADE;'
                            with self.engine.connect() as connection:
                                query = sqlalchemy.text(
                                    query_.format(*(query_.count('{}') * [schema_name])))
                                connection.execute(query)

                            if verbose:
                                schema_exists = self.schema_exists(schema_name=schema_name)
                                print("Done.") if not schema_exists else print("Failed.")

                        except Exception as e:
                            _print_failure_msg(e=e, msg="Failed.")

    def get_table_names(self, schema_name, verbose=False):
        """
        Get names of all tables stored in a schema.

        :param schema_name: name of a schema, defaults to ``None``
        :type schema_name: str | list | None
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool | int
        :return: table names of the given schema(s) ``schema_name``
        :rtype: dict
        """

        schema_name_ = self._schema_name(schema_name=schema_name)
        if isinstance(schema_name_, str):
            schema_name_ = [schema_name_]

        inspector = sqlalchemy.inspection.inspect(self.engine)

        table_names = dict()
        for schema in schema_name_:
            if not self.schema_exists(schema_name=schema):
                if verbose:
                    schema_ = f"[{schema}]" if self.engine.dialect.name == 'mssql' else f'"{schema}"'
                    print(f'The schema {schema_} does not exist.')
            table_names[schema] = inspector.get_table_names(schema=schema)

        return table_names

    def table_exists(self, table_name, schema_name):
        pass

    def _drop_table(self, table_name, query_fmt, schema_name=None, confirmation_required=True,
                    verbose=False):
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
                        # e.g. 'DROP TABLE {} CASCADE;'.format(table_name_)
                        query = sqlalchemy.text(query_fmt.format(table_name_))
                        connection.execute(query)

                    if verbose:
                        print("Done.")

                except Exception as e:
                    _print_failure_msg(e)

    def drop_table(self, table_name, schema_name, confirmation_required=True, verbose=False):
        pass

    def _import_data(self, data, table_name, schema_name=None, if_exists='fail',
                     force_replace=False, chunk_size=None, col_type=None, method='multi',
                     index=False, confirmation_required=True, verbose=False, **kwargs):
        """
        Import tabular data into a table.

        :param data: tabular data to be dumped into a database
        :type data: pandas.DataFrame | pandas.io.parsers.TextFileReader | list | tuple
        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :type schema_name: str | None
        :param if_exists: if the table already exists, to ``'replace'``, ``'append'``
            or, by default, ``'fail'`` and do nothing but raise a ValueError.
        :type if_exists: str
        :param force_replace: whether to force replacing existing table, defaults to ``False``
        :type force_replace: bool
        :param chunk_size: the number of rows in each batch to be written at a time,
            defaults to ``None``
        :type chunk_size: int | None
        :param col_type: data types for columns, defaults to ``None``
        :type col_type: dict | None
        :param method: method for SQL insertion clause, defaults to ``'multi'``

            - ``None``: uses standard SQL ``INSERT`` clause (one per row);
            - ``'multi'``: pass multiple values in a single ``INSERT`` clause;
            - callable (e.g. ``PostgreSQL.psql_insert_copy``)
              with signature ``(pd_table, conn, keys, data_iter)``.

        :type method: str | None | typing.Callable
        :param index: whether to dump the index as a column
        :type index: bool
        :param confirmation_required: whether to prompt a message for confirmation to proceed,
            defaults to ``True``
        :type confirmation_required: bool
        :param verbose: whether to print relevant information in console, defaults to ``False``
        :type verbose: bool | int
        :param kwargs: [optional] parameters of `pandas.DataFrame.to_sql`_

        .. _`pandas.DataFrame.to_sql`:
            https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html
        """

        schema_name_ = self._schema_name(schema_name=schema_name)
        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name_)

        if _confirmed(f"To import data into the table {table_name_} at {self.address}\n?",
                      confirmation_required=confirmation_required):

            inspector = sqlalchemy.inspect(self.engine)
            if schema_name_ not in inspector.get_schema_names():
                self.create_schema(schema_name=schema_name_, verbose=verbose)

            if self.table_exists(table_name=table_name, schema_name=schema_name_):
                if verbose:
                    if_exists_msg = f"The table {table_name_} already exists"
                    if if_exists == 'fail':
                        if not force_replace:
                            add_msg = ("Use `if_exists='replace'` or "
                                       "`force_replace=True` to update it.")
                            print(if_exists_msg + f". ({add_msg})")
                            return None
                    elif if_exists == 'replace':
                        print(if_exists_msg + " and is being replaced.")

                    if force_replace:
                        verbose_ = True if verbose == 2 else False
                        if verbose_:
                            print("The existing table is forced to be dropped.")
                        self.drop_table(
                            table_name=table_name, schema_name=schema_name_,
                            confirmation_required=confirmation_required, verbose=verbose_)

            if verbose:
                if confirmation_required:
                    log_msg = f"Importing the data into {table_name_}"
                else:
                    log_msg = f"Importing data into the table {table_name_} at {self.address}"
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

            if verbose:
                print("Done.")

    def get_column_info(self, table_name, schema_name=None, as_dict=True):
        """
        Get information about columns of a table.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema; when ``schema_name=None`` (default), it defaults to
            :py:attr:`~pyhelpers.dbms.PostgreSQL.DEFAULT_SCHEMA` (i.e. ``'public'``)
        :type schema_name: str | None
        :param as_dict: whether to return the column information as a dictionary, defaults to ``True``
        :type as_dict: bool
        :return: information about all columns of the given table
        :rtype: pandas.DataFrame | dict

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL, MSSQL

            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.

            >>> # Create a new table named 'test_table'
            >>> tbl_name = 'test_table'
            >>> col_spec = 'col_name_1 INT, col_name_2 TEXT'
            >>> testdb.create_table(table_name=tbl_name, column_specs=col_spec, verbose=True)
            Creating a table "public"."test_table" ... Done.

            >>> # Get information about all columns of the table "public"."test_table"
            >>> test_tbl_col_info = testdb.get_column_info(table_name=tbl_name, as_dict=False)
            >>> test_tbl_col_info.head()
                                column_0    column_1
            table_catalog         testdb      testdb
            table_schema          public      public
            table_name        test_table  test_table
            column_name       col_name_1  col_name_2
            ordinal_position           1           2

            >>> mssql = MSSQL()
            Connecting <server_name>@localhost:1433/master ... Successfully.
            >>> mssql.get_column_info(table_name='')
        """

        schema_name_ = self._schema_name(schema_name=schema_name)

        with self.engine.connect() as connection:
            query = sqlalchemy.text(
                f"SELECT * FROM information_schema.columns "
                f"WHERE table_schema='{schema_name_}' AND table_name='{table_name}';")
            res = connection.execute(query)

        keys, values = list(res.keys()), res.fetchall()
        idx = ['column_{}'.format(x) for x in range(len(values))]

        column_info = pd.DataFrame(values, index=idx, columns=keys).T

        if as_dict:
            column_info = {k: v.to_list() for k, v in column_info.iterrows()}

        return column_info

    def validate_column_names(self, table_name, schema_name=None, column_names=None):
        """
        Validate column names for query statement.

        :param table_name: name of a table
        :type table_name: str
        :param schema_name: name of a schema, defaults to ``None``
        :type schema_name: str
        :param column_names: column name(s) for a dataframe
        :type column_names: str | list | tuple | None
        :return: column names for PostgreSQL query statement
        :rtype: str
        """

        tbl_col_info = self.get_column_info(
            table_name=table_name, schema_name=schema_name, as_dict=False)

        tbl_col_info.index = [x.lower() for x in tbl_col_info.index]
        tbl_col_names = tbl_col_info.loc['column_name'].to_list()

        if isinstance(column_names, str):
            assert column_names in tbl_col_names, \
                f'"{column_names}" is not in the existing column names.'
            column_names_ = f'"{column_names}"'

        elif isinstance(column_names, typing.Iterable):
            if not all(col in tbl_col_names for col in column_names):
                x_ = list(set(column_names) - set(tbl_col_names))
                if len(x_) == 1:
                    x, be = f'"{x_[0]}"', 'is'
                else:
                    x, be = '["' + '", "'.join(x_) + '"]', 'are'
                raise AssertionError(f'{x} {be} not in the existing column names.')
            column_names_ = '"{}"'.format('", "'.join([str(col) for col in column_names]))

        else:
            column_names_ = '"{}"'.format('", "'.join([str(col) for col in tbl_col_names]))  # '*'

        return column_names_

    def read_sql_query(self, sql_query, method, max_size_spooled, delimiter, tempfile_kwargs,
                       stringio_kwargs, **kwargs):
        pass

    def _read_sql_query_args(self):
        """
        Get names of arguments that are exclusive to the method
        :meth:`~pyhelpers.dbms.postgresql.PostgreSQL.read_sql_query`.

        :return: names of arguments exclusive to :py:meth:`~pyhelpers.dbms.PostgreSQL.read_sql_query`
        :rtype: dict
        """

        rsq_args = map(lambda x: inspect.getfullargspec(x).args, (self.read_sql_query, pd.read_csv))
        rsq_args_spec = set(itertools.chain(*rsq_args))

        read_sql_args = set(inspect.getfullargspec(func=pd.read_sql).args)

        return rsq_args_spec - read_sql_args
