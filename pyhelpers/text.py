""" Helper functions for manipulating textual data """

import collections.abc
import os
import pathlib
import re
import string
import subprocess

import numpy as np
import pandas as pd

from pyhelpers.ops import dict_to_dataframe
from pyhelpers.store import get_specific_filepath_info


def find_similar_str(x, lookup_list, processor='fuzzywuzzy', **kwargs):
    """
    Find similar string from a list of strings.

    :param x: a string-type variable
    :type x: str
    :param lookup_list: a sequence of strings for lookup
    :type lookup_list: iterable
    :param processor: the package to use for this function, incl. `'fuzzywuzzy'` (default) and `'nltk'`

        - if `processor == 'fuzzywuzzy'`, the function relies on `fuzzywuzzy.fuzz.token_set_ratio`_
        - if `processor == 'nltk'`, the function relies on `nltk.metrics.distance.edit_distance`_

    :type processor: str
    :param kwargs: optional parameters of `fuzzywuzzy.fuzz.token_set_ratio`_ or `nltk.metrics.distance.edit_distance`_
    :return: a string-type variable that should be similar to (or the same as) ``x``
    :rtype: str

    .. _`fuzzywuzzy.fuzz.token_set_ratio`: https://github.com/seatgeek/fuzzywuzzy
    .. _`nltk.metrics.distance.edit_distance`:
        https://www.nltk.org/api/nltk.metrics.html#nltk.metrics.distance.edit_distance

    **Examples**::

        from pyhelpers.text import find_similar_str

        x = 'apple'
        lookup_list = ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel']

        processor = 'fuzzywuzzy'
        find_similar_str(x, lookup_list, processor)  # 'app'

        processor = 'nltk'
        find_similar_str(x, lookup_list, processor, substitution_cost=1)  # 'apple'
        find_similar_str(x, lookup_list, processor, substitution_cost=100)  # 'app'
    """

    assert processor in ('fuzzywuzzy', 'nltk'), "`processor` must be either \"fuzzywuzzy\" or \"nltk\"."

    if processor == 'fuzzywuzzy':
        import fuzzywuzzy.fuzz
        l_distances = [fuzzywuzzy.fuzz.token_set_ratio(x, a, **kwargs) for a in lookup_list]
        return lookup_list[l_distances.index(max(l_distances))] if l_distances else None
    elif processor == 'nltk':
        import nltk.metrics.distance
        l_distances = [nltk.metrics.distance.edit_distance(x, a, **kwargs) for a in lookup_list]
        return lookup_list[l_distances.index(min(l_distances))] if l_distances else None


def find_matched_str(x, lookup_list):
    """
    Find from a list the closest, case-insensitive, str to the given one.

    :param x: a string-type variable, if None, the function will return None
    :type x: str, None
    :param lookup_list: a sequence of strings for lookup
    :type lookup_list: iterable
    :return: a string-type variable that is case-insensitively the same as ``x``
    :rtype: generator

    **Examples**::

        from pyhelpers.text import find_matched_str

        x = 'apple'
        lookup_list_0 = ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel']

        res_0 = find_matched_str(x, lookup_list_0)  # list(res_0) == []

        lookup_list_1 = ['abc', 'aapl', 'app', 'apple', 'ape', 'apex', 'apel']

        res_1 = find_matched_str(x, lookup_list_1)  # list(res_1) == ['apple']
    """

    assert isinstance(x, str), "`x` must be a string."
    assert isinstance(lookup_list, collections.abc.Iterable), "`lookup_list` must be iterable."
    if x == '' or x is None:
        return None
    else:
        for y in lookup_list:
            if re.match(x, y, re.IGNORECASE):
                yield y


def remove_punctuation(raw_txt, rm_whitespace=False):
    """
    Remove punctuation from string-type data.

    :param raw_txt: string-type data
    :type raw_txt: str
    :param rm_whitespace: whether to remove whitespace from the input string as well, defaults to ``False``
    :type rm_whitespace: bool
    :return: text with punctuation removed
    :rtype: str

    **Examples**::

        from pyhelpers.text import remove_punctuation

        raw_txt = 'Hello\tworld! :-)'
        txt = remove_punctuation(raw_txt)  # 'Hello\tworld '

        rm_whitespace = True
        txt = remove_punctuation(raw_txt, rm_whitespace)  # 'Hello world'
    """

    try:
        txt = raw_txt.translate(str.maketrans('', '', string.punctuation))
    except Exception as e:
        print(e)
        txt = ''.join(x for x in raw_txt if x not in string.punctuation)
    if rm_whitespace:
        txt = ' '.join(txt.split())
    return txt


