# pyhelpers
(Version 1.0.8)

This package contains a few helper functions to facilitate trivial processes, such as prompting confirmation (yes/no), saving and loading pickle/json files...

Currently, the package includes the following modules: *dir*, *download*, *geom*, *misc*, *settings*, *store* and *text*. 



#### Quick Start

```python
from pyhelpers.misc import confirmed
from pyhelpers.store import cd, save_pickle, load_pickle
```

###### A confirmation of whether to continue is needed:

```python
confirmed(prompt="Continue?...")
```

###### To save/retrieve data to/from a pickle file:

```python
example_var = 1
path_to_pickle = cd("example_var.pickle")  # cd() returns the current working directory

# Save `example_var` as a pickle file
save_pickle(ex_var, path_to_pickle)

# Retrieve `example_var` from `path_to_pickle`
example_var_retrieved = load_pickle(path_to_pickle)

print(example_var_retrieved == example_var)  # should return True
```

... 