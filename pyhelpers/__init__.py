#  Copyright (c) 2026 Qian Fu
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
Package initialization and metadata loading.
"""

import datetime
import importlib.metadata
import logging
import pathlib
import tomllib

from . import dbms, dirs, geom, ops, settings, store, text, viz

logging.getLogger(__name__).addHandler(logging.NullHandler())


def _load_metadata():
    """
    Extract package metadata from local configuration or installed distribution.

    This function attempts to parse metadata from ``pyproject.toml`` during
    local development and falls back gracefully to ``importlib.metadata`` when
    running within an installed site-packages environment.

    :return: A dictionary containing metadata key-value pairs.
    :rtype: dict[str, str | None]
    """

    package_name = __package__ or 'pyhelpers'

    # Fetch standard distribution metadata
    dist_meta = importlib.metadata.metadata(package_name)
    version = dist_meta.get('Version')
    description = dist_meta.get('Summary')
    license_str = dist_meta.get('License')

    # Safely locate pyproject.toml for custom tool metadata
    current_dir = pathlib.Path(__file__).resolve().parent
    pyproject_toml = "pyproject.toml"

    possible_paths = [
        current_dir / pyproject_toml,  # Installed wheel location
        current_dir.parent / pyproject_toml,  # Local repository root
        pathlib.Path.cwd() / pyproject_toml,  # Working directory fallback
    ]

    pyproject_path = next((p for p in possible_paths if p.is_file()), None)

    if not pyproject_path:
        raise FileNotFoundError(
            f'Fatal error: "{pyproject_toml}" not found. '
            f'Configuration source is missing.'
        )

    with open(pyproject_path, mode='rb') as f:
        cfg = tomllib.load(f)

    project_info = cfg.get('project', {})
    custom_info = cfg.get('tool', {}).get('custom', {}).get('metadata', {})

    name = project_info.get('name', package_name)
    version = version or project_info.get('version')
    description = description or project_info.get('description')

    authors_str = ', '.join(a.get('name', '') for a in project_info['authors'])

    # Format copyright string
    start_year = 2019
    current_year = datetime.date.today().year
    years = f'{start_year}-{current_year}' if current_year > start_year else f'{start_year}'
    copyright_str = f'Copyright (c) {years} {authors_str}'.strip()

    # Parse corresponding author details
    corr_auth_list = custom_info.get('corresponding_author', [])
    corr_author_str = ''
    affiliation_str = ''

    if isinstance(corr_auth_list, list) and corr_auth_list:
        first_corr = corr_auth_list[0]
        if isinstance(first_corr, dict):
            c_name = first_corr.get('name', '')
            c_email = first_corr.get('email', '')
            corr_author_str = f'{c_name} <{c_email}>' if c_email else c_name
            affiliation_str = first_corr.get('affiliation', '')

    return {
        'name': name,
        'version': version,
        'description': description,
        'license': license_str,
        'authors': authors_str,
        'copyright': copyright_str,

        # Custom medata
        'project_start': custom_info.get('project_start', ''),
        'corresponding_author': corr_author_str,
        'affiliation': affiliation_str,
        'funder': custom_info.get('funder', ''),
    }


METADATA = _load_metadata()


__project__ = 'PyHelpers'
__pkgname__ = METADATA.get('name')
__description__ = METADATA.get('description')
__title__ = f"{__project__}: {__description__}" if __description__ else __project__
__version__ = METADATA.get('version')
__license__ = METADATA.get('license')
__copyright__ = METADATA.get('copyright')
__first_release__ = METADATA.get('project_start')

__funder__ = METADATA.get("funder")

__author__ = METADATA.get('authors')
__corresponding_author__ = METADATA.get('corresponding_author')
__affiliation__ = METADATA.get('affiliation')

__all__ = [
    '__project__',
    '__title__',
    '__version__',
    '__license__',
    '__copyright__',
    '__first_release__',
    '__funder__',
    '__author__',
    '__corresponding_author__',
    'dbms',
    'dirs',
    'geom',
    'ops',
    'settings',
    'store',
    'text',
    'viz'
]
