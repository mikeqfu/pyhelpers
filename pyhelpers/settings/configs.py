"""
Configurations.
"""

from .._cache import _check_dependency


# ==================================================================================================
# Configurations
# ==================================================================================================

def gdal_configurations(reset=False, max_tmpfile_size=None, interleaved_reading=True,
                        custom_indexing=False, compress_nodes=True):
    """
    Alter some default `configuration options <https://gdal.org/user/configoptions.html>`_
    of `GDAL/OGR <https://gdal.org>`_ drivers.

    :param reset: whether to reset to default settings, defaults to ``False``
    :type reset: bool
    :param max_tmpfile_size: maximum size of the temporary file, defaults to ``None``
    :type max_tmpfile_size: int | None
    :param interleaved_reading: whether to enable interleaved reading, defaults to ``True``
    :type interleaved_reading: bool
    :param custom_indexing: whether to enable custom indexing, defaults to ``False``
    :type custom_indexing: bool
    :param compress_nodes: whether to compress nodes in temporary DB. defaults to ``True``
    :type compress_nodes: bool

    **Examples**::

        >>> from pyhelpers.settings import gdal_configurations

        >>> gdal_configurations()

    .. note::

        This can be useful when using `GDAL`_ to parse a large PBF file.
        For example, ``gdal_configurations()`` is applied by default when importing the package
        `pydriosm`_, which can be used to work with `OpenStreetMap`_ data of `PBF format`_.

        .. _GDAL: https://pypi.org/project/GDAL/
        .. _pydriosm: https://pypi.org/project/pydriosm/
        .. _OpenStreetMap: https://www.openstreetmap.org/
        .. _PBF format: https://wiki.openstreetmap.org/wiki/PBF_Format

    .. seealso::

        - `OpenStreetMap XML and PBF <https://gdal.org/drivers/vector/osm.html>`_
        - `pydriosm Documentation <https://pydriosm.readthedocs.io/en/latest/>`_
    """

    osgeo_gdal = _check_dependency(name='osgeo.gdal')

    if reset is False:
        max_tmpfile_size_ = 5000 if max_tmpfile_size is None else max_tmpfile_size

        # Max. size (MB) of in-memory temporary file. Defaults to 100.
        osgeo_gdal.SetConfigOption('OSM_MAX_TMPFILE_SIZE', str(max_tmpfile_size_))
        # If it exceeds that value, it will go to disk.

        val_dict = {True: 'YES', False: 'NO'}

        osgeo_gdal.SetConfigOption('OGR_INTERLEAVED_READING', val_dict[interleaved_reading])
        osgeo_gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', val_dict[custom_indexing])
        osgeo_gdal.SetConfigOption('OSM_COMPRESS_NODES', val_dict[compress_nodes])

    elif reset is True:
        osgeo_gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'NO')
        osgeo_gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'YES')
        osgeo_gdal.SetConfigOption('OSM_COMPRESS_NODES', 'NO')
        osgeo_gdal.SetConfigOption('OSM_MAX_TMPFILE_SIZE', '100')
