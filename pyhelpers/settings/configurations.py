"""
Configurations.
"""

from .._cache import _check_dependency


def gdal_configurations(reset=False, max_tmpfile_size=None, interleaved_reading=True,
                        custom_indexing=False, compress_nodes=True):
    """
    Alters some default `configuration options <https://gdal.org/user/configoptions.html>`_
    of `GDAL/OGR <https://gdal.org>`_ drivers.

    :param reset: Whether to reset to default settings; defaults to ``False``.
    :type reset: bool
    :param max_tmpfile_size: Maximum size of the temporary file; defaults to ``None``.
    :type max_tmpfile_size: int | None
    :param interleaved_reading: Whether to enable interleaved reading; defaults to ``True``.
    :type interleaved_reading: bool
    :param custom_indexing: Whether to enable custom indexing; defaults to ``False``.
    :type custom_indexing: bool
    :param compress_nodes: Whether to compress nodes in temporary database; defaults to ``True``.
    :type compress_nodes: bool

    **Examples**::

        >>> from pyhelpers.settings import gdal_configurations
        >>> gdal_configurations()

    .. note::

        These configurations are particularly useful when working with
        `GDAL <https://pypi.org/project/GDAL/>`_ to process large
        `PBF <https://wiki.openstreetmap.org/wiki/PBF_Format>`_ files.
        For instance, these settings are applied by default in the
        `pydriosm <https://pypi.org/project/pydriosm/>`_ package for handling
        `OpenStreetMap <https://www.openstreetmap.org/>`_ data in PBF format.

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
