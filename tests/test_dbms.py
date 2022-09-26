"""Test the module :mod:`~pyhelpers.dbms`."""

import pytest


def test_make_database_address():
    from pyhelpers.dbms import make_database_address

    db_addr = make_database_address('localhost', 5432, 'postgres', 'postgres')
    assert db_addr == 'postgres:***@localhost:5432/postgres'


def test_get_default_database_address():
    from pyhelpers.dbms import get_default_database_address, PostgreSQL

    db_addr = get_default_database_address(db_cls=PostgreSQL)
    assert db_addr == 'None:***@None:None'


if __name__ == '__main__':
    pytest.main()
