============
Installation
============

PyHelpers can be installed using `uv`_ (recommended for speed, reliability and modern dependency resolution) or traditional `pip`_.


Using ``uv`` (Recommended)
==========================

`uv`_ is a fast Python package installer and project manager written in Rust.

Adding to a ``uv`` Project
---------------------------

To add the latest release of PyHelpers to your existing project managed by ``uv``:

.. code-block:: console

    > uv add pyhelpers

To include all optional dependencies (e.g. geospatial and data manipulation libraries):

.. code-block:: console

    > uv add "pyhelpers[full]"

Installing in a Virtual Environment
-----------------------------------

If you are working inside an active virtual environment and wish to install PyHelpers directly using ``uv pip``:

.. code-block:: console

    > uv pip install --upgrade pyhelpers

To install the latest development version directly from `GitHub <https://github.com/mikeqfu/pyhelpers>`_:

.. code-block:: console

    > uv pip install --upgrade git+https://github.com/mikeqfu/pyhelpers.git


Using ``pip``
=============

If you prefer standard Python packaging tools, ensure your `virtual environment`_ is activated and use `pip install`_:

.. code-block:: console

    > pip install --upgrade pyhelpers

To install with all optional dependencies:

.. code-block:: console

    > pip install --upgrade "pyhelpers[full]"

To install the development version from GitHub:

.. code-block:: console

    > pip install --upgrade git+https://github.com/mikeqfu/pyhelpers.git

.. note::

    **Windows Users Installing Geospatial Dependencies via ``pip``:**

    Standard ``pip`` installation of C-extension packages such as ``gdal`` or ``fiona`` may fail on Windows due to missing C++ compilers and underlying C libraries. (When using ``uv``, this wheel index is configured automatically).

    If you use ``pip`` rather than ``uv``, install pre-compiled wheel files directly from the `geospatial-wheels`_ repository index:

    .. code-block:: console

        > pip install gdal --find-links https://nathanjmcdougall.github.io/geospatial-wheels-index/

    Alternatively, download the appropriate ``.whl`` file matching your Python version and architecture from `geospatial-wheels releases`_ and install it manually:

    .. code-block:: console

        > pip install path/to/gdal-3.x.x-cp3x-cp3x-win_amd64.whl


Verification
============

To verify the installation, import the package in a Python interpreter shell:

.. code-block:: python
    :name: cmd current version

    >>> import pyhelpers
    >>> pyhelpers.__version__  # Check the latest version

.. parsed-literal::
    The latest version is: |version|


.. note::

    - Core dependencies are installed automatically. To keep the base installation lightweight, optional features (e.g. advanced geospatial tools or database connectors) require extra dependencies. Install these using the ``[full]`` extra (e.g. ``pyhelpers[full]``) or install individual missing packages as indicated by any `ModuleNotFoundError`_.
    - For general guidelines on Python virtual environments and dependency management, refer to the `Python Packaging User Guide`_.

.. _`uv`: https://docs.astral.sh/uv/
.. _`virtual environment`: https://packaging.python.org/glossary/#term-Virtual-Environment
.. _`pip install`: https://pip.pypa.io/en/stable/cli/pip_install/
.. _`pip`: https://pip.pypa.io/en/stable/cli/pip/
.. _`geospatial-wheels`: https://nathanjmcdougall.github.io/geospatial-wheels-index/
.. _`geospatial-wheels releases`: https://github.com/nathanjmcdougall/geospatial-wheels/releases
.. _`ModuleNotFoundError`: https://docs.python.org/3/library/exceptions.html#ModuleNotFoundError
.. _`Python Packaging User Guide`: https://packaging.python.org/tutorials/installing-packages/
