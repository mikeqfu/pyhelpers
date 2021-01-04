===========
Quick start
===========

The current release includes the following modules, with each containing a number of helper functions:

.. py:module:: pyhelpers
    :noindex:

.. autosummary::

    settings
    dir
    ops
    store
    geom
    text
    sql

This part of the documentation provides a quick tutorial with **a couple of examples for each module** to demonstrate what the package may offer to assist with our data manipulation.


.. _settings-examples:

Change settings of working environment
======================================

The module :ref:`pyhelpers.settings<settings>` can be used to alter settings with `pandas`_, `numpy`_, `matplotlib`_ and `GDAL`_ for our working environment. For example, the function :py:func:`pd_preferences()<pyhelpers.settings.pd_preferences>` alters a few default `pandas`_ settings (given ``reset=False``), such as representation and maximum number of columns when displaying a `pandas.DataFrame`_:

.. code-block:: python

    >>> from pyhelpers.settings import pd_preferences
    >>> # Or simply,
    >>> # from pyhelpers import pd_preferences

    >>> pd_preferences(reset=False)

When ``reset=True``, all parameters are reset to their default values.

.. note::

    The preset parameters included in the functions of the module :ref:`pyhelpers.settings<settings>` are only a few of all that are available and for the module author's personal preference. To suit individual tastes, we may have to try to change them in the source code.


.. _dir-examples:

Specify directory/file paths
============================

The module :ref:`pyhelpers.dir<dir>` can be used to help change/manipulate directories. For example, the function :py:func:`cd()<pyhelpers.dir.cd>` returns an absolute path to the current working directory (and, optionally, its any of its sub-directories / files):

.. code-block:: python

    >>> from pyhelpers.dir import cd
    >>> # Or simply,
    >>> # from pyhelpers import cd

    >>> cwd = cd()
    >>> print(cwd)
    <An absolute path to the current working directory (cwd)>

To direct to a custom folder, say ``"pyhelpers_quick_start"``:

.. code-block:: python

    >>> path_to_qs = cd("pyhelpers_quick_start")

    >>> import os

    >>> print(os.path.relpath(path_to_qs))
    pyhelpers_quick_start

In the case the the folder ``'pyhelpers_quick_start'`` does not exist, we could set the parameter ``mkdir`` (which defaults to ``False``) to be ``True``; the folder will be created:

.. code-block:: python

    >>> path_to_qs = cd("pyhelpers_quick_start", mkdir=True)

    >>> print("The directory \"{}\" exists? {}".format(
    ...     os.path.relpath(path_to_qs), os.path.isdir(path_to_qs)))
    he directory "pyhelpers_quick_start" exists? True.

If we provide a filename (formed of a name and of a file and a file extension), we can get an absolute path to the file as well. For example:

.. code-block:: python

    >>> path_to_pickle = cd(path_to_qs, "dat.pickle")
    >>> # equivalent to: cd("pyhelpers_quick_start", "dat.pickle")

    >>> print(os.path.relpath(path_to_pickle))
    pyhelpers_quick_start\dat.pickle

When a filename is provided and ``mkdir=True``, the function will just create the parent folder (if it does not exist) rather than taking the filename as a folder name. For example:

.. _path-to-dat:

.. code-block:: python

    >>> path_to_qs_data_dir = cd(path_to_qs, "data")

    >>> print("The directory \"{}\" exists? {}".format(
    ...     os.path.relpath(path_to_qs_data_dir), os.path.exists(path_to_qs_data_dir)))
    he directory "pyhelpers_quick_start\data" exists? False

    >>> dat_filename = "dat.pickle"

    >>> path_to_dat = cd(path_to_qs_data_dir, dat_filename)

    >>> print(os.path.relpath(path_to_dat))
    pyhelpers_quick_start\data\dat.pickle

    >>> print("The directory \"{}\" exists? {}".format(
    ...     os.path.relpath(path_to_qs_data_dir), os.path.exists(path_to_qs_data_dir)))
    The directory "pyhelpers_quick_start\data" exists? False

    >>> path_to_dat = cd(path_to_qs_data_dir, dat_filename, mkdir=True)

    >>> print("The directory \"{}\" exists? {}".format(
    ...     os.path.relpath(path_to_qs_data_dir), os.path.exists(path_to_qs_data_dir)))
    The directory "pyhelpers_quick_start\data" exists? True

