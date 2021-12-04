ops
===

.. py:module:: pyhelpers.ops

.. automodule:: pyhelpers.ops
    :noindex:
    :no-members:
    :no-inherited-members:

General use
-----------

.. autosummary::
    :toctree: _generated/
    :template: function.rst

    confirmed
    get_obj_attr
    eval_dtype
    gps_to_utc
    parse_size
    get_number_of_chunks

Basic data manipulation
-----------------------

.. rubric:: Iterable
.. autosummary::
    :toctree: _generated/
    :template: function.rst

    loop_in_pairs
    split_list_by_size
    split_list
    split_iterable
    update_dict
    update_dict_keys
    get_dict_values
    remove_dict_keys
    merge_dicts

.. rubric:: Tabular data
.. autosummary::
    :toctree: _generated/
    :template: function.rst

    detect_nan_for_str_column
    create_rotation_matrix
    dict_to_dataframe
    parse_csr_matrix
    swap_cols
    swap_rows

Basic computation
-----------------

.. autosummary::
    :toctree: _generated/
    :template: function.rst

    get_extreme_outlier_bounds
    interquartile_range
    find_closest_date

Graph plotting
--------------

.. autosummary::
    :toctree: _generated/
    :template: function.rst

    cmap_discretisation
    colour_bar_index

Web data extraction
-------------------

.. autosummary::
    :toctree: _generated/
    :template: function.rst

    is_network_connected
    is_url
    is_url_connectable
    is_downloadable
    init_requests_session
    get_user_agent_strings
    get_user_agent_string
    fake_requests_headers
    download_file_from_url
