#  Copyright (c) 2019-2026 Qian Fu
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

"""
Utilities for directory and file operations, navigation and management.
"""

from .formatting import format_display_path, get_relative_path, normalize_path, standardize_path
from .management import delete_dir, get_file_paths
from .navigation import cd, cd_data, cdd, find_executable, resolve_dir_path
from .validation import check_files_exist, is_dir_path, validate_filename

__all__ = [
    # formatting
    'format_display_path',
    'get_relative_path',
    'normalize_path',
    'standardize_path',

    # management
    'delete_dir',
    'get_file_paths',

    # navigation
    'cd',
    'cd_data',
    'cdd',
    'find_executable',
    'resolve_dir_path',

    # validation
    'check_files_exist',
    'is_dir_path',
    "validate_filename"
]
