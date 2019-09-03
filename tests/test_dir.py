# dir.py

from pyhelpers.dir import cd

path_to_pickle = cd("tests", "dat.pickle")
print(path_to_pickle)

path_to_test_pickle = cd("tests\\data", "dat.pickle")  # cd("tests\\data\\dat.pickle")
print(path_to_test_pickle)
