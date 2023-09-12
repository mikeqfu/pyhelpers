"""
Database tools/utilities.
"""

import copy
import gc
import inspect
import sys

import sqlalchemy.dialects

from .._cache import _check_dependency, _confirmed


def make_database_address(host, port, username, database_name=""):
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

    **Examples**::

        >>> from pyhelpers.dbms.utils import make_database_address

        >>> db_addr = make_database_address('localhost', 5432, 'postgres', 'postgres')
        >>> db_addr
        'postgres:***@localhost:5432/postgres'
    """

    database_address = f"{username}:***@{host}:{port}"

    if database_name:
        database_address += f"/{database_name}"

    return database_address


def get_default_database_address(db_cls):
    """
    Get default database address of a given class in the current module.

    :param db_cls: a class representation of a database
    :type db_cls: object
    :return: default address of database
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


def mssql_to_postgresql(mssql, postgres, mssql_schema=None, postgres_schema=None, chunk_size=None,
                        excluded_tables=None, file_tables=False, memory_threshold=2., update=False,
                        confirmation_required=True, verbose=True):
    """
    Copy tables of a database from a Microsoft SQL server to a PostgreSQL server.

    :param mssql: name of a Microsoft SQL (source) database
    :type mssql: pyhelpers.dbms.MSSQL
    :param postgres: name of a PostgreSQL (destination) database
    :type postgres: pyhelpers.dbms.PostgreSQL
    :param mssql_schema: name of a schema to be migrated from the SQl Server
    :type mssql_schema: str or None
    :param postgres_schema: name of a schema to store the migrated data in the PostgreSQL server
    :type postgres_schema: str or None
    :param chunk_size: number of rows in each batch to be read/written at a time, defaults to ``None``
    :type chunk_size: int or None
    :param excluded_tables: names of tables that are excluded from the data migration
    :type excluded_tables: list or None
    :param file_tables: whether to include FileTables, defaults to ``False``
    :type file_tables: bool
    :param memory_threshold: threshold (in GiB) beyond which the data is migrated by partitions,
        defaults to ``2.``
    :type memory_threshold: float or int
    :param update: whether to redo the transfer between the database servers, defaults to ``False``
    :type update: bool
    :param confirmation_required: whether asking for confirmation to proceed, defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information, defaults to ``True``
    :type verbose: bool or int

    **Examples**::

        >>> from pyhelpers.dbms.utils import mssql_to_postgresql
        >>> from pyhelpers.dbms import PostgreSQL, MSSQL
        >>> from pyhelpers._cache import example_dataframe

        >>> # Connect/create a PostgreSQL database, which is named [testdb]
        >>> mssql_testdb = MSSQL(database_name='testdb')
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
        >>> postgres_testdb = PostgreSQL(database_name='testdb')
        Password (postgres@localhost:5432): ***
        Creating a database: "testdb" ... Done.
        Connecting postgres:***@localhost:5432/testdb ... Successfully.

        >>> # For now, the newly-created database doesn't contain any tables
        >>> postgres_testdb.get_table_names()
        []

        >>> # Copy the example data from the SQL Server to the PostgreSQL "testdb" (under "public")
        >>> mssql_to_postgresql(mssql=mssql_testdb, postgres=postgres_testdb)
        To copy tables from [testdb] (MSSQL) to "testdb" (PostgreSQL)
        ? [No]|Yes: yes
        Processing tables ...
            (1/1) Copying [dbo].[example_df] to "public"."example_df" ... Done.
        Completed.

        >>> postgres_testdb.get_table_names()
        ['example_df']

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
        mssql_table_names = mssql.get_table_names(schema_name=mssql_schema_name)

        # PostgreSQL
        postgres_schema_name = postgres.DEFAULT_SCHEMA if postgres_schema is None else postgres_schema

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

                    row_count = mssql.get_row_count(mssql_table_name)

                    if row_count >= 1000000:

                        if chunk_size is None:
                            chunk_size = 1000000

                    source_data = mssql.read_table(table_name=mssql_table_name, chunk_size=chunk_size)

                    col_type = {}

                    check_dtypes = ['hierarchyid', 'varbinary']
                    check_dtypes_rslt = mssql.has_dtypes(mssql_table_name, dtypes=check_dtypes)

                    for dtype, if_exists, col_names in check_dtypes_rslt:
                        if if_exists:
                            if dtype == 'hierarchyid':
                                source_data.loc[:, col_names] = source_data[col_names].applymap(
                                    lambda x: str(x).replace('\\', '\\\\'))

                            bytea_list = [sqlalchemy.dialects.postgresql.BYTEA] * len(col_names)
                            col_type.update(dict(zip(col_names, bytea_list)))

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

                    if verbose:
                        print("Done.")

                except Exception as e:
                    print("Failed.")

                    error_log.update({mssql_table_name: "{}".format(e)})

            else:
                if verbose:
                    postgresql_tbl = f'"{postgres_schema_name}"."{mssql_table_name}"'
                    print(f"\t{counter_msg} {postgresql_tbl} already exists.")

            table_counter += 1

        if verbose:
            print(f"Completed.")

        if bool(error_log):
            return error_log
