""" Download files """

import os

import progressbar
import requests
import tqdm


# Download and show progress
def download(url, path_to_file):
    """

    Reference: https://stackoverflow.com/questions/37573483/progress-bar-while-download-file-over-http-with-requests

    :param url:
    :param path_to_file:
    :return:
    """
    r = requests.get(url, stream=True)  # Streaming, so we can iterate over the response
    total_size = int(r.headers.get('content-length'))  # Total size in bytes
    block_size = 1024 * 1024
    wrote = 0

    directory = os.path.dirname(path_to_file)
    if not os.path.exists(directory):
        os.mkdir(directory)

    with open(path_to_file, 'wb') as f:
        for data in tqdm.tqdm(r.iter_content(block_size), total=total_size // block_size, unit='MB'):
            wrote = wrote + len(data)
            f.write(data)
    if total_size != 0 and wrote != total_size:
        print("ERROR, something went wrong")


# Make a custom bar to show downloading progress
def make_custom_progressbar():
    widgets = [progressbar.Bar(),
               ' ',
               progressbar.Percentage(),
               ' [',
               progressbar.Timer(),
               '] ',
               progressbar.FileTransferSpeed(),
               ' (',
               progressbar.ETA(),
               ') ']
    progress_bar = progressbar.ProgressBar(widgets=widgets)
    return progress_bar


#
def show_progress(block_count, block_size, total_size):
    p_bar = make_custom_progressbar()
    if p_bar.max_value is None:
        p_bar.max_value = total_size
        p_bar.start()
    p_bar.update(min(block_count * block_size, total_size))
