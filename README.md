# PyHelpers

*An open-source toolkit for facilitating Python users' data manipulation tasks.*

[![PyPI Release Version](https://img.shields.io/pypi/v/pyhelpers)](https://pypi.org/project/pyhelpers/)
[![Python Version](https://img.shields.io/pypi/pyversions/pyhelpers)](https://docs.python.org/3/)
[![License](https://img.shields.io/github/license/mikeqfu/pyhelpers)](https://github.com/mikeqfu/pyhelpers/blob/master/LICENSE)
[![ReadTheDocs Documentation](https://img.shields.io/readthedocs/pyhelpers?logo=readthedocs)](https://pyhelpers.readthedocs.io/en/latest/?badge=latest)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/mikeqfu/pyhelpers/github-pages.yml?logo=github&branch=master)](https://github.com/mikeqfu/pyhelpers/actions)
[![Codacy - Code Quality](https://app.codacy.com/project/badge/Grade/c3ed8571c494450da12cb0c4d3c8c7e9)](https://app.codacy.com/gh/mikeqfu/pyhelpers/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![DOI](https://img.shields.io/badge/10.5281%2Fzenodo.4017438-blue?label=doi)](https://doi.org/10.5281/zenodo.4017438)

PyHelpers is an open-source Python package designed to streamline data (pre-)processing and manipulation tasks. It accommodates a wide range of functions and classes grounded in practical applications, making common data operations more accessible and efficient. This toolkit is particularly useful for Python learners, researchers and data scientists seeking to enhance their workflows.

The package supports handling various data types, such as geographical and textual data, allowing for flexibility for diverse data processing needs. It also simplifies data input and output operations by offering functionalities for managing many different file-like objects. In addition, PyHelpers facilitates communication with relational databases, such as PostgreSQL and Microsoft SQL Server. This capability greatly smooths data integration with database systems through efficient data storage and retrieval.

With its comprehensive suite of practical tools, PyHelpers simplifies complex data processing tasks and boosts productivity. It is ready to serve as an essential resource for effective data manipulation, management and analysis for anyone working with data in Python.

## Installation

PyHelpers can be installed using [`uv`](https://docs.astral.sh/uv/) (recommended) or [`pip`](https://pip.pypa.io/en/stable/cli/pip/).

<details open>
<summary><b>Using <code>uv</code> (Recommended)</b></summary>

To add PyHelpers to an existing project:

```bash
uv add pyhelpers
```

To include all optional features (e.g. geospatial and database tools):

```bash
uv add "pyhelpers[full]"
```

If you are working in an activated virtual environment:

```bash
uv pip install --upgrade pyhelpers
```

</details>

<details>
<summary><b>Using pip</b></summary>

If you prefer standard Python packaging tools, ensure your `virtual environment`_ is activated:

```bash
pip install --upgrade pyhelpers
```

To install with all optional dependencies:

```bash
pip install --upgrade "pyhelpers[full]"
```

</details>

For detailed options, development setup and Windows troubleshooting (e.g. installing C-extension wheels), see the full [Installation Guide](https://pyhelpers.readthedocs.io/en/latest/installation.html).

## Quick start

For a concise guide on how to use PyHelpers, check out the [Quick Start](https://pyhelpers.readthedocs.io/en/latest/quick-start.html) tutorial, which includes illustrative examples for each of the [subpackages](https://pyhelpers.readthedocs.io/en/latest/subpackages.html).

These examples briefly demonstrate the capabilities of PyHelpers in facilitating data manipulation tasks and streamlining work processes.

## Documentation

The complete PyHelpers Documentation is available in [HTML](https://pyhelpers.readthedocs.io/en/latest/) and [PDF](https://pyhelpers.readthedocs.io/_/downloads/en/latest/pdf/) formats. 

It is hosted on [Read the Docs](https://app.readthedocs.org/projects/pyhelpers/), and the HTML version is also accessible via [GitHub Pages](https://mikeqfu.github.io/pyhelpers/). The documentation includes detailed examples, tutorials and comprehensive references to help users get the most out of PyHelpers. 

## Cite as

Fu, Q. (2020). PyHelpers: An open-source toolkit for facilitating Python users' data manipulation tasks. Zenodo. [doi:10.5281/zenodo.4017438](https://doi.org/10.5281/zenodo.4017438).

```bibtex
@software{Fu_PyHelpers_2020, 
    author = {Fu, Qian},
    title = {{PyHelpers: An open-source toolkit for facilitating Python users' data manipulation tasks}},
    year = {2020},
    publisher = {Zenodo},
    doi = {10.5281/zenodo.4017438},
    license = {MIT},
    url = {https://doi.org/10.5281/zenodo.4017438},
}
```

For specific version references, please refer to [Zenodo](https://zenodo.org/search?q=conceptrecid%3A%224017438%22&f=allversions%3Atrue&l=list&p=1&s=10&sort=version).

## License

PyHelpers is licensed under the [MIT License](https://github.com/mikeqfu/pyhelpers/blob/master/LICENSE).

Please note that this project was initially licensed under the [GPLv3+](https://www.gnu.org/licenses/gpl-3.0.en.html#license-text) up to version *1.5.2*. Starting with version *2.0.0*, it has been re-licensed under the MIT License.
