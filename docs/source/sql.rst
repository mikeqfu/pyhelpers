.. _pyhelpers-sql:

sql
---

.. module:: pyhelpers.sql

A module for manipulation of databases.

*(The current release includes PostgreSQL only.)*

.. autosummary::

   PostgreSQL

PostgreSQL
**********

.. autoclass:: pyhelpers.sql.PostgreSQL

   .. automethod:: database_exists

   .. automethod:: connect_database

   .. automethod:: create_database

   .. automethod:: get_database_size

   .. automethod:: disconnect_database

   .. automethod:: disconnect_all_other_databases

   .. _sql-postgresql-drop-database:

   .. automethod:: drop_database

   .. automethod:: schema_exists

   .. automethod:: create_schema

   .. automethod:: printing_messages_for_multi_names

   .. automethod:: drop_schema

   .. automethod:: table_exists

   .. automethod:: create_table

   .. automethod:: get_column_info

   .. automethod:: drop_table

   .. _sql-postgresql-psql-insert-copy:

   .. automethod:: psql_insert_copy

   .. _sql-postgresql-dump-data:

   .. automethod:: dump_data

   .. _sql-postgresql-read-table:

   .. automethod:: read_table

   .. _sql-postgresql-read-sql-query:

   .. automethod:: read_sql_query
