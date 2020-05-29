""" Text-related """

import collections
import collections.abc
import re
import string

import numpy as np
import pandas as pd

from pyhelpers.ops import dict_to_dataframe


# Find similar string from a list of strings
def find_similar_str(x, lookup_list, processor='fuzzywuzzy', **kwargs):
    """
    :param x: [str] a string-type variable
    :param lookup_list: [iterable] (a list of) candidate strings for lookup
    :param processor: [str] (default: 'fuzzywuzzy')
    :param kwargs: optional arguments used by
                    `fuzzywuzzy.fuzz.token_set_ratio()` if `processor == 'fuzzywuzzy'`;
                    `nltk.edit_distance()` if `processor == 'nltk'`, e.g. `substitution_cost=100`
    :return: [str] a string-type variable that should be similar to (or the same as) `x`
    """
    assert processor in ('fuzzywuzzy', 'nltk'), '\"processor\" must be either \"fuzzywuzzy\" or \"nltk\".'

    if processor == 'fuzzywuzzy':
        import fuzzywuzzy.fuzz
        l_distances = [fuzzywuzzy.fuzz.token_set_ratio(x, a, **kwargs) for a in lookup_list]
        the_one = lookup_list[l_distances.index(max(l_distances))] if l_distances else None

    elif processor == 'nltk':
        import nltk.metrics
        l_distances = [nltk.edit_distance(x, a, **kwargs) for a in lookup_list]
        the_one = lookup_list[l_distances.index(min(l_distances))] if l_distances else None

    else:
        the_one = None

    return the_one


# Find from a list the closest, case-insensitive, str to the given one
def find_matched_str(x, lookup_list):
    """
    :param x: [str; None] a string-type variable; if None, the function will return None
    :param lookup_list: [iterable] (a list of) candidate strings for lookup
    :return: [str; list; None] a string-type variable that is case-insensitively the same as `x`
    """
    assert isinstance(x, str), "\"x\" must be a string."
    assert isinstance(lookup_list, collections.abc.Iterable), "\"lookup_list\" must be iterable"
    if x == '' or x is None:
        return None
    else:
        for y in lookup_list:
            if re.match(x, y, re.IGNORECASE):
                return y


# Remove punctuation
def remove_punctuation(raw_txt):
    """
    :param raw_txt: [str]
    :return:

    Example:
        raw_txt = 'Hello world!'

        remove_punctuation(raw_txt)  # 'Hello world'
    """
    try:
        # txt = text.lower().translate(str.maketrans('', '', string.punctuation))
        txt = raw_txt.translate(str.maketrans('', '', string.punctuation))
    except Exception as e:
        print(e)
        # txt = ''.join(x for x in text.lower() if x not in string.punctuation)
        txt = ''.join(x for x in raw_txt if x not in string.punctuation)
    return txt


# Count number of each different word
def count_words(raw_txt):
    """
    :param raw_txt: [str] any text
    :return: [dict] total number of each different word in `raw_docs`

    Example:
        raw_txt = 'This is an apple. That is a pear. Hello world!'

        count_words(raw_txt)
    """
    import nltk
    doc_text = str(raw_txt)
    tokens = nltk.word_tokenize(doc_text)
    word_count_dict = dict(collections.Counter(tokens))
    return word_count_dict


# Calculate inverse document frequency
def calculate_idf(raw_documents):
    """
    :param raw_documents: [pd.Series]
    :return: [tuple] of length 2 - (tf of a number of documents, idf)

    Example:
        raw_documents = pd.Series(['This is an apple.', 'That is a pear.', 'It is human being.', 'Hello world!'])

        docs_tf, corpus_idf = calculate_idf(raw_documents)
    """
    assert isinstance(raw_documents, (pd.Series, pd.DataFrame))

    docs_tf = raw_documents.map(count_words)
    tokens_in_docs = docs_tf.map(lambda x: list(x.keys()))

    n = len(raw_documents)
    tokens = [w for tokens in tokens_in_docs for w in tokens]
    tokens_counter = dict_to_dataframe(dict(collections.Counter(tokens)), 'token', 'count')
    tokens_counter['idf'] = np.log(n / (1 + tokens_counter['count'].values))

    corpus_idf = dict(zip(tokens_counter['token'], tokens_counter['idf']))

    return docs_tf, corpus_idf


# Count term frequency–inverse document frequency
def calculate_tf_idf(raw_documents):
    """
    :param raw_documents: [pd.Series]
    :return: [dict] tf-idf of the `raw_documents`

    Example:
        raw_documents = pd.Series(['This is an apple.', 'That is a pear.', 'It is human being.', 'Hello world!'])

        calculate_tf_idf(raw_documents)
    """
    docs_tf, corpus_idf = calculate_idf(raw_documents)
    docs_tf_idf = docs_tf.apply(lambda x: {k: v * corpus_idf[k] for k, v in x.items() if k in corpus_idf})
    return docs_tf_idf


# Compute Euclidean distance of two sentences
def euclidean_distance_between_texts(txt1, txt2):
    """
    :param txt1: [str] any text
    :param txt2: [str] any text
    :return: [numbers.Number]

    Example:
        s1 = 'This is an apple.'
        s2 = 'That is a pear.'

        ed = euclidean_distance_between_texts(s1, s2)  # 2.6457513110645907
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


# Compute cosine similarity of two sentences
def cosine_similarity_between_texts(txt1, txt2, cosine_distance=False):
    """
    :param txt1: [str] any text
    :param txt2: [str] any text
    :param cosine_distance: [bool] whether to get cosine distance, which is 1 - cosine similarity (default: False)
    :return: [numbers.Number] cosine similarity (or distance)

    Example:
        s1 = 'This is an apple.'
        s2 = 'That is a pear.'

        cosine_distance = False
        cos_similarity = cosine_similarity_between_texts(s1, s2)  # 0.6963106238227914

        cosine_distance = True
        cos_similarity = cosine_similarity_between_texts(s1, s2, cosine_distance)  # 0.3036893761772086
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
