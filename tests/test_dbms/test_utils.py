"""
Test the module :mod:`~pyhelpers.dbms`.
"""

import pandas as pd
import pytest
from dotenv import load_dotenv

from pyhelpers._cache import example_dataframe
from pyhelpers.dbms.mssql import MSSQL
from pyhelpers.dbms.postgresql import PostgreSQL
from pyhelpers.dbms.utils import add_sql_query_condition, get_default_database_address, \
    import_data, make_database_address, mssql_to_postgresql, read_data
from tests.conftest import requires_mssql, requires_postgres

load_dotenv()


def test_make_database_address():
    """
    Test generation of a masked database connection string.
    """

    db_addr = make_database_address('localhost', 5432, 'postgres', 'postgres')
    assert db_addr == 'postgres:***@localhost:5432/postgres'


def test_get_default_database_address():
    """
    Test retrieving default database connection address for a class.
    """

    db_addr = get_default_database_address(db_cls=PostgreSQL)
    assert db_addr == 'None:***@None:None'


def test_add_sql_query_condition():
    """
    Test appending conditional clauses to a base SQL query string.
    """

    query = 'SELECT * FROM a_table'

    # Default query without additional parameters
    assert add_sql_query_condition(query) == 'SELECT * FROM a_table'

    # Single column filter
    assert add_sql_query_condition(query, COL_NAME_1='A') == (
        'SELECT * FROM a_table WHERE "COL_NAME_1"=\'A\''
    )

    # Multiple column filters including list values
    assert add_sql_query_condition(
        query, COL_NAME_1='A', COL_NAME_2=['B', 'C']
    ) == 'SELECT * FROM a_table WHERE "COL_NAME_1"=\'A\' AND "COL_NAME_2" IN (\'B\', \'C\')'

    # Table prefix addition
    assert add_sql_query_condition(
        query, COL_NAME_1='A', add_table_name='t1'
    ) == 'SELECT * FROM a_table WHERE t1."COL_NAME_1"=\'A\''


@requires_postgres
def test_import_and_read_data(postgres_kwargs):
    """
    Test importing and reading data with custom schemas in PostgreSQL.
    """

    test_db_name = 'testdb_import_read'
    testdb = PostgreSQL(database_name=test_db_name, **postgres_kwargs)

    example_df = example_dataframe()

    try:
        test_schema_name = 'points'
        test_table_name = 'England'
        test_data_name = 'the data of "England points"'

        import_data(
            testdb,
            example_df,
            test_schema_name,
            test_table_name,
            test_data_name,
            index=True,
            confirmation_required=False,
            verbose=True,
        )

        example_df_ = read_data(
            testdb,
            test_schema_name,
            test_table_name,
            data_name=test_data_name,
            index_col='City',
            verbose=True,
        )

        assert isinstance(example_df_, pd.DataFrame)
        assert example_df_.equals(example_df)

    finally:
        testdb.drop_database(confirmation_required=False)


@requires_postgres
@requires_mssql
def test_mssql_to_postgresql(capfd, mssql_kwargs, postgres_kwargs):
    """
    Test copying tables natively from an MSSQL to a PostgreSQL database.

    :param capfd: Stream capture fixture.
    :type capfd: pytest.CaptureFixture[str]
    """

    example_df = example_dataframe()
    test_db_name = 'testdb_migration'

    mssql_testdb = MSSQL(database_name=test_db_name, **mssql_kwargs)
    postgres_testdb = PostgreSQL(database_name=test_db_name, **postgres_kwargs)

    try:
        test_table_name = 'test_table'
        test_table_exists = mssql_testdb.table_exists(table_name=test_table_name)
        if test_table_exists:
            msg = f"The table [dbo].[{test_table_name}] already exists."
        else:
            msg = f"Importing data into [dbo].[{test_table_name}] ... Done."

        mssql_testdb.import_data(
            example_df,
            table_name=test_table_name,
            index=True,
            confirmation_required=False,
            verbose=2
        )
        out, _ = capfd.readouterr()
        assert msg in out

        column_names = mssql_testdb.get_column_names(table_name=test_table_name)
        assert column_names == ['City', 'Longitude', 'Latitude']

        assert postgres_testdb.get_table_names() == {'public': []}

        result = mssql_to_postgresql(
            mssql=mssql_testdb,
            postgres=postgres_testdb,
            confirmation_required=False
        )
        out, _ = capfd.readouterr()
        assert result is None, f"Migration failed: {result}"

        # Verify the logs explicitly map to the dynamic test_db_name string
        assert (f'Copying tables from [{test_db_name}] (MSSQL) to "{test_db_name}" (PostgreSQL)'
                in out)
        assert f'(1/1) Copying [dbo].[{test_table_name}] to "public"."{test_table_name}"' in out
        assert "Done." in out and "Completed." in out

        assert postgres_testdb.get_table_names() == {'public': [test_table_name]}

    finally:
        postgres_testdb.drop_database(confirmation_required=False, verbose=True)
        mssql_testdb.drop_database(confirmation_required=False, verbose=True)


if __name__ == '__main__':
    pytest.main()
