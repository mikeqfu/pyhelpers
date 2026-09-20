"""
Test the :mod:`~pyhelpers.dbms.postgresql` submodule.
"""

import os

import pandas as pd
import pytest
from dotenv import load_dotenv

from pyhelpers._cache import example_dataframe
from pyhelpers.dbms import PostgreSQL

# Load variables from a local .env file into the environment
# This should silently fail if no .env file exists (e.g. in CI environments)
load_dotenv()


class TestPostgreSQL:
    """
    Test suite for the PostgreSQL database manager class.
    """

    # Provide fallbacks for local testing without CI services
    SERVER = os.getenv('POSTGRES_SERVER', 'localhost')
    PORT = int(os.getenv('POSTGRES_PORT', 5432))
    USERNAME = os.getenv('POSTGRES_USER', 'postgres')

    # Safely retrieve the password from the environment.
    # Fall back to an empty string, meaning it will attempt passwordless
    # 'trust' authentication if no password is provided.
    PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    DATABASE_NAME = os.getenv('POSTGRES_DB', 'testdb')

    DEFAULT_ADDRESS = f'{USERNAME}:***@{SERVER}:{PORT}/postgres'
    ADDRESS = f'{USERNAME}:***@{SERVER}:{PORT}/{DATABASE_NAME}'

    # noinspection PyNestedDecorators
    @pytest.fixture(scope='class')
    @classmethod
    def testdb(cls):
        """
        Class fixture providing a connected PostgreSQL instance.

        :return: Initialised PostgreSQL client instance.
        :rtype: typing.Generator[pyhelpers.dbms.PostgreSQL, None, None]
        """

        db = PostgreSQL(
            host=cls.SERVER,
            port=cls.PORT,
            username=cls.USERNAME,
            password=cls.PASSWORD,
            database_name=cls.DATABASE_NAME
        )
        if not db.database_exists(database_name=cls.DATABASE_NAME):
            db.create_database(database_name=cls.DATABASE_NAME)

        yield db

    def test_init(self, testdb, monkeypatch):
        """
        Test the initialization and authentication logic of the PostgreSQL class.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        :param monkeypatch: Pytest monkeypatch fixture.
        :type monkeypatch: pytest.MonkeyPatch
        """

        assert testdb.address == self.ADDRESS

        monkeypatch.setattr('getpass.getpass', lambda _: 'abc')
        with pytest.raises(Exception) as exc_info:
            _ = PostgreSQL(
                host=self.SERVER,
                port=self.PORT,
                username=self.USERNAME,
                database_name=self.DATABASE_NAME
            )
        assert 'password authentication failed' in str(exc_info.value).lower()

        monkeypatch.setattr('getpass.getpass', lambda _: str(self.PASSWORD))
        testdb_ = PostgreSQL(
            host=self.SERVER,
            port=self.PORT,
            username=self.USERNAME
        )
        assert testdb_.address == self.DEFAULT_ADDRESS

        monkeypatch.setattr('getpass.getpass', lambda _: str(self.PASSWORD))
        testdb_ = PostgreSQL(
            host=self.SERVER,
            port=self.PORT,
            username=self.USERNAME,
            database_name=self.DATABASE_NAME
        )
        assert testdb_.address == self.ADDRESS

    @staticmethod
    def test_get_database_names(testdb):
        """
        Test retrieving a list of available database names.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        """
        result = testdb.get_database_names(names_only=False)
        assert isinstance(result, pd.DataFrame)
        assert 'postgres' in result['datname'].to_list()

    @staticmethod
    def test_database_exists(testdb):
        """
        Test the verification of database existence.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        """
        assert testdb.database_exists()

    @staticmethod
    def test_create_database_and_connection(testdb, capfd):
        """
        Test database creation, connection switching and teardown.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        original_db = testdb.database_name
        assert original_db == TestPostgreSQL.DATABASE_NAME

        temp_db1 = f'{original_db}1'
        temp_db2 = f'{original_db}2'

        try:
            testdb.create_database(database_name=temp_db1, verbose=True)
            out, _ = capfd.readouterr()
            assert f'Creating a database: "{temp_db1}" ... Done.' in out
            assert testdb.database_name == temp_db1

            testdb.create_database(database_name=temp_db1, verbose=True)
            out, _ = capfd.readouterr()
            assert "The database already exists." in out

            testdb.connect_database(database_name=temp_db2, verbose=True)
            assert testdb.database_name == temp_db2

            testdb.drop_database(confirmation_required=False, verbose=True)
            assert testdb.database_name == 'postgres'

            testdb.drop_database(database_name=temp_db1, confirmation_required=False, verbose=True)
            assert testdb.database_name == 'postgres'

            testdb.connect_database(verbose=True)
            out, _ = capfd.readouterr()
            assert f"Being connected with {testdb.address}." in out
            assert testdb.database_name == 'postgres'

            testdb.connect_database(database_name=original_db, verbose=True)
            assert testdb.database_name == original_db

            testdb.disconnect_database(database_name=original_db, verbose=True)
            out, _ = capfd.readouterr()
            assert f'Disconnecting the database "{original_db}" ... Done.' in out
            assert testdb.database_name == 'postgres'

            testdb.disconnect_all_others()
            assert testdb.database_name == 'postgres'

        finally:
            testdb.connect_database(database_name=original_db, verbose=True)
            assert testdb.database_name == original_db

    @staticmethod
    def test_get_database_size(testdb):
        """
        Test querying the formatted size of the active database.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        """
        database_size = testdb.get_database_size()
        if database_size:
            assert ' kB' in database_size or ' MB' in database_size

    @staticmethod
    def test_create_and_drop_schema(testdb, capfd):
        """
        Test the lifecycle of a schema, including metadata querying.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        test_schema_name = 'test_schema'

        # Ensure idempotency by clearing residual state from previous failed runs
        if testdb.schema_exists(schema_name=test_schema_name):
            testdb.drop_schema(schema_names=test_schema_name, confirmation_required=False)

        _ = capfd.readouterr()  # Flush capture buffer

        try:
            assert not testdb.schema_exists(schema_name=test_schema_name)

            testdb.create_schema(schema_name=test_schema_name, verbose=True)
            out, _ = capfd.readouterr()
            assert f'Creating a schema: "{test_schema_name}"' in out and 'Done.' in out

            assert testdb.schema_exists(test_schema_name)

            testdb.create_schema(schema_name=test_schema_name, verbose=True)
            out, _ = capfd.readouterr()
            assert f'The schema "{test_schema_name}" already exists.' in out

            schema_names = testdb.get_schema_info()
            assert isinstance(schema_names, list)
            assert 'public' in schema_names

            schema_names_all = testdb.get_schema_info(names_only=False, include_all=True)
            assert isinstance(schema_names_all, pd.DataFrame)
            assert 'information_schema' in schema_names_all['schema_name'].values

            schema_names_all = testdb.get_schema_info(
                names_only=False, include_all=True, column_names=['a', 'b', 'c', 'd']
            )
            assert isinstance(schema_names_all, pd.DataFrame)
            assert 'information_schema' in schema_names_all['a'].values

            res = testdb._msg_for_multi_items(item_names=None, desc='schema')
            assert all(x in res[0] for x in ['information_schema', 'public', test_schema_name])
            res = testdb._msg_for_multi_items(item_names=['public'], desc='schema')
            assert res == (['public'], 'schema', '"public"', '  ')

            testdb.drop_schema(test_schema_name, confirmation_required=False, verbose=True)
            out, _ = capfd.readouterr()
            assert f'Dropping the schema: "{test_schema_name}" ... Done.' in out

            testdb.drop_schema('abc', confirmation_required=False, verbose=True)
            out, _ = capfd.readouterr()
            assert 'Dropping the schema: "abc" ... The schema "abc" does not exist.' in out

            testdb.drop_schema(['abc', 'bcd'], confirmation_required=False, verbose=True)
            out, _ = capfd.readouterr()
            assert "Dropping the following schemas from" in out and '"bcd" (does not exist.)' in out

            testdb.drop_schema(schema_names, confirmation_required=False, verbose=True)
            out, _ = capfd.readouterr()
            assert all(x in out for x in ['Dropping', f"{test_schema_name}", 'Done.'])

            schema_info = testdb.get_schema_info(verbose=True)
            out, _ = capfd.readouterr()
            assert (f'No schema exists in the currently-connected database '
                    f'"{testdb.database_name}".') in out
            assert schema_info is None

        finally:
            if not testdb.schema_exists('public'):
                testdb.create_schema(schema_name='public')

    @staticmethod
    def test_create_table(testdb, capfd):
        """
        Test table creation across custom and default schemas.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        tbl_name = 'test_table'
        test_schema = 'test_schema'

        if not testdb.schema_exists(schema_name=test_schema):
            testdb.create_schema(schema_name=test_schema)

        if testdb.table_exists(table_name=tbl_name, schema_name=test_schema):
            testdb.drop_table(table_name=tbl_name, schema_name=test_schema, confirmation_required=False)

        _ = capfd.readouterr()

        assert not testdb.table_exists(table_name=tbl_name, schema_name=test_schema)

        col_spec = 'col_name_1 INT, col_name_2 TEXT'
        testdb.create_table(
            table_name=tbl_name, column_specs=col_spec, schema_name=test_schema, verbose=1
        )
        out, _ = capfd.readouterr()
        assert f'Creating a table: "{test_schema}"."{tbl_name}"' in out and 'Done.' in out
        assert testdb.table_exists(table_name=tbl_name, schema_name=test_schema)

        testdb.create_table(
            table_name=tbl_name, column_specs=col_spec, schema_name=test_schema, verbose=True
        )
        out, _ = capfd.readouterr()
        assert f'The table "{test_schema}"."{tbl_name}" already exists.' in out

        testdb.create_table(table_name=tbl_name, column_specs=col_spec)

    @staticmethod
    def test_get_column_info_and_dtypes(testdb):
        """
        Test retrieving column information, data types and column name validation.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        """

        tbl_name = 'test_table'

        test_tbl_col_info = testdb.get_column_info(table_name=tbl_name, as_dict=False)
        assert isinstance(test_tbl_col_info, pd.DataFrame)

        test_tbl_dtypes = testdb.get_column_dtype(table_name=tbl_name)
        assert test_tbl_dtypes == {'col_name_1': 'integer', 'col_name_2': 'text'}

        missing_tbl_dtypes = testdb.get_column_dtype(table_name='non_existent_table')
        assert missing_tbl_dtypes is None

        result = testdb.validate_column_names(tbl_name)
        assert result == '"col_name_1", "col_name_2"'

    @staticmethod
    def test_get_table_names(testdb, capfd):
        """
        Test querying existing table names within active and invalid schemas.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        tbl_name = 'test_table'

        tbl_names = testdb.get_table_names()
        assert isinstance(tbl_names, dict)
        assert tbl_name in tbl_names.get('public', [])

        missing_schema_tbls = testdb.get_table_names(schema_name='abc', verbose=True)
        out, _ = capfd.readouterr()
        assert 'The schema "abc" does not exist.' in out
        assert missing_schema_tbls is None

    @staticmethod
    def test_alter_table_schema(testdb, capfd, monkeypatch):
        """
        Test relocating tables between database schemas.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        :param monkeypatch: Pytest monkeypatch fixture.
        :type monkeypatch: pytest.MonkeyPatch
        """

        tbl_name = 'test_table'
        new_schema_name = 'test_schema_2'

        if not testdb.schema_exists(schema_name=new_schema_name):
            testdb.create_schema(schema_name=new_schema_name)

        monkeypatch.setattr('builtins.input', lambda _: "Yes")
        testdb.alter_table_schema(
            table_name=tbl_name, schema_name='public', new_schema_name=new_schema_name,
            confirmation_required=True, verbose=True
        )
        out, _ = capfd.readouterr()
        assert f'Moving "public"."{tbl_name}" to "{new_schema_name}" ... Done.' in out

        testdb.alter_table_schema(
            table_name=tbl_name, schema_name='public', new_schema_name=new_schema_name,
            confirmation_required=False, verbose=True
        )
        out, _ = capfd.readouterr()
        assert f'The table "public"."{tbl_name}" does not exist.' in out

        testdb.alter_table_schema(
            table_name=tbl_name, schema_name=new_schema_name, new_schema_name=f'{new_schema_name}_',
            confirmation_required=False, verbose=True
        )

        testdb.alter_table_schema(
            table_name=tbl_name, schema_name=f'{new_schema_name}_', new_schema_name='public',
            confirmation_required=False, verbose=True
        )
        out, _ = capfd.readouterr()
        assert f'Moving the table "{tbl_name}" from "{new_schema_name}_" to "public" ... Done.' in out

    @staticmethod
    def test_import_data(testdb, capfd):
        """
        Test importing DataFrames with various replacement modes.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        tbl_name = 'test_table'
        dat = example_dataframe()

        testdb.import_data(
            data=dat, table_name=tbl_name, index=True, confirmation_required=False,
            if_exists='replace', verbose=True
        )
        out, _ = capfd.readouterr()
        assert f'Importing data into "public"."{tbl_name}"' in out and "Done." in out

        testdb.import_data(
            data=dat, table_name=tbl_name, index=True, confirmation_required=False,
            if_exists='replace', force_replace=True, verbose=2
        )
        out, _ = capfd.readouterr()
        assert f'Forcing drop of existing table "public"."{tbl_name}"' in out

        testdb.import_data(
            data=dat, table_name=tbl_name, index=True, confirmation_required=False,
            if_exists='fail', verbose=True
        )
        out, _ = capfd.readouterr()
        assert "Use `if_exists='replace'` or `force_replace=True` to update." in out

    @staticmethod
    def test_primary_keys(testdb):
        """
        Test setting and querying primary key constraints.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        """

        tbl_name = 'test_table'
        dat = example_dataframe()

        pri_keys = testdb.get_primary_keys(table_name=tbl_name)
        assert isinstance(pri_keys, list) and not pri_keys

        testdb.add_primary_keys(primary_keys='City', table_name=tbl_name)
        pri_keys: list = testdb.get_primary_keys(table_name=tbl_name)
        assert pri_keys == ['City']

        testdb.import_data(
            data=dat, table_name=tbl_name, index=True, confirmation_required=False,
            if_exists='replace'
        )
        testdb.add_primary_keys(primary_keys=['Longitude', 'Latitude'], table_name=tbl_name)
        pri_keys_df = testdb.get_primary_keys(table_name=tbl_name, names_only=False)
        assert isinstance(pri_keys_df, pd.DataFrame)

    @staticmethod
    def test_null_text_to_empty_string(testdb):
        """
        Test converting SQL NULL text values to empty strings.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        """

        tbl_name = 'test_table'
        dat = example_dataframe()

        dat['Longitude'] = dat['Longitude'].astype(str)
        dat.loc['London', 'Longitude'] = None
        testdb.import_data(
            data=dat, table_name=tbl_name, index=True, confirmation_required=False,
            if_exists='replace'
        )
        dat_ = testdb.read_table(tbl_name)
        assert pd.isna(dat_.loc[0, 'Longitude'])

        testdb.null_text_to_empty_string(table_name=tbl_name)
        dat_ = testdb.read_table(tbl_name, method='tempfile', keep_default_na=False)
        assert dat_.loc[0, 'Longitude'] == ''

    @staticmethod
    def test_drop_table(testdb, capfd):
        """
        Test table deletion and verification of non-existence.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        tbl_name = 'test_table'

        testdb.drop_table(table_name=tbl_name, confirmation_required=False, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Dropping "public"."{tbl_name}" from' in out and "Done." in out

        testdb.drop_table(table_name=tbl_name, confirmation_required=False, verbose=True)
        out, _ = capfd.readouterr()
        assert f'The table "public"."{tbl_name}" does not exist.' in out

    def test_drop_database(self, testdb, capfd):
        """
        Test database deletion logic using an isolated temporary database.

        :param testdb: The class-scoped PostgreSQL fixture.
        :type testdb: pyhelpers.dbms.PostgreSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        temp_db_name = f"{testdb.database_name}_drop_test"

        try:
            testdb.create_database(database_name=temp_db_name)
            assert testdb.database_exists(database_name=temp_db_name)

            testdb.drop_database(
                database_name=temp_db_name,
                confirmation_required=False,
                verbose=True
            )
            out, _ = capfd.readouterr()
            assert f'Dropping the database "{temp_db_name}"' in out and "Done." in out
            assert not testdb.database_exists(database_name=temp_db_name)

            testdb.drop_database(
                database_name=temp_db_name,
                confirmation_required=False,
                verbose=True
            )
            out, _ = capfd.readouterr()
            assert f'The database "{temp_db_name}" does not exist.' in out

        finally:
            testdb.connect_database(database_name=TestPostgreSQL.DATABASE_NAME)


if __name__ == '__main__':
    pytest.main()
