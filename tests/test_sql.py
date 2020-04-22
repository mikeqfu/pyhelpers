import time

import numpy as np
import pandas as pd

from pyhelpers.settings import pd_preferences
from pyhelpers.sql import PostgreSQL

pd_preferences()

# Use the example data frame from test_store.py
xy_array = np.array([(530034, 180381),   # London
                     (406689, 286822),   # Birmingham
                     (383819, 398052),   # Manchester
                     (582044, 152953)],  # Leeds
                    dtype=np.int64)
dat = pd.DataFrame(xy_array, columns=['Easting', 'Northing'])

# Connect database
testdb = PostgreSQL(host='localhost', port=5432, username='postgres', password=None, database_name='postgres')

table_name = 'England'
schema_name = 'points'

testdb.table_exists(table_name, schema_name)

dat.to_sql(table_name, testdb.engine, schema_name, if_exists='append', index=False, method=testdb.psql_insert_copy)

testdb.table_exists(table_name, schema_name)

dat_retrieval = testdb.read_sql_query('SELECT * FROM {}."{}"'.format(schema_name, table_name))
dat_retrieval.equals(dat)

testdb.drop_schema(schema_name)

# Import data
testdb.dump_data(dat, table_name, schema_name, if_exists='replace', chunk_size=None, force_replace=False,
                 col_type=None, verbose=True)

# Retrieve the dumped data
dat_retrieval = testdb.read_table(table_name, schema_name)
dat_retrieval.equals(dat)

# Drop the table
testdb.drop_table(table_name, schema_name, confirmation_required=False, verbose=True)
testdb.schema_exists(schema_name)
testdb.drop_schema(schema_name)

####

testdb.database_exists('test_database')  # Check if a database exists

# Create a new database
testdb.create_database('test_database', verbose=True)

# Connect another database '123FuQ456WhoAMI'
testdb_ = PostgreSQL('147.188.146.15', 5432, 'fuq', password=None, database_name='OSM_Geofabrik')

start1 = time.time()
dat_1 = testdb_.read_sql_query('SELECT * FROM points."Greater London"', low_memory=False)
print(time.time() - start1)

start2 = time.time()
dat_2 = testdb_.read_table(table_name='Greater London', schema_name='points')
print(time.time() - start2)

###

start1 = time.time()
testdb.dump_data(dat_1, table_name, schema_name, if_exists='replace', method=None)
print(time.time() - start1)

start2 = time.time()
testdb.dump_data(dat_1, table_name, schema_name, if_exists='replace', method='multi')
print(time.time() - start2)

start3 = time.time()
testdb.dump_data(dat_1, table_name, schema_name, if_exists='replace', method=testdb.psql_insert_copy)
print(time.time() - start3)

len(testdb.read_sql_query('SELECT * FROM {}."{}"'.format(schema_name, table_name), low_memory=False))

# Drop the newly created database: 'test_database'
testdb.drop_database(confirmation_required=True, verbose=True)
