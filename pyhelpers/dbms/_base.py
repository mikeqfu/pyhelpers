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

from .._cache import _confirmed, _lazy_check_dependencies, _print_failure_message


class _Base:
    """
    A base class for communication with database servers.
    """

    #: Default schema name.
    DEFAULT_SCHEMA: str = ''
    #: Names of built-in schemas.
    BUILTIN_SCHEMAS: set = set()

    def __init__(self):
        """
        :ivar str database_name: Name of the database; defaults to ``''``.
        :ivar str address: Address of the server; defaults to ``''``.
        :ivar str engine: Engine; defaults to ``None``.
        :ivar set builtin_schema_names: Names of the built-in schemas; defaults to ``{}``.
        """

        self.database_name = ''
        self.address = ''
        self.engine = None
        self.builtin_schema_names = {}

    def _execute(self, query):
        """
        Executes a database query and check if an item exists.

        :param query: The SQL query to execute.
        :type query: str or sqlalchemy.TextClause
        :return: Whether an item exists.
        :rtype: list

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
        Formats a database name.

        :param database_name: Database name as an input; defaults to ``None``.
        :type database_name: str | None
        :param fmt: String format of the database name; defaults to ``'"{}"'``.
        :type fmt: str
        :return: A formatted database name.
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

    def _create_db(self, confirm_db_creation, fmt='"{}"', verbose=False, raise_error=False):
        """
        Creates a database (if it does not exist) when creating an instance.

        :param confirm_db_creation: Whether to prompt a confirmation before creating a new database
            (if the specified database does not exist).
        :type confirm_db_creation: bool
        :param fmt: String format of the database name; defaults to ``'"{}"'``.
        :type fmt: str
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool
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
                _print_failure_message(
                    e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

    def database_exists(self, database_name=None):
        """
        Checks if a database exists.

        :param database_name: Name of the database to check.
        :type database_name: str | None
        :return: Whether the database exists.
        :rtype: bool
        """
        return None

    def connect_database(self, database_name, verbose=False):
        """
        Connects to a specified database.

        :param database_name: Name of the database to connect to.
        :type database_name: str
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        """
        return None

    def disconnect_database(self, database_name=None, verbose=False):
        """
        Disconnects from a specified database.

        :param database_name: Name of the database to disconnect from;
            defaults to ``None``.
        :type database_name: str or None
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool
        """
        return None

    def _create_database(self, database_name, verbose, fmt):
        """
        Creates a new database if it does not already exist.

        :param database_name: Name of the database to create.
        :type database_name: str
        :param verbose: Whether to print relevant information to the console.
        :type verbose: bool | int
        :param fmt: String format of the database name.
        :type fmt: str
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

    def _drop_database(self, database_name=None, fmt='"{}"', confirmation_required=True, verbose=False,
                       raise_error=False):
        """
        Drops (deletes) a database from the server.

        :param database_name: Name of the database to drop.
        :type database_name: str | None
        :param fmt: String format of the database name. Defaults to ``'"{}"'``.
        :type fmt: str
        :param confirmation_required: Whether to prompt a message for confirmation before
            proceeding. Defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool
        """

        # Resolve and check existence
        db_name = self._database_name(database_name, fmt=fmt)

        if not self.database_exists(database_name=database_name):
            if verbose:
                print(f"The database {db_name} does not exist.")
            return

        # address = self.address.replace(f"/{db_name}", "")
        address = self.address.split('/')[0]
        prompt = f"Drop the database {db_name} from {address}?\n"
        if not _confirmed(prompt=prompt, confirmation_required=confirmation_required):
            if verbose:
                print("Canceled.")
            return

        if verbose:
            if confirmation_required:
                log_msg = f"Dropping {db_name}"
            else:
                log_msg = f"Dropping the database {db_name} from {address}"
            print(log_msg, end=" ... ", flush=True)

        try:
            self.disconnect_database(database_name=database_name)

            with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                query = sqlalchemy.text(f'DROP DATABASE {db_name};')
                conn.execute(query)

            if verbose:
                print("Done.")

        except Exception as e:
            _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

    def _schema_name(self, schema_name=None):
        """
        Gets a schema name.

        :param schema_name: Schema name as an input; defaults to ``None``.
        :type schema_name: str | list | tuple | None
        :return: The schema name.
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
        Gets a formatted table name.

        :param table_name: Table name as an input.
        :type table_name: str
        :param schema_name: Schema name as an input; defaults to ``None``.
        :type schema_name: str | None
        :param fmt: String format of the full table name; defaults to ``'"{}"."{}"'``.
        :type fmt: str
        :return: A formatted table name, which is used in a SQL query statement.
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

    def _msg_for_multi_items(self, item_names, desc, fmt='"{}"', indent=2):
        # noinspection PyShadowingNames
        """
        Formulates a message for printing multiple items with singular/plural logic.

        :param item_names: One or several item names.
        :type item_names: str | typing.Iterable[str] | None
        :param desc: Description of the items (e.g. ``'table'``, ``'schema'``).
        :type desc: str
        :param fmt: Format string for each item. Defaults to ``'"{}"'``.
        :type fmt: str
        :param indent: Indentation level; if an integer, represents the number of spaces;
            If a string, used as the indentation character (e.g. ``'\\t'``);
            defaults to ``2`` (two spaces).
        :type indent: int | str
        :return: Formatted message for printing.
        :rtype: tuple[list[str], str, str, str]

        **Examples**::

            >>> from pyhelpers.dbms import PostgreSQL
            >>> testdb = PostgreSQL('localhost', 5432, 'postgres', database_name='testdb')
            Password (postgres@localhost:5432): ***
            Creating a database: "testdb" ... Done.
            Connecting postgres:***@localhost:5432/testdb ... Successfully.
            >>> item_names = 'points'
            >>> item_names_, print_plural, print_items, indent_str = testdb._msg_for_multi_items(
            ...     item_names, desc='schema')
            >>> item_names_
            ['points']
            >>> print_plural
            'schema'
            >>> print_items
            '"points"'
            >>> indent_str
            '  '
            >>> item_names = ['points', 'lines', 'polygons']
            >>> item_names_, print_plural, print_items, indent_str = testdb._msg_for_multi_items(
            ...     item_names, desc='schema')
            >>> item_names_
            ['points', 'lines', 'polygons']
            >>> print_plural
            'schemas'
            >>> print_items
            '\n  "points"\n  "lines"\n  "polygons"'
            >>> print(print_items)

              "points"
              "lines"
              "polygons"
        """

        # Handle integer vs string indentation
        indent_str = " " * max(0, indent) if isinstance(indent, int) else str(indent or "")

        # Item normalisation
        if item_names is None:
            item_names_ = sqlalchemy.inspect(self.engine).get_schema_names()
        else:
            item_names_ = [item_names] if isinstance(item_names, str) else list(item_names)

        # Singular vs. plural logic
        if len(item_names_) == 1:
            print_plural = f"{desc}"
            print_items = fmt.format(item_names_[0])
        else:
            print_plural = f"{desc}s"  # Use simple pluralisation (suffix 's')
            # Build the multi-line string using the resolved indent_str
            item_lines = [f"{indent_str}{fmt.format(name)}" for name in item_names_]
            print_items = "\n" + "\n".join(item_lines)

        return item_names_, print_plural, print_items, indent_str

    def create_schema(self, schema_name, verbose=False):
        """
        Creates a new schema.

        :param schema_name: Name of the schema to create.
        :type schema_name: str
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        """
        return None

    def schema_exists(self, schema_name):
        """
        Checks if a schema exists.

        :param schema_name: Name of the schema to check.
        :type schema_name: str
        :return: Whether the schema exists.
        :rtype: bool
        """
        return None

    def __drop_schema(self, schema_name, query_, verbose=False, raise_error=False):
        """
        Drops a schema if it is not a built-in schema.

        :param schema_name: Name of the schema to drop.
        :type schema_name: str
        :param query_: SQL query to drop the schema.
        :type query_: str
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool
        """

        if schema_name in self.BUILTIN_SCHEMAS:
            if verbose:
                print("(Built-in schemas which cannot be deleted.)")

        else:
            try:  # e.g. query_ = 'DROP SCHEMA "{}" CASCADE;'
                with self.engine.connect() as connection:
                    query = sqlalchemy.text(query_.format(*(query_.count('{}') * [schema_name])))
                    connection.execute(query)

                if verbose:
                    if not self.schema_exists(schema_name=schema_name):
                        print("Done.")
                    else:
                        print("Failed.")

            except Exception as e:
                _print_failure_message(
                    e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

    def _drop_schema(self, schema_names, fmt, query_, confirmation_required=True, verbose=False,
                     indent=2, raise_error=False):
        """
        Drops one or more schemas.

        :param schema_names: Name(s) of the schemas to drop.
        :type schema_names: str | typing.Iterable[str]
        :param fmt: String format of the schema name.
        :type fmt: str
        :param query_: SQL query to drop the schema.
        :type query_: str
        :param confirmation_required: Whether to prompt a message for confirmation before
            proceeding; defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param indent: Indentation level; if an integer, represents the number of spaces;
            If a string, used as the indentation character (e.g. ``'\\t'``);
            defaults to ``2`` (two spaces).
        :type indent: int | str
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool
        """

        schema_names_, print_plural, print_schema, indent_str = self._msg_for_multi_items(
            item_names=schema_names, desc='schema', fmt=fmt, indent=indent)

        if len(schema_names_) == 1:
            cfm_msg = f"To drop the {print_plural} {print_schema} from {self.address}\n?"
        else:
            cfm_msg = f"To drop the following {print_plural} from {self.address}: {print_schema}\n?"

        if _confirmed(cfm_msg, confirmation_required=confirmation_required):
            if verbose:
                if len(schema_names_) == 1:
                    log_msg = f"Dropping {print_schema}" if confirmation_required else \
                        f"Dropping the {print_plural}: {print_schema}"
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
                            print(f"The schema \"{schema_name}\" does not exist.")
                        else:
                            print(f"{indent_str}\"{schema_name}\" (does not exist.)")

                else:
                    if len(schema_names_) > 1 and verbose:
                        print(f"{indent_str}\"{schema_name}\"", end=" ... ")

                    self.__drop_schema(
                        schema_name=schema_name, query_=query_, verbose=verbose,
                        raise_error=raise_error)

    def get_table_names(self, schema_name, verbose=False):
        """
        Gets names of all tables stored in one or more schemas.

        :param schema_name: Name of a schema or a list of schema names.
            If ``None``, defaults to the default schema.
        :type schema_name: str | list | None
        :param verbose: Whether to print relevant information to the console. Defaults to ``False``.
        :type verbose: bool | int
        :return: A dictionary where keys are schema names and values are lists of table names.
        :rtype: dict[str, list[str]]
        """

        # Normalize schema names to a list
        schema_input = self._schema_name(schema_name=schema_name)
        schema_names = [schema_input] if isinstance(schema_input, str) else list(schema_input)

        inspector = sqlalchemy.inspect(self.engine)

        table_names_map = {}

        for schema in schema_names:
            if not self.schema_exists(schema_name=schema):  # Check existence before inspecting
                if verbose:
                    s = f"[{schema}]" if self.engine.dialect.name == 'mssql' else f'"{schema}"'
                    print(f'The schema {s} does not exist.')
                continue  # Skip to the next schema to avoid crashing

            # Safe inspection
            try:
                table_names_map[schema] = inspector.get_table_names(schema=schema)
            except Exception as e:
                if verbose:
                    print(f"Warning: Could not retrieve tables for '{schema}'. Error: {e}")
                table_names_map[schema] = []

        return table_names_map or None

    def table_exists(self, table_name, schema_name):
        """
        Checks if a table exists in a specified schema.

        :param table_name: Name of the table to check.
        :type table_name: str
        :param schema_name: Name of the schema to check in.
        :type schema_name: str | None
        :return: Whether the table exists.
        :rtype: bool
        """
        return None

    def _create_table(self, table_name, column_specs, schema_name, verbose=False, raise_error=True):
        """
        Creates a new table with the specified column definitions.

        If the table already exists, the operation is skipped.
        If the schema does not exist, it is created automatically.

        :param table_name: Name of the table to be created.
        :type table_name: str
        :param column_specs: SQL fragment defining columns
            (e.g. ``'id INT PRIMARY KEY, val TEXT'``).
        :type column_specs: str
        :param schema_name: Name of the schema where the table will be created;
            if ``None``, defaults to the engine's default schema.
        :type schema_name: str | None
        :param verbose: Whether to print relevant information to the console. Defaults to ``False``.
        :type verbose: bool | int
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False``, the error will be suppressed. Defaults to ``True``.
        :type raise_error: bool
        """

        # Resolve full table name (e.g. "schema"."table")
        full_table_name = self._table_name(table_name=table_name, schema_name=schema_name)

        # Check existence
        if self.table_exists(table_name=table_name, schema_name=schema_name):
            if verbose:
                print(f"The table {full_table_name} already exists.")
            return

        # Ensure schema exists
        if schema_name and not self.schema_exists(schema_name):
            self.create_schema(schema_name=schema_name, verbose=False)

        # Execute creation
        try:
            if verbose:
                print(f"Creating a table: {full_table_name} ... ", end="", flush=True)

            with self.engine.connect() as connection:
                query = sqlalchemy.text(f'CREATE TABLE {full_table_name} ({column_specs});')
                connection.execute(query)

            if verbose:
                print("Done.")

        except Exception as e:
            _print_failure_message(e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

    def _drop_table(self, table_name, query_fmt, schema_name=None, confirmation_required=True,
                    verbose=False, indent=0, raise_error=False):
        """
        Drops a table from a specified schema.

        :param table_name: Name of the table to drop.
        :type table_name: str
        :param query_fmt: SQL query format to drop the table.
        :type query_fmt: str
        :param schema_name: Name of the schema containing the table; defaults to ``None``.
        :type schema_name: str | None
        :param confirmation_required: Whether to prompt a message for confirmation before
            proceeding; defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param indent: Indentation level; if an integer, represents the number of spaces;
            If a string, used as the indentation character (e.g. ``'\\t'``);
            defaults to ``0`` (no space).
        :type indent: int | str
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool
        """

        full_table_name = self._table_name(table_name=table_name, schema_name=schema_name)

        if not self.table_exists(table_name=table_name, schema_name=schema_name):
            if verbose:
                print(f"The table {full_table_name} does not exist.")
            return

        indent_str = " " * max(0, indent) if isinstance(indent, int) else str(indent or "")

        prompt = f"{indent_str}Drop the table {full_table_name} from {self.address}?\n"
        if not _confirmed(prompt, confirmation_required=confirmation_required):
            if verbose:
                print("Canceled.")
            return

        if verbose:
            if confirmation_required:
                log_msg = f"  {indent_str}Dropping {full_table_name}"
            else:
                log_msg = f"{indent_str}Dropping {full_table_name} from {self.address}"
            print(log_msg, end=" ... ")

        try:
            with self.engine.connect() as connection:
                # e.g. 'DROP TABLE {} CASCADE;'.format(table_name_)
                query = sqlalchemy.text(query_fmt.format(full_table_name))
                connection.execute(query)

            if verbose:
                print("Done.")

        except Exception as e:
            _print_failure_message(e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

    def drop_table(self, table_name, schema_name=None, confirmation_required=True, verbose=False,
                   indent=0):
        """
        Drops a table from a specified schema.

        :param table_name: Name of the table to drop.
        :type table_name: str
        :param schema_name: Name of the schema containing the table.
        :type schema_name: str | None
        :param confirmation_required: Whether to prompt a message for confirmation before
            proceeding; defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param indent: Indentation level; if an integer, represents the number of spaces;
            If a string, used as the indentation character (e.g. ``'\\t'``);
            defaults to ``0`` (no space).
        :type indent: int | str
        """
        return None

    @_lazy_check_dependencies(pd_io_parsers='pandas.io.parsers')
    def _import_data(self, data, table_name, schema_name=None, if_exists='fail',
                     force_replace=False, chunk_size=None, dtype=None, method='multi',
                     index=False, confirmation_required=True, verbose=False, **kwargs):
        """
        Imports tabular data into a database table.

        :param data: Tabular data to be imported into a database.
        :type data: pandas.DataFrame | pandas.io.parsers.TextFileReader | list | tuple
        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema; defaults to the default schema if ``None``.
        :type schema_name: str | None
        :param if_exists: What to do if the table already exists: ``'replace'``, ``'append'`` or
            ``'fail'`` (default).
        :type if_exists: str
        :param force_replace: Whether to force replacing an existing table; defaults to ``False``.
        :type force_replace: bool
        :param chunk_size: Number of rows in each batch to be written at a time;
            defaults to ``None``.
        :type chunk_size: int | None
        :param dtype: Data types for columns; defaults to ``None``.
        :type dtype: dict | None
        :param method: Method for SQL insertion clause; defaults to ``'multi'``.

            - ``None``: Uses standard SQL ``INSERT`` clause (one per row).
            - ``'multi'``: Passes multiple values in a single ``INSERT`` clause.
            - Callable: A callable (e.g., ``PostgreSQL.psql_insert_copy``) with the signature
              ``(pd_table, conn, keys, data_iter)``.

        :type method: str | None | typing.Callable
        :param index: Whether to import the index as a column; defaults to ``False``.
        :type index: bool
        :param confirmation_required: Whether to prompt a message for confirmation before
            proceeding; defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: Whether to print relevant information to the console; defaults to ``False``.
        :type verbose: bool | int
        :param kwargs: [Optional] Additional parameters for the method `pandas.DataFrame.to_sql()`_.

        .. _`pandas.DataFrame.to_sql()`:
            https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html
        """

        schema_name_ = self._schema_name(schema_name=schema_name)
        table_name_ = self._table_name(table_name=table_name, schema_name=schema_name_)

        prompt = f"Import data into {table_name_} at {self.address}?\n"
        if not _confirmed(prompt, confirmation_required=confirmation_required):
            if verbose:
                print("Canceled.")
            return

        # Schema existence check
        if not self.schema_exists(schema_name_):
            self.create_schema(schema_name=schema_name_, verbose=verbose)

        # Handle 'force_replace' logic independently of pandas
        table_exists = self.table_exists(table_name=table_name, schema_name=schema_name_)

        if table_exists:
            if force_replace:
                if verbose:
                    print(f"Forcing drop of existing table {table_name_} ... ")
                self.drop_table(
                    table_name=table_name, schema_name=schema_name_, confirmation_required=False,
                    verbose=verbose == 2, indent=2)
                # After dropping, change `if_exists` to 'fail' (let pandas create it) or keep as is.
                if_exists = 'fail'  # Setting to 'fail' is safest
            elif if_exists == 'fail':
                if verbose:
                    print(f"The table {table_name_} already exists.\n"
                          "  Use `if_exists='replace'` or `force_replace=True` to update.")
                return

        # Prepare Pandas arguments
        to_sql_kwargs = {
            'name': table_name,
            'con': self.engine,
            'schema': schema_name_,
            'if_exists': if_exists,
            'index': index,
            'dtype': dtype,
            'method': method,
            'chunksize': chunk_size
        }
        # Allow user kwargs to supplement, but not overwrite core mapping
        import_kwargs = {**kwargs, **to_sql_kwargs}

        # Execution logic
        if verbose:
            if confirmation_required:
                print(f"Importing the data", end=" ... ", flush=True)
            else:
                print(f"Importing data into {table_name_}", end=" ... ", flush=True)

        try:
            # Check if data is an iterable of DataFrames or a single DataFrame
            if isinstance(data, (pd_io_parsers.TextFileReader, list, tuple)):  # noqa
                for i, chunk in enumerate(data):
                    # If appending a list, the first chunk follows 'if_exists', others MUST be 'append'
                    if i > 0:
                        import_kwargs['if_exists'] = 'append'
                    if isinstance(chunk, pd.DataFrame):
                        chunk.to_sql(**import_kwargs)
                    else:  # Fallback for non-dataframe items in a list
                        pd.DataFrame(chunk).to_sql(**import_kwargs)

            elif isinstance(data, pd.DataFrame):
                # noinspection PyUnresolvedReferences
                data.to_sql(**import_kwargs)

            else:
                raise TypeError("The input `data` type is not accepted.")

            if verbose:
                print("Done.")

        except Exception as e:
            _print_failure_message(e, prefix="Failed.", verbose=verbose, raise_error=True)

        finally:
            gc.collect()  # Final cleanup

    def get_column_info(self, table_name, schema_name=None, as_dict=True):
        # noinspection PyUnresolvedReferences
        """
        Gets information about columns of a table.

        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema; defaults to ``'public'`` if ``schema_name=None``.
        :type schema_name: str | None
        :param as_dict: Whether to return the column information as a dictionary;
            defaults to ``True``.
        :type as_dict: bool
        :return: Information about all columns of the specified table.
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

    def get_column_names(self, table_name, schema_name=None):
        """
        Retrieves column names of a table.

        :param table_name: Name of the table to retrieve column names from.
        :type table_name: str
        :param schema_name: Name of the schema where the table is located; defaults to ``None``.
        :type schema_name: str | None
        :return: List of column names in the specified table in the currently-connected database.
        :rtype: list
        """

        return []

    def validate_column_names(self, table_name, schema_name=None, column_names=None):
        """
        Validates column names for a query statement.

        :param table_name: Name of the table.
        :type table_name: str
        :param schema_name: Name of the schema; defaults to ``None``.
        :type schema_name: str | None
        :param column_names: Column name(s) to validate; defaults to ``None``.
        :type column_names: str | list | tuple | None
        :return: Validated column names for a PostgreSQL query statement.
        :rtype: str
        """

        tbl_col_names = self.get_column_names(table_name=table_name, schema_name=schema_name)

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

    def read_sql_query(self, sql_query, method='tempfile', max_size_spooled=1, delimiter=',',
                       tempfile_kwargs=None, stringio_kwargs=None, **kwargs):
        """
        Executes a SQL query and read the result into a DataFrame.

        :param sql_query: SQL query to execute.
        :type sql_query: str
        :param method: Method for reading the query result.
        :type method: str
        :param max_size_spooled: Maximum size in bytes before spooling to disk.
        :type max_size_spooled: int
        :param delimiter: Delimiter to use for reading the query result.
        :type delimiter: str
        :param tempfile_kwargs: Additional keyword arguments for ``tempfile``.
        :type tempfile_kwargs: dict
        :param stringio_kwargs: Additional keyword arguments for ``StringIO``.
        :type stringio_kwargs: dict
        :param kwargs: [Optional] Additional arguments passed to the reading method.
        """
        return None

    def _read_sql_query_args(self):
        """
        Gets names of arguments that are exclusive to the ``.read_sql_query()`` method.

        :return: Names of arguments exclusive to ``.read_sql_query()`` method.
        :rtype: set
        """

        rsq_args = map(lambda x: inspect.getfullargspec(x).args, (self.read_sql_query, pd.read_csv))
        rsq_args_spec = set(itertools.chain(*rsq_args))

        read_sql_args = set(inspect.getfullargspec(func=pd.read_sql).args)

        return rsq_args_spec - read_sql_args
