# pyhelpers
**Author**: Qian Fu [![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/Qian_Fu?label=Follow&style=social)](https://twitter.com/Qian_Fu)

[![PyPI](https://img.shields.io/pypi/v/pyhelpers?color=important&label=PyPI)](https://pypi.org/project/pyhelpers/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyhelpers?label=Python)](https://www.python.org/downloads/windows/)
[![GitHub](https://img.shields.io/github/license/mikeqfu/pyhelpers?color=green&label=License)](https://github.com/mikeqfu/pyhelpers/blob/master/LICENSE)
[![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/mikeqfu/pyhelpers?color=yellowgreen&label=Code%20size)](https://github.com/mikeqfu/pyhelpers/tree/master/pyhelpers)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pyhelpers?color=yellow&label=Downloads)](https://pypistats.org/packages/pyhelpers)

A toolkit of helper functions to facilitate data manipulation. 



------

**<span style="font-size:larger;">Contents</span>**

- [Installation](#installation)
- [Quick start - some examples](#quick-start)

------



## Installation <a name="installation"></a>

```
pip install pyhelpers
```

**Note:**

- Only a few frequently-used dependencies are required for installation. 
- When importing the module/functions whose dependencies are not available with the installation of this package (or if you happen not to have those dependencies installed yet), an "*ModuleNotFoundError*" will be prompted and you may install them separately. 



## Quick start - some examples <a name="quick-start"></a>

The current version includes the following modules: 

- [`settings`](#settings)
- [`dir`](#dir_py)
- [`download`](#download)
- [`store`](#store)
- [`geom`](#geom)
- [`text`](#text)
- [`ops`](#ops)
- [`sql`](#sql)

There are a number of functions included in each of the above-listed modules. For a quick start, one example is provided for each module to demonstrate how '**pyhelpers**' may assist you in your work. 



### settings <a name="settings"></a>

This module can be used to change some common settings with 'pandas', 'numpy', 'matplotlib' and 'gdal'. For example:

```python
from pyhelpers.settings import pd_preferences
```

`pd_preferences` changes a few default 'pandas' settings (when `reset=False`), such as the display representation and maximum number of columns when viewing a pandas.DataFrame. 

```python
pd_preferences(reset=False)
```

If `reset=True`, all changed parameters should be reset to their default values.

**Note** that the preset parameters are for the authors' own preference; however you can always change them in the source code to whatever suits your use. 



### dir <a name="dir_py"></a>

```python
from pyhelpers.dir import cd, regulate_input_data_dir
```

`cd()` returns the current working directory

```python
print(cd())
```

If you would like to save `dat` to a customised folder, say "data". `cd()` can also change directory

```python
path_to_folder = cd("tests", mkdir=False)
print(path_to_folder)
```

If `path_to_folder` does not exist, setting `mkdir=True` (default: False) will create just it. 

More examples:

```python
path_to_pickle = cd("tests", "dat.pickle")
print(path_to_pickle)

path_to_test_pickle = cd("tests", "data", "dat.pickle")  # cd("tests\\data\\dat.pickle")
print(path_to_test_pickle)
```

You should see the difference between `path_to_pickle` and `path_to_test_pickle`.

Check also:

```python
print(regulate_input_data_dir("tests"))
print(regulate_input_data_dir(path_to_test_pickle))
```



### download <a name="download"></a>

```python
from pyhelpers.download import download
```

**Note** that this module requires [**requests**](https://2.python-requests.org/en/master/) and [**tqdm**](https://pypi.org/project/tqdm/). 

Suppose you would like to download a Python logo from online where URL is as follows:

```python
url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
```

Firstly, specify where the .png file will be saved and what the filename will be. For example, to name the downloaded file as "python-logo.png" and save it to a folder named "picture":

```python
path_to_python_logo = cd("tests", "picture", "python-logo.png")
```

Then use `download()`

```python
download(url, path_to_python_logo)
```

If you happen to have [**Pillow**](https://pypi.org/project/Pillow/) installed, you may also view the downloaded picture:

```python
from PIL import Image

python_logo = Image.open(path_to_python_logo)
python_logo.show()
```

To remove the download directory:

```python
from pyhelpers.dir import rm_dir

rm_dir(cd("tests", "picture"), confirmation_required=True)  # Remove "picture" folder
# rm_dir(cd("tests"), confirmation_required=True)
```



### store <a name="store"></a>

Let's now create a pandas.DataFrame (using the above `xy_array`) as follows:

```python
import numpy as np
import pandas as pd

xy_array = np.array([(530034, 180381),   # London
                     (406689, 286822),   # Birmingham
                     (383819, 398052),   # Manchester
                     (582044, 152953)],  # Leeds
                    dtype=np.int64)

dat = pd.DataFrame(xy_array, columns=['Easting', 'Northing'])
```

If you would like to save `dat` as a "pickle" file and retrieve it later, you may import `save_pickle` and `load_pickle`:

```python
from pyhelpers.store import save_pickle, load_pickle
```

To save `dat` to `path_to_test_pickle` (see [`dir`](#dir_py)):

```python
save_pickle(dat, path_to_test_pickle, verbose=True)  # default: verbose=False
```

To retrieve/load `dat` from `path_to_test_pickle`:

```python
dat_retrieved = load_pickle(path_to_test_pickle, verbose=True)
```

`dat_retrieved` and `dat`  should be identical:

```python
print(dat_retrieved.equals(dat))  # should return True
```

In addition to **.pickle**, `store.py` also works with other formats, such as **.feather**, **.csv** and **.xlsx**/**.xls**.



### geom <a name="geom"></a>

If you need to convert coordinates from British national grid (OSGB36) to latitude and longitude (WGS84), you import  `osgb36_to_wgs84` from `geom.py`

```python
from pyhelpers.geom import osgb36_to_wgs84
```

To convert a single coordinate, `xy`:

```python
xy = np.array((530034, 180381))  # London

easting, northing = xy
lonlat = osgb36_to_wgs84(easting, northing)  # osgb36_to_wgs84(xy[0], xy[1])
print(lonlat)  # (-0.12772400574286874, 51.50740692743041)
```

To convert an array of OSGB36 coordinates, `xy_array`:

```python
eastings, northings = xy_array.T
lonlat_array = np.array(osgb36_to_wgs84(eastings, northings))
print(lonlat_array.T)
```

Similarly, if you would like to convert coordinates from latitude and longitude (WGS84) to OSGB36, import `wgs84_to_osgb36` instead.



### text <a name="text"></a>

Suppose you have a `str` type variable, named `string` :

```python
string = 'ang'
```

If you would like to find the most similar text to one of the following `lookup_list`:

```python
lookup_list = ['Anglia',
               'East Coast',
               'East Midlands',
               'North and East',
               'London North Western',
               'Scotland',
               'South East',
               'Wales',
               'Wessex',
               'Western']
```

Let's try `find_similar_str` included in `text.py`:

```python
from pyhelpers.text import find_similar_str
```

Setting `processor='fuzzywuzzy'` requires '[**fuzzywuzzy**](https://github.com/seatgeek/fuzzywuzzy)' (recommended) - `token_set_ratio`

```python
result_1 = find_similar_str(string, lookup_list, processor='fuzzywuzzy')
print(result_1)
```

Setting `processor='nltk'` requires '[**nltk**](https://www.nltk.org/)' - `edit_distance`

```python
result_2 = find_similar_str(string, lookup_list, processor='nltk', substitution_cost=100)
print(result_2)
```

You may also give `find_matched_str()` a try:

```python
from pyhelpers.text import find_matched_str

result_3 = find_matched_str(string, lookup_list)
print(result_3)
```



### ops <a name="ops"></a>

If you would like to request a confirmation before proceeding with some processes, you may use `confirmed` included in `ops.py`:

```python
from pyhelpers.ops import confirmed
```

You may specify, by setting `prompt`, what you would like to be asked as to the confirmation:

```python
confirmed(prompt="Continue?...", confirmation_required=True)
```

```
Continue?... [No]|Yes:
>? # Input something here, e.g. Yes, Y, or y
```

If you input `Yes` (or `Y`, `yes`, or something like `ye`), it should return `True`; otherwise, `False` given the input being `No` (or something like `n`). When `confirmation_required` is `False`, this function would be null, as it would always return `True`. 



### sql <a name="sql"></a>

This module provides a convenient way to establish a connection with a SQL server. The current release supports only [PostgreSQL](https://www.postgresql.org/). A quick example is given below. 

```python
from pyhelpers.sql import PostgreSQL
```

Now you can connect the PostgreSQL server by specifying **host** (default: `'localhost'`), **port** (default: `5432`), **username** (default: `'postgres'`), **password** and **name of the database** (default: `'postgres'`)

```python
# Connect to 'postgres' (using all default parameters)
test_db = PostgreSQL(host='localhost', port=5432, username='postgres', password=None, 
                     database_name='postgres', verbose=True)

# Or simply, 
# test_db = PostgreSQL()
```

If `password=None`, you will be asked to input your password. 

After you have successfully established the connection, you could try to dump `dat` ([see above](#store)) into the database "postgres":

```python
test_db.dump_data(dat, table_name='test_table', schema_name='public', 
                  if_exists='replace', chunk_size=None,
                  force_replace=False, col_type=None, verbose=True)
```

To retrieve the dumped data:

```python
dat_retrieved = test_db.read_table('test_table')
# print(dat.equals(dat_retrieved))
```

To drop the table 'test_table' (If `confirmation_required=True`(default: False), you will be asked to confirm whether you are sure to drop the table):

```python
test_db.drop_table('test_table', confirmation_required=True, verbose=True)
# Confirmed to drop the table "test_table" from the database "postgres"? [No]|Yes: 
# >? Yes
# The table "test_table" has been dropped successfully.
```

If you would like to create your own database, for example, which is named 'test_database':

```python
test_db.create_db("test_database", verbose=True)

# After successfully creating the database, you could check
print(test_db.database_name)
```

To drop this database, similarly, you will also be asked to confirm whether you are sure to drop the database if `confirmation_required=True` (default):

```python
test_db.drop(confirmation_required=True, verbose=True)
# Confirmed to drop the database "test_database" for postgres@localhost? [No]|Yes: 
# >? Yes
```

