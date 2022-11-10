"""Manipulation of textual data."""

import collections
import re
import string

import numpy as np

from ._cache import _check_dependency, _ENGLISH_WRITTEN_NUMBERS


# ==================================================================================================
# Textual data preprocessing
# ==================================================================================================


def get_acronym(text, only_capitals=False, capitals_in_words=False):
    """
    Get an acronym (in capital letters) of an input text.

    :param text: any text
    :type text: str
    :param only_capitals: whether to include capital letters only, defaults to ``False``
    :type only_capitals: bool
    :param capitals_in_words: whether to include all captical letters in a single word,
        defaults to ``False``
    :type capitals_in_words: bool
    :return: acronym of the input ``str_var``
    :rtype: str

    **Examples**::

        >>> from pyhelpers.text import get_acronym

        >>> text_a = 'This is an apple.'
        >>> acron = get_acronym(text_a)
        >>> acron
        'TIAA'

        >>> text_b = "I'm at the University of Birmingham."
        >>> acron = get_acronym(text_b, only_capitals=True)
        >>> acron
        'IUB'

        >>> text_c = 'There is a "ConnectionError"!'
        >>> acron = get_acronym(text_c, capitals_in_words=True)
        >>> acron
        'TCE'
    """

    txt = remove_punctuation(text)

    if only_capitals:
        acronym = ''.join(x[0] for x in txt.split() if x[0].isupper())
    elif capitals_in_words:
        acronym = ''.join(list(filter(str.isupper, txt)))
    else:
        acronym = ''.join(x[0].upper() for x in txt.split())

    return acronym


def remove_punctuation(x, rm_whitespace=True):
    """
    Remove punctuation from string-type data.

    :param x: raw string-type data
    :type x: str
    :param rm_whitespace: whether to remove whitespace (incl. escape characters), defaults to ``True``
    :type rm_whitespace: bool
    :return: text with punctuation removed
    :rtype: str

    **Examples**::

        >>> from pyhelpers.text import remove_punctuation

        >>> raw_text = 'Hello world!\tThis is a test. :-)'

        >>> text = remove_punctuation(raw_text)
        >>> text
        'Hello world This is a test'

        >>> text = remove_punctuation(raw_text, rm_whitespace=False)
        >>> text
        'Hello world \tThis is a test'
    """

    x_ = re.sub(r'[^\w\s]', ' ', x)

    # y = ''.join(y_ for y_ in x_ if y_ not in string.punctuation)
    y = x_.translate(str.maketrans('', '', string.punctuation))

    z = y.strip()

    if rm_whitespace:
        z = ' '.join(z.split())

    return z


def extract_words1upper(x, join_with=None):
    """
    Extract words from a string by spliting it at occurrence of an uppercase letter.

    :param x: a string joined by a number of words each starting with an uppercase letter
    :type x: str
    :param join_with: a string with which to (re)join the single words, defaults to ``None``
    :type join_with: str or None
    :return: a list of single words each starting with an uppercase letter,
        or a single string joined together by them with ``join_with``
    :rtype: list or str

    **Examples**::

        >>> from pyhelpers.text import extract_words1upper

        >>> x1 = 'Network_Waymarks'
        >>> x1_ = extract_words1upper(x1)
        >>> x1_
        ['Network', 'Waymarks']

        >>> x2 = 'NetworkRailRetainingWall'
        >>> x2_ = extract_words1upper(x2, join_with=' ')
        >>> x2_
        'Network Rail Retaining Wall'
    """

    y = remove_punctuation(x)

    # re.sub(r"([A-Z])", r" \1", x).split()
    extracted_words = re.findall(r'[a-zA-Z][^A-Z]*', y)

    if join_with:
        extracted_words = join_with.join(extracted_words)

    return extracted_words


def numeral_english_to_arabic(x):
    """
    Convert a string which potentially is a number written in English to an Arabic number

    :param x: a number written in English
    :type x: str
    :return: a number written in Arabic
    :rtype: int

    **Examples**::

        >>> from pyhelpers.text import numeral_english_to_arabic

        >>> numeral_english_to_arabic('one')
        1

        >>> numeral_english_to_arabic('one hundred and one')
        101

        >>> numeral_english_to_arabic('a thousand two hundred and three')
        1203

        >>> numeral_english_to_arabic('200 and five')
        205

        >>> numeral_english_to_arabic('Two hundred and fivety')  # Two hundred and fifty
        Exception: Illegal word: "fivety"
    """

    current = result = 0

    for word in x.lower().replace('-', ' ').split():
        if word not in _ENGLISH_WRITTEN_NUMBERS and not word.isdigit():
            # word_ = find_similar_str(word, ENGLISH_WRITTEN_NUMBERS)
            # if word_ is None:
            raise Exception(f"Illegal word: \"{word}\"")
            # else:
            #     word = word_

        if word.isdigit():
            scale, increment = (1, int(word))
        else:
            scale, increment = _ENGLISH_WRITTEN_NUMBERS[word]
        current = current * scale + increment

        if scale > 100:
            result += current
            current = 0

    return result + current


