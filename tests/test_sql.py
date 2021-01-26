"""
Test module sql.py
"""

from pyhelpers.sql import *


def test_get_db_address():

    db_addr = get_db_address(db_cls=PostgreSQL)

    print(db_addr)
    # None:***@None:None/None


def test_postgresql():
    testdb = PostgreSQL(host='localhost', port=5432, username='postgres', database_name='testdb')
    # Password (postgres@localhost:5432): ***
    # Connecting postgres:***@localhost:5432/testdb ... Successfully.

    table_name = 'England'
    schema_name = 'points'

    res = testdb.table_exists(table_name, schema_name)
    print("\nThe table '{}.{}' exists? {}.".format(schema_name, table_name, res))
    # The table 'points.England' exists? False.

    print("")

    table_name = 'test_table'
    schema_name = 'public'
    column_specs = 'col_name_1 INT, col_name_2 TEXT'

    testdb.create_table(table_name, column_specs, schema_name, verbose=True)
    # Creating a table: "public"."test_table" ... Done.

    res = testdb.table_exists(table_name, schema_name)
    print("\nThe table \"{}\".\"{}\" exists? {}.".format(schema_name, table_name, res))
    # The table "public"."test_table" exists? True.

    print("")

    testdb.drop_table(table_name, verbose=True)
    # To drop the table "public"."test_table" from postgres:***@localhost:5432/testdb
    # ? [No]|Yes: yes
    # Dropping "public"."test_table" ... Done.

    print("")

    xy_array = [(530034, 180381),
                (406689, 286822),
                (383819, 398052),
                (582044, 152953)]
    dat = pd.DataFrame(xy_array, columns=['Easting', 'Northing'])

    print(dat)
    #    Easting  Northing
    # 0   530034    180381
    # 1   406689    286822
    # 2   383819    398052
    # 3   582044    152953

    print("")

    table_name = 'England'
    schema_name = 'points'

    testdb.import_data(dat, table_name, schema_name, if_exists='replace', chunk_size=None,
                       force_replace=False, col_type=None, verbose=True)
    # To import the data into table "points"."England" at postgres:***@localhost:5432/testdb
    # ? [No]|Yes: yes
    # Creating a schema: "points" ... Done.
    # Importing data into "points"."England" ... Done.

    res = testdb.table_exists(table_name, schema_name)
    print("\nThe table \"{}\".\"{}\" exists? {}.".format(schema_name, table_name, res))
    # The table "points"."England" exists? True.

    print("")

    dat_retrieval = testdb.read_table(table_name, schema_name)
    print(dat_retrieval)
    #    Easting  Northing
    # 0   530034    180381
    # 1   406689    286822
    # 2   383819    398052
    # 3   582044    152953

    print("")

    sql_query = 'SELECT * FROM "{}"."{}"'.format(schema_name, table_name)
    dat_retrieval_1 = testdb.read_sql_query(sql_query, method='tempfile')
    dat_retrieval_2 = testdb.read_sql_query(sql_query, method='stringio')

    print("The retrieved data are consistent? {}".format(dat_retrieval_1.equals(dat_retrieval_2)))
    # The retrieved data are consistent? True

    print("")

    try:
        dat_ = testdb.read_sql_query(sql_query, method='spooled')
        print("SpooledTemporaryFile works now? {}".format(dat_retrieval_1.equals(dat_)))
    except Exception as e:
        print("SpooledTemporaryFile still doesn't work? True")
        print(e)
    # SpooledTemporaryFile still doesn't work? True
    # 'SpooledTemporaryFile' object has no attribute 'readable'

    print("")

    testdb.drop_schema('points', verbose=True)
    # To drop the schema "points" from postgres:***@localhost:5432/testdb
    # ? [No]|Yes: yes
    # Dropping "points" ... Done.

    print("")

    testdb.drop_database(verbose=True)
    # To drop the database "testdb" from postgres:***@localhost:5432
    # ? [No]|Yes: yes
    # Dropping "testdb" ... Done.


if __name__ == '__main__':
    print("\nTesting 'get_db_address()':")
    test_get_db_address()

    print("\nTesting 'PostgreSQL()':")
    test_postgresql()
