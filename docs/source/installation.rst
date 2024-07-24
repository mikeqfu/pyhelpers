============
Installation
============

Using ``pip``
=============

.. note::

    - If you are using a `virtual environment`_, ensure it is activated.
    - Use the ``--upgrade`` (or ``-U``) option with `pip install`_ to get the latest stable release.

To install the latest release of PyHelpers from `PyPI <https://pypi.org/project/pyhelpers/>`_ via `pip <https://pip.pypa.io/en/stable/cli/pip/>`_:

.. code-block:: console

    > pip install --upgrade pyhelpers

To install the latest development version of PyHelpers from `GitHub <https://github.com/mikeqfu/pyhelpers>`_:

.. code-block:: console

    > pip install --upgrade git+https://github.com/mikeqfu/pyhelpers.git

Verification
============

To verify the installation of PyHelpers, try importing the package in an interpreter shell:

.. code-block:: python
    :name: cmd current version

    >>> import pyhelpers
    >>> pyhelpers.__version__  # Check the latest version

.. parsed-literal::
    The latest version is: |version|


.. note::

    - Not all dependencies of PyHelpers are installed automatically to optimise installation requirements. If you encounter a `ModuleNotFoundError`_ or an `ImportError`_, install the missing package(s) as indicated in the error message.
    - When using the package, Windows users might face issues with `pip`_ failing to install some packages. In such cases, try `installing the wheel (.whl) files`_ instead. Refer to `Christoph Gohlke's homepage`_ for essential and downloadable wheel files.
    - For more general instructions on installing Python packages, refer to the `Installing Packages`_ guide.

.. _`virtual environment`: https://packaging.python.org/glossary/#term-Virtual-Environment
.. _`pip install`: https://pip.pypa.io/en/stable/cli/pip_install/
.. _`ModuleNotFoundError`: https://docs.python.org/3/library/exceptions.html#ModuleNotFoundError
.. _`ImportError`: https://docs.python.org/3/library/exceptions.html#ImportError
.. _`pip`: https://pip.pypa.io/en/stable/cli/pip/
.. _`installing the wheel (.whl) files`: https://stackoverflow.com/a/27909082/4981844
.. _`Christoph Gohlke's homepage`: https://www.cgohlke.com/
.. _`Installing Packages`: https://packaging.python.org/tutorials/installing-packages/
