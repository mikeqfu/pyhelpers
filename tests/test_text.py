"""
Test module text.py
"""

from pyhelpers.text import *


def test_find_similar_str():
    x = 'apple'
    lookup_list = ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel']

    processor = 'fuzzywuzzy'
    sim_str = find_similar_str(x, lookup_list, processor)
    print(sim_str)
    # app

    processor = 'nltk'
    sim_str = find_similar_str(x, lookup_list, processor, substitution_cost=1)
    print(sim_str)
    # aapl

    sim_str = find_similar_str(x, lookup_list, processor, substitution_cost=100)
    print(sim_str)
    # app


def test_find_matched_str():
    x = 'apple'

    lookup_list = ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel']
    res = find_matched_str(x, lookup_list)
    print(list(res))
    # []

    lookup_list = ['abc', 'aapl', 'app', 'apple', 'ape', 'apex', 'apel']
    res = find_matched_str(x, lookup_list)
    print(list(res))
    # ['apple']


def test_remove_punctuation():
    raw_txt = 'Hello\tworld! :-)'
    txt = remove_punctuation(raw_txt)
    print(txt)
    # Hello<\t>world<space>

    rm_whitespace = True
    txt = remove_punctuation(raw_txt, rm_whitespace)
    print(txt)
    # Hello world


def test_count_words():
    raw_txt = 'This is an apple. That is a pear. Hello world!'

    word_count_dict = count_words(raw_txt)
    print(word_count_dict)
    # {'This': 1, 'is': 2, 'an': 1, 'apple': 1, '.': 2, 'That': 1, 'a': 1, 'pear': 1,
    #  'Hello': 1, 'world': 1, '!': 1}

    word_count_dict = count_words(remove_punctuation(raw_txt))
    print(word_count_dict)
    # {'This': 1, 'is': 2, 'an': 1, 'apple': 1, 'That': 1, 'a': 1, 'pear': 1, 'Hello': 1,
    #  'world': 1}


def test_calculate_idf():
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
    # dtype: object
    print(corpus_idf)
    # {'This': 0.6931471805599453, 'is': 0.0, 'an': 0.6931471805599453, ...

    rm_punc = True
    docs_tf, corpus_idf = calculate_idf(raw_documents, rm_punc)
    print(docs_tf)
    # 0     {'This': 1, 'is': 1, 'an': 1, 'apple': 1}
    # 1       {'That': 1, 'is': 1, 'a': 1, 'pear': 1}
    # 2    {'It': 1, 'is': 1, 'human': 1, 'being': 1}
    # 3                      {'Hello': 1, 'world': 1}
    # dtype: object
    print(corpus_idf)
    # {'This': 0.6931471805599453, 'is': 0.0, 'an': 0.6931471805599453, ...


def test_calculate_tf_idf():
    raw_documents = pd.Series(['This is an apple.',
                               'That is a pear.',
                               'It is human being.',
                               'Hello world!'])

    rm_punc = False
    docs_tf_idf = calculate_tf_idf(raw_documents, rm_punc)
    print(docs_tf_idf)
    # 0    {'This': 0.6931471805599453, 'is': 0.0, 'an': ...
    # 1    {'That': 0.6931471805599453, 'is': 0.0, 'a': 0...
    # 2    {'It': 0.6931471805599453, 'is': 0.0, 'human':...
    # 3    {'Hello': 0.6931471805599453, 'world': 0.69314...
    # dtype: object

    rm_punc = True
    docs_tf_idf = calculate_tf_idf(raw_documents, rm_punc)
    print(docs_tf_idf)
    # 0    {'This': 0.6931471805599453, 'is': 0.0, 'an': ...
    # 1    {'That': 0.6931471805599453, 'is': 0.0, 'a': 0...
    # 2    {'It': 0.6931471805599453, 'is': 0.0, 'human':...
    # 3    {'Hello': 0.6931471805599453, 'world': 0.69314...
    # dtype: object


def test_euclidean_distance_between_texts():
    txt1, txt2 = 'This is an apple.', 'That is a pear.'

    ed = euclidean_distance_between_texts(txt1, txt2)
    print(ed)
    # 2.6457513110645907


def test_cosine_similarity_between_texts():
    txt1, txt2 = 'This is an apple.', 'That is a pear.'

    cos_similarity = cosine_similarity_between_texts(txt1, txt2)
    print(cos_similarity)
    # 0.6963106238227914

    cosine_distance = True
    cos_similarity = cosine_similarity_between_texts(txt1, txt2, cosine_distance)
    print(cos_similarity)
    # 0.3036893761772086


def test_convert_md_to_rst():
    from pyhelpers.dir import cd

    dat_dir = cd("tests\\data")

    path_to_md = cd(dat_dir, "markdown.md")
    path_to_rst = cd(dat_dir, "markdown.rst")
    verbose = True

    convert_md_to_rst(path_to_md, path_to_rst, verbose)
    # Converting "markdown.md" to .rst ...
    # Saving "markdown.rst" to "..\\tests\\data" ... Done.


if __name__ == '__main__':
    print("\nTesting 'find_similar_str()':")
    test_find_similar_str()

    print("\nTesting 'find_matched_str()':")
    test_find_matched_str()

    print("\nTesting 'remove_punctuation()':")
    test_remove_punctuation()

    print("\nTesting 'count_words()':")
    test_count_words()

    print("\nTesting 'calculate_idf()':")
    test_calculate_idf()

    print("\nTesting 'calculate_tf_idf()':")
    test_calculate_tf_idf()

    print("\nTesting 'euclidean_distance_between_texts()':")
    test_euclidean_distance_between_texts()

    print("\nTesting 'cosine_similarity_between_texts()':")
    test_cosine_similarity_between_texts()

    print("\nTesting 'convert_md_to_rst()':")
    test_convert_md_to_rst()
