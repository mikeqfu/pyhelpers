"""
Test the :mod:`~pyhelpers.dbms.mssql` submodule.
"""

import os
import tempfile

import pandas as pd
import pytest
import shapely.geometry
import shapely.wkt
import sqlalchemy

from pyhelpers._cache import example_dataframe
from pyhelpers.dbms import MSSQL


class TestMSSQL:
    """
    Test suite for the MSSQL database manager class.
    """

    SERVER = os.getenv('MSSQL_SERVER', 'localhost')
    PORT = int(os.getenv('MSSQL_PORT', 1433))
    DATABASE_NAME = os.getenv('MSSQL_DB', 'testdb')

    # Dynamically switch between CI SQL Authentication and local Windows Authentication
    if os.getenv('MSSQL_USER'):
        # CI Environment (Linux/Docker) using SQL Server Authentication
        USERNAME = os.getenv('MSSQL_USER')
        PASSWORD = os.getenv('MSSQL_PASSWORD', '')
    elif os.name == 'nt':
        # Local Windows development using Windows Authentication
        DOMAIN = os.environ.get('USERDOMAIN', '')
        WIN_USER = os.environ.get('USERNAME', '')
        USERNAME = f'{DOMAIN}\\{WIN_USER}' if DOMAIN else WIN_USER
        PASSWORD = 123
    else:
        # Local POSIX fallback
        USERNAME = 'sa'
        PASSWORD = 'StrongPassword123!'

    ADDRESS = f'{USERNAME}@{SERVER}:{PORT}/{DATABASE_NAME}'

    # noinspection PyNestedDecorators
    @pytest.fixture(scope='class')
    @classmethod
    def testdb(cls):
        """
        Class-scoped fixture providing an active MSSQL instance.

        :return: An initialised MSSQL database manager object.
        :rtype: pyhelpers.dbms.MSSQL
        """

        # If CI variables exist or we are on POSIX, use explicit credentials
        if os.getenv('MSSQL_USER') or os.name != 'nt':
            return MSSQL(
                host=cls.SERVER,
                port=cls.PORT,
                username=cls.USERNAME,
                password=cls.PASSWORD,
                database_name=cls.DATABASE_NAME
            )

        # On Windows without env vars, rely on the class's default Windows Auth
        return MSSQL(database_name=cls.DATABASE_NAME)

    def test_init(self, testdb):
        """
        Test the initialization and default properties of the MSSQL class.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        """

        assert testdb.address == self.ADDRESS
        assert testdb.DEFAULT_ODBC_DRIVER == 'ODBC Driver 18 for SQL Server'

        default_database = 'master'

        if os.getenv('MSSQL_USER') or os.name != 'nt':
            testdb_ = MSSQL(
                host=self.SERVER,
                port=self.PORT,
                username=self.USERNAME,
                password=self.PASSWORD
            )
        else:
            testdb_ = MSSQL()

        expected_address = f'{self.USERNAME}@{self.SERVER}:{self.PORT}/{default_database}'

        assert testdb_.address == expected_address
        assert testdb_.database_name == default_database

        del testdb_

    def test_specify_conn_str(self, testdb, monkeypatch):
        """
        Test the generation of raw ODBC connection strings.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        :param monkeypatch: Pytest monkeypatch fixture.
        :type monkeypatch: pytest.MonkeyPatch
        """

        monkeypatch.setattr('getpass.getpass', lambda _: self.PASSWORD)

        auth_method = 'SQL Server Authentication'

        conn_str = testdb.specify_conn_str(auth=auth_method)
        assert f'DRIVER={{{testdb.odbc_driver}}}' in conn_str
        assert f'SERVER={{{self.SERVER}}}' in conn_str
        assert f'DATABASE={{{self.DATABASE_NAME}}}' in conn_str
        assert f'UID={{{self.USERNAME}}}' in conn_str
        assert f'PWD={{{self.PASSWORD}}}' in conn_str

        conn_str_ = testdb.specify_conn_str(auth=auth_method, password=self.PASSWORD)
        assert conn_str_ == conn_str

    @staticmethod
    def test_create_engine(testdb):
        """
        Test SQLAlchemy engine creation and basic query execution.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        """

        db_engine = testdb.create_engine()
        assert db_engine.name == 'mssql'

        db_engine.dispose()
        del db_engine

        db_conn = testdb.create_connection()
        assert not db_conn.should_close_with_result
        assert not db_conn.closed

        # noinspection PyTypeChecker
        res = db_conn.execute(sqlalchemy.text('SELECT 1'))
        assert res.fetchall() == [(1,)]
        assert not db_conn.closed
        db_conn.close()
        assert db_conn.closed

        del db_conn

    @staticmethod
    def test_get_database_names(testdb):
        """
        Test querying existing database names from the server.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        """

        database_names = testdb.get_database_names()
        assert isinstance(database_names, list)
        assert 'testdb' in database_names

        database_names_df = testdb.get_database_names(names_only=False)
        assert isinstance(database_names_df, pd.DataFrame)
        assert 'testdb' in database_names_df['name'].to_list()

    @staticmethod
    def test_database_exists(testdb):
        """
        Test database existence validation.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        """

        assert testdb.database_exists()

    def test_connect_database(self, testdb, capfd):
        """
        Test connecting to and switching between different databases.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        testdb.connect_database(verbose=True)
        out, _ = capfd.readouterr()
        assert f'Being connected with {self.ADDRESS}.' in out

        temp_addr_pref = f'{self.USERNAME}@{testdb.host}:{testdb.port}'

        testdb.connect_database(database_name=testdb.DEFAULT_DATABASE, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Connecting {temp_addr_pref}/{testdb.DEFAULT_DATABASE} ... Successfully.' in out
        assert testdb.database_name == testdb.DEFAULT_DATABASE

        testdb1_name = 'testdb1'

        testdb.connect_database(database_name=testdb1_name, verbose=True)
        out, _ = capfd.readouterr()
        temp_addr = self.ADDRESS.replace('testdb', testdb1_name)
        assert f'Connecting {temp_addr} ... Successfully.' in out
        assert testdb.database_name == testdb1_name

        testdb.disconnect_database(verbose=True)
        out, _ = capfd.readouterr()
        assert f'Disconnecting the database [{testdb1_name}] ... Done.' in out
        assert testdb.database_name == testdb.DEFAULT_DATABASE

        testdb.disconnect_database(verbose=True)
        out, _ = capfd.readouterr()
        assert f'Being connected with {temp_addr_pref}/master.' in out

        testdb.drop_database(database_name=testdb1_name, confirmation_required=False, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Dropping the database [{testdb1_name}] from {temp_addr_pref} ... Done.' in out

        testdb.connect_database(database_name='testdb')
        assert testdb.database_name == 'testdb'

    @staticmethod
    def test_create_and_drop_schema(testdb, capfd):
        """
        Test the lifecycle of a database schema including idempotency.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        test_schema_name = 'test_schema'

        # Idempotency clear
        if testdb.schema_exists(schema_name=test_schema_name):
            testdb.drop_schema(test_schema_name, confirmation_required=False)

        assert not testdb.schema_exists(schema_name=test_schema_name)

        testdb.create_schema(schema_name=test_schema_name, verbose=True)
        out, _ = capfd.readouterr()
        assert f'Creating a schema: [{test_schema_name}]' in out and 'Done.' in out

        assert testdb.schema_exists(test_schema_name)

        testdb.create_schema(schema_name=test_schema_name, verbose=True)
        out, _ = capfd.readouterr()
        assert f"The schema [{test_schema_name}] already exists." in out

        schema_names = testdb.get_schema_info()
        assert isinstance(schema_names, list)
        assert 'dbo' in schema_names

        schema_names_all = testdb.get_schema_info(names_only=False, include_all=True)
        assert isinstance(schema_names_all, pd.DataFrame)
        assert 'INFORMATION_SCHEMA' in schema_names_all['schema_name'].values

        schema_names_all = testdb.get_schema_info(
            names_only=False, include_all=True, column_names=['a', 'b', 'c'])
        assert isinstance(schema_names_all, pd.DataFrame)
        assert 'INFORMATION_SCHEMA' in schema_names_all['a'].values

        testdb.drop_schema(schema_names, confirmation_required=False, verbose=True)
        out, _ = capfd.readouterr()
        assert all(x in out for x in [
            "Dropping the following schemas",
            "(Built-in schemas which cannot be deleted.)", "Done."] + schema_names)
        schema_info = testdb.get_schema_info(verbose=True)
        assert isinstance(schema_info, list)
        assert schema_info == ['dbo']

    @staticmethod
    def test_create_table(testdb, capfd):
        """
        Test table creation and schema validation.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        test_table_name = 'test_table'
        test_schema_name = 'test_schema'

        # Idempotency clear
        if testdb.table_exists(table_name=test_table_name):
            testdb.drop_table(table_name=test_table_name, confirmation_required=False)
        if testdb.table_exists(table_name=test_table_name, schema_name=test_schema_name):
            testdb.drop_table(table_name=test_table_name, schema_name=test_schema_name,
                              confirmation_required=False)

        # .table_exists()
        assert not testdb.table_exists(table_name=test_table_name)

        # .create_table()
        col_spec = 'col_name_1 INT, col_name_2 varchar(255)'
        testdb.create_table(table_name=test_table_name, column_specs=col_spec, verbose=1)
        out, _ = capfd.readouterr()
        assert f'Creating a table: [dbo].[{test_table_name}]' in out and 'Done.' in out
        assert testdb.table_exists(table_name=test_table_name)

        testdb.create_table(table_name=test_table_name, column_specs=col_spec, verbose=True)
        out, _ = capfd.readouterr()
        assert f"The table [dbo].[{test_table_name}] already exists." in out

        testdb.create_table(
            table_name=test_table_name, column_specs=col_spec, schema_name=test_schema_name,
            verbose=True)
        out, _ = capfd.readouterr()
        assert f"Creating a table: [{test_schema_name}].[{test_table_name}] ... Done." in out

        # .get_table_names()
        tbl_names = testdb.get_table_names()
        assert tbl_names['dbo'] == [test_table_name]

    def test_get_file_tables(self, testdb):
        """
        Test retrieving file tables from the database.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        """

        file_tables = testdb.get_file_tables(names_only=False)
        assert isinstance(file_tables, pd.DataFrame)
        assert file_tables.empty

    def test_column_info(self, testdb):
        """
        Test fetching column names, details and validating column availability.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        """

        test_table_name = 'test_table'

        # .get_column_names()
        column_names = testdb.get_column_names(table_name=test_table_name)
        assert column_names == ['col_name_1', 'col_name_2']

        # .get_column_info()
        column_info = testdb.get_column_info(table_name=test_table_name)
        assert column_info['COLUMN_NAME'] == ['col_name_1', 'col_name_2']

        column_info_df = testdb.get_column_info(table_name=test_table_name, as_dict=False)
        assert isinstance(column_info_df, pd.DataFrame)
        assert column_info_df.loc['COLUMN_NAME', :].tolist() == ['col_name_1', 'col_name_2']

        # .validate_column_names()
        col_names = testdb.validate_column_names(table_name=test_table_name)
        assert col_names == '"col_name_1", "col_name_2"'

        col_names = testdb.validate_column_names(
            table_name=test_table_name, column_names='col_name_1')
        assert col_names == '"col_name_1"'

        col_names = testdb.validate_column_names(
            table_name=test_table_name, column_names=['col_name_1', 'col_name_2'])
        assert col_names == '"col_name_1", "col_name_2"'

        with pytest.raises(AssertionError) as exc_info:
            _ = testdb.validate_column_names(
                table_name=test_table_name, column_names=['col_name_1', 'a'])
            assert str(exc_info.value) == '"a" is not in the existing column names.'

        with pytest.raises(AssertionError) as exc_info:
            _ = testdb.validate_column_names(
                table_name=test_table_name, column_names=['col_name_1', 'a'])
            assert str(exc_info.value) == '"a" is not in the existing column names.'

        with pytest.raises(AssertionError) as exc_info:
            _ = testdb.validate_column_names(
                table_name=test_table_name, column_names=['a', 'b'])
            assert str(exc_info.value) == '["a", "b"] are not in the existing column names.'

    def test_has_types(self, testdb, capfd):
        """
        Test querying column data types.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        # .has_dtypes()
        res = testdb._has_dtypes(table_name='MSreplication_options', dtypes='varbinary')
        assert res == (False, [])

        res_has = testdb.has_dtypes(table_name='spt_monitor', dtypes='varbinary')
        assert list(res_has) == [('varbinary', False, [])]

        testdb.connect_database(database_name=testdb.DEFAULT_DATABASE)

        res_multi = testdb._has_dtypes(
            table_name='MSreplication_options',
            dtypes=['varbinary', 'int']
        )
        assert res_multi == (True, ['major_version', 'minor_version', 'revision', 'install_failures'])

        res_has_multi = testdb.has_dtypes(table_name='spt_monitor', dtypes=['geometry', 'int'])
        assert list(res_has_multi)[0] == ('geometry', False, [])

    def test__column_names_in_query(self, testdb):
        """
        Test generating query-safe column string arrays.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        """

        testdb.connect_database(database_name=testdb.DEFAULT_DATABASE)

        res = testdb._column_names_in_query('MSreplication_options')
        assert isinstance(res, tuple)

        res_spec = testdb._column_names_in_query('MSreplication_options', column_names=['optname'])
        assert res_spec[0] == '[dbo].[optname]'

        testdb.connect_database(database_name='testdb')

    def test_import_data(self, testdb, capfd):
        """
        Test importing dataframes, including spatial formats.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        test_table_name = 'test_table'
        df = example_dataframe()

        testdb.import_data(
            data=df,
            table_name=test_table_name,
            confirmation_required=False,
            if_exists='replace',
            verbose=2
        )
        out, _ = capfd.readouterr()
        assert f"Importing data into [dbo].[{test_table_name}] " in out

        df['geometry'] = df.apply(lambda x: shapely.Point(x.iloc[0], x.iloc[1]).wkt, axis=1)

        testdb.import_data(
            data=df,
            table_name=test_table_name,
            index=True,
            if_exists='replace',
            confirmation_required=False,
            verbose=2
        )
        out, _ = capfd.readouterr()
        assert f"Importing data into [dbo].[{test_table_name}] " in out

        testdb.import_data(
            data=df,
            table_name=test_table_name,
            index=True,
            if_exists='replace',
            geom_column_name='geometry',
            confirmation_required=False,
            verbose=True
        )
        out, _ = capfd.readouterr()
        assert f"Converting 'geometry' to Geometry (SRID 0)" in out and "Done." in out

        # .get_primary_keys()
        pri_keys = testdb.get_primary_keys(table_name=test_table_name)
        assert not pri_keys

        # .add_primary_key()
        testdb.add_primary_key(column_name='City', table_name=test_table_name)
        pri_keys = testdb.get_primary_keys(table_name=test_table_name)
        assert pri_keys == ['City']

    def test_read_data(self, testdb, capfd):
        """
        Test reading tables, executing queries, and saving to disk.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        test_table_name = 'test_table'

        # .read_columns()
        column_names = ['Latitude', 'Longitude']
        dat_1 = testdb.read_columns(table_name=test_table_name, column_names=column_names)
        assert dat_1.columns.to_list() == column_names

        dat_1 = testdb.read_columns(
            table_name=test_table_name,
            column_names=['geometry'],
            dtype='geometry',
            chunk_size=1
        )
        assert isinstance(dat_1.loc[0, 'geometry'], shapely.geometry.Point)

        dat_2 = testdb.read_table(table_name=test_table_name, index_col='City')
        assert shapely.wkt.loads(dat_2['geometry'].iloc[0]) == dat_1.loc[0, 'geometry']

        dat_2 = testdb.read_table(
            table_name=test_table_name,
            column_names=['City', 'Longitude', 'Latitude'],
            conditions="WHERE City = 'Birmingham'",
            chunk_size=1,
            verbose=True
        )
        assert dat_2.columns.to_list() == ['City', 'Longitude', 'Latitude']

        temp_dir = tempfile.mkdtemp()

        dat_2 = testdb.read_table(
            table_name=test_table_name,
            index_col='City',
            save_as=".csv",
            data_dir=temp_dir,
            verbose=True,
            save_args={'index': True}
        )
        out, _ = capfd.readouterr()
        assert 'Saving "test_table.csv" to ' in out and ' ... Done.' in out

        file_path = os.path.join(temp_dir, f"{test_table_name}.csv")
        # noinspection argument-list
        dat_3: pd.DataFrame = pd.read_csv(file_path, index_col=['City'])
        assert dat_2.shape == dat_3.shape

        # .drop_table()
        testdb.drop_table(table_name=test_table_name, confirmation_required=False, verbose=True)
        out, _ = capfd.readouterr()
        assert f"Dropping the table [dbo].[{test_table_name}] from {self.ADDRESS} ... Done." in out

        testdb.drop_table(table_name='abc', confirmation_required=False, verbose=True)
        out, _ = capfd.readouterr()
        assert "The table [dbo].[abc] does not exist." in out

    def test_drop_database(self, testdb, capfd):
        """
        Test dropping the operational database.

        :param testdb: The class-scoped MSSQL fixture.
        :type testdb: pyhelpers.dbms.MSSQL
        :param capfd: Stream capture fixture.
        :type capfd: pytest.CaptureFixture[str]
        """

        test_db_name = self.DATABASE_NAME

        assert testdb.database_exists(database_name=test_db_name)

        testdb.drop_database(
            database_name=test_db_name,
            confirmation_required=False,
            verbose=True
        )
        out, _ = capfd.readouterr()
        assert f"Dropping the database [{test_db_name}] " in out

        expected_from = f'{self.USERNAME}@{self.SERVER}:{self.PORT}'
        assert f"from {expected_from} ... Done." in out

        assert not testdb.database_exists(database_name=test_db_name)


if __name__ == '__main__':
    pytest.main()
