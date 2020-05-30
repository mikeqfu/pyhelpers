# store.py

from pyhelpers.dir import cd
from pyhelpers.store import *

xy_array = np.array([(530034, 180381),   # London
                     (406689, 286822),   # Birmingham
                     (383819, 398052),   # Manchester
                     (582044, 152953)])  # Leeds
dat = pd.DataFrame(xy_array, columns=['Easting', 'Northing'])

path_to_test_pickle = cd("tests", "data", "dat.pickle")  # path_to_test_pickle == cd("tests\\data\\dat.pickle")
print(path_to_test_pickle)  # C:\Users\fuq\DataShare\Experiments\pyhelpers\tests\data\dat.pickle

# Save dat as a pickle file
save_pickle(dat, path_to_test_pickle, verbose=True)
dat_retrieved = load_pickle(path_to_test_pickle)
print(dat_retrieved.equals(dat))  # should return True

# Save dat as a feather file
path_to_test_feather = path_to_test_pickle.replace(".pickle", ".feather")
save_feather(dat, path_to_test_feather, verbose=True)
dat_retrieved = load_feather(path_to_test_feather)
print(dat_retrieved.equals(dat))  # should return True
