"""
Tests the :mod:`~pyhelpers.dirs.management` submodule.
"""

import os

import pytest

from pyhelpers.dirs import cd, delete_dir, format_display_path, get_file_paths


def test_delete_dir(tmp_path, capfd):
    """Test :func:`~pyhelpers.dirs.delete_dir`."""

    # import tempfile, pathlib; tmp_path = pathlib.Path(tempfile.mkdtemp())
    test_dirs = []
    for x in range(3):
        tmp_dir_pathname = f"{tmp_path}{x}"
        test_dirs.append(cd(tmp_dir_pathname, mkdir=True))
        if x == 0:
            cd(tmp_dir_pathname, "a_folder", mkdir=True)
        elif x == 1:
            open(cd(tmp_dir_pathname, "file"), 'w').close()

    delete_dir(tmp_path, confirmation_required=False, verbose=True)
    out, _ = capfd.readouterr()  # Capture the output
    expected_out = f'Deleting {format_display_path(os.path.normpath(tmp_path))} ... Done.\n'
    assert expected_out == out

    # Test deleting multiple directories
    delete_dir(dir_path=test_dirs, confirmation_required=False, verbose=True)
    out, _ = capfd.readouterr()
    expected_output = "Deleting:\n  " + "\n  ".join(
        [f'{format_display_path(str(tmp_path) + str(x))} ... Done.' for x in range(3)]
    ) + '\n'
    assert expected_output == out


def test_get_file_paths(dat_dir, img_dir):
    dat_filenames = os.listdir(dat_dir)

    result_1 = get_file_paths(dat_dir)
    assert isinstance(result_1, list)
    assert all(os.path.basename(x) in dat_filenames for x in result_1)

    result_2 = get_file_paths(dat_dir, incl_subdir=True)
    assert all(os.path.basename(x) in dat_filenames for x in result_2)

    result_3 = get_file_paths(dat_dir, file_ext=".xz")
    assert all(os.path.basename(x) in ['dat.pickle.xz', 'dat.processed.pkl.xz'] for x in result_3)

    result_4 = get_file_paths(img_dir, file_ext=".png", incl_subdir=True)
    png_filenames = [
        'ops-download_file_from_url-demo.png',
        'store-save_fig-demo.png',
        'store-save_figure-demo.png'
    ]
    assert all(os.path.basename(x) in png_filenames for x in result_4)


if __name__ == '__main__':
    pytest.main()
