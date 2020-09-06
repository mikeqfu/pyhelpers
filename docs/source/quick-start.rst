Quick start
===========

The current release includes the following modules, with each containing a number of helper functions:

1. :ref:`settings<settings-examples>`
2. :ref:`dir<dir-examples>`
3. :ref:`ops<ops-examples>`
4. :ref:`store<store-examples>`
5. :ref:`geom<geom-examples>`
6. :ref:`text<text-examples>`
7. :ref:`sql<sql-examples>`

**This part of the documentation provides some quick examples to demonstrate what these modules may offer to assist with your data manipulation.**

For more details and examples, you can check :ref:`Modules<pyhelpers-modules>`.

|

.. _settings-examples:

**1. settings**

The :ref:`pyhelpers-settings` module can be used to alter some settings with `pandas`_, `numpy`_, `matplotlib`_ and `gdal`_. For example, the function :ref:`pd_preferences()<settings-pd-preferences>` alters a few default `pandas`_ settings (when ``reset=False``), such as representation and maximum number of columns when displaying a ``pandas.DataFrame``:

.. code-block:: python

   >>> from pyhelpers.settings import pd_preferences

   >>> pd_preferences(reset=False)

If ``reset=True``, all parameters are reset to their default values.

Note that the preset default parameters are for the module author's personal preference; you can always change them in the source code to whatever suits your own use.

|

.. _dir-examples:

**2. dir**

The :ref:`pyhelpers-dir` module can be used to help manipulate directories. For example, the function :ref:`cd()<dir-cd>` returns a full path to the current working directory:

.. code-block:: python

   >>> from pyhelpers.dir import cd

   >>> cwd = cd()
   >>> print(cwd)
   <The full path to the cwd>

If you would like to direct to a custom folder, say ``"pyhelpers_quick_start"``, use ``cd()`` to change directory:

.. code-block:: python

   >>> path_to_qs = cd("pyhelpers_quick_start")
   >>> print(path_to_qs)
   <The full path to the cwd>/pyhelpers_quick_start/

