""" Download files """

import os
import time

import tqdm


# Download and show progress
def download(url, path_to_file, wait_to_retry=3600, **kwargs):
    """
    :param url: [str] URL
    :param path_to_file: [str] a full path to which the downloaded object is saved as
    :param wait_to_retry: [int; float] a wait time to retry downloading (default: 3600 sec)
    :param kwargs: optional arguments used by `open()`

    Example:
        url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        path_to_file = os.path.join(os.getcwd(), "python-logo.png")
        wait_to_retry = 3600
        download(url, path_to_file, wait_to_retry)

    Reference: https://stackoverflow.com/questions/37573483/
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
