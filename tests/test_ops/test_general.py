"""
Tests the :mod:`~pyhelpers.ops.general` submodule.
"""

import time

import pytest

from pyhelpers.dbms import PostgreSQL
from pyhelpers.ops.general import *


def test_confirmed(monkeypatch):
    assert confirmed(confirmation_required=False)

    monkeypatch.setattr('builtins.input', lambda _: "Yes")
    assert confirmed()

    monkeypatch.setattr('builtins.input', lambda _: "")
    assert not confirmed()

    monkeypatch.setattr('builtins.input', lambda _: "no")
    assert not confirmed(resp=True)

    prompt = "Testing if the function works?"
    monkeypatch.setattr('builtins.input', lambda _: "Yes")
    assert confirmed(prompt=prompt, resp=False)


@pytest.mark.parametrize('col_names', [None, ['a', 'b']])
@pytest.mark.parametrize('as_dataframe', [False, True])
def test_get_obj_attr(col_names, as_dataframe):
    res = get_obj_attr(PostgreSQL, col_names=col_names, as_dataframe=as_dataframe)

    if as_dataframe:
        assert isinstance(res, pd.DataFrame)
        if col_names:
            assert res.columns.tolist() == col_names
        else:
            assert res.columns.tolist() == ['attribute', 'value']
    else:
        assert isinstance(res, list)


def test_eval_dtype():
    from pyhelpers.ops import eval_dtype

    val_1 = '1'
    origin_val = eval_dtype(val_1)
    assert origin_val == 1

    val_2 = '1.1.1'
    origin_val = eval_dtype(val_2)
    assert origin_val == '1.1.1'


def test_hash_password():
    test_pwd = 'test%123'
    salt_size_ = 16
    sk = hash_password(password=test_pwd, salt_size=salt_size_)  # salt and key
    salt_data, key_data = sk[:salt_size_].hex(), sk[salt_size_:].hex()
    assert verify_password(password=test_pwd, salt=salt_data, key=key_data)

    test_pwd = b'test%123'
    sk = hash_password(password=test_pwd)
    salt_data, key_data = sk[:128].hex(), sk[128:].hex()
    assert verify_password(password=test_pwd, salt=salt_data, key=key_data)


def test_func_running_time(capfd):
    @func_running_time
    def test_func():
        print("Testing if the function works.")
        time.sleep(3)

    test_func()
    out, _ = capfd.readouterr()
    assert "INFO Finished running function: test_func, total: 3s" in out


def test_get_git_branch(capfd):
    branch_name = get_git_branch(verbose=True)
    out, _ = capfd.readouterr()
    if out:
        assert branch_name is None
    else:
        assert isinstance(branch_name, str)


@pytest.mark.parametrize('colours', ['invalid_colour', 'invalid_color'])
def test_get_ansi_color_code(colours):
    with pytest.raises(ValueError, match=f"'{colours}' is not a valid"):
        _ = get_ansi_color_code(colours)


@pytest.fixture
def mock_project(tmp_path):
    """Creates a mock directory structure for testing get_project_structure."""

    # 1. Create structure for Example 1 (testing traversal/ignore)
    start_path_1 = tmp_path / "pyhelpers"
    start_path_1.mkdir()

    (start_path_1 / "__pycache__").mkdir()
    (start_path_1 / "core.py").touch()

    # Nested directory
    nested_dir = start_path_1 / "dirs"
    nested_dir.mkdir()
    (nested_dir / "init.py").touch()
    (nested_dir / "data.txt").touch()

    # 2. Create structure for Example 2 (testing file output)
    start_path_2 = tmp_path / "my_project"
    start_path_2.mkdir()
    (start_path_2 / "main.py").touch()
    (start_path_2 / "config.ini").touch()

    return {
        "pyhelpers_path": str(start_path_1),
        "my_project_path": str(start_path_2),
        "output_file": str(tmp_path / "structure.txt"),
    }


def test_get_project_structure(mock_project, capsys):
    # Test 1: Console Output
    pyhelpers_path = mock_project["pyhelpers_path"]

    # Run the function with default settings (print_in_console=True)
    get_project_structure(start_path=pyhelpers_path)

    # Capture the output printed to stdout
    captured = capsys.readouterr()
    console_output = captured.out.strip()

    # Define the expected console structure (ignoring __pycache__)
    expected_console_lines = [
        "├── pyhelpers/",
        "│   ├── core.py",
        "│   ├── dirs/",
        "│   │   ├── data.txt",
        "│   │   ├── init.py",
    ]
    expected_console_output = "\n".join(expected_console_lines)

    clean_console_output = console_output.replace('\\', '/').strip()
    clean_expected_console = expected_console_output.replace('\\', '/').strip()

    # Verification: Check for containment of expected lines
    for line in clean_expected_console.split('\n'):
        assert line in clean_console_output, f"Console output missing expected line: {line}"
    assert "__pycache__" not in clean_console_output, "Ignored directory found in console output."

    # Test 2:
    my_project_path = mock_project["my_project_path"]
    out_file_path = mock_project["output_file"]

    # Run the function, suppressing console output and writing to a file
    get_project_structure(start_path=my_project_path, print_in_console=False, out_file=out_file_path)

    # Check that stdout was empty during this run (use capsys again)
    # Note: If the function was run twice sequentially, capsys.readouterr()
    # would only capture output since the last call. We rely on the capsys
    # being cleared after the first test section.
    captured_file_run = capsys.readouterr()
    assert captured_file_run.out == "", "Console output should be suppressed for file output test."

    # Read the content of the output file
    with open(out_file_path, 'r', encoding='utf-8') as f:
        file_content = f.read().strip()

    # Define the expected file structure.
    expected_file_lines = [
        "├── my_project/",
        "│   ├── config.ini",
        "│   ├── main.py",
    ]
    expected_file_output = "\n".join(expected_file_lines)

    # Verification: Check if the file content matches
    clean_file_content = file_content.replace('\\', '/').strip()
    clean_expected_file = expected_file_output.replace('\\', '/').strip()

    assert clean_expected_file in clean_file_content, "File content does not match expected structure."
    assert os.path.isfile(out_file_path)


if __name__ == '__main__':
    pytest.main()
