ops
===

.. py:module:: pyhelpers.ops

.. automodule:: pyhelpers.ops
    :noindex:
    :no-members:
    :no-inherited-members:

Basic computation / conversion
------------------------------

.. autosummary::
    :toctree: _generated/
    :template: function.rst

    get_utc_tai_offset
    gps_time_to_utc
    find_closest_date
    parse_size
    get_number_of_chunks
    interquartile_range
    get_extreme_outlier_bounds

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
    compare_dicts
    merge_dicts

.. rubric:: Tabular data
.. autosummary::
    :toctree: _generated/
    :template: function.rst

    detect_nan_for_str_column
    create_rotation_matrix
    dict_to_dataframe
    swap_cols
    swap_rows
    np_shift
    downcast_numeric_columns
    flatten_columns

Web data manipulation
---------------------

.. rubric:: Internet-related utilities
.. autosummary::
    :toctree: _generated/
    :template: function.rst

    is_network_connected
    is_url
    is_url_connectable
    init_requests_session
    load_user_agent_strings
    get_user_agent_string
    fake_requests_headers

.. rubric:: File downloads utilities
.. autosummary::
    :toctree: _generated/
    :template: function.rst

    is_downloadable
    download_file_from_url

.. autosummary::
    :toctree: _generated/
    :template: class.rst

    GitHubFileDownloader

.. rubric:: API-related utilities
.. autosummary::
    :toctree: _generated/
    :template: class.rst

    CrossRefOrcid

Misc general utilities
----------------------

.. autosummary::
    :toctree: _generated/
    :template: function.rst

    confirmed
    get_obj_attr
    eval_dtype
    hash_password
    verify_password
    func_running_time
    get_git_branch
    get_ansi_colour_code
