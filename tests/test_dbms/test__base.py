"""
Test the :mod:`~pyhelpers.dbms._base` submodule.
"""

import pytest

from pyhelpers.dbms._base import _Base


class TestBase:
    """
    Test suite for the internal base database manager class.
    """

    # noinspection PyNestedDecorators
    @pytest.fixture(scope='class')
    @classmethod
    def b(cls):
        """
        Class fixture providing a base database manager instance.

        :return: An uninitialised base database manager instance.
        :rtype: pyhelpers.dbms._base._Base
        """

        return _Base()

    @staticmethod
    def test_pass(b):
        """
        Verify placeholder callability of base methods without connection.

        :param b: The base database fixture.
        :type b: pyhelpers.dbms._base._Base
        """

        b.database_exists(database_name='')
        b.connect_database(database_name='')
        b.disconnect_database()

        b.create_schema(schema_name='')
        b.schema_exists(schema_name='')

        b.table_exists(table_name='', schema_name='')

        b.drop_table(table_name='', schema_name='')

        b.read_sql_query(sql_query='')


if __name__ == '__main__':
    pytest.main()
