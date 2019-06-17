""" Download files """

import os
import time
import urllib.request

import requests
import tqdm


# Download and show progress
def download(url, path_to_file, wait_to_retry=3600, show_progress=True):
    """
    Reference: https://stackoverflow.com/questions/37573483/progress-bar-while-download-file-over-http-with-requests
    :param url: [str]
    :param path_to_file: [str]
    :param wait_to_retry: [int; float]
    :param show_progress: [bool]
    :return:
    """

    directory = os.path.dirname(path_to_file)
    if not os.path.exists(directory):
        os.mkdir(directory)

    if show_progress:
        # Using 'Requests'
        r = requests.get(url, stream=True)  # Streaming, so we can iterate over the response

        if r.status_code == 429:
            time.sleep(wait_to_retry)

        total_size = int(r.headers.get('content-length'))  # Total size in bytes
        if total_size == 0:
            print("ERROR! Something went wrong")
        block_size = 1024 * 1024
        block_no = total_size // block_size

        wrote = 0
        with open(path_to_file, 'wb') as f:
            for data in tqdm.tqdm(r.iter_content(block_size), total=block_no, unit='MB'):
                wrote = wrote + len(data)
                f.write(data)
            f.close()

        if wrote != total_size:
            print("ERROR! Something went wrong")

        r.close()

    else:
        print("\nDownloading \"{}\" ... ".format(os.path.basename(path_to_file)), end="")
        try:
            urllib.request.urlretrieve(url, path_to_file)
            print("\nDone.")
        except Exception as e:
            print("\nFailed. {}".format(e))


# Show downloading progress
def show_progress_bar(block_count, block_size, total_size):

    import progressbar

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

    p_bar = make_custom_progressbar()
    if p_bar.max_value is None:
        p_bar.max_value = total_size
        p_bar.start()
    p_bar.update(min(block_count * block_size, total_size))