To delete the directory of ``"pyhelpers_quick_start"``, we may use the function :py:func:`delete_dir()<pyhelpers.dir.delete_dir>`:

.. code-block:: python

    >>> from pyhelpers.dir import delete_dir
    >>> # Or simply,
    >>> # from pyhelpers import delete_dir

    >>> delete_dir(path_to_qs, verbose=True)
    The directory "\pyhelpers_quick_start" is not empty.
    Confirmed to delete it? [No]|Yes: yes
    Deleting "\pyhelpers_quick_start" ... Done.


.. _ops-examples:

Download an image file
======================

The module :ref:`pyhelpers.ops<ops>` is intended to provide a miscellany of helper functions.

.. code-block:: python

    >>> from pyhelpers.ops import download_file_from_url
    >>> # Or simply,
    >>> # from pyhelpers import download_file_from_url

For example, we can use the function :py:func:`download_file_from_url()<pyhelpers.ops.download_file_from_url>` to download files from a given URL.

.. note::

    :py:func:`download_file_from_url()<pyhelpers.ops.download_file_from_url>` depends on `requests`_ and `tqdm`_, which are not required for installation of PyHelpers. If any of the dependencies is currently not on our system, we need to install it before we proceed.

If we would like to download a Python logo from the homepage of `Python`_, where the URL of the logo is:

.. code-block:: python

    >>> url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'

Then specify where you would like to save the .png file and what the filename it is. For example, to name the downloaded file as ``"python-logo.png"`` and save it to the directory ``"\pyhelpers_quick_start\images\"``:

.. code-block:: python

    >>> python_logo_dir = cd(path_to_qs, "images", mkdir=True)
    >>> path_to_python_logo = cd(python_logo_dir, "python-logo.png")

    >>> download_file_from_url(url, path_to_python_logo)

We may view the downloaded picture by using `Pillow`_:

.. code-block:: python

    >>> from PIL import Image

    >>> python_logo = Image.open(path_to_python_logo)
    >>> python_logo.show()

Again, if we would like to delete the download directory, ``"pyhelpers_quick_start\images\"``, use the function :py:func:`delete_dir()<pyhelpers.dir.delete_dir>`:

.. code-block:: python

    >>> delete_dir(python_logo_dir, verbose=True)
    The directory "\pyhelpers_quick_start\images" is not empty.
    Confirmed to delete it? [No]|Yes: yes
    Deleting "\pyhelpers_quick_start\images" ... Done.

For another example, the function :py:func:`confirmed()<pyhelpers.ops.confirmed>` may also be quite helpful sometimes, especially when we would like to request a confirmation before proceeding with some processes.

.. code-block:: python

    >>> from pyhelpers.ops import confirmed
    >>> # Or simply,
    >>> # from pyhelpers import confirmed

.. code-block:: python

    >>> confirmed(prompt="Continue? ...", confirmation_required=True)
    Continue? ... [No]|Yes: yes
    True

.. note::

    - We may specify the prompting message as to the confirmation by altering the value of ``prompt``.

    - If we type ``Yes`` (or ``Y``, ``yes``, or something like ``ye``), it should return ``True``; otherwise, ``False`` (if the input being *No* or *n*).

    - By setting ``confirmation_required=False``, a confirmation is not required, in which case this function will become ineffective as it just returns ``True``.


.. _store-examples:

Save and load data with Pickle
==============================

The module :ref:`pyhelpers.store<store>` can be used to help save and load data. Some functions require `openpyxl`_, `XlsxWriter`_ and `xlrd`_.

Before we continue, let’s create a `pandas.DataFrame`_ first:

.. _store-xy-array:
.. _store-dat:

.. code-block:: python

    >>> import numpy as np
    >>> import pandas as pd

    >>> xy_array = np.array([(530034, 180381),   # London
    ...                      (406689, 286822),   # Birmingham
    ...                      (383819, 398052),   # Manchester
    ...                      (582044, 152953)],  # Leeds
    ...                     dtype=np.int64)

    >>> dat = pd.DataFrame(xy_array, columns=['Easting', 'Northing'])

    >>> print(dat)
       Easting  Northing
    0   530034    180381
    1   406689    286822
    2   383819    398052
    3   582044    152953

