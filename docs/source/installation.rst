============
Installation
============

.. note::

    - If using a `virtual environment`_, make sure it is activated.

.. _`virtual environment`: https://packaging.python.org/glossary/#term-Virtual-Environment


To install the latest release of pyhelpers from `PyPI`_:

.. _`PyPi`: https://pypi.org/project/pyhelpers/

.. code-block:: console

    pip install --upgrade pyhelpers


To install the most recent version of pyhelpers hosted on `GitHub`_:

.. _`GitHub`: https://github.com/mikeqfu/pyhelpers

.. code-block:: console

    pip install --upgrade git+https://github.com/mikeqfu/pyhelpers.git


.. note::

    - It is recommended to add `pip install`_ the option ``--upgrade`` (or simply ``-U``), which is to ensure you are getting the latest stable release of the package.
    - Not all dependencies of pyhelpers are enforced to be installed along with the installation of the package. This is intended to optimise the requirements for installing pyhelpers. If a `ModuleNotFoundError`_ or an `ImportError`_ pops out when importing a function, try to install the module(s)/package(s) mentioned in the error message first, and then try importing the function again.
    - For Windows users, `pip`_ may possibly fail to install some dependencies, such as `GDAL`_ and `Shapely`_. If errors occur while installing any of the required packages, try instead to `install their .whl files`_, which can be downloaded from the web page of the `unofficial Windows binaries for Python extension packages`_.
    - For more general instructions on the installation of Python packages, please refer to the official guide of `Installing Packages`_.

.. _`pip install`: https://pip.pypa.io/en/stable/cli/pip_install/
.. _`ModuleNotFoundError`: https://docs.python.org/3/library/exceptions.html#ModuleNotFoundError
.. _`ImportError`: https://docs.python.org/3/library/exceptions.html#ImportError
.. _`pip`: https://pip.pypa.io/en/stable/cli/pip/
.. _`GDAL`: https://pypi.org/project/GDAL/
.. _`Shapely`: https://pypi.org/project/Shapely/
.. _`install their .whl files`: https://stackoverflow.com/a/27909082/4981844
.. _`unofficial Windows binaries for Python extension packages`: https://www.lfd.uci.edu/~gohlke/pythonlibs/
.. _`Installing Packages`: https://packaging.python.org/tutorials/installing-packages/


To check whether **pyhelpers** has been correctly installed, try to import the package via an interpreter shell:

.. code-block:: python
    :name: cmd current release

    >>> import pyhelpers

    >>> pyhelpers.__version__  # Check the current release

.. parsed-literal::
    The current release version is: |version|