def count_words(raw_txt):
    """
    Count the total for each different word.

    :param raw_txt: any text
    :type raw_txt: str
    :return: number of each word in ``raw_docs``
    :rtype: dict

    **Examples**::

        from pyhelpers.text import remove_punctuation
        from pyhelpers.text import count_words

        raw_txt = 'This is an apple. That is a pear. Hello world!'

        count_words(raw_txt)
        # {'This': 1,
        #  'is': 2,
        #  'an': 1,
        #  'apple': 1,
        #  '.': 2,
        #  'That': 1,
        #  'a': 1,
        #  'pear': 1,
        #  'Hello': 1,
        #  'world': 1,
        #  '!': 1}

        count_words(remove_punctuation(raw_txt))
        # {'This': 1,
        #  'is': 2,
        #  'an': 1,
        #  'apple': 1,
        #  'That': 1,
        #  'a': 1,
        #  'pear': 1,
        #  'Hello': 1,
        #  'world': 1}
    """

    import nltk
    doc_text = str(raw_txt)
    tokens = nltk.word_tokenize(doc_text)
    word_count_dict = dict(collections.Counter(tokens))
    return word_count_dict


def calculate_idf(raw_documents, rm_punc=False):
    """
    Calculate inverse document frequency.

    :param raw_documents: a series of documents
    :type raw_documents: pandas.Series
    :param rm_punc: whether to remove punctuation from ``raw_documents``, defaults to ``False``
    :type rm_punc: bool
    :return: term frequency (TF) of ``raw_documents``, and inverse document frequency
    :rtype: tuple [of length 2]

    **Examples**::

        import pandas as pd
        from pyhelpers.text import calculate_idf

        raw_documents = pd.Series(['This is an apple.',
                                   'That is a pear.',
                                   'It is human being.',
                                   'Hello world!'])

        rm_punc = False
        docs_tf, corpus_idf = calculate_idf(raw_documents, rm_punc)
        print(docs_tf)
        # 0    {'This': 1, 'is': 1, 'an': 1, 'apple': 1, '.': 1}
        # 1      {'That': 1, 'is': 1, 'a': 1, 'pear': 1, '.': 1}
        # 2    {'It': 1, 'is': 1, 'human': 1, 'being': 1, '.'...
        # 3                     {'Hello': 1, 'world': 1, '!': 1}
        print(corpus_idf)
        # {'This': 0.6931471805599453, 'is': 0.0, 'an': 0.6931471805599453, ...

        rm_punc = True
        docs_tf, corpus_idf = calculate_idf(raw_documents, rm_punc)
        print(docs_tf)
        # 0     {'This': 1, 'is': 1, 'an': 1, 'apple': 1}
        # 1       {'That': 1, 'is': 1, 'a': 1, 'pear': 1}
        # 2    {'It': 1, 'is': 1, 'human': 1, 'being': 1}
        # 3                      {'Hello': 1, 'world': 1}
        print(corpus_idf)
        # {'This': 0.6931471805599453, 'is': 0.0, 'an': 0.6931471805599453, ...
    """

    assert isinstance(raw_documents, pd.Series)

    raw_docs = raw_documents.copy()
    if rm_punc:
        raw_docs = raw_docs.map(remove_punctuation)

    docs_tf = raw_docs.map(count_words)
    tokens_in_docs = docs_tf.map(lambda x: list(x.keys()))

    n = len(raw_docs)
    tokens = [w for tokens in tokens_in_docs for w in tokens]
    tokens_counter = dict_to_dataframe(dict(collections.Counter(tokens)), 'token', 'count')
    tokens_counter['idf'] = np.log(n / (1 + tokens_counter['count'].values))

    corpus_idf = dict(zip(tokens_counter['token'], tokens_counter['idf']))

    return docs_tf, corpus_idf


