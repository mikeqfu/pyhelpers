"""
Textual data (pre)processing.
"""

import collections
import copy
import math
import re
import string

from .._cache import _check_dependency, _ENGLISH_NUMERALS


def remove_punctuation(x, rm_whitespace=True):
    """
    Removes punctuation from textual data.

    :param x: The input text from which punctuation will be removed.
    :type x: str
    :param rm_whitespace: Whether to remove whitespace characters as well; defaults to ``True``.
    :type rm_whitespace: bool
    :return: The input text without punctuation (and optionally without whitespace).
    :rtype: str

    **Examples**::

        >>> from pyhelpers.text import remove_punctuation
        >>> remove_punctuation('Hello, world!')
        'Hello world'
        >>> remove_punctuation('   How   are you? ', rm_whitespace=False)
        'How   are you'
        >>> remove_punctuation('No-punctuation!')
        'No punctuation'
        >>> raw_text = 'Hello world!\tThis is a test. :-)'
        >>> remove_punctuation(raw_text)
        'Hello world This is a test'
        >>> remove_punctuation(raw_text, rm_whitespace=False)
        'Hello world \tThis is a test'
    """

    x_ = re.sub(r'[^\w\s]', ' ', x)

    # y = ''.join(y_ for y_ in x_ if y_ not in string.punctuation)
    y = x_.translate(str.maketrans('', '', string.punctuation))

    z = y.strip()

    if rm_whitespace:
        z = ' '.join(z.split())

    return z


def get_acronym(text, only_capitals=False, capitals_in_words=False, keep_punctuation=False):
    """
    Generates an acronym (in capital letters) from textual data.

    An acronym is typically formed by taking the initial letters of each word in a phrase
    and combining them into a single string of uppercase letters.

    :param text: The input text from which to generate the acronym.
    :type text: str
    :param only_capitals: Whether to include only capital letters in the acronym;
        defaults to ``False``.
    :type only_capitals: bool
    :param capitals_in_words: Whether to treat all capital letters within words as part of the
        acronym; defaults to ``False``.
    :type capitals_in_words: bool
    :param keep_punctuation: Whether to retain punctuation in the input text; defaults to ``False``.
    :type keep_punctuation: bool
    :return: The acronym generated from the input text.
    :rtype: str

    **Examples**::

        >>> from pyhelpers.text import get_acronym
        >>> text_a = 'This is an apple.'
        >>> get_acronym(text_a)
        'TIAA'
        >>> text_b = "I'm at the University of Birmingham."
        >>> get_acronym(text_b, only_capitals=True)
        'IUB'
        >>> text_c = 'There is a "ConnectionError"!'
        >>> get_acronym(text_c, capitals_in_words=True)
        'TIACE'
        >>> get_acronym(text_c, only_capitals=True, capitals_in_words=True)
        'TCE'
        >>> get_acronym(text_c, only_capitals=True, capitals_in_words=True, keep_punctuation=True)
        'T"CE"!'
        >>> get_acronym(text_c, only_capitals=True, keep_punctuation=True)
        'T"C"!'
        >>> get_acronym(text_c, capitals_in_words=True, keep_punctuation=True)
        'TIA"CE"!'
    """

    if keep_punctuation:
        txt = ''.join(f' {x} ' if x in string.punctuation else x for x in text)
    else:
        txt = remove_punctuation(text)

    if only_capitals and capitals_in_words:
        acronym = ''.join(filter(lambda x: x.isupper() or x in string.punctuation, txt))
    else:
        if only_capitals:
            acronym = ''.join(
                x[0] for x in txt.split() if x[0].isupper() or x[0] in string.punctuation)
        elif capitals_in_words:
            txt_ = ' '.join(x[0].title() + x[1:] for x in txt.split())
            acronym = ''.join(filter(lambda x: x.isupper() or x in string.punctuation, txt_))
        else:
            acronym = ''.join(x[0].upper() for x in txt.split())

    return acronym


