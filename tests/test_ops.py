import matplotlib.pyplot as plt

from pyhelpers.ops import *


# For general use

def test_confirmed():
    prompt = "Create Directory?"

    if confirmed(prompt, resp=True):
        print(True)
    # Create Directory? [No]|Yes: yes
    # True


# For iterable manipulation

def test_split_list_by_size():
    lst = list(range(0, 10))

    sub_len = 3
    lists = split_list_by_size(lst, sub_len)
    print(list(lists))
    # [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


def test_split_list():
    lst = list(range(0, 10))

    num_of_sub = 3
    lists = list(split_list(lst, num_of_sub))
    print(list(lists))
    # [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]


def test_split_iterable():
    iterable = list(range(0, 10))
    chunk_size = 3
    for x in split_iterable(iterable, chunk_size):
        print(list(x))
    # [0, 1, 2]
    # [3, 4, 5]
    # [6, 7, 8]
    # [9]

    iterable = pd.Series(range(0, 20))
    chunk_size = 5
    for x in split_iterable(iterable, chunk_size):
        print(list(x))
    # [0, 1, 2, 3, 4]
    # [5, 6, 7, 8, 9]
    # [10, 11, 12, 13, 14]
    # [15, 16, 17, 18, 19]


def test_update_nested_dict():
    source_dict = {'key_1': 1}
    updates = {'key_2': 2}
    source_dict = update_nested_dict(source_dict, updates)
    print(source_dict)
    # {'key_1': 1, 'key_2': 2}

    source_dict = {'key': 'val_old'}
    updates = {'key': 'val_new'}
    source_dict = update_nested_dict(source_dict, updates)
    print(source_dict)
    # {'key': 'val_new'}

    source_dict = {'key': {'k1': 'v1_old', 'k2': 'v2'}}
    updates = {'key': {'k1': 'v1_new'}}
    source_dict = update_nested_dict(source_dict, updates)
    print(source_dict)
    # {'key': {'k1': 'v1_new', 'k2': 'v2'}}

    source_dict = {'key': {'k1': {}, 'k2': 'v2'}}
    updates = {'key': {'k1': 'v1'}}
    source_dict = update_nested_dict(source_dict, updates)
    print(source_dict)
    # {'key': {'k1': 'v1', 'k2': 'v2'}}

    source_dict = {'key': {'k1': 'v1', 'k2': 'v2'}}
    updates = {'key': {'k1': {}}}
    source_dict = update_nested_dict(source_dict, updates)
    print(source_dict)
    # {'key': {'k1': 'v1', 'k2': 'v2'}}


def test_get_all_values_from_nested_dict():
    key = 'key'
    target_dict = {'key': 'val'}
    val = get_all_values_from_nested_dict(key, target_dict)
    print(list(val))
    # [['val']]

    key = 'k1'
    target_dict = {'key': {'k1': 'v1', 'k2': 'v2'}}
    val = get_all_values_from_nested_dict(key, target_dict)
    print(list(val))
    # [['v1']]

    key = 'k1'
    target_dict = {'key': {'k1': ['v1', 'v1_1']}}
    val = get_all_values_from_nested_dict(key, target_dict)
    print(list(val))
    # [['v1', 'v1_1']]

    key = 'k2'
    target_dict = {'key': {'k1': 'v1', 'k2': ['v2', 'v2_1']}}
    val = get_all_values_from_nested_dict(key, target_dict)
    print(list(val))
    # [['v2', 'v2_1']]


def test_remove_multiple_keys_from_dict():
    target_dict = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'k4': 'v4', 'k5': 'v5'}

    remove_multiple_keys_from_dict(target_dict, 'k1', 'k3', 'k4')

    print(target_dict)
    # {'k2': 'v2', 'k5': 'v5'}


# Tabular data

def test_detect_nan_for_str_column():
    data_frame = pd.DataFrame(np.resize(range(10), (10, 2)), columns=['a', 'b'])
    data_frame.iloc[3, 1] = np.nan

    nan_col_pos = detect_nan_for_str_column(data_frame, column_names=None)
    print(list(nan_col_pos))
    # [1]


def test_create_rotation_matrix():
    theta = 30

    rotation_mat = create_rotation_matrix(theta)
    print(rotation_mat)
    # [[-0.98803162  0.15425145]
    #  [-0.15425145 -0.98803162]]


def test_dict_to_dataframe():
    input_dict = {'a': 1, 'b': 2}

    data_frame = dict_to_dataframe(input_dict)
    print(data_frame)
    #   key  value
    # 0   a      1
    # 1   b      2


def test_parse_csr_matrix():
    import scipy.sparse
    from pyhelpers.dir import cd

    indptr = np.array([0, 2, 3, 6])
    indices = np.array([0, 2, 2, 0, 1, 2])
    data = np.array([1, 2, 3, 4, 5, 6])
    csr_m = scipy.sparse.csr_matrix((data, indices, indptr), shape=(3, 3))

    path_to_csr = cd("tests\\data", "csr_mat.npz")
    np.savez_compressed(path_to_csr,
                        indptr=csr_m.indptr,
                        indices=csr_m.indices,
                        data=csr_m.data,
                        shape=csr_m.shape)

    csr_mat = parse_csr_matrix(path_to_csr, verbose=True)
    # Loading "..\\tests\\data\\csr_mat.npz" ... Done.

    # .nnz gets the count of explicitly-stored values (non-zeros)
    print((csr_mat != csr_m).count_nonzero() == 0)
    # True

    print((csr_mat != csr_m).nnz == 0)
    # True


