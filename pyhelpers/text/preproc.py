"""
Textual data (pre)processing.
"""

import collections
import re
import string

import numpy as np

from .._cache import _check_dependency, _ENGLISH_NUMERALS


def remove_punctuation(x, rm_whitespace=True):
    """
    Remove punctuation from textual data.

    :param x: Textual data.
    :type x: str
    :param rm_whitespace: Whether to remove whitespace (incl. escape characters);
        defaults to ``True``.
    :type rm_whitespace: bool
    :return: Text without punctuation.
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


def get_acronym(text, only_capitals=False, capitals_in_words=False, keep_punctuation=False):
    """
    Get an acronym (in capital letters) of textual data.

    :param text: Textual data.
    :type text: str
    :param only_capitals: Whether to include capital letters only; defaults to ``False``.
    :type only_capitals: bool
    :param capitals_in_words: Whether to include all captical letters in a single word;
        defaults to ``False``.
    :type capitals_in_words: bool
    :param keep_punctuation: Whether to keep punctuation in ``text``; defaults to ``False``.
    :type keep_punctuation: bool
    :return: Acronym of the input ``text``.
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
    Extract words from a string by spliting it at occurrence of an uppercase letter.

    :param x: Textual data (joined by a number of words each starting with an uppercase letter).
    :type x: str
    :param join_with: Character(s) with which to (re)join the single words; defaults to ``None``.
    :type join_with: str | None
    :return: A list of single words each starting with an uppercase letter,
        or a single string joined together by them with ``join_with``.
    :rtype: list | str

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


def _english_numerals():
    """
    English numerals.

    :return: English numerals
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.text.preproc import _english_numerals
        >>> _english_numerals()
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
    Convert a number written in English words into its equivalent numerical value represented in
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


def count_words(raw_txt):
    """
    Count the total for each different word.

    :param raw_txt: Textual data.
    :type raw_txt: str
    :return: The number of each word in ``raw_docs``.
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

    :param raw_documents: A sequence of textual data.
    :type raw_documents: typing.Iterable | typing.Sequence
    :param rm_punc: Whether to remove punctuation from the input textual data;
        defaults to ``False``.
    :type rm_punc: bool
    :return: Term frequency (TF) of the input textual data, and inverse document frequency.
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

    :param raw_documents: A sequence of textual data.
    :type raw_documents: typing.Iterable | typing.Sequence
    :param rm_punc: Whether to remove punctuation from the input textual data;
        defaults to ``False``.
    :type rm_punc: bool
    :return: TF-IDF of the input textual data.
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
