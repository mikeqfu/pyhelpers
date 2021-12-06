============
Installation
============

To install the latest release of pyhelpers from `PyPI`_ via `pip`_:

.. _`PyPI`: https://pypi.org/project/pyhelpers/
.. _`pip`: https://pip.pypa.io/en/stable/cli/pip/

.. code-block:: console

    pip install --upgrade pyhelpers


To install the most recent version of pyhelpers hosted on `GitHub`_:

.. _GitHub: https://github.com/mikeqfu/pyhelpers

.. code-block:: console

    pip install --upgrade git+https://github.com/mikeqfu/pyhelpers.git


.. note::

    - If using a `virtual environment`_, make sure it is activated.
    - It is recommended to add `pip install`_ the option ``--upgrade`` (or ``-U``) to ensure that you are getting the latest stable release of the package.
    - Not all dependencies of pyhelpers are enforced to be installed along with the installation of the package. This is intended to optimise the installation requirements. If a `ModuleNotFoundError`_ or an `ImportError`_ pops out when importing/running a function, first try to install the module(s)/package(s) mentioned in the error message, and then try importing/running the function again.
    - For Windows users, `pip`_ may possibly fail to install some packages. In such circumstances, try instead to `install their .whl files`_, which can be downloaded from the web page of the `unofficial Windows binaries for Python extension packages`_.
    - For more general instructions on the installation of Python packages, please refer to the official guide of `Installing Packages`_.

    .. _`virtual environment`: https://packaging.python.org/glossary/#term-Virtual-Environment
    .. _`pip install`: https://pip.pypa.io/en/stable/cli/pip_install/
    .. _`ModuleNotFoundError`: https://docs.python.org/3/library/exceptions.html#ModuleNotFoundError
    .. _`ImportError`: https://docs.python.org/3/library/exceptions.html#ImportError
    .. _`GDAL`: https://pypi.org/project/GDAL/
    .. _`Shapely`: https://pypi.org/project/Shapely/
    .. _`install their .whl files`: https://stackoverflow.com/a/27909082/4981844
    .. _`unofficial Windows binaries for Python extension packages`: https://www.lfd.uci.edu/~gohlke/pythonlibs/
    .. _`Installing Packages`: https://packaging.python.org/tutorials/installing-packages/


To check whether pyhelpers has been correctly installed, try to import the package via an interpreter shell:

.. code-block:: python
    :name: cmd current version

    >>> import pyhelpers

    >>> pyhelpers.__version__  # Check the latest version

.. parsed-literal::
    The latest version is: |version|
