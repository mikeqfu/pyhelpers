""" Download files """

import os
import time


# Download and show progress
def download(url, path_to_file, wait_to_retry=3600):
    """
    Reference: https://stackoverflow.com/questions/37573483/progress-bar-while-download-file-over-http-with-requests
    :param url: [str]
    :param path_to_file: [str]
    :param wait_to_retry: [int; float]
    :return:
    """
    import requests
    r = requests.get(url, stream=True)  # Streaming, so we can iterate over the response

    if r.status_code == 429:
        time.sleep(wait_to_retry)

    total_size = int(r.headers.get('content-length'))  # Total size in bytes
    block_size = 1024 * 1024
    wrote = 0

    directory = os.path.dirname(path_to_file)
    if not os.path.exists(directory):
        os.mkdir(directory)

    import tqdm
    with open(path_to_file, 'wb') as f:
        for data in tqdm.tqdm(r.iter_content(block_size), total=total_size // block_size, unit='MB'):
            wrote = wrote + len(data)
            f.write(data)

    f.close()

    r.close()

    if total_size != 0 and wrote != total_size:
        print("ERROR, something went wrong")
