"""
Utilities for measuring similarity between textual data.
"""

import re

import numpy as np

from .._cache import _check_dependency, _remove_punctuation, _vectorize_text


def euclidean_distance_between_texts(txt1, txt2):
    # noinspection PyShadowingNames
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
        >>> txt1, txt2 = 'This is an apple.', 'That is a pear.'
        >>> euclidean_distance = euclidean_distance_between_texts(txt1, txt2)
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


def find_matched_str(input_str, lookup_list, use_regex=True):
    # noinspection PyShadowingNames
    """
    Finds all strings (in a sequence) that match a given string or regex pattern.

    :param input_str: The string to match.
    :type input_str: str
    :param lookup_list: A sequence of strings for lookup.
    :type lookup_list: typing.Iterable[str]
    :param use_regex: Whether to treat `text` as a regex pattern; defaults to `True`.
    :type use_regex: bool
    :return: A generator containing all strings that match ``text``.
    :rtype: typing.Generator | None

    **Examples**::

        >>> from pyhelpers.text import find_matched_str
        >>> lookup_lst = ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel']
        >>> text_ = find_matched_str('apple', lookup_lst)
        >>> list(text_)
        []
        >>> lookup_lst += ['apple']
        >>> lookup_lst
        ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel', 'apple']
        >>> text_ = find_matched_str('apple', lookup_lst)
        >>> list(text_)
        ['apple']
        >>> text_ = find_matched_str(r'app(le)?', lookup_lst)
        >>> list(text_)
        ['app', 'apple']
        >>> text_ = find_matched_str('app(le)?', lookup_lst, use_regex=False)
        >>> list(text_)  # No match because regex behavior is disabled
        []
    """

    if not isinstance(input_str, str):
        raise TypeError("The search string `'input_str'` must be a string.")

    if use_regex:
        pattern = re.compile(input_str, re.IGNORECASE)
    else:
        # Treat `input_str` as a literal string
        pattern = re.compile(re.escape(input_str), re.IGNORECASE)

    for output_str in lookup_list:
        if pattern.fullmatch(output_str):  # Ensures full matching
            yield output_str


def _find_str_by_difflib(input_str, lookup_list, n=1, ignore_punctuation=True, **kwargs):
    """
    Finds ``n`` strings similar to ``input_str`` from a sequence of candidates
    by using `difflib <https://docs.python.org/3/library/difflib.html>`_.

    :param input_str: The string to match.
    :type input_str: str
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
    :return: A string or list of strings similar to (or the same as) ``input_str``.
    :rtype: str | list | None

    .. _`difflib.get_close_matches()`:
        https://docs.python.org/3/library/difflib.html#difflib.get_close_matches
    """

    if not lookup_list:  # Handle empty lookup lists
        return None

    difflib_ = _check_dependency(name='difflib')

    x, lookup_dict = input_str.lower(), {y.lower(): y for y in lookup_list}

    if ignore_punctuation:
        x = _remove_punctuation(x)
        lookup_dict = {_remove_punctuation(k): v for k, v in lookup_dict.items()}

    matches = difflib_.get_close_matches(word=x, possibilities=lookup_dict.keys(), n=n, **kwargs)

    if not matches:
        sim_str = None
    elif len(matches) == 1:
        sim_str = lookup_dict[matches[0]]
    else:
        sim_str = [lookup_dict[k] for k in matches]

    return sim_str


def _find_str_by_rapidfuzz(input_str, lookup_list, n=1, **kwargs):
    """
    Finds ``n`` strings that are similar to ``input_str`` from a sequence of candidates
    using `RapidFuzz <https://pypi.org/project/rapidfuzz/>`_.

    :param input_str: The string to match.
    :type input_str: str
    :param lookup_list: A sequence of strings for lookup.
    :type lookup_list: typing.Iterable
    :param n: Number of similar strings to return; defaults to ``1``;
        when ``n=None``, the function returns the entire ``lookup_list`` sorted by similarity
        in descending order.
    :type n: int | None
    :param kwargs: [Optional] Additional parameters for the function `rapidfuzz.fuzz.QRatio()`_.
    :return: A string or list of strings similar to (or the same as) ``text``.
    :rtype: str | list | None

    .. _`rapidfuzz.fuzz.QRatio()`: https://github.com/maxbachmann/RapidFuzz#quick-ratio

    **Tests**::

        >>> from pyhelpers.text.similarity import _find_str_by_rapidfuzz
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

    if not lookup_list:
        return None
    else:
        lookup_list_ = list(lookup_list)

    rapidfuzz_fuzz, rapidfuzz_utils = map(_check_dependency, ['rapidfuzz.fuzz', 'rapidfuzz.utils'])

    kwargs.setdefault('processor', rapidfuzz_utils.default_process)
    l_distances = [rapidfuzz_fuzz.QRatio(s1=input_str, s2=a, **kwargs) for a in lookup_list_]

    if max(l_distances) == 0:  # If all scores are zero, return None
        sim_str = None

    else:
        # Sort indices based on similarity scores
        sorted_indices = np.argsort(l_distances)[::-1]

        if n == 1:
            sim_str = lookup_list_[sorted_indices[0]]
        elif n is None:
            sim_str = [lookup_list_[i] for i in sorted_indices]
        else:
            sim_str = [lookup_list_[i] for i in sorted_indices[:n]]

    return sim_str


def find_similar_str(input_str, lookup_list, n=1, ignore_punctuation=True, engine='difflib',
                     **kwargs):
    # noinspection PyShadowingNames
    """
    Finds ``n`` strings that are similar to ``input_str`` from a sequence of candidates.

    :param input_str: The string to find similar matches for.
    :type input_str: str
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
    :return: A string or list of strings similar to ``input_str``,
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
        >>> lookup_list = ['Anglia',
        ...                'East Coast',
        ...                'East Midlands',
        ...                'North and East',
        ...                'London North Western',
        ...                'Scotland',
        ...                'South East',
        ...                'Wales',
        ...                'Wessex',
        ...                'Western']
        >>> find_similar_str('angle', lookup_list)
        'Anglia'
        >>> find_similar_str('angle', lookup_list, n=2)
        ['Anglia', 'Wales']
        >>> find_similar_str('angle', lookup_list, engine='fuzz')
        'Anglia'
        >>> find_similar_str('angle', lookup_list, n=2, engine='fuzz')
        ['Anglia', 'Wales']
        >>> find_similar_str('x', lookup_list) is None
        True
        >>> find_similar_str('x', lookup_list, cutoff=0.25)
        'Wessex'
        >>> find_similar_str('x', lookup_list, n=2, cutoff=0.25)
        'Wessex'
        >>> find_similar_str('x', lookup_list, engine='fuzz')
        'Wessex'
        >>> find_similar_str('x', lookup_list, n=2, engine='fuzz')
        ['Wessex', 'Western']
    """

    methods = {'difflib', 'fuzzywuzzy', 'rapidfuzz', 'fuzz', None}
    if not (engine in methods or callable(engine)):
        raise ValueError(f"Invalid engine: {engine}. Valid options are {methods}.")

    if engine in {'difflib', None}:
        sim_str = _find_str_by_difflib(
            input_str=input_str, lookup_list=lookup_list, n=n,
            ignore_punctuation=ignore_punctuation, **kwargs)

    elif engine in {'rapidfuzz', 'fuzz'}:
        sim_str = _find_str_by_rapidfuzz(
            input_str=input_str, lookup_list=lookup_list, n=n, **kwargs)

    else:
        sim_str = engine(input_str, lookup_list, **kwargs)

    return sim_str