# For simple computation

def test_get_extreme_outlier_bounds():
    num_dat = pd.DataFrame(range(100), columns=['col'])

    k = 1.5
    lower_bound, upper_bound = get_extreme_outlier_bounds(num_dat, k)

    print((lower_bound, upper_bound))
    # (0.0, 148.5)


def test_interquartile_range():
    num_dat = pd.DataFrame(range(100), columns=['col'])

    iqr = interquartile_range(num_dat)
    print(iqr)
    # 49.5


def test_find_closest_date():
    date = '2019-01-01'
    date_list = ['2019-01-02', '2019-01-03', '2019-01-04', '2019-01-05', '2019-01-06']

    closest_date = find_closest_date(date, date_list, as_datetime=True)
    print(closest_date)
    # 2019-01-02 00:00:00

    date = pd.to_datetime('2019-01-01')
    date_list = []
    for d in range(1, 11):
        date_list.append(date + pd.Timedelta(days=d))

    closest_date = find_closest_date(date, date_list, as_datetime=False)
    print(closest_date)
    # 2019-01-02 00:00:00.000000


# For graph plotting

def test_cmap_discretisation():
    import matplotlib.cm

    cmap = matplotlib.cm.Accent
    n_colours = 5

    cm_accent = cmap_discretisation(cmap, n_colours)

    x = np.resize(range(100), (5, 100))

    print("Colour map", end=" ... ")

    fig, ax = plt.subplots(figsize=(10, 2))
    ax.imshow(x, cmap=cm_accent, interpolation='nearest')
    plt.axis('off')
    plt.tight_layout()

    print("Done.")


def test_colour_bar_index():
    import matplotlib.cm

    cmap = matplotlib.cm.Accent
    n_colours = 5

    print("Colour bar index 1", end=" ... ")

    plt.figure(figsize=(2, 6))
    cbar = colour_bar_index(cmap, n_colours)
    cbar.ax.tick_params(labelsize=18)
    plt.axis('off')
    plt.tight_layout()

    print("Done.")

    labels = list('abcde')

    print("Colour bar index 2", end=" ... ")

    plt.figure(figsize=(2, 6))
    colour_bar = colour_bar_index(cmap, n_colours, labels)
    colour_bar.ax.tick_params(labelsize=18)
    plt.axis('off')
    plt.tight_layout()

    print("Done.")


# For web scraping

def test_fake_requests_headers():
    fake_header = fake_requests_headers()
    print(fake_header)
    # {'User-Agent': '<str>'}

    random = True
    fake_header = fake_requests_headers(random)
    print(fake_header)
    # {'User-Agent': '<str>'}


def test_download_file_from_url():
    url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'

    from pyhelpers.dir import cd

    path_to_file = cd("tests\\images", "python-logo.png")

    download_file_from_url(url, path_to_file)


if __name__ == '__main__':
    # For general use
    print("\nTesting 'confirmed()':")
    test_confirmed()

    # For iterable manipulation
    print("\nTesting 'split_list_by_size()':")
    test_split_list_by_size()

    print("\nTesting 'split_list()':")
    test_split_list()

    print("\nTesting 'split_iterable()':")
    test_split_iterable()

    print("\nTesting 'update_nested_dict()':")
    test_update_nested_dict()

    print("\nTesting 'get_all_values_from_nested_dict()':")
    test_get_all_values_from_nested_dict()

    print("\nTesting 'remove_multiple_keys_from_dict()':")
    test_remove_multiple_keys_from_dict()

    # Tabular data
    print("\nTesting 'detect_nan_for_str_column()':")
    test_detect_nan_for_str_column()

    print("\nTesting 'create_rotation_matrix()':")
    test_create_rotation_matrix()

    print("\nTesting 'dict_to_dataframe()':")
    test_dict_to_dataframe()

    print("\nTesting 'load_csr_matrix()':")
    test_parse_csr_matrix()

    # For simple computation
    print("\nTesting 'get_extreme_outlier_bounds()':")
    test_get_extreme_outlier_bounds()

    print("\nTesting 'interquartile_range()':")
    test_interquartile_range()

    print("\nTesting 'find_closest_date()':")
    test_find_closest_date()

    # For graph plotting
    print("\nTesting 'cmap_discretisation()':")
    test_cmap_discretisation()

    print("\nTesting 'colour_bar_index()':")
    test_colour_bar_index()

    plt.show()

    # For web scraping
    print("\nTesting 'fake_requests_headers()':")
    test_fake_requests_headers()

    print("\nTesting 'download_file_from_url()':")
    test_download_file_from_url()