# ==================================================================================================
# Textual data computation
# ==================================================================================================


def count_words(raw_txt):
    """
    Count the total for each different word.

    :param raw_txt: any text
    :type raw_txt: str
    :return: number of each word in ``raw_docs``
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.text import count_words, remove_punctuation

        >>> raw_text = 'This is an apple. That is a pear. Hello world!'

        >>> count_words(raw_text)
        {'This': 1,
         'is': 2,
         'an': 1,
         'apple': 1,
         '.': 2,
         'That': 1,
         'a': 1,
         'pear': 1,
         'Hello': 1,
         'world': 1,
         '!': 1}

        >>> count_words(remove_punctuation(raw_text))
        {'This': 1,
         'is': 2,
         'an': 1,
         'apple': 1,
         'That': 1,
         'a': 1,
         'pear': 1,
         'Hello': 1,
         'world': 1}
    """

    nltk_ = _check_dependency(name='nltk')

    doc_text = str(raw_txt)
    tokens = nltk_.word_tokenize(doc_text)

    word_count_dict = dict(collections.Counter(tokens))

    return word_count_dict


def calculate_idf(raw_documents, rm_punc=False):
    """
    Calculate inverse document frequency.

    :param raw_documents: a sequence of textual data
    :type raw_documents: typing.Iterable or typing.Sequence
    :param rm_punc: whether to remove punctuation from the input textual data, defaults to ``False``
    :type rm_punc: bool
    :return: term frequency (TF) of the input textual data, and inverse document frequency
    :rtype: tuple[list[dict], dict]

    **Examples**::

        >>> from pyhelpers.text import calculate_idf

        >>> raw_doc = [
        ...     'This is an apple.',
        ...     'That is a pear.',
        ...     'It is human being.',
        ...     'Hello world!']

        >>> docs_tf_, corpus_idf_ = calculate_idf(raw_doc, rm_punc=False)
        >>> docs_tf_
        [{'This': 1, 'is': 1, 'an': 1, 'apple': 1, '.': 1},
         {'That': 1, 'is': 1, 'a': 1, 'pear': 1, '.': 1},
         {'It': 1, 'is': 1, 'human': 1, 'being': 1, '.': 1},
         {'Hello': 1, 'world': 1, '!': 1}]

        >>> corpus_idf_
        {'This': 0.6931471805599453,
         'is': 0.0,
         'an': 0.6931471805599453,
         'apple': 0.6931471805599453,
         '.': 0.0,
         'That': 0.6931471805599453,
         'a': 0.6931471805599453,
         'pear': 0.6931471805599453,
         'It': 0.6931471805599453,
         'human': 0.6931471805599453,
         'being': 0.6931471805599453,
         'Hello': 0.6931471805599453,
         'world': 0.6931471805599453,
         '!': 0.6931471805599453}

        >>> docs_tf_, corpus_idf_ = calculate_idf(raw_doc, rm_punc=True)
        >>> docs_tf_
        [{'This': 1, 'is': 1, 'an': 1, 'apple': 1},
         {'That': 1, 'is': 1, 'a': 1, 'pear': 1},
         {'It': 1, 'is': 1, 'human': 1, 'being': 1},
         {'Hello': 1, 'world': 1}]

        >>> corpus_idf_
        {'This': 0.6931471805599453,
         'is': 0.0,
         'an': 0.6931471805599453,
         'apple': 0.6931471805599453,
         'That': 0.6931471805599453,
         'a': 0.6931471805599453,
         'pear': 0.6931471805599453,
         'It': 0.6931471805599453,
         'human': 0.6931471805599453,
         'being': 0.6931471805599453,
         'Hello': 0.6931471805599453,
         'world': 0.6931471805599453}
    """

    if rm_punc:
        raw_docs = [remove_punctuation(x) for x in raw_documents]
    else:
        raw_docs = raw_documents

    docs_tf = [count_words(x) for x in raw_docs]
    tokens_in_docs = (x.keys() for x in docs_tf)
    tokens = [k for keys in tokens_in_docs for k in keys]

    tokens_counter_dict = dict(collections.Counter(tokens))
    tokens_idf = np.log(len(raw_docs) / (1 + np.asarray(list(tokens_counter_dict.values()))))

    corpus_idf = dict(zip(tokens_counter_dict.keys(), tokens_idf))

    return docs_tf, corpus_idf


