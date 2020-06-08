""" Helper functions for downloading """

import os
import time

import tqdm


def download(url, path_to_file, wait_to_retry=3600, **kwargs):
    """
    Download an object available at the given ``url``. See also [`D-1 <https://stackoverflow.com/questions/37573483/>`_]

    :param url: URL
    :type url: str
    :param path_to_file: a full path to which the downloaded object is saved as
    :type url: str
    :param wait_to_retry: a wait time to retry downloading, defaults to ``3600`` (in second)
    :type url: int, float
    :param kwargs: optional arguments of `io.open <https://docs.python.org/3/library/functions.html#open>`_

    Example::

        from pyhelpers.dir import cd

        url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        path_to_file = cd("python-logo.png")
        wait_to_retry = 3600

        download(url, path_to_file, wait_to_retry)
    """

    import requests
    r = requests.get(url, stream=True)  # Streaming, so we can iterate over the response

    if r.status_code == 429:
        time.sleep(wait_to_retry)

    total_size = int(r.headers.get('content-length'))  # Total size in bytes
    block_size = 1024 * 1024
    wrote = 0

    directory = os.path.dirname(path_to_file)
    if directory == "":
        path_to_file = os.path.join(os.getcwd(), path_to_file)
    else:
        if not os.path.exists(directory):
            os.makedirs(directory)

    with open(path_to_file, mode='wb', **kwargs) as f:
        for data in tqdm.tqdm(r.iter_content(block_size), total=total_size // block_size, unit='MB'):
            wrote = wrote + len(data)
            f.write(data)
    f.close()

    r.close()

    if total_size != 0 and wrote != total_size:
        print("ERROR, something went wrong")
