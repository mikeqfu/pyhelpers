"""
Manipulation of textual data.
"""

import re

import numpy as np

from .preproc import remove_punctuation
from .._cache import _check_dependency


def _vectorize_text(*txt):
    txt_ = [
        re.compile(r"\w+").findall(x.lower()) if isinstance(x, str) else [x_.lower() for x_ in x]
        for x in txt]
    doc_words = set().union(*txt_)

    for x in txt_:
        yield [x.count(word) for word in doc_words]


def euclidean_distance_between_texts(txt1, txt2):
    """
    Computes the Euclidean distance between two sentences.

    :param txt1: The first text.
    :type txt1: str
    :param txt2: The second text.
    :type txt2: str
    :return: The Euclidean distance between the input texts.
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
    # noinspection PyShadowingNames
    """
    Calculates the cosine similarity between two sentences.

    :param txt1: The first text.
    :type txt1: str
    :param txt2: The second text.
    :type txt2: str
    :param cosine_distance: Whether to return cosine distance (i.e. 1 - cosine similarity);
        defaults to ``False``.
    :type cosine_distance: bool
    :return: The cosine similarity (or distance) between the input texts.
    :rtype: float

    **Examples**::

        >>> from pyhelpers.text import cosine_similarity_between_texts
        >>> txt1, txt2 = 'This is an apple.', 'That is a pear.'
        >>> cos_sim = cosine_similarity_between_texts(txt1, txt2)
        >>> cos_sim
        0.25
        >>> cos_dist = cosine_similarity_between_texts(txt1, txt2, cosine_distance=True)
        >>> cos_dist  # 1 - cos_sim
        0.75
    """

    # noinspection PyTypeChecker
    s1_count, s2_count = map(np.array, _vectorize_text(txt1, txt2))

    similarity = np.dot(s1_count, s2_count)
    cos_similarity = np.divide(similarity, np.linalg.norm(s1_count) * np.linalg.norm(s2_count))

    if cosine_distance:
        cos_similarity = 1 - cos_similarity

    return cos_similarity


def find_matched_str(x, lookup_list):
    """
    Finds all strings (in a sequence) that match a given string.

    :param x: The string to match.
    :type x: str
    :param lookup_list: A sequence of strings for lookup.
    :type lookup_list: typing.Iterable
    :return: A generator containing all strings that match ``x``.
    :rtype: typing.Generator | None

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
    Finds ``n`` strings similar to ``x`` from a sequence of candidates
    by using `difflib <https://docs.python.org/3/library/difflib.html>`_.

    :param x: The string to match.
    :type x: str
    :param lookup_list: A sequence of strings for lookup.
    :type lookup_list: typing.Iterable
    :param n: The number of similar strings to return; defaults to ``1``;
        when ``n=None``, the function returns the entire ``lookup_list`` sorted by similarity
        in descending order.
    :type n: int | None
    :param ignore_punctuation: Whether to ignore punctuation in the search for similar texts;
        defaults to ``True``.
    :type ignore_punctuation: bool
    :param kwargs: [Optional] Additional parameters for the function `difflib.get_close_matches()`.
    :return: A string or list of strings similar to (or the same as) ``x``.
    :rtype: str | list | None

    .. _`difflib.get_close_matches()`:
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