def calculate_tf_idf(raw_documents, rm_punc=False):
    """
    Count term frequency–inverse document frequency.

    :param raw_documents: a sequence of textual data
    :type raw_documents: typing.Iterable or typing.Sequence
    :param rm_punc: whether to remove punctuation from the input textual data, defaults to ``False``
    :type rm_punc: bool
    :return: tf-idf of the input textual data
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.text import calculate_tf_idf

        >>> raw_doc = [
        ...     'This is an apple.',
        ...     'That is a pear.',
        ...     'It is human being.',
        ...     'Hello world!']

        >>> docs_tf_idf_ = calculate_tf_idf(raw_documents=raw_doc)
        >>> docs_tf_idf_
        {'This': 0.6931471805599453,
         'is': 0.0,
         'an': 0.6931471805599453,
         'apple': 0.6931471805599453,
         '.': 0.0,
         'That': 0.6931471805599453,
         'a': 0.6931471805599453,
         'pear': 0.6931471805599453,
         'It': 0.6931471805599453,
         'human': 0.6931471805599453,
         'being': 0.6931471805599453,
         'Hello': 0.6931471805599453,
         'world': 0.6931471805599453,
         '!': 0.6931471805599453}

        >>> docs_tf_idf_ = calculate_tf_idf(raw_documents=raw_doc, rm_punc=True)
        >>> docs_tf_idf_
        {'This': 0.6931471805599453,
         'is': 0.0,
         'an': 0.6931471805599453,
         'apple': 0.6931471805599453,
         'That': 0.6931471805599453,
         'a': 0.6931471805599453,
         'pear': 0.6931471805599453,
         'It': 0.6931471805599453,
         'human': 0.6931471805599453,
         'being': 0.6931471805599453,
         'Hello': 0.6931471805599453,
         'world': 0.6931471805599453}
    """

    docs_tf, corpus_idf = calculate_idf(raw_documents=raw_documents, rm_punc=rm_punc)

    docs_tf_idf = {k: v * corpus_idf[k] for x in docs_tf for k, v in x.items() if k in corpus_idf}

    return docs_tf_idf


def _vectorize_text(*txt):
    txt_ = [
        re.compile(r"\w+").findall(x.lower()) if isinstance(x, str) else [x_.lower() for x_ in x]
        for x in txt]
    doc_words = set().union(*txt_)

    for x in txt_:
        yield [x.count(word) for word in doc_words]