If we would like to save ``dat`` as a `pickle`_ file and retrieve it later, use the functions :py:func:`save_pickle()<pyhelpers.store.save_pickle>` and :py:func:`load_pickle()<pyhelpers.store.load_pickle>`:

.. code-block:: python

    >>> from pyhelpers.store import save_pickle, load_pickle
    >>> # Or simply,
    >>> # from pyhelpers import save_pickle, load_pickle

For example, to save ``dat`` to ``path_to_dat`` (see the :ref:`path_to_dat<path-to-dat>` in :ref:`dir<dir-examples>` above):

.. code-block:: python

    >>> save_pickle(dat, path_to_dat, verbose=True)
    Saving "dat.pickle" to "\pyhelpers_quick_start\data" ... Done.

To retrieve ``dat`` from ``path_to_dat``:

.. code-block:: python

    >>> dat_retrieved = load_pickle(path_to_dat, verbose=True)
    Loading "\pyhelpers_quick_start\data\dat.pickle" ... Done.

``dat_retrieved`` should be equal to ``dat``:

.. code-block:: python

    >>> print("`dat_retrieved` is equal to `dat`? {}".format(dat_retrieved.equals(dat)))
    `dat_retrieved` is equal to `dat`? True

The :ref:`pyhelpers.store<store>` module also have functions for saving/loading data of some other formats, such as ``.csv``, ``.txt``, ``.json``, ``.xlsx`` (or ``.xls``) and ``.feather``.

Now, before we move on, we can delete the directory *'pyhelpers_quick_start'* (i.e. ``path_to_qs``) to clear up the mess we've produced so far:

.. code-block:: python

    >>> delete_dir(path_to_qs, verbose=True)
    The directory "\pyhelpers_quick_start" is not empty.
    Confirmed to delete it? [No]|Yes: yes
    Deleting "\pyhelpers_quick_start" ... Done.


.. _geom-examples:

Convert coordinates between OSGB36 and WGS84
============================================

The module :ref:`pyhelpers.geom<geom>` can be used to assist in manipulating geometric and geographical data.

For example, to convert coordinates from OSGB36 (British national grid) to WGS84 (latitude and longitude), we can use :py:func:`osgb36_to_wgs84()<pyhelpers.geom.osgb36_to_wgs84>`:

.. note::

    :py:func:`osgb36_to_wgs84()<pyhelpers.geom.osgb36_to_wgs84>` depends on `pyproj`_, which is not required for installing PyHelpers. If the dependency is currently not on our system, we need to install it before we proceed.

.. code-block:: python

    >>> from pyhelpers.geom import osgb36_to_wgs84
    >>> # Or simply,
    >>> # from pyhelpers import osgb36_to_wgs84

To convert coordinate of a single point ``(530034, 180381)``:

.. code-block:: python

    >>> xy = np.array((530034, 180381))  # London

    >>> easting, northing = xy
    >>> longlat = osgb36_to_wgs84(easting, northing)

    >>> print(longlat)
    (-0.12772400574286874, 51.50740692743041)

To convert an array of OSGB36 coordinates (e.g. ``xy_array``, see the example for :ref:`pyhelpers.store<store-xy-array>` above):

.. code-block:: python

    >>> eastings, northings = xy_array.T
    >>> longlat_array = np.array(osgb36_to_wgs84(eastings, northings))

    >>> print(longlat_array.T)
    [[-0.12772401 51.50740693]
     [-1.90294064 52.47928436]
     [-2.24527795 53.47894006]
     [ 0.60693267 51.24669501]]

Similarly, if we can use the function :py:func:`wgs84_to_osgb36()<pyhelpers.geom.wgs84_to_osgb36>` to convert coordinates from latitude/longitude (WGS84) back to easting/northing (OSGB36).


.. _text-examples:

Find similar texts
==================

The module :ref:`pyhelpers.text<text>` can be used to assist in manipulating textual data.

For example, suppose we have a ``str`` type variable ``string``:

.. code-block:: python

    >>> string = 'ang'

If we would like to find one, from the ``lookup_list`` below, that is the most similar text to ``string``, we can try the function :py:func:`find_similar_str()<pyhelpers.text.find_similar_str>`:

.. code-block:: python

    >>> from pyhelpers.text import find_similar_str
    >>> # Or simply,
    >>> # from pyhelpers import find_similar_str

    >>> lookup_list = ['Anglia',
    ...                'East Coast',
    ...                'East Midlands',
    ...                'North and East',
    ...                'London North Western',
    ...                'Scotland',
    ...                'South East',
    ...                'Wales',
    ...                'Wessex',
    ...                'Western']