If the folder *'pyhelpers_quick_start'`* does not exist, setting ``mkdir=True`` (default: ``False``) will create it as you run the following line:

.. code-block:: python

   >>> path_to_qs = cd("pyhelpers_quick_start", mkdir=True)

To get a full path to a file, just to further provide the filename:

.. code-block:: python

   >>> path_to_pickle = cd(path_to_qs, "dat.pickle")  # equivalent to: cd("pyhelpers_quick_start", "dat.pickle")
   >>> print(path_to_pickle)
   <The full path to the cwd>\pyhelpers_quick_start\dat.pickle

If a filename (formed of a name and of a file and a suffix) is provided, setting ``mkdir=True`` will just create the parent folder rather than taking the filename as a folder name. For example:

.. _path-to-dat:

.. code-block:: python

   >>> import os

   >>> path_to_qs_data_dir = cd(path_to_qs, "data") # equivalent to: cd("pyhelpers_quick_start\\data")
   >>> res = os.path.exists(path_to_qs_data_dir)  # Check if "pyhelpers_quick_start\data\" exists
   >>> print(res)
   False

   >>> dat_filename = "dat.pickle"
   >>> path_to_dat = cd(path_to_qs_data_dir, dat_filename)
   >>> print(path_to_dat)
   <The full path to the cwd>/pyhelpers_quick_start\data\dat.pickle
   >>> res = os.path.exists(path_to_qs_data_dir)  # Check if "pyhelpers_quick_start\data\" exists
   >>> print(res)
   False

   >>> path_to_dat = cd(path_to_qs_data_dir, dat_filename, mkdir=True)
   >>> res = os.path.isfile(path_to_dat)  # Check if the file "dat.pickle" exists
   >>> print(res)
   False
   >>> res = os.path.exists(path_to_qs_data_dir)  # Check again if the directory has been created
   >>> print(res)
   True

To delete the ``path_to_qs``, you may use the function :ref:`rm_dir()<dir-rm-dir>`:

.. code-block:: python

   >>> from pyhelpers.dir import rm_dir

   >>> rm_dir(path_to_qs, verbose=True)
   To remove the directory "<The full path to the cwd>\pyhelpers_quick_start"? [No]|Yes: yes
   Done.

|

.. _ops-examples:

**3. ops**

The :ref:`pyhelpers-ops` module gathers a miscellany of helper functions.

Take for example :ref:`download_file_from_url()<ops-download-file-from-url>` (requiring `requests`_ and `tqdm`_) which is used for downloading data from a given URL. Let's import the function:

.. code-block:: python

   >>> from pyhelpers.ops import download_file_from_url

Suppose you would like to download a Python logo from the homepage of `Python`_, where the URL of the logo is as follows:

.. code-block:: python

   >>> url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'

Specify where you would like to save the .png file and what the filename it is. For example, to name the downloaded file as ``"python-logo.png"`` and save it to the directory ``"pyhelpers_quick_start\images\"``:

.. code-block:: python

   >>> python_logo_dir = cd(path_to_qs, "images", mkdir=True)
   >>> path_to_python_logo = cd(python_logo_dir, "python-logo.png")

Then use :ref:`download_file_from_url()<ops-download-file-from-url>`:

.. code-block:: python

   >>> download_file_from_url(url, path_to_python_logo)

You may view the downloaded picture by using `Pillow`_:

.. code-block:: python

   >>> from PIL import Image

   >>> python_logo = Image.open(path_to_python_logo)
   >>> python_logo.show()

If you would like to remove the download directory, ``"pyhelpers_quick_start\images\"``. you will be asked to confirm whether you want to proceed if the folder is not empty:

.. code-block:: python

   >>> rm_dir(python_logo_dir, verbose=True)
   "<The full path to the cwd>\pyhelpers_quick_start\images" is not empty. Confirmed to remove the directory? [No]|Yes: yes
   Done.

Another function, :ref:`confirmed()<ops-confirmed>`, may also be quite helpful sometimes.

.. code-block:: python

   >>> from pyhelpers.ops import confirmed

For example, if you would like to request a confirmation before proceeding with some processes (Note that you may specify the prompting message as to the confirmation by altering the value of ``prompt``):

.. code-block:: python

   >>> confirmed(prompt="Continue? ...", confirmation_required=True)
   Continue? ... [No]|Yes: yes
   True

If you type ``Yes`` (or *Y*, *yes*, or something like *ye*), it should return ``True``; otherwise, ``False`` (if the input being *No* or *n*).

By setting ``confirmation_required=False``, a confirmation is not required, in which case this function will become ineffective as it just returns ``True``.

|

.. _store-examples:

**4. store**

The :ref:`pyhelpers-store` module can be used to help save and retrieve data. Some functions require `openpyxl`_, `XlsxWriter`_ and `xlrd`_.

Before we continue, let’s create a ``pandas.DataFrame`` first:

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

If you would like to save ``dat`` as a `pickle`_ file and retrieve it later, use :ref:`save_pickle()<store-save-pickle>` and :ref:`load_pickle()<store-load-pickle>`:

.. code-block:: python

   >>> from pyhelpers.store import save_pickle, load_pickle

For example, to save ``dat`` to ``path_to_dat`` (see the :ref:`path_to_dat<path-to-dat>` in :ref:`dir<dir-examples>` above):

.. code-block:: python

   >>> save_pickle(dat, path_to_dat, verbose=True)  # default: verbose=False
   Saving "dat.pickle" to "..\pyhelpers_quick_start\data" ... Done.

To retrieve ``dat`` from ``path_to_dat``:

.. code-block:: python

   >>> dat_retrieved = load_pickle(path_to_dat, verbose=True)  # default: verbose=False
   Loading "..\pyhelpers_quick_start\data\dat.pickle" ... Done.

``dat_retrieved`` should be equal to ``dat``:

.. code-block:: python

   >>> res = dat_retrieved.equals(dat)
   >>> print(res)
   True

The :ref:`pyhelpers-store` module also have functions for working with some other formats, such as ``.csv``, ``.txt``, ``.json``, ``.xlsx``/``.xls`` and ``.feather``.

|

.. _geom-examples:

**5. geom**

The :ref:`pyhelpers-geom` module can be used to assist in manipulating geometric and geographical data.

For example, if you need to convert coordinates from OSGB36 (British national grid) to WGS84 (latitude and longitude),
use :ref:`osgb36_to_wgs84()<geom-osgb36-to-wgs84>`:

.. code-block:: python

   >>> from pyhelpers.geom import osgb36_to_wgs84

To convert a single coordinate (530034, 180381):

.. code-block:: python

   >>> xy = np.array((530034, 180381))  # London

   >>> easting, northing = xy
   >>> lonlat = osgb36_to_wgs84(easting, northing)  # osgb36_to_wgs84(xy[0], xy[1])

   >>> print(lonlat)
   (-0.12772400574286874, 51.50740692743041)

To convert an array of OSGB36 coordinates (e.g. ``xy_array``, see the :ref:`store<store-xy-array>` example above):

.. code-block:: python

   >>> eastings, northings = xy_array.T
   >>> lonlat_array = np.array(osgb36_to_wgs84(eastings, northings))

   >>> print(lonlat_array.T)
   [[-0.12772401 51.50740693]
    [-1.90294064 52.47928436]
    [-2.24527795 53.47894006]
    [ 0.60693267 51.24669501]]

Similarly, if you would like to convert coordinates from latitude/longitude (WGS84) to easting/northing (OSGB36), use :ref:`wgs84_to_osgb36()<geom-wgs84-to-osgb36>` instead.

|

.. _text-examples:

**6. text**

The :ref:`pyhelpers-text` module can be used to assist in manipulating text data.

For example, suppose you have a ``str`` type variable, named ``string``:

.. code-block:: python

   >>> string = 'ang'

If you would like to find the most similar text to one of the following ``lookup_list``, Use the function :ref:`find_similar_str()<text-find-similar-str>`:

.. code-block:: python

   >>> from pyhelpers.text import find_similar_str

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

If ``processor='fuzzywuzzy'``, it requires `fuzzywuzzy`_:

.. code-block:: python

   >>> result_1 = find_similar_str(string, lookup_list, processor='fuzzywuzzy')
   >>> print(result_1)
   Anglia

Alternatively, if ``processor='nltk'``, it requires `nltk`_:

.. code-block:: python

   >>> result_2 = find_similar_str(string, lookup_list, processor='nltk')
   >>> print(result_2)
   Anglia

|

.. _sql-examples:

**7. sql**

The :ref:`pyhelpers-sql` module provides a convenient way to establish a connection with a SQL server. The current release supports only `PostgreSQL`_.

.. code-block:: python

   >>> from pyhelpers.sql import PostgreSQL


**7.1 Connect to a database**

You can connect a PostgreSQL server by specifying *host* (default: ``'localhost'``), *port* (default: ``5432``), *username* (default: ``'postgres'``), *password* and *name of the database* (default: ``'postgres'``).

To connect to 'postgres' using all the default parameters:

.. code-block:: python

   >>> testdb = PostgreSQL(host='localhost', port=5432, username='postgres', password=None,
   ...                     database_name='postgres', verbose=True)
   Password (postgres@localhost:5432): ********
   Connecting to PostgreSQL database: postgres:***@localhost:5432/postgres ... Successfully.

When ``password=None``, you will be asked to type your password manually. Similarly, if ``host``, ``port``, ``username`` and ``database_name`` are all ``None``, you will also be asked to type the information as you run :ref:`PostgreSQL()<pyhelpers-sql>`.


**7.2 Import and dump data into the database**

After you have successfully established the connection, you could try to dump ``dat`` (see the example of :ref:`store<store-dat>` above) into a table named ``'pyhelpers_quick_start'`` at the database ``'postgres'``:

.. code-block:: python

   >>> testdb.dump_data(dat, table_name='pyhelpers_quick_start', schema_name='public',
   ...                  if_exists='replace', force_replace=False, chunk_size=None,
   ...                  col_type=None, method='multi',verbose=True)
   Dumping data to public."pyhelpers_quick_start" at postgres:***@localhost:5432/postgres ... Done.

The :ref:`.dump_data()<sql-postgresql-dump-data>` method relies on `pandas.DataFrame.to_sql`_; however, the default ``method`` is set to be ``'multi'`` (i.e. ``method='multi'``) for a faster process. In addition, :ref:`.dump_data()<sql-postgresql-dump-data>` further includes a callable :ref:`psql_insert_copy<sql-postgresql-psql-insert-copy>`, whereby the processing speed could be even faster.

For example:

.. code-block:: python

   >>> testdb.dump_data(dat, table_name='pyhelpers_quick_start', method=testdb.psql_insert_copy,
   ...                  verbose=True)
   The table public."pyhelpers_quick_start" already exists and is replaced ...
   Dumping data to public."pyhelpers_quick_start" at postgres:***@localhost:5432/postgres ... Done.

**7.3 Read/retrieve data from the database**

To retrieve the dumped data, use the method :ref:`.read_table()<sql-postgresql-read-table>`:

.. code-block:: python

   >>> dat_retrieved = testdb.read_table('pyhelpers_quick_start')

   >>> res = dat.equals(dat_retrieved)
   >>> print(res)
   True

Besides, there is an alternative way, :ref:`.read_sql_query()<sql-postgresql-read-sql-query>`, which is more flexible with PostgreSQL statement (and could be faster especially when the tabular data is fairly large):

.. code-block:: python

   >>> sql_query = 'SELECT * FROM pyhelpers_quick_start'  # Or 'SELECT * FROM public.test_table'
   >>> dat_retrieved_ = testdb.read_sql_query(sql_query)

   >>> res = dat_retrieved_.equals(dat_retrieved)
   >>> print(res)
   True

Note that ``sql_query`` should end without **';'**


**7.4 Some other methods**

To drop ``'pyhelpers_quick_start'``, if ``confirmation_required=True`` (default: ``False``), you will be asked to confirm whether you are sure to drop the table:

.. code-block:: python

   >>> testdb.drop_table('pyhelpers_quick_start', schema_name='public', confirmation_required=True,
   ...                   verbose=True)
   Confirmed to drop the table public."pyhelpers_quick_start" from postgres:***@localhost:5432/postgres? [No]|Yes: yes
   The table 'public."pyhelpers_quick_start"' has been dropped successfully.

To create your own database and name it as ``'test_database'``:

.. code-block:: python

   >>> testdb.create_database('test_database', verbose=True)
   Creating a database "test_database" ... Done.

To check if the database has been successfully created:

.. code-block:: python

   >>> testdb.database_exists('test_database')
   True

   >>> print(testdb.database_name)
   test_database

To drop the database, use the method :ref:`.drop_database()<sql-postgresql-drop-database>`. Again, it is recommended to always set ``confirmation_required=True`` (default), which would ask for confirmation as to whether to proceed:

.. code-block:: python

   >>> testdb.drop_database(confirmation_required=True, verbose=True)
   Confirmed to drop the database: postgres:***@localhost:5432/postgres? [No]|Yes: yes
   Dropping the database "test_database" ... Done.

   >>> print(testdb.database_name)  # Check the currently connected database
   postgres


.. _`Python`: https://www.python.org/
.. _`numpy`: https://numpy.org/
.. _`pandas`: https://pandas.pydata.org/
.. _`matplotlib`: https://matplotlib.org/
.. _`gdal`: https://pypi.org/project/GDAL/
.. _`requests`: https://2.python-requests.org/en/master/
.. _`tqdm`: https://pypi.org/project/tqdm/
.. _`Pillow`: https://pypi.org/project/Pillow/
.. _`openpyxl`: https://openpyxl.readthedocs.io/en/stable/
.. _`XlsxWriter`: https://xlsxwriter.readthedocs.io
.. _`xlrd`: https://xlrd.readthedocs.io/en/latest/
.. _`pickle`: https://docs.python.org/3/library/pickle.html
.. _`fuzzywuzzy`: https://github.com/seatgeek/fuzzywuzzy/
.. _`nltk`: https://www.nltk.org/
.. _`PostgreSQL`: https://www.postgresql.org/
.. _`pandas.DataFrame.to_sql`: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html
