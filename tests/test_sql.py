"""
Test module sql.py
"""

from pyhelpers.sql import *


def test_postgresql():
    testdb = PostgreSQL(host='localhost', port=5432, username='postgres',
                        database_name='testdb')
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
    # Creating a table '"public"."test_table"' ... Done.

    res = testdb.table_exists(table_name, schema_name)
    print("\nThe table '{}.{}' exists? {}.".format(schema_name, table_name, res))
    # The table 'public.test_table' exists? True.

    print("")
    testdb.drop_table(table_name, verbose=True)
    # Confirmed to drop '"public"."test_table"'
    # 	from postgres:***@localhost:5432/testdb?
    #   [No]|Yes: >? yes
    # Dropping '"public"."test_table"' ... Done.

    print("")

    xy_array = [(530034, 180381), (406689, 286822), (383819, 398052), (582044, 152953)]
    dat = pd.DataFrame(xy_array, columns=['Easting', 'Northing'])

    table_name = 'England'
    schema_name = 'points'

    testdb.import_data(dat, table_name, schema_name, if_exists='replace', chunk_size=None,
                       force_replace=False, col_type=None, verbose=True)
    # Creating a schema "points" ... Done.
    # Dumping data to "points"."England"
    # 	at postgres:***@localhost:5432/testdb ...
    # 	Done.

    res = testdb.table_exists(table_name, schema_name)
    print("\nThe table '{}.{}' exists? {}.".format(schema_name, table_name, res))
    # The table 'points.England' exists? True.

    print("")

    dat_retrieval = testdb.read_table(table_name, schema_name)
    print(dat_retrieval)
    #    Easting  Northing
    # 0   530034    180381
    # 1   406689    286822
    # 2   383819    398052
    # 3   582044    152953

    print("")

    testdb.drop_schema('points', verbose=True)
    # Confirmed to drop the following schema:
    # 	"points"
    #   from postgres:***@localhost:5432/testdb?
    #   [No]|Yes: >? yes
    # Dropping ...
    # 	"points" ... Done.

    testdb.drop_database(verbose=True)
    # Confirmed to drop the database "testdb"
    # 	from postgres:***@localhost:5432/testdb?
    #   [No]|Yes: >? yes
    # Dropping the database "testdb" ... Done.


if __name__ == '__main__':
    print("\nTesting 'sql.PostgreSQL()':")

    test_postgresql()
