# PyHelpers
**Author**: Qian Fu [![Twitter Follow](https://img.shields.io/twitter/follow/Qian_Fu?label=Follow&style=social)](https://twitter.com/Qian_Fu)

[![PyPI](https://img.shields.io/pypi/v/pyhelpers?color=important)](https://pypi.org/project/pyhelpers/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyhelpers)
[![PyPI - License](https://img.shields.io/pypi/l/pyrcs)](https://github.com/mikeqfu/pyhelpers/blob/master/LICENSE)
![GitHub repo size](https://img.shields.io/github/repo-size/mikeqfu/pyhelpers?color=yellowgreen)



This is a set of helper functions to facilitate trivial processes, such as prompting confirmation (yes/no), saving and loading pickle/json files. Current modules include: *dir.py*, *download.py*, *geom.py*, *misc.py*, *settings.py*, *store.py* and *text.py*. 

(Work still in progress.)



## Contents

- [Installation](#installation)
- [Quick start](#quick-start)
  - 



## Installation



## Quick start

```python
from pyhelpers.misc import confirmed
from pyhelpers.store import cd, save_pickle, load_pickle
```

### A confirmation of whether to continue is needed:

```python
confirmed(prompt="Continue?...")
```

### To save/retrieve data to/from a pickle file

```python
example_var = 1
path_to_pickle = cd("example_var.pickle")  # cd() returns the current working directory

# Save `example_var` as a pickle file
save_pickle(ex_var, path_to_pickle)

# Retrieve `example_var` from `path_to_pickle`
example_var_retrieved = load_pickle(path_to_pickle)

print(example_var_retrieved == example_var)  # should return True
```

