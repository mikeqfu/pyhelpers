# store.py

import numpy as np
import pandas as pd

from pyhelpers.dir import cd
from pyhelpers.store import load_pickle, save_pickle

xy_array = np.array([(530034, 180381),   # London
                     (406689, 286822),   # Birmingham
                     (383819, 398052),   # Manchester
                     (582044, 152953)])  # Leeds
dat = pd.DataFrame(xy_array, columns=['Easting', 'Northing'])

path_to_test_pickle = cd("tests", "data", "dat.pickle")  # cd("tests\\data\\dat.pickle")
print(path_to_test_pickle)

save_pickle(dat, path_to_test_pickle)
dat_retrieved = load_pickle(path_to_test_pickle)
print(dat_retrieved.equals(dat))  # should return True