def extract_words1upper(x, join_with=None):
    """
    Extracts words from a string by splitting it at occurrences of uppercase letters.

    This function takes a string and splits it into individual words wherever an uppercase letter
    is encountered. Optionally, it can join these words back into a single string using a specified
    delimiter.

    :param x: Input text containing a number of words each starting with an uppercase letter.
    :type x: str
    :param join_with: Optional delimiter used to join the extracted words into a single string;
        defaults to ``None``.
    :type join_with: str | None
    :return: If ``join_with=None``, the function returns a list of words extracted from ``x`` where
        each word starts with an uppercase letter; if ``join_with`` is specified, it returns a
        single string where these words are joined by ``join_with``.
    :rtype: list | str

    **Examples**::

        >>> from pyhelpers.text import extract_words1upper
        >>> extract_words1upper('Network_Waymarks')
        ['Network', 'Waymarks']
        >>> extract_words1upper('NetworkRailRetainingWall', join_with=' ')
        'Network Rail Retaining Wall'
    """

    y = remove_punctuation(x)

    # re.sub(r"([A-Z])", r" \1", x).split()
    extracted_words = re.findall(r'[a-zA-Z][^A-Z]*', y)

    if join_with:
        extracted_words = join_with.join(extracted_words)

    return extracted_words


def _english_numerals():
    """
    Returns a dictionary facilitaing to map textual English numerals to their corresponding
    numerical representations.

    :return: Dictionary facilitaing to map textual English numerals to their corresponding
        numerical representations.
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.text.preproc import _english_numerals
        >>> eng_num = _english_numerals()
        >>> list(eng_num.keys())[:5]
        ['and', 'zero', 'one', 'two', 'three']
        >>> list(eng_num.values())[:5]
        [[1, 0], [1, 0], [1, 1], [1, 2], [1, 3]]
    """

    metadata = dict()

    # Singles
    units = [
        'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
        'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
        'sixteen', 'seventeen', 'eighteen', 'nineteen', 'a',
    ]

    # Tens
    tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']

    # Larger scales
    scales = ['hundred', 'thousand', 'million', 'billion', 'trillion']

    # divisors
    metadata['and'] = [1, 0]

    # perform our loops and start the swap
    for i, word in enumerate(units):
        if word == 'a':
            metadata[word] = [1, 1]
        else:
            metadata[word] = [1, i]
    for i, word in enumerate(tens):
        metadata[word] = [1, i * 10]
    for i, word in enumerate(scales):
        metadata[word] = [10 ** (i * 3 or 2), 0]

    return metadata


