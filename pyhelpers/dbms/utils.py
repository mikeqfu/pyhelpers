"""
Database tools/utilities.
"""

import copy
import gc
import inspect
import re
import sys

import pandas as pd
import sqlalchemy.dialects

from .._cache import _check_dependency, _confirmed, _print_failure_msg


def make_database_address(host, port, username, database_name=""):
    """
    Generate a string representing a database address.

    :param host: Host name or IP address of the database server.
    :type host: str
    :param port: Port number on which the database server is listening.
    :type port: int | str
    :param username: Username used to connect to the database server.
    :type username: str
    :param database_name: Name of the PostgreSQL database; defaults to an empty string.
    :type database_name: str | None
    :return: Address of the database in the format '<username>@<host>:<port>/<database_name>'.
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dbms.utils import make_database_address
        >>> make_database_address('localhost', 5432, 'postgres', 'postgres')
        'postgres:***@localhost:5432/postgres'
        >>> make_database_address('localhost', 5432, 'admin', 'my_database')
        'admin:***@localhost:5432/my_database'
        >>> make_database_address('127.0.0.1', '5432', 'user', '')
        'user:***@127.0.0.1:5432'
    """

    database_address = f"{username}:***@{host}:{port}"

    if database_name:
        database_address += f"/{database_name}"

    return database_address


def get_default_database_address(db_cls):
    """
    Retrieve the database address of a database class given its default parameters.

    :param db_cls: Class representing a database.
    :type db_cls: object
    :return: Address of the database given its default parameters in the format
        '<username>@<host>:<port>/<database_name>'.
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dbms.utils import get_default_database_address
        >>> from pyhelpers.dbms import PostgreSQL
        >>> db_addr = get_default_database_address(db_cls=PostgreSQL)
        >>> db_addr
        'None:***@None:None'
    """

    args_spec = inspect.getfullargspec(func=db_cls)

    args_dict = dict(zip([x for x in args_spec.args if x != 'self'], args_spec.defaults))

    database_address = make_database_address(
        args_dict['host'], args_dict['port'], args_dict['username'], args_dict['database_name'])

    return database_address


def _add_sql_query_args(arg, val, tbl_name):
    if isinstance(val, str):
        x = f' {tbl_name}"{arg}"=\'{val}\''
    elif isinstance(val, (tuple, list)):
        x = f' {tbl_name}"{arg}" IN {tuple(x for x in val if x is not None)}'
    elif isinstance(val, pd.DatetimeIndex):
        x = f' {tbl_name}"{arg}" IN {tuple(str(x) for x in val)}'
    else:
        x = ''
    return x


def add_sql_query_condition(sql_query, add_table_name=None, **kwargs):
    """
    Add a condition to a given SQL query statement.

    :param sql_query: SQL query statement to which the condition will be added.
    :type sql_query: str
    :param add_table_name: [Optional] table name to add to each column name in the condition;
        defaults to ``None``.
    :type add_table_name: str | None
    :return: Updated SQL query statement with the specified conditions.
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dbms.utils import add_sql_query_condition
        >>> query = 'SELECT * FROM a_table'
        >>> query
        'SELECT * FROM a_table'
        >>> add_sql_query_condition(query)
        'SELECT * FROM a_table'
        >>> add_sql_query_condition(query, COL_NAME_1='A')
        'SELECT * FROM a_table WHERE "COL_NAME_1"=\'A\''
        >>> add_sql_query_condition(query, COL_NAME_1='A', COL_NAME_2=['B', 'C'])
        'SELECT * FROM a_table WHERE "COL_NAME_1"=\'A\' AND "COL_NAME_2" IN (\'B\', \'C\')'
        >>> add_sql_query_condition(query, COL_NAME_1='A', add_table_name='t1')
        'SELECT * FROM a_table WHERE t1."COL_NAME_1"=\'A\''
    """

    locals().update(kwargs)

    for k, v in locals().items():
        if k not in {'sql_query', 'add_table_name', 'tbl_name'}:
            argument = _add_sql_query_args(
                k, v, '' if add_table_name is None else f'{add_table_name}.')

            if argument:
                sql_query += \
                    f' {"AND" if re.search(r"where", sql_query, re.IGNORECASE) else "WHERE"}' \
                    f'{argument}'

    return sql_query


