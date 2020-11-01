============
Installation
============

To install the latest release of PyHelpers at `PyPI`_ via `pip`_:

.. code-block:: bash

    pip install --upgrade pyhelpers

To install the more recent version hosted directly from `GitHub repository`_:

.. code-block:: bash

    pip install --upgrade git+https://github.com/mikeqfu/pyhelpers.git

To test if PyHelpers is correctly installed, try importing the package via an interpreter shell:

.. code-block:: python

    >>> import pyhelpers

    >>> pyhelpers.__version__  # Check the current release

.. parsed-literal::
    The current release version is: |version|


.. note::

    - If using a `virtual environment`_, ensure that it is activated.

    - It is always recommended to add ``--upgrade`` (or ``-U``) to ``pip install`` so as to get the latest version of the package.

    - The package has not yet been tested with `Python 2`_. For users who have installed both `Python 2`_ and `Python 3`_, it would be recommended to replace ``pip`` with ``pip3``. But you are more than welcome to volunteer testing the package with `Python 2`_ and any issues should be logged/reported onto the `Issues`_ page.

    - For *Windows* users, The ``pip`` method might fail to install some dependencies, such as `GDAL`_, `Shapely`_ and `python-Levenshtein`_. If errors occur when ``pip`` installing any of those dependencies, try instead to ``pip install`` their respective *.whl* files, which can be downloaded from the `Unofficial Windows Binaries for Python Extension Packages`_. After they are installed successfully, try to install pyhelpers again.

    - It is possible to get a ``ModuleNotFoundError`` when using some functions, as not all dependencies are required (so as to minimise the requirements) for the installation of the package. In that case, just install the 'missing' module(s). See, for example, the use of the functions :ref:`pyhelpers.ops.download_file_from_url()<ops-examples>` and :ref:`pyhelpers.text.find_similar_str<text-examples>`.

    - For more general instructions, check the "`Installing Packages <https://packaging.python.org/tutorials/installing-packages>`_".


.. _`PyPI`: https://pypi.org/project/pyhelpers/
.. _`pip`: https://packaging.python.org/key_projects/#pip
.. _`GitHub repository`: https://github.com/mikeqfu/pyhelpers

.. _`virtual environment`: https://packaging.python.org/glossary/#term-Virtual-Environment
.. _`virtualenv`: https://packaging.python.org/key_projects/#virtualenv
.. _`Python 2`: https://docs.python.org/2/
.. _`Python 3`: https://docs.python.org/3/
.. _`Issues`: https://github.com/mikeqfu/pyhelpers/issues

.. _`GDAL`: https://pypi.org/project/GDAL/
.. _`Shapely`: https://pypi.org/project/Shapely/
.. _`python-Levenshtein`: https://pypi.org/project/python-Levenshtein/
.. _`Unofficial Windows Binaries for Python Extension Packages`: https://www.lfd.uci.edu/~gohlke/pythonlibs/
.. _`Installing Packages`: https://packaging.python.org/tutorials/installing-packages