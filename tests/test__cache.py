"""Test the module ``_cache.py``"""

import pytest


def test__check_dependency():
    from pyhelpers._cache import _check_dependency

    sqlalchemy_dialects = _check_dependency(name='dialects', package='sqlalchemy')
    assert sqlalchemy_dialects.__name__ == 'sqlalchemy.dialects'


def test__check_rel_pathname():
    from pyhelpers._cache import _check_rel_pathname

    pathname = ""
    pathname_ = _check_rel_pathname(pathname=pathname)
    assert pathname_ == pathname


if __name__ == '__main__':
    pytest.main()