def numeral_english_to_arabic(x):
    """
    Converts a number written in English words into its equivalent numerical value represented in
    Arabic numerals.

    :param x: A number expressed in the English language.
    :type x: str
    :return: The equivalent Arabic number.
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
        if word not in _ENGLISH_NUMERALS and not word.isdigit():
            # word_ = find_similar_str(word, ENGLISH_WRITTEN_NUMBERS)
            # if word_ is None:
            raise Exception(f"Illegal word: \"{word}\"")
            # else:
            #     word = word_

        if word.isdigit():
            scale, increment = (1, int(word))
        else:
            scale, increment = _ENGLISH_NUMERALS[word]
        current = current * scale + increment

        if scale > 100:
            result += current
            current = 0

    result += current

    return result


def count_words(text, lowercase=False, ignore_punctuation=False, stop_words=None, **kwargs):
    # noinspection PyShadowingNames
    """
    Counts the occurrences of each word in the given text.

    :param text: The input text from which words will be counted.
    :type text: str
    :param lowercase: Whether to convert the text to lowercase before counting;
        defaults to ``False``.
    :type lowercase: bool
    :param ignore_punctuation: Whether to exclude punctuation marks from the text;
        defaults to ``False``.
    :type ignore_punctuation: bool
    :param stop_words: List of words to be excluded from the word count;

        - If ``stop_words=None`` (default), no words are excluded.
        - If ``stop_words=True``, NLTK's built-in stopwords are used.

    :type stop_words: list[str] | bool | None
    :param kwargs: [Optional] Additional parameters for the function `nltk.word_tokenize()`_.
    :return: A dictionary where keys are unique words and values are their respective counts.
    :rtype: dict

    .. _`NLTK`: https://www.nltk.org/
    .. _`nltk.word_tokenize()`: https://www.nltk.org/api/nltk.tokenize.word_tokenize.html

    **Examples**::

        >>> from pyhelpers.text import count_words
        >>> text = 'This is an apple. That is a pear. Hello world!'
        >>> count_words(text)
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
        >>> count_words(text, lowercase=True)
        {'this': 1,
         'is': 2,
         'an': 1,
         'apple': 1,
         '.': 2,
         'that': 1,
         'a': 1,
         'pear': 1,
         'hello': 1,
         'world': 1,
         '!': 1}
        >>> count_words(text, lowercase=True, ignore_punctuation=True)
        {'this': 1,
         'is': 2,
         'an': 1,
         'apple': 1,
         'that': 1,
         'a': 1,
         'pear': 1,
         'hello': 1,
         'world': 1}
        >>> count_words(text, lowercase=True, ignore_punctuation=True, stop_words=['is'])
        {'this': 1,
         'an': 1,
         'apple': 1,
         'that': 1,
         'a': 1,
         'pear': 1,
         'hello': 1,
         'world': 1}
        >>> count_words(text, lowercase=True, ignore_punctuation=True, stop_words=True)
        {'apple': 1, 'pear': 1, 'hello': 1, 'world': 1}
    """

    nltk_ = _check_dependency(name='nltk')

    doc = str(text).lower() if lowercase else str(text)
    if ignore_punctuation:
        doc = remove_punctuation(doc, rm_whitespace=False)

    tokens = nltk_.word_tokenize(doc, **kwargs)

    if stop_words:  # Remove stop words if provided
        if stop_words is True:
            language = kwargs['language'] if 'language' in kwargs else 'english'
            stop_words_ = set(nltk_.corpus.stopwords.words(language))
        else:
            stop_words_ = copy.copy(stop_words)
        tokens = [w for w in tokens if not w.lower() in stop_words_]

    word_count_dict = dict(collections.Counter(tokens))

    return word_count_dict


def calculate_idf(documents, lowercase=True, ignore_punctuation=True, stop_words=None,
                  smoothing_factor=1, log_base=None, **kwargs):
    # noinspection PyShadowingNames
    """
    Calculates Inverse Document Frequency (IDF) for a sequence of textual documents.

    :param documents: A sequence of textual data.
    :type documents: typing.Iterable | typing.Sequence
    :param lowercase: Whether to convert the documents to lowercase before calculating IDF;
        defaults to ``True``.
    :type lowercase: bool
    :param ignore_punctuation: Whether to exclude punctuation marks from the textual data;
        defaults to ``True``.
    :type ignore_punctuation: bool
    :param stop_words: List of words to be excluded from the IDF calculation;

        - If ``stop_words=None`` (default), no words are excluded.
        - If ``stop_words=True``, NLTK's built-in stopwords are used.

    :type stop_words: list[str] | bool | None
    :param smoothing_factor: Factor added to the denominator in the IDF formula:

        - For smaller corpora: Use ``smoothing_factor=1`` (default) to prevent IDF values from
          becoming too extreme (e.g. zero for terms in all documents). This adjustment ensures more
          stable IDF values reflecting term rarity.
        - For larger corpora: Use ``smoothing_factor=0`` for standard IDF calculations,
          which provides a measure of how terms are distributed across documents.
          This can generally be sufficient and standard practice.

    :type smoothing_factor: int | float
    :param log_base: The logarithm base in the IDF formula;
        when ``log_base=None`` (default), use `math.e`_.
    :type log_base: int
    :param kwargs: [Optional] Additional parameters for the function `nltk.word_tokenize()`_; 
        also refer to the function :func:`~pyhelpers.text.count_words`, which calculates
        term frequencies (TF) for each document.

    :return: Tuple containing:

        - Term frequency (TF) of each document as a list of dictionaries, where each dictionary
          represents TF for one document.
        - Inverse document frequency (IDF) as a dictionary, where keys are unique terms across
          all documents and values are their IDF scores.

    :rtype: tuple[list[dict], dict]

    .. _`math.e`: https://docs.python.org/3/library/math.html#math.e
    .. _`nltk.word_tokenize()`: https://www.nltk.org/api/nltk.tokenize.word_tokenize.html

    **Examples**::

        >>> from pyhelpers.text import calculate_idf
        >>> documents = [
        ...     'This is an apple.',
        ...     'That is a pear.',
        ...     'It is human being.',
        ...     'Hello world!']
        >>> docs_tf, corpus_idf = calculate_idf(documents)
        >>> docs_tf
        [{'this': 1, 'is': 1, 'an': 1, 'apple': 1},
         {'that': 1, 'is': 1, 'a': 1, 'pear': 1},
         {'it': 1, 'is': 1, 'human': 1, 'being': 1},
         {'hello': 1, 'world': 1}]
        >>> corpus_idf
        {'this': 0.6931471805599453,
         'is': 0.0,
         'an': 0.6931471805599453,
         'apple': 0.6931471805599453,
         'that': 0.6931471805599453,
         'a': 0.6931471805599453,
         'pear': 0.6931471805599453,
         'it': 0.6931471805599453,
         'human': 0.6931471805599453,
         'being': 0.6931471805599453,
         'hello': 0.6931471805599453,
         'world': 0.6931471805599453}
        >>> docs_tf, corpus_idf = calculate_idf(documents, ignore_punctuation=False)
        >>> docs_tf
        [{'this': 1, 'is': 1, 'an': 1, 'apple': 1, '.': 1},
         {'that': 1, 'is': 1, 'a': 1, 'pear': 1, '.': 1},
         {'it': 1, 'is': 1, 'human': 1, 'being': 1, '.': 1},
         {'hello': 1, 'world': 1, '!': 1}]
        >>> corpus_idf
        {'this': 0.6931471805599453,
         'is': 0.0,
         'an': 0.6931471805599453,
         'apple': 0.6931471805599453,
         '.': 0.0,
         'that': 0.6931471805599453,
         'a': 0.6931471805599453,
         'pear': 0.6931471805599453,
         'it': 0.6931471805599453,
         'human': 0.6931471805599453,
         'being': 0.6931471805599453,
         'hello': 0.6931471805599453,
         'world': 0.6931471805599453,
         '!': 0.6931471805599453}
    """

    docs_tf = [
        count_words(
            doc, lowercase=lowercase, ignore_punctuation=ignore_punctuation, stop_words=stop_words,
            **kwargs)
        for doc in documents]

    # Create set of all unique tokens in the corpus
    all_tokens = [k for keys in (x.keys() for x in docs_tf) for k in keys]

    # Calculate IDF for each token
    n_docs = len(documents)
    log_base = log_base if log_base else math.e

    corpus_idf = {}
    for token in all_tokens:
        token_count = sum(1 for tf in docs_tf if token in tf)
        corpus_idf[token] = math.log(n_docs / (smoothing_factor + token_count), log_base)

    return docs_tf, corpus_idf


def calculate_tfidf(documents, **kwargs):
    # noinspection PyShadowingNames
    """
    Calculates TF-IDF (Term Frequency-Inverse Document Frequency) for the given textual documents.

    TF (Term Frequency) measures how frequently a term appears in a document relative to its length.
    IDF (Inverse Document Frequency) measures how important a term is across the entire corpus of
    documents.

    :param documents: A sequence of textual data.
    :type documents: typing.Iterable | typing.Sequence
    :param kwargs: [Optional] Additional parameters for the function
        :func:`~pyhelpers.text.calculate_idf`; also refer to :func:`~pyhelpers.text.count_words`.
    :return: TF-IDF values for the input textual data, represented as a dictionary.
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.text import calculate_tfidf
        >>> documents = [
        ...     'This is an apple.',
        ...     'That is a pear.',
        ...     'It is human being.',
        ...     'Hello world!']
        >>> tfidf = calculate_tfidf(documents)
        >>> tfidf
        {'this': 0.6931471805599453,
         'is': 0.0,
         'an': 0.6931471805599453,
         'apple': 0.6931471805599453,
         'that': 0.6931471805599453,
         'a': 0.6931471805599453,
         'pear': 0.6931471805599453,
         'it': 0.6931471805599453,
         'human': 0.6931471805599453,
         'being': 0.6931471805599453,
         'hello': 0.6931471805599453,
         'world': 0.6931471805599453}
        >>> tfidf = calculate_tfidf(documents, lowercase=False)
        >>> tfidf
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

    docs_tf, corpus_idf = calculate_idf(documents=documents, **kwargs)

    tfidf = {
        token: tf * corpus_idf[token] for doc_tf in docs_tf for token, tf in doc_tf.items()
        if token in corpus_idf}

    return tfidf
