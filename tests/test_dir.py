"""
Test module dir.py
"""

from pyhelpers.dir import *


# Change directories -------------------------------------------------------------------

def test_cd():
    # Can use a breakpoint in the code line below to debug the script.
    path = cd()
    print(path)  # Press Ctrl+F8 to toggle the breakpoint.
    # <cwd>  # Current working directory

    mkdir = True
    path = cd("tests", mkdir=mkdir)
    print(".  ".join([path, "(This directory will be created if it does not exists.)"]))
    # <cwd>\\tests. (This directory will be created if it does not exists.)


def test_cdd():
    path = cdd()
    print(".  ".join([path, "(This directory will NOT be created if it does not exists.)"]))
    # <cwd>\\data. (This directory will NOT be created if it does not exists).

    mkdir = True

    path = cdd(mkdir=mkdir)
    print(".  ".join([path, "(This directory will be created if it does not exists.)"]))
    # <cwd>\\data. (This directory will be created if it does not exists.)

    path = cdd("data", data_dir="tests", mkdir=mkdir)
    print(".  ".join([path, "(This directory will be created if it does not exists.)"]))
    # <cwd>\\tests\\data. (This directory will be created if it does not exists.)


def test_cd_dat():
    dat_dir = "dat"
    mkdir = False

    path = cd_dat("tests", dat_dir=dat_dir, mkdir=mkdir)
    print(".  ".join([path, "(This directory will NOT be created if it does not exists.)"]))
    # <package directory>\\dat\\tests. (This directory will NOT be created if it does not exists.)


# Validate directories -----------------------------------------------------------------

def test_is_dir():
    dir_name = "tests"
    print(is_dirname(dir_name))
    # False

    dir_name = "\\tests"
    print(is_dirname(dir_name))
    # True

    dir_name = cd("tests")
    print(is_dirname(dir_name))
    # True


def test_validate_input_data_dir():
    data_dir = "tests"

    data_dir_ = validate_input_data_dir(data_dir)

    print(data_dir_)
    # <cwd>\\tests


# Delete directories -------------------------------------------------------------------

def test_delete_dir():
    path_to_dir = cdd(mkdir=True)
    print("The directory \"{}\" exists? {}".format(path_to_dir, os.path.exists(path_to_dir)))
    # The directory "<cwd>\\data\\dat" exists? True

    delete_dir(path_to_dir, confirmation_required=True, verbose=True)
    # To remove the directory "<cwd>\\data\\dat"? [No]|Yes: no
    # Cancelled.

    print("The directory \"{}\" exists? {}".format(path_to_dir, os.path.exists(path_to_dir)))
    # The directory "<cwd>\\data\\dat" exists? True


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Change directories ---------------------------------------------------------------

    print("\nTesting 'cd()':")
    test_cd()

    print("\nTesting 'cdd()':")
    test_cdd()

    print("\nTesting 'cd_dat()':")
    test_cd_dat()

    # Validate directories -------------------------------------------------------------

    print("\nTesting 'is_dir()':")
    test_is_dir()

    print("\nTesting 'validate_input_data_dir()':")
    test_validate_input_data_dir()

    # Delete directories ---------------------------------------------------------------

    print("\nTesting 'rm_dir()':")
    test_delete_dir()