def calculate_tf_idf(raw_documents, rm_punc=False):
    """
    Count term frequency–inverse document frequency.

    :param raw_documents: a series of documents
    :type raw_documents: pandas.Series
    :param rm_punc: whether to remove punctuation from ``raw_documents``, defaults to ``False``
    :type rm_punc: bool
    :return: tf-idf of the ``raw_documents``
    :rtype: dict

    **Examples**::

        import pandas as pd
        from pyhelpers.text import calculate_tf_idf

        raw_documents = pd.Series(['This is an apple.',
                                   'That is a pear.',
                                   'It is human being.',
                                   'Hello world!'])

        rm_punc = False
        docs_tf_idf = calculate_tf_idf(raw_documents, rm_punc)
        # 0    {'This': 0.6931471805599453, 'is': 0.0, 'an': ...
        # 1    {'That': 0.6931471805599453, 'is': 0.0, 'a': 0...
        # 2    {'It': 0.6931471805599453, 'is': 0.0, 'human':...
        # 3    {'Hello': 0.6931471805599453, 'world': 0.69314...

        rm_punc = True
        docs_tf_idf = calculate_tf_idf(raw_documents, rm_punc)
        # 0    {'This': 0.6931471805599453, 'is': 0.0, 'an': ...
        # 1    {'That': 0.6931471805599453, 'is': 0.0, 'a': 0...
        # 2    {'It': 0.6931471805599453, 'is': 0.0, 'human':...
        # 3    {'Hello': 0.6931471805599453, 'world': 0.69314...
    """

    docs_tf, corpus_idf = calculate_idf(raw_documents=raw_documents, rm_punc=rm_punc)
    docs_tf_idf = docs_tf.apply(lambda x: {k: v * corpus_idf[k] for k, v in x.items() if k in corpus_idf})
    return docs_tf_idf


def euclidean_distance_between_texts(txt1, txt2):
    """
    Compute Euclidean distance of two sentences.

    :param txt1: any text
    :type txt1: str
    :param txt2: any text
    :type txt2: str
    :return: Euclidean distance between ``txt1`` and ``txt2``
    :rtype: float

    **Example**::

        from pyhelpers.text import euclidean_distance_between_texts

        txt1, txt2 = 'This is an apple.', 'That is a pear.'
        euclidean_distance_between_texts(txt1, txt2)  # 2.6457513110645907
    """

    if isinstance(txt1, str) and isinstance(txt2, str):
        doc_words = set(txt1.split() + txt2.split())
    else:
        assert isinstance(txt1, list), isinstance(txt2, list)
        doc_words = set(txt1 + txt2)

    s1_count, s2_count = [], []
    for word in doc_words:
        s1_count.append(txt1.count(word))
        s2_count.append(txt2.count(word))

    # ed = np.sqrt(np.sum((np.array(s1_count) - np.array(s2_count)) ** 2))
    ed = np.linalg.norm(np.array(s1_count) - np.array(s2_count))

    return ed


def cosine_similarity_between_texts(txt1, txt2, cosine_distance=False):
    """
    Calculate cosine similarity of two sentences.

    :param txt1: any text
    :type txt1: str
    :param txt2: any text
    :type txt2: str
    :param cosine_distance: whether to get cosine distance, which is (1 - cosine similarity), defaults to ``False``
    :type cosine_distance: bool
    :return: cosine similarity (or distance)
    :rtype: float

    **Examples**::

        from pyhelpers.text import cosine_similarity_between_texts

        txt1, txt2 = 'This is an apple.', 'That is a pear.'

        cosine_distance = False
        cosine_similarity_between_texts(txt1, txt2)  # 0.6963106238227914

        cosine_distance = True
        cosine_similarity_between_texts(txt1, txt2, cosine_distance)  # 0.3036893761772086
    """

    if isinstance(txt1, str) and isinstance(txt2, str):
        doc_words = set(txt1.split() + txt2.split())
    else:
        assert isinstance(txt1, list), isinstance(txt2, list)
        doc_words = set(txt1 + txt2)

    s1_count, s2_count = [], []
    for word in doc_words:
        s1_count.append(txt1.count(word))
        s2_count.append(txt2.count(word))

    s1_count, s2_count = np.array(s1_count), np.array(s2_count)

    similarity = np.dot(s1_count, s2_count)
    cos_similarity = np.divide(similarity, np.linalg.norm(s1_count) * np.linalg.norm(s2_count))

    if cosine_distance:
        cos_similarity = 1 - cos_similarity

    return cos_similarity