The parameter ``processor`` for the function is by default ``'fuzzywuzzy'``, meaning that it would rely on the Python package `FuzzyWuzzy`_:

.. note::

    `FuzzyWuzzy`_ is not required for installation of PyHelpers. If it is currently not on our system, we need to install it before we proceed.

.. code-block:: python

    >>> result_1 = find_similar_str(string, lookup_list, processor='fuzzywuzzy')
    >>> print(result_1)
    Anglia

Alternatively, we could also turn to another Python library `NLTK`_ by setting ``processor`` to be ``'nltk'``:

.. note::

    `NLTK`_ is also excluded from the installation requirement of PyHelpers. Again, if it is not available yet on our system, we need to install it to run the following code.

.. code-block:: python

    >>> result_2 = find_similar_str(string, lookup_list, processor='nltk')
    >>> print(result_2)
    Anglia


.. _sql-examples:

Work with PostgreSQL database
=============================

The module :ref:`pyhelpers.sql<sql>` provides a convenient way to establish a connection with a SQL database. The current release of PyHelpers contains only :py:class:`PostgreSQL<pyhelpers.sql.PostgreSQL>` that allows us to implement some basic queries in a `PostgreSQL`_ database.

.. code-block:: python

    >>> from pyhelpers.sql import PostgreSQL
    >>> # Or simply,
    >>> # from pyhelpers import PostgreSQL

.. note::

    The constructor method of :py:class:`PostgreSQL<pyhelpers.sql.PostgreSQL>` depends on `SQLAlchemy`_, `SQLAlchemy-Utils`_ and `psycopg2`_, which are not required for the installation of PyHelpers. To successfully create an instance of the class, we need make sure all of the three dependencies are installed on our system before we proceed.

Connect to a database
---------------------

We can now connect a PostgreSQL server by specifying the parameters: ``host``, ``port``, ``username``, ``password`` and ``database_name``.

For example, to connect to a database named *'testdb'*:

.. code-block:: python

    >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres', password=None,
    ...                     database_name='testdb')
    Password (postgres@localhost:5432): ***
    Connecting postgres:***@localhost:5432/testdb ... Successfully.

.. note::

    - As ``password`` is ``None`` above, we will be asked to type in the password manually.

    - Similarly, if any of the other parameters is also ``None``, you will also be asked to type in the information.

    - If the database *'testdb'* does not exist, it will be created as we create the instance ``testdb``.

To create another database ``'test_database'``:

.. code-block:: python

    >>> testdb.create_database('test_database', verbose=True)
    Creating a database: "test_database" ... Done.

To check if the database has been successfully created:

.. code-block:: python

    >>> testdb.database_exists('test_database')
    True

    >>> print(testdb.database_name)
    test_database

.. note::

    After we create a new database, the instance ``testdb`` is now connected with the new database *'test_database'*.

If we would like to connect back to *'testdb'*:

.. code-block:: python

    >>> testdb.connect_database('testdb', verbose=True)
    Connecting postgres:***@localhost:5432/testdb ... Successfully.


Import data into the database
-----------------------------

After we have established the connection, we can use the method :py:meth:`.import_data()<pyhelpers.sql.PostgreSQL.import_data>` to import ``dat`` (see the example for :ref:`pyhelpers.store<store-dat>` above) into a table named *'pyhelpers_quick_start'*:

.. code-block:: python

    >>> testdb.import_data(dat, table_name='pyhelpers_quick_start', verbose=True)
    To import the data into table "public"."pyhelpers_quick_start" at postgres:***@localhost:5432/testdb
    ? [No]|Yes: yes
    Importing data into "public"."pyhelpers_quick_start" ... Done.

The method :py:meth:`.import_data()<pyhelpers.sql.PostgreSQL.import_data>` relies on `pandas.DataFrame.to_sql`_, with the parameter ``'method'`` is set to be ``'multi'`` by default. However, it can also take a callable :py:meth:`.psql_insert_copy()<pyhelpers.sql.PostgreSQL.psql_insert_copy>` as an an alternative ``'method'`` to significantly speed up importing data into the database:

