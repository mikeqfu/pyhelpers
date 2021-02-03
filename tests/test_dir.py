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
    path = cd("test_dir", mkdir=mkdir)
    print(".  ".join([path, "(This directory will be created if it does not exists.)"]))
    # <cwd>\\test_dir. (This directory will be created if it does not exists.)


def test_cdd():
    path = cdd()
    print(".  ".join([path, "(This directory will NOT be created if it does not exists.)"]))
    # <cwd>\\data. (This directory will NOT be created if it does not exists).

    mkdir = True

    path = cdd(mkdir=mkdir)
    print(".  ".join([path, "(This directory will be created if it does not exists.)"]))
    # <cwd>\\data. (This directory will be created if it does not exists.)

    path = cdd("test_dir", data_dir="tests", mkdir=mkdir)
    print(".  ".join([path, "(This directory will be created if it does not exists.)"]))
    # <cwd>\\tests\\test_dir. (This directory will be created if it does not exists.)

    delete_dir(os.path.dirname(path), confirmation_required=False)


def test_cd_dat():
    dat_dir = "dat"
    mkdir = False

    path = cd_dat("test_dir", dat_dir=dat_dir, mkdir=mkdir)
    print(".  ".join([path, "(This directory will NOT be created if it does not exists.)"]))
    # <package directory>\\dat\\test_dir. (This directory will NOT be created if it does not exists.)


# Validate directories -----------------------------------------------------------------

def test_is_dir():
    dir_name = "test_dir"
    print(is_dirname(dir_name))
    # False

    dir_name = "\\test_dir"
    print(is_dirname(dir_name))
    # True

    dir_name = cd("test_dir")
    print(is_dirname(dir_name))
    # True


def test_validate_input_data_dir():
    data_dir = "tests"

    data_dir_ = validate_input_data_dir(data_dir)

    print(data_dir_)
    # <cwd>\\tests


# Delete directories -------------------------------------------------------------------

def test_delete_dir():

    dir_path = cd("test_dir", mkdir=True)
    rel_dir_path = os.path.relpath(dir_path)

    print('The directory "{}" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
    # The directory "test_dir" exists? True
    delete_dir(dir_path, verbose=True)
    # To delete the directory "test_dir"? [No]|Yes: yes
    # Deleting "test_dir" ... Done.
    print('The directory "{}" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
    # The directory "test_dir" exists? False

    dir_path = cd("test_dir", "folder", mkdir=True)
    rel_dir_path = os.path.relpath(dir_path)

    print('The directory "{}" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
    # The directory "test_dir\\folder" exists? True
    delete_dir(cd("test_dir"), verbose=True)
    # The directory "test_dir" is not empty.
    # Confirmed to delete it? [No]|Yes: yes
    # Deleting "test_dir" ... Done.
    print('The directory "{}" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
    # The directory "test_dir\\folder" exists? False


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

    print("\nTesting 'delete_dir()':")
    test_delete_dir()
