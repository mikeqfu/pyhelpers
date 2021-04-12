============
Installation
============

To install the latest release of PyHelpers from `PyPI`_ by using `pip`_:

.. code-block:: bash

    pip install --upgrade pyhelpers

To install a more recent version of PyHelpers hosted on `GitHub repository`_:

.. code-block:: bash

    pip install --upgrade git+https://github.com/mikeqfu/pyhelpers.git

To test if PyHelpers is correctly installed, try to import the package via an interpreter shell:

.. code-block:: python

    >>> import pyhelpers

    >>> pyhelpers.__version__  # Check the current release

.. parsed-literal::
    The current release version is: |version|


.. note::

    - If you are using a `virtual environment`_, ensure that it is activated.

    - It is recommended to add ``--upgrade`` (or ``-U``) when you use ``pip install`` (see the instruction above) so as to get the latest stable release of the package.

    - Not all dependencies of PyHelpers are required (so as to optimise the requirements) for the installation of the package. If a ``ModuleNotFoundError`` or an ``ImportError`` pops out when importing a function, just install the 'missing' module/package and then try to import the function again. See, for example, the use of the functions :ref:`pyhelpers.text.find_similar_str<text-examples>`.

    - For *Windows* users, The ``pip`` method **might** fail to install some dependencies (e.g. `GDAL`_ and `Shapely`_). If errors occur when you try to install any of those dependencies, try instead to ``pip install`` their *.whl* files, which can be downloaded from the `Unofficial Windows Binaries for Python Extension Packages`_.

    - For more general instructions on the installation of Python packages, check the "`Installing Packages`_".

    - PyHelpers has not yet been tested with `Python 2`_. For users who have installed both `Python 2`_ and `Python 3`_, it would be recommended to replace ``pip`` with ``pip3``. But you are more than welcome to volunteer testing the package with `Python 2`_ and any issues should be logged/reported onto `Issue Tracker`_.

.. _`PyPI`: https://pypi.org/project/pyhelpers/
.. _`pip`: https://packaging.python.org/key_projects/#pip

.. _`GitHub repository`: https://github.com/mikeqfu/pyhelpers

.. _`virtual environment`: https://packaging.python.org/glossary/#term-Virtual-Environment

.. _`GDAL`: https://pypi.org/project/GDAL/
.. _`Shapely`: https://pypi.org/project/Shapely/
.. _`Unofficial Windows Binaries for Python Extension Packages`: https://www.lfd.uci.edu/~gohlke/pythonlibs/

.. _`Installing Packages`: https://packaging.python.org/tutorials/installing-packages

.. _`Python 2`: https://docs.python.org/2/
.. _`Python 3`: https://docs.python.org/3/
.. _`Issue Tracker`: https://github.com/mikeqfu/pyhelpers/issues
