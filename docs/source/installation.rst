Installation
============

If you are using a `virtualenv <https://packaging.python.org/key_projects/#virtualenv>`_, ensure that the virtualenv is activated.

To install the latest release of `pyhelpers <https://github.com/mikeqfu/pyhelpers>`_ at `PyPI <https://pypi.org/project/pyhelpers/>`_ via `pip <https://packaging.python.org/key_projects/#pip>`_ on Windows Command Prompt (CMD) or Linux/Unix terminal.

.. code-block:: bash

   pip install --upgrade pyhelpers

If you would like to try the more recent version under development, install it from GitHub

.. code-block:: bash

   pip install --upgrade git+https://github.com/mikeqfu/pyhelpers.git

To test if pyhelpers is correctly installed, try importing the package from an interpreter shell:

.. parsed-literal::

    >>> import pyhelpers
    >>> pyhelpers.__version__  # Check the current release
    |version|

.. note::

    - To ensure you get the most recent version, it is always recommended to add ``-U`` (or ``--upgrade``) to ``pip install``.
    - `pyhelpers <https://github.com/mikeqfu/pyhelpers>`_ has not yet been tested with Python 2. For users who have installed both Python 2 and 3, it would be recommended to replace ``pip`` with ``pip3``. But you are more than welcome to volunteer testing the package with Python 2 and any issues should be logged/reported onto the web page of "`Issues <https://github.com/mikeqfu/pyhelpers/issues>`_".
    - It is possible that the ``pip`` method may fail to install some dependencies, such as `GDAL <https://pypi.org/project/GDAL/>`_ and `Shapely <https://pypi.org/project/Shapely/>`_, especially on Windows operating systems. Therefore, only some frequently-used dependencies are required for the installation of the package. If those "left-out" dependencies happen not to be available yet in your working environment, importing some functions from the this package (for which the dependencies have not been installed) may prompt an ``ModuleNotFoundError``. Under that circumstance, try to install them separately. Windows users are recommended to try to ``pip install`` their corresponding Windows binaries that can be downloaded from the `Unofficial Windows Binaries for Python Extension Packages <https://www.lfd.uci.edu/~gohlke/pythonlibs>`_.
    - For more general instructions, check the web page of "`Installing Packages <https://packaging.python.org/tutorials/installing-packages>`_".