def save_web_page_as_pdf(url_to_web_page, path_to_pdf, page_size='A4', zoom=1.0, encoding='UTF-8', verbose=False,
                         **kwargs):
    """
    Save a web page as a PDF file, using `wkhtmltopdf <https://wkhtmltopdf.org/>`_.

    :param url_to_web_page: URL of a web page
    :type url_to_web_page: str
    :param path_to_pdf: path where a .pdf is saved
    :type path_to_pdf: str
    :param page_size: page size, defaults to ``'A4'``
    :type page_size: str
    :param zoom: a parameter to zoom in/out, defaults to ``1.0``
    :type zoom: float
    :param encoding: encoding format defaults to ``'UTF-8'``
    :type encoding: str
    :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
    :type verbose: bool
    :param kwargs: optional parameters of `pdfkit.from_url <https://pypi.org/project/pdfkit/>`_

    **Example**::

        from pyhelpers.dir import cd
        from pyhelpers.text import save_web_page_as_pdf

        page_size = 'A4'
        zoom = 1.0
        encoding = 'UTF-8'
        verbose = True

        url_to_web_page = 'https://github.com/mikeqfu/pyhelpers'
        path_to_pdf = cd("tests/data", "pyhelpers.pdf")

        save_web_page_as_pdf(url_to_web_page, path_to_pdf, verbose=verbose)
    """

    path_to_wkhtmltopdf = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"

    import pdfkit
    if os.path.isfile(path_to_wkhtmltopdf):
        config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    else:
        config = pdfkit.configuration(wkhtmltopdf="wkhtmltopdf.exe")

    get_specific_filepath_info(path_to_pdf, verbose=verbose, vb_end=" ... \n", ret_info=False)

    try:
        # print("Saving the web page \"{}\" as PDF".format(url_to_web_page)) if verbose else ""
        pdf_options = {'page-size': page_size,
                       # 'margin-top': '0',
                       # 'margin-right': '0',
                       # 'margin-left': '0',
                       # 'margin-bottom': '0',
                       'zoom': str(float(zoom)),
                       'encoding': encoding}
        os.makedirs(os.path.dirname(path_to_pdf), exist_ok=True)
        if os.path.isfile(path_to_pdf):
            os.remove(path_to_pdf)
        status = pdfkit.from_url(url_to_web_page, path_to_pdf, configuration=config, options=pdf_options, **kwargs)
        if verbose and not status:
            print("Failed. Check if the URL is available.")

    except Exception as e:
        print("Failed. {}".format(e)) if verbose else ""
        print("\"wkhtmltopdf\" (https://wkhtmltopdf.org/) is required to run this function. "
              "It is not found on this device.") if verbose else ""


def convert_md_to_rst(path_to_md, path_to_rst, verbose=False, **kwargs):
    """
    Convert a markdown file (.md) to a reStructuredText (.rst) file, using `Pandoc`_ or `pypandoc`_.

    .. _`Pandoc`: https://pandoc.org/
    .. _`pypandoc`: https://github.com/bebraw/pypandoc

    :param path_to_md: path where a markdown file is saved
    :type path_to_md: str
    :param path_to_rst: path where a reStructuredText file is saved
    :type path_to_rst: str
    :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
    :type verbose: bool
    :param kwargs: optional parameters of `pypandoc.convert_file <https://github.com/bebraw/pypandoc>`_

    **Example**::

        from pyhelpers.dir import cd
        from pyhelpers.text import convert_md_to_rst

        path_to_md = cd("tests/data", "markdown.md")
        path_to_rst = cd("tests/data", "markdown.rst")
        verbose = True

        convert_md_to_rst(path_to_md, path_to_rst, verbose)
    """

    abs_md_path, abs_rst_path = pathlib.Path(path_to_md), pathlib.Path(path_to_rst)
    # assert abs_md_path.suffix == ".md" and abs_rst_path.suffix == ".rst"

    if verbose:
        print("Converting \"{}\" to .rst ... ".format(abs_md_path.name))
        get_specific_filepath_info(abs_rst_path, verbose=verbose, vb_end=" ... ")
    try:
        pandoc_exe = "C:\\Program Files\\Pandoc\\pandoc.exe"
        if os.path.isfile(pandoc_exe):
            subprocess.call('"{}" "{}" -f markdown -t rst -s -o "{}"'.format(pandoc_exe, abs_md_path, abs_rst_path))
        else:
            subprocess.call('pandoc "{}" -f markdown -t rst -s -o "{}"'.format(abs_md_path, abs_rst_path))
        print("Successfully.") if verbose else ""
    except FileNotFoundError:
        import pypandoc
        pypandoc.convert_file(str(abs_md_path), 'rst', outputfile=str(abs_rst_path), **kwargs)
        print("Successfully.") if verbose else ""
    except Exception as e:
        print("Failed. {}".format(e))