def euclidean_distance_between_texts(txt1, txt2):
    """
    Compute Euclidean distance of two sentences.

    :param txt1: any text
    :type txt1: str
    :param txt2: any text
    :type txt2: str
    :return: Euclidean distance between the input textual data
    :rtype: float

    **Examples**::

        >>> from pyhelpers.text import euclidean_distance_between_texts

        >>> txt_1, txt_2 = 'This is an apple.', 'That is a pear.'

        >>> euclidean_distance = euclidean_distance_between_texts(txt_1, txt_2)
        >>> euclidean_distance
        2.449489742783178
    """

    s1_count, s2_count = list(_vectorize_text(txt1, txt2))

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
    :param cosine_distance: whether to get cosine distance, which is (1 - cosine similarity),
        defaults to ``False``
    :type cosine_distance: bool
    :return: cosine similarity (or distance)
    :rtype: float

    **Examples**::

        >>> from pyhelpers.text import cosine_similarity_between_texts

        >>> txt_1, txt_2 = 'This is an apple.', 'That is a pear.'

        >>> cos_sim = cosine_similarity_between_texts(txt_1, txt_2)
        >>> cos_sim
        0.25

        >>> cos_dist = cosine_similarity_between_texts(txt_1, txt_2, cosine_distance=True)
        >>> cos_dist  # 1 - cos_sim
        0.75
    """

    s1_count, s2_count = map(np.array, _vectorize_text(txt1, txt2))

    similarity = np.dot(s1_count, s2_count)
    cos_similarity = np.divide(similarity, np.linalg.norm(s1_count) * np.linalg.norm(s2_count))

    if cosine_distance:
        cos_similarity = 1 - cos_similarity

    return cos_similarity


# ==================================================================================================
# Textual data comparison
# ==================================================================================================


def find_matched_str(x, lookup_list):
    """
    Find all that are matched with a string from among a sequence of strings.

    :param x: a string-type variable
    :type x: str
    :param lookup_list: a sequence of strings for lookup
    :type lookup_list: typing.Iterable
    :return: a generator containing all that are matched with ``x``
    :rtype: typing.Generator or None

    **Examples**::

        >>> from pyhelpers.text import find_matched_str

        >>> lookup_lst = ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel']
        >>> res = find_matched_str('apple', lookup_lst)
        >>> list(res)
        []

        >>> lookup_lst += ['apple']
        >>> lookup_lst
        ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel', 'apple']

        >>> res = find_matched_str('apple', lookup_lst)
        >>> list(res)
        ['apple']

        >>> res = find_matched_str(r'app(le)?', lookup_lst)
        >>> list(res)
        ['app', 'apple']
    """

    if x is not None:
        for y in lookup_list:
            if re.match(x, y, re.IGNORECASE):
                yield y


def _find_str_by_difflib(x, lookup_list, n=1, ignore_punctuation=True, **kwargs):
    """
    Find ``n`` strings that are similar to ``x`` from among a sequence of candidates
    by using `difflib <https://docs.python.org/3/library/difflib.html>`_.

    :param x: a string-type variable
    :type x: str
    :param lookup_list: a sequence of strings for lookup
    :type lookup_list: typing.Iterable
    :param n: number of similar strings to return, defaults to ``1``;
        when ``n=None``, the function returns a sorted ``lookup_list``
        (in the descending order of similarity)
    :type n: int or None
    :param ignore_punctuation: whether to ignore punctuations in the search for similar texts,
        defaults to ``True``
    :type ignore_punctuation: bool
    :param kwargs: [optional] parameters of `difflib.get_close_matches`_
    :return: a string-type variable that should be similar to (or the same as) ``x``
    :rtype: str or list or None

    .. _`difflib.get_close_matches`:
        https://docs.python.org/3/library/difflib.html#difflib.get_close_matches
    """

    difflib_ = _check_dependency(name='difflib')

    x_, lookup_dict = x.lower(), {y.lower(): y for y in lookup_list}

    if ignore_punctuation:
        x_ = remove_punctuation(x_)
        lookup_dict = {remove_punctuation(k): v for k, v in lookup_dict.items()}

    sim_str_ = difflib_.get_close_matches(word=x_, possibilities=lookup_dict.keys(), n=n, **kwargs)

    if not sim_str_:
        sim_str = None
    elif len(sim_str_) == 1:
        sim_str = lookup_dict[sim_str_[0]]
    else:
        sim_str = [lookup_dict[k] for k in sim_str_]

    return sim_str


def _find_str_by_fuzzywuzzy(x, lookup_list, n=1, **kwargs):
    """
    Find ``n`` strings that are similar to ``x`` from among a sequence of candidates
    by using `FuzzyWuzzy <https://pypi.org/project/fuzzywuzzy/>`_.

    :param x: a string-type variable
    :type x: str
    :param lookup_list: a sequence of strings for lookup
    :type lookup_list: typing.Iterable
    :param n: number of similar strings to return, defaults to ``1``;
        when ``n=None``, the function returns a sorted ``lookup_list``
        (in the descending order of similarity)
    :type n: int or None
    :param kwargs: [optional] parameters of `fuzzywuzzy.fuzz.token_set_ratio`_
    :return: a string-type variable that should be similar to (or the same as) ``x``
    :rtype: str or list or None

    .. _`fuzzywuzzy.fuzz.token_set_ratio`: https://github.com/seatgeek/fuzzywuzzy

    **Tests**::

        >>> from pyhelpers.text import _find_str_by_fuzzywuzzy

        >>> lookup_lst = ['Anglia',
        ...               'East Coast',
        ...               'East Midlands',
        ...               'North and East',
        ...               'London North Western',
        ...               'Scotland',
        ...               'South East',
        ...               'Wales',
        ...               'Wessex',
        ...               'Western']

        >>> y = _find_str_by_fuzzywuzzy(x='angle', lookup_list=lookup_lst, n=1)
        >>> y
        'Anglia'

        >>> y = _find_str_by_fuzzywuzzy(x='123', lookup_list=lookup_lst, n=1)
        >>> y is None
        True
    """

    fuzzywuzzy_fuzz = _check_dependency(name='fuzzywuzzy.fuzz')

    lookup_list_ = list(lookup_list)

    l_distances = [fuzzywuzzy_fuzz.token_set_ratio(s1=x, s2=a, **kwargs) for a in lookup_list_]

    if sum(l_distances) == 0:
        sim_str = None
    else:
        if n == 1:
            sim_str = lookup_list_[l_distances.index(max(l_distances))]
        else:
            sim_str = [lookup_list_[i] for i in np.argsort(l_distances)[::-1]][:n]

    return sim_str


def find_similar_str(x, lookup_list, n=1, ignore_punctuation=True, engine='difflib', **kwargs):
    """
    Find ``n`` strings that are similar to ``x`` from among a sequence of candidates.

    :param x: a string-type variable
    :type x: str
    :param lookup_list: a sequence of strings for lookup
    :type lookup_list: typing.Iterable
    :param n: number of similar strings to return, defaults to ``1``;
        when ``n=None``, the function returns a sorted ``lookup_list``
        (in the descending order of similarity)
    :type n: int or None
    :param ignore_punctuation: whether to ignore punctuations in the search for similar texts,
        defaults to ``True``
    :type ignore_punctuation: bool
    :param engine: options include ``'difflib'`` (default) and ``'fuzzywuzzy'``

        - if ``engine='difflib'``, the function relies on `difflib.get_close_matches`_
        - if ``engine='fuzzywuzzy'``, the function relies on `fuzzywuzzy.fuzz.token_set_ratio`_

    :type engine: str or typing.Callable
    :param kwargs: [optional] parameters of `difflib.get_close_matches`_ (e.g. ``cutoff=0.6``) or
        `fuzzywuzzy.fuzz.token_set_ratio`_, depending on ``engine``
    :return: a string-type variable that should be similar to (or the same as) ``x``
    :rtype: str or list or None

    .. _`difflib.get_close_matches`:
        https://docs.python.org/3/library/difflib.html#difflib.get_close_matches
    .. _`fuzzywuzzy.fuzz.token_set_ratio`:
        https://github.com/seatgeek/fuzzywuzzy

    .. note::

        - By default, the function uses the built-in module
          `difflib <https://docs.python.org/3/library/difflib.html>`_; when we set the parameter
          ``engine='fuzzywuzzy'``, the function then relies on
          `FuzzyWuzzy <https://pypi.org/project/fuzzywuzzy/>`_, which is not an essential dependency
          for installing pyhelpers. We could however use ``pip`` (or ``conda``) to install it first
          separately.

    **Examples**::

        >>> from pyhelpers.text import find_similar_str

        >>> lookup_lst = ['Anglia',
        ...               'East Coast',
        ...               'East Midlands',
        ...               'North and East',
        ...               'London North Western',
        ...               'Scotland',
        ...               'South East',
        ...               'Wales',
        ...               'Wessex',
        ...               'Western']

        >>> y = find_similar_str(x='angle', lookup_list=lookup_lst)
        >>> y
        'Anglia'
        >>> y = find_similar_str(x='angle', lookup_list=lookup_lst, n=2)
        >>> y
        ['Anglia', 'Wales']

        >>> y = find_similar_str(x='angle', lookup_list=lookup_lst, engine='fuzzywuzzy')
        >>> y
        'Anglia'
        >>> y = find_similar_str('angle', lookup_lst, n=2, engine='fuzzywuzzy')
        >>> y
        ['Anglia', 'Wales']

        >>> y = find_similar_str(x='x', lookup_list=lookup_lst)
        >>> y is None
        True
        >>> y = find_similar_str(x='x', lookup_list=lookup_lst, cutoff=0.25)
        >>> y
        'Wessex'
        >>> y = find_similar_str(x='x', lookup_list=lookup_lst, n=2, cutoff=0.25)
        >>> y
        'Wessex'

        >>> y = find_similar_str(x='x', lookup_list=lookup_lst, engine='fuzzywuzzy')
        >>> y
        'Wessex'
        >>> y = find_similar_str(x='x', lookup_list=lookup_lst, n=2, engine='fuzzywuzzy')
        >>> y
        ['Wessex', 'Western']
    """

    methods = {'difflib', 'fuzzywuzzy', None}
    assert engine in methods or callable(engine), \
        f"Invalid input: `engine`. Valid options can include {methods}."

    if engine == 'difflib' or engine is None:
        sim_str = _find_str_by_difflib(x, lookup_list, n, ignore_punctuation, **kwargs)

    elif engine == 'fuzzywuzzy':
        sim_str = _find_str_by_fuzzywuzzy(x, lookup_list, n, **kwargs)

    else:
        sim_str = engine(x, lookup_list, **kwargs)

    return sim_str
