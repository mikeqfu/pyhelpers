"""Test the module :mod:`~pyhelpers.dbms`."""

import pytest

from pyhelpers.dbms import PostgreSQL
from pyhelpers.dbms.utils import *


def test_make_database_address():
    db_addr = make_database_address('localhost', 5432, 'postgres', 'postgres')
    assert db_addr == 'postgres:***@localhost:5432/postgres'


def test_get_default_database_address():
    db_addr = get_default_database_address(db_cls=PostgreSQL)
    assert db_addr == 'None:***@None:None'


def test_add_sql_query_condition():
    query = 'SELECT * FROM a_table'

    query_ = add_sql_query_condition(query)
    assert query_ == 'SELECT * FROM a_table'
    query_ = add_sql_query_condition(query, COL_NAME_1='A')
    assert query_ == 'SELECT * FROM a_table WHERE "COL_NAME_1"=\'A\''
    query_ = add_sql_query_condition(query, COL_NAME_1='A', COL_NAME_2=['B', 'C'])
    assert query_ == 'SELECT * FROM a_table WHERE "COL_NAME_1"=\'A\' AND "COL_NAME_2" IN (\'B\', \'C\')'
    query_ = add_sql_query_condition(query, COL_NAME_1='A', add_table_name='t1')
    assert query_ == 'SELECT * FROM a_table WHERE t1."COL_NAME_1"=\'A\''


if __name__ == '__main__':
    pytest.main()
