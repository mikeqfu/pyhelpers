import numpy as np
import pandas as pd

from pyhelpers.sql import PostgreSQL

# Use the example data frame from test_store.py
xy_array = np.array([(530034, 180381),   # London
                     (406689, 286822),   # Birmingham
                     (383819, 398052),   # Manchester
                     (582044, 152953)],  # Leeds
                    dtype=np.int64)
dat = pd.DataFrame(xy_array, columns=['Easting', 'Northing'])

# Connect database
test_db = PostgreSQL(host='localhost', port=5432, username='postgres', password=None, database_name='postgres')

# Import data
test_db.dump_data(dat, table_name='test_table', schema_name='public', if_exists='replace', chunk_size=None,
                  force_replace=False, col_type=None, verbose=True)

# Retrieve the dumped data
dat_retrieved = test_db.read_table('test_table')
dat.equals(dat_retrieved)

# Drop the table
test_db.drop_table('test_table', confirmation_required=True, verbose=True)

####

test_db.db_exists("test_database")

test_db.create_db("test_database", verbose=True)

test_db.drop(confirmation_required=True, verbose=True)