def _mssql_postgres_import_data(mssql, postgres, source_data, postgres_schema_name,
                                mssql_table_name, memory_threshold, chunk_size, col_type):
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


def _get_col_type(mssql, mssql_table_name, source_data):

    source_data_ = source_data.copy()

    col_type = {}

    check_dtypes = ['hierarchyid', 'varbinary']
    check_dtypes_rslt = mssql.has_dtypes(mssql_table_name, dtypes=check_dtypes)

    for dtype, if_exists, col_names in check_dtypes_rslt:
        if if_exists:
            if dtype == 'hierarchyid':
                source_data_.loc[:, col_names] = source_data_[col_names].applymap(
                    lambda x: str(x).replace('\\', '\\\\'))

            bytea_list = [sqlalchemy.dialects.postgresql.BYTEA] * len(col_names)
            col_type.update(dict(zip(col_names, bytea_list)))

    return source_data_, col_type


def _get_chunk_size(mssql, mssql_table_name, chunk_size=None):
    row_count = mssql.get_row_count(mssql_table_name)

    if row_count >= 1000000:

        if chunk_size is None:
            chunk_size = 1000000

    return chunk_size


def mssql_to_postgresql(mssql, postgres, mssql_schema=None, postgres_schema=None, chunk_size=None,
                        excluded_tables=None, file_tables=False, memory_threshold=2., update=False,
                        confirmation_required=True, verbose=True):
    """
    Copy tables of a database from a Microsoft SQL server to a PostgreSQL server.

    :param mssql: Name of the Microsoft SQL (source) database.
    :type mssql: pyhelpers.dbms.MSSQL
    :param postgres: Name of the PostgreSQL (destination) database.
    :type postgres: pyhelpers.dbms.PostgreSQL
    :param mssql_schema: Name of the schema to be migrated from the SQL Server.
    :type mssql_schema: str | None
    :param postgres_schema: Name of the schema to store the migrated data in the PostgreSQL server.
    :type postgres_schema: str | None
    :param chunk_size: Number of rows in each batch to be read/written at a time;
        defaults to ``None``.
    :type chunk_size: int | None
    :param excluded_tables: Names of tables excluded from data migration.
    :type excluded_tables: list | None
    :param file_tables: Whether to include FileTables; defaults to ``False``.
    :type file_tables: bool
    :param memory_threshold: Threshold (in GiB) beyond which data is migrated by partitions;
        defaults to ``2.``.
    :type memory_threshold: float | int
    :param update: Whether to redo the transfer between database servers; defaults to ``False``.
    :type update: bool
    :param confirmation_required: Whether to request confirmation before proceeding;
        defaults to ``True``.
    :type confirmation_required: bool
    :param verbose: Whether to print relevant information; defaults to ``True``.
    :type verbose: bool | int

    **Examples**::

        >>> from pyhelpers.dbms.utils import mssql_to_postgresql
        >>> from pyhelpers.dbms import PostgreSQL, MSSQL
        >>> from pyhelpers._cache import example_dataframe
        >>> # Connect/create a PostgreSQL database, which is named [testdb]
        >>> mssql_testdb = MSSQL(database_name='testdb', verbose=True)
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
        >>> postgres_testdb = PostgreSQL(database_name='testdb', verbose=True)
        Password (postgres@localhost:5432): ***
        Creating a database: "testdb" ... Done.
        Connecting postgres:***@localhost:5432/testdb ... Successfully.
        >>> # For now, the newly-created database doesn't contain any tables
        >>> postgres_testdb.get_table_names()
        {'public': []}
        >>> # Copy the example data from the SQL Server to the PostgreSQL "testdb" (under "public")
        >>> mssql_to_postgresql(mssql=mssql_testdb, postgres=postgres_testdb)
        To copy tables from [testdb] (MSSQL) to "testdb" (PostgreSQL)
        ? [No]|Yes: yes
        Processing tables ...
            (1/1) Copying [dbo].[example_df] to "public"."example_df" ... Done.
        Completed.
        >>> postgres_testdb.get_table_names()
        {'public': ['example_df']}

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

    if _confirmed(f'To copy tables {task_msg}\n?', confirmation_required=confirmation_required):

        # MSSQL
        mssql_schema_name = mssql._schema_name(schema_name=mssql_schema)
        mssql_table_names = mssql.get_table_names(schema_name=mssql_schema_name)[mssql_schema_name]

        # PostgreSQL
        if postgres_schema is None:
            postgres_schema_name = postgres.DEFAULT_SCHEMA
        else:
            postgres_schema_name = postgres_schema

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

                    chunk_size_ = _get_chunk_size(mssql, mssql_table_name, chunk_size=chunk_size)

                    source_data = mssql.read_table(
                        table_name=mssql_table_name, chunk_size=chunk_size_)

                    source_data_, col_type = _get_col_type(mssql, mssql_table_name, source_data)

                    _mssql_postgres_import_data(
                        mssql=mssql, postgres=postgres, source_data=source_data_,
                        postgres_schema_name=postgres_schema_name,
                        mssql_table_name=mssql_table_name, memory_threshold=memory_threshold,
                        chunk_size=chunk_size_, col_type=col_type)

                    if verbose:
                        print("Done.")

                except Exception as e:
                    print("Failed.")

                    error_log.update({mssql_table_name: f"{e}"})

            else:
                if verbose:
                    postgresql_tbl = f'"{postgres_schema_name}"."{mssql_table_name}"'
                    print(f"\t{counter_msg} {postgresql_tbl} already exists.")

            table_counter += 1

        if bool(error_log):
            return error_log
        else:
            if verbose:
                print("Completed.")


def import_data(db_instance, data, schema_name, table_name, data_name="data", prefix='', suffix='',
                confirmation_required=True, verbose=False, **kwargs):
    """
    Import data into the project database.

    :param db_instance: A class instance for handling the database.
    :type db_instance: typing.Any
    :param data: Data to import (from a local directory).
    :type data: pandas.DataFrame
    :param schema_name: Name of the schema where the table resides.
    :type schema_name: str
    :param table_name: Name of the table where data will be imported.
    :type table_name: str
    :param data_name: Name identifier for the data; defaults to ``"data"``.
    :type data_name: str
    :param prefix: Prefix to prepend to ``data_name``; defaults to ``''``.
    :type prefix: str
    :param suffix: Suffix to append to ``data_name``; defaults to ``''``.
    :type suffix: str
    :param confirmation_required: Whether to request confirmation before proceeding;
        defaults to ``True``.
    :type confirmation_required: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] additional parameters for the method
        :meth:`PostgreSQL.import_data()<pyhelpers.dbms.PostgreSQL.import_data>` or
        :meth:`MSSQL.import_data()<pyhelpers.dbms.MSSQL.import_data>`.

    .. seealso::

        - Examples for the method :func:`~pyhelpers.dbms.utils.read_data`.
    """

    tbl_name = f'"{schema_name}"."{table_name}"'
    data_name_ = f'{prefix}{data_name}{suffix}'
    if _confirmed(f"To import {data_name_} into {tbl_name}?\n", confirmation_required):

        if verbose:
            if not confirmation_required:
                print(f"Importing {data_name_} into {tbl_name}", end=" ... ")
            else:
                print("Importing the data", end=" ... ")

        try:
            import_args = {
                'data': data,
                'schema_name': schema_name,
                'table_name': table_name,
                'method': db_instance.psql_insert_copy,
                'confirmation_required': False,
            }
            kwargs.update(import_args)
            db_instance.import_data(**kwargs)

            if verbose:
                print("Done.")

        except Exception as e:
            _print_failure_msg(e, msg="Failed.", verbose=verbose)


def read_data(db_instance, schema_name, table_name, sql_query=None, data_name="data", prefix='',
              suffix='', verbose=False, **kwargs):
    """
    Read data from the project database.

    :param db_instance: A class instance for handling the database.
    :type db_instance: pyhelpers.dbms.PostgreSQL | pyhelpers.dbms.MSSQL
    :param schema_name: Name of the schema from which to load data.
    :type schema_name: str
    :param table_name: Name of the table from which to load data.
    :type table_name: str
    :param sql_query: SQL query statement for custom data retrieval; defaults to ``None``.
    :type sql_query: str | None
    :param data_name: Name identifier for the loaded data; defaults to ``"data"``.
    :type data_name: str
    :param prefix: Prefix to prepend to ``data_name``; defaults to ``''``.
    :type prefix: str
    :param suffix: Suffix to append to ``data_name``; defaults to ``''``.
    :type suffix: str
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] additional parameters for the method
        :meth:`PostgreSQL.read_sql_query()<pyhelpers.dbms.PostgreSQL.read_sql_query>`,
        :meth:`PostgreSQL.read_table()<pyhelpers.dbms.PostgreSQL.read_table>` or
        :meth:`MSSQL.read_table()<pyhelpers.dbms.MSSQL.read_table>`.
    :return: Queried data as a dataframe.
    :rtype: pandas.DataFrame | None

    .. _`pyhelpers.dbms.PostgreSQL.read_sql_query`:
        https://pyhelpers.readthedocs.io/en/latest/_generated/
        pyhelpers.dbms.PostgreSQL.read_sql_query.html
    .. _`pyhelpers.dbms.MSSQL.read_table`:
        https://pyhelpers.readthedocs.io/en/latest/_generated/
        pyhelpers.dbms.MSSQL.read_table.html

    **Examples**::

        >>> from pyhelpers.dbms.utils import import_data, read_data
        >>> from pyhelpers.dbms import PostgreSQL
        >>> from pyhelpers._cache import example_dataframe
        >>> testdb_name = 'testdb'
        >>> testdb = PostgreSQL(database_name=testdb_name, verbose=True)
        Password (postgres@localhost:5432): ***
        Creating a database: "testdb" ... Done.
        Connecting postgres:***@localhost:5432/testdb ... Successfully.
        >>> # Import an example dataframe into a table named "points"."England"
        >>> example_df = example_dataframe()
        >>> test_schema_name = 'points'
        >>> test_table_name = 'England'
        >>> test_data_name = 'the data of "England points"'
        >>> import_data(
        ...     testdb, example_df, test_schema_name, test_table_name, test_data_name, index=True,
        ...     verbose=True)
        To import the data of "England points" into "points"."England"?
         [No]|Yes: yes
        Importing the data ... Done.
        >>> # Retrieve the data
        >>> example_df_ = read_data(
        ...     testdb, test_schema_name, test_table_name, data_name=test_data_name,
        ...     index_col='City', verbose=True)
        Reading the data of "England points" from "points"."England" ... Done.
        >>> # Check whether the retrieved data is the same as the original example dataframe
        >>> example_df_.equals(example_df)
        True
        >>> # Delete the database "testdb"
        >>> testdb.drop_database(verbose=True)
        To drop the database "testdb" from postgres:***@localhost:5432
        ? [No]|Yes: yes
        Dropping "testdb" ... Done.
    """

    tbl = f'"{schema_name}"."{table_name}"'

    if not db_instance.table_exists(table_name=table_name, schema_name=schema_name):
        if verbose:
            print(f"The table {tbl} does not exist.")
        data = None

    else:
        try:
            if verbose:
                print(f'Reading {prefix}{data_name}{suffix} from {tbl}', end=" ... ")

            # noinspection PyBroadException
            try:
                sql_query_ = f'SELECT * FROM {tbl}' if sql_query is None else sql_query
                data = db_instance.read_sql_query(sql_query=sql_query_, **kwargs)

            except Exception:
                kwargs.update({'table_name': table_name, 'schema_name': schema_name})
                data = db_instance.read_table(**kwargs)

            if verbose:
                print("Done.")

        except Exception as e:
            _print_failure_msg(e, msg="Failed.", verbose=verbose)
            data = None

    return data