def _find_str_by_rapidfuzz(x, lookup_list, n=1, **kwargs):
    """
    Finds ``n`` strings that are similar to ``x`` from a sequence of candidates
    using `RapidFuzz <https://pypi.org/project/rapidfuzz/>`_.

    :param x: The string to match.
    :type x: str
    :param lookup_list: A sequence of strings for lookup.
    :type lookup_list: typing.Iterable
    :param n: Number of similar strings to return; defaults to ``1``;
        when ``n=None``, the function returns the entire ``lookup_list`` sorted by similarity
        in descending order.
    :type n: int | None
    :param kwargs: [Optional] Additional parameters for the function `rapidfuzz.fuzz.QRatio()`_.
    :return: A string or list of strings similar to (or the same as) ``x``.
    :rtype: str | list | None

    .. _`rapidfuzz.fuzz.QRatio()`: https://github.com/maxbachmann/RapidFuzz#quick-ratio

    **Tests**::

        >>> from pyhelpers.text.analyser import _find_str_by_rapidfuzz
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
        >>> y = _find_str_by_rapidfuzz(x='angle', lookup_list=lookup_lst, n=1)
        >>> y
        'Anglia'
        >>> y = _find_str_by_rapidfuzz(x='123', lookup_list=lookup_lst, n=1)
        >>> y is None
        True
    """

    rapidfuzz_fuzz, rapidfuzz_utils = map(_check_dependency, ['rapidfuzz.fuzz', 'rapidfuzz.utils'])

    lookup_list_ = list(lookup_list)

    kwargs.update({'processor': rapidfuzz_utils.default_process})
    l_distances = [rapidfuzz_fuzz.QRatio(s1=x, s2=a, **kwargs) for a in lookup_list_]

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
    Finds ``n`` strings that are similar to ``x`` from a sequence of candidates.

    :param x: The string to find similar matches for.
    :type x: str
    :param lookup_list: A sequence of strings to search for matches.
    :type lookup_list: typing.Iterable
    :param n: Number of similar strings to return; defaults to ``1``;
        when ``n=None``, the function returns the entire ``lookup_list`` sorted by similarity
        in descending order.
    :type n: int | None
    :param ignore_punctuation: Whether to ignore punctuation in the comparison;
        defaults to ``True``.
    :type ignore_punctuation: bool
    :param engine: Method for finding similarities; options include:

        - ``'difflib'`` (default), which uses `difflib.get_close_matches()`_.
        - ``'rapidfuzz'`` (or ``'fuzz'``), which uses `rapidfuzz.fuzz.QRatio()`_.

    :type engine: str | typing.Callable
    :param kwargs: [Optional] Additional parameters for the chosen engine; for instance,
        ``cutoff`` for ``'difflib'`` and ``score_cutoff`` for ``'rapidfuzz'``.
    :return: A string or list of strings similar to ``x``,
        depending on ``n`` and the ``engine`` used.
    :rtype: str | list | None

    .. _`difflib.get_close_matches()`:
        https://docs.python.org/3/library/difflib.html#difflib.get_close_matches
    .. _`rapidfuzz.fuzz.QRatio()`:
        https://github.com/maxbachmann/RapidFuzz#quick-ratio

    .. note::

        - By default, the function uses the built-in
          `difflib  <https://docs.python.org/3/library/difflib.html>`_ module.
        - When ``engine='rapidfuzz'`` (or simply, ``engine='fuzz'``), the function relies on
          `RapidFuzz <https://pypi.org/project/rapidfuzz/>`_, which is not a dependency of
          pyhelpers. Install it separately using ``pip`` or ``conda``.

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
        >>> y = find_similar_str(x='angle', lookup_list=lookup_lst, engine='fuzz')
        >>> y
        'Anglia'
        >>> y = find_similar_str('angle', lookup_lst, n=2, engine='fuzz')
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
        >>> y = find_similar_str(x='x', lookup_list=lookup_lst, engine='fuzz')
        >>> y
        'Wessex'
        >>> y = find_similar_str(x='x', lookup_list=lookup_lst, n=2, engine='fuzz')
        >>> y
        ['Wessex', 'Western']
    """

    methods = {'difflib', 'fuzzywuzzy', 'rapidfuzz', 'fuzz', None}
    assert engine in methods or callable(engine), \
        f"Invalid input: `engine`. Valid options can include {methods}."

    if engine in {'difflib', None}:
        sim_str = _find_str_by_difflib(x, lookup_list, n, ignore_punctuation, **kwargs)

    elif engine in {'rapidfuzz', 'fuzz'}:
        sim_str = _find_str_by_rapidfuzz(x, lookup_list, n, **kwargs)

    else:
        sim_str = engine(x, lookup_list, **kwargs)

    return sim_str
