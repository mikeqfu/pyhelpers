from pyhelpers.sql import *


def test_postgresql():
    testdb = PostgreSQL(host='localhost', port=5432, username='postgres', database_name='postgres')
    # Password (postgres@localhost:5432):
    # Connecting to PostgreSQL database: postgres:***@localhost:5432/postgres ... Successfully.

    table_name = 'England'
    schema_name = 'points'

    res = testdb.table_exists(table_name, schema_name)
    print("\nThe table '{}.{}' exists? {}.".format(schema_name, table_name, res))
    # False  # (if 'points.England' does not exist)

    print("")

    table_name = 'test_table'
    schema_name = 'public'
    column_specs = 'col_name_1 INT, col_name_2 TEXT'

    testdb.create_table(table_name, column_specs, schema_name, verbose=True)
    # Creating a table 'public."test_table"' ... Done.

    res = testdb.table_exists(table_name, schema_name)
    print("\nThe table '{}.{}' exists? {}.".format(schema_name, table_name, res))
    # The table 'public.test_table' exists? True.

    print("")
    testdb.drop_table(table_name, verbose=True)
    # Confirmed to drop the table public."test_table" from postgres:***@localhost:5432/postgres? [No]|Yes: yes
    # The table 'public."test_table"' has been dropped successfully.

    print("")

    xy_array = [(530034, 180381), (406689, 286822), (383819, 398052), (582044, 152953)]
    dat = pd.DataFrame(xy_array, columns=['Easting', 'Northing'])

    table_name = 'England'
    schema_name = 'points'

    testdb.dump_data(dat, table_name, schema_name, if_exists='replace', chunk_size=None,
                     force_replace=False, col_type=None, verbose=True)
    # Creating a schema "points" ... Done.
    # Dumping data to points."England" at postgres:***@localhost:5432/postgres ... Done.

    res = testdb.table_exists(table_name, schema_name)
    print("\nThe table '{}.{}' exists? {}.".format(schema_name, table_name, res))
    # True

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
    # Confirmed to drop the schema "points" from postgres:***@localhost:5432/postgres? [No]|Yes: yes
    # Dropping the schema "points" ... Done.


if __name__ == '__main__':
    print("\nTesting 'sql.PostgreSQL()':")

    test_postgresql()