.. code-block:: python

    >>> testdb.import_data(dat, table_name='pyhelpers_quick_start', method=testdb.psql_insert_copy,
    ...                    verbose=True)
    To import the data into table "public"."pyhelpers_quick_start" at postgres:***@localhost:5432/testdb
    ? [No]|Yes: yes
    The table "public"."pyhelpers_quick_start" already exists and is replaced ...
    Importing data into "public"."pyhelpers_quick_start" ... Done.


Fetch data from the database
----------------------------

To retrieve the imported data, we can use the method :py:meth:`.read_table()<pyhelpers.sql.PostgreSQL.read_table>`:

.. code-block:: python

    >>> dat_retrieval = testdb.read_table('pyhelpers_quick_start')

    >>> print("`dat_retrieval` is equal to `dat`? {}".format(dat_retrieval.equals(dat)))
    `dat_retrieval` is equal to `dat`? True

Besides, the method :py:meth:`.read_sql_query()<pyhelpers.sql.PostgreSQL.read_sql_query>` could be more flexible in reading/querying data by PostgreSQL statement (and could be much faster especially when the tabular data is fairly large):

.. code-block:: python

    >>> sql_query = 'SELECT * FROM public.pyhelpers_quick_start'
    >>> dat_retrieval_ = testdb.read_sql_query(sql_query)

    >>> print("`dat_retrieval_` is equal to `dat`? {}".format(dat_retrieval_.equals(dat)))
    `dat_retrieval_` is equal to `dat`? True

.. note::

    ``sql_query`` should end without ``';'``.


Drop data
---------

To drop ``'pyhelpers_quick_start'``, we can use the method :py:meth:`.drop_table()<pyhelpers.sql.PostgreSQL.drop_table>`:

.. code-block:: python

    >>> testdb.drop_table('pyhelpers_quick_start', verbose=True)
    To drop the table "public"."pyhelpers_quick_start" from postgres:***@localhost:5432/testdb
    ? [No]|Yes: yes
    Dropping "public"."pyhelpers_quick_start" ... Done.

Note that we have created two databases: *'testdb'* (currently being connected) and *'test_database'*. To drop both of them, we can use the method :py:meth:`.drop_database()<pyhelpers.sql.PostgreSQL.drop_database>`.

.. code-block:: python

    >>> # Drop 'testdb'
    >>> testdb.drop_database(verbose=True)
    To drop the database "testdb" from postgres:***@localhost:5432
    ? [No]|Yes: yes
    Dropping "testdb" ... Done.

    >>> print(testdb.database_name)  # Check the currently connected database
    postgres

    >>> # Drop 'test_database'
    >>> testdb.drop_database('test_database', verbose=True)
    To drop the database "test_database" from postgres:***@localhost:5432/postgres
    ? [No]|Yes: yes
    Dropping "test_database" ... Done.


.. _`Python`: https://www.python.org/
.. _`numpy`: https://numpy.org/
.. _`pandas`: https://pandas.pydata.org/
.. _`pandas.DataFrame`: https://pandas.pydata.org/pandas-docs/stable/user_guide/dsintro.html#dataframe
.. _`matplotlib`: https://matplotlib.org/
.. _`GDAL`: https://gdal.org/
.. _`requests`: https://github.com/psf/requests
.. _`tqdm`: https://github.com/tqdm/tqdm
.. _`Pillow`: https://python-pillow.org/
.. _`openpyxl`: https://openpyxl.readthedocs.io/en/stable/
.. _`XlsxWriter`: https://xlsxwriter.readthedocs.io
.. _`xlrd`: https://xlrd.readthedocs.io/en/latest/
.. _`pickle`: https://docs.python.org/3/library/pickle.html
.. _`pyproj`: https://github.com/pyproj4/pyproj
.. _`FuzzyWuzzy`: https://github.com/seatgeek/fuzzywuzzy/
.. _`NLTK`: https://www.nltk.org/
.. _`PostgreSQL`: https://www.postgresql.org/
.. _`SQLAlchemy`: https://www.sqlalchemy.org/
.. _`SQLAlchemy-Utils`: https://github.com/kvesteri/sqlalchemy-utils
.. _`psycopg2`: https://www.psycopg.org/
.. _`pandas.DataFrame.to_sql`: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html

|

**(The end of the quick start)**

For more details and examples, check :ref:`Modules<modules>`.
