"""Test the module :mod:`~pyhelpers.text`."""

import pytest
import functools

from pyhelpers.text import *


@pytest.mark.parametrize('rm_whitespace', [True, False])
def test_remove_punctuation(rm_whitespace):
    raw_text = 'Hello world!\tThis is a test. :-)'
    text = remove_punctuation(raw_text, rm_whitespace)

    if rm_whitespace:
        assert text == 'Hello world This is a test'
    else:
        assert text == 'Hello world \tThis is a test'


@pytest.mark.parametrize('only_capitals', [False, True])
@pytest.mark.parametrize('capitals_in_words', [False, True])
@pytest.mark.parametrize('keep_punctuation', [False, True])
def test_get_acronym(only_capitals, capitals_in_words, keep_punctuation):
    text_a = 'This is an apple.'
    assert get_acronym(text_a) == 'TIAA'

    text_b = "I'm at the University of Birmingham."
    acron_b = get_acronym(text_b, only_capitals=only_capitals)
    if not only_capitals:
        assert acron_b == 'IMATUOB'
    else:
        assert acron_b == 'IUB'

    text_c = 'There is a "ConnectionError"!'
    acron_c = get_acronym(text_c, only_capitals, capitals_in_words, keep_punctuation)
    if capitals_in_words and not (only_capitals or keep_punctuation):
        assert acron_c == 'TIACE'
    if only_capitals and capitals_in_words and not keep_punctuation:
        assert acron_c == 'TCE'
    if only_capitals and keep_punctuation and not capitals_in_words:
        assert acron_c == 'T"C"!'
    if capitals_in_words and keep_punctuation and not only_capitals:
        assert acron_c == 'TIA"CE"!'
    if all([only_capitals, capitals_in_words, keep_punctuation]):
        assert acron_c == 'T"CE"!'


@pytest.mark.parametrize('join_with', [None, ' '])
def test_extract_words1upper(join_with):
    x1, x2 = 'Network_Waymarks', 'NetworkRailRetainingWall'
    y1, y2 = map(functools.partial(extract_words1upper, join_with=join_with), [x1, x2])

    if join_with:
        assert y1 == 'Network Waymarks'
        assert y2 == 'Network Rail Retaining Wall'
    else:
        assert y1 == ['Network', 'Waymarks']
        assert y2 == ['Network', 'Rail', 'Retaining', 'Wall']


def test__english_numerals():
    from pyhelpers.text.preproc import _english_numerals

    res = _english_numerals()
    assert isinstance(res, dict)
    assert len(res) >= 36


def test_numeral_english_to_arabic():
    assert numeral_english_to_arabic('one') == 1

    assert numeral_english_to_arabic('one hundred and one') == 101

    assert numeral_english_to_arabic('a thousand two hundred and three') == 1203

    assert numeral_english_to_arabic('200 and five') == 205

    with pytest.raises(Exception, match='Illegal word: "fivety"'):
        numeral_english_to_arabic('Two hundred and fivety')  # Two hundred and fifty


def test_count_words():
    raw_text = 'This is an apple. That is a pear. Hello world!'

    assert count_words(raw_text) == {
        'This': 1,
        'is': 2,
        'an': 1,
        'apple': 1,
        '.': 2,
        'That': 1,
        'a': 1,
        'pear': 1,
        'Hello': 1,
        'world': 1,
        '!': 1,
    }

    assert count_words(remove_punctuation(raw_text)) == {
        'This': 1,
        'is': 2,
        'an': 1,
        'apple': 1,
        'That': 1,
        'a': 1,
        'pear': 1,
        'Hello': 1,
        'world': 1,
    }


@pytest.mark.parametrize('rm_punc', [False, True])
def test_calculate_idf(rm_punc):
    raw_doc = [
        'This is an apple.',
        'That is a pear.',
        'It is human being.',
        'Hello world!']
    docs_tf_, corpus_idf_ = calculate_idf(raw_doc, rm_punc=rm_punc)

    if not rm_punc:
        assert docs_tf_ == [
            {'This': 1, 'is': 1, 'an': 1, 'apple': 1, '.': 1},
            {'That': 1, 'is': 1, 'a': 1, 'pear': 1, '.': 1},
            {'It': 1, 'is': 1, 'human': 1, 'being': 1, '.': 1},
            {'Hello': 1, 'world': 1, '!': 1}]
        assert corpus_idf_ == {
            'This': 0.6931471805599453,
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

    else:
        assert docs_tf_ == [
            {'This': 1, 'is': 1, 'an': 1, 'apple': 1},
            {'That': 1, 'is': 1, 'a': 1, 'pear': 1},
            {'It': 1, 'is': 1, 'human': 1, 'being': 1},
            {'Hello': 1, 'world': 1}]
        assert corpus_idf_ == {
            'This': 0.6931471805599453,
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


def test_calculate_tf_idf():
    raw_doc = [
        'This is an apple.',
        'That is a pear.',
        'It is human being.',
        'Hello world!']

    docs_tf_idf_ = calculate_tf_idf(raw_documents=raw_doc)
    assert docs_tf_idf_ == {
        'This': 0.6931471805599453,
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

    docs_tf_idf_ = calculate_tf_idf(raw_documents=raw_doc, rm_punc=True)
    assert docs_tf_idf_ == {
        'This': 0.6931471805599453,
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


def test_euclidean_distance_between_texts():
    txt_1, txt_2 = 'This is an apple.', 'That is a pear.'

    euclidean_distance = euclidean_distance_between_texts(txt_1, txt_2)
    assert euclidean_distance == 2.449489742783178


def test_cosine_similarity_between_texts():
    txt_1, txt_2 = 'This is an apple.', 'That is a pear.'

    cos_sim = cosine_similarity_between_texts(txt_1, txt_2)
    assert cos_sim == 0.25

    cos_dist = cosine_similarity_between_texts(txt_1, txt_2, cosine_distance=True)  # 1 - cos_sim
    assert cos_dist == 0.75


def test_find_matched_str():
    lookup_lst = ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel']
    res = find_matched_str('apple', lookup_lst)
    assert list(res) == []

    lookup_lst += ['apple']
    assert lookup_lst == ['abc', 'aapl', 'app', 'ap', 'ape', 'apex', 'apel', 'apple']

    res = find_matched_str('apple', lookup_lst)
    assert list(res) == ['apple']

    res = find_matched_str(r'app(le)?', lookup_lst)
    assert list(res) == ['app', 'apple']


def test_find_similar_str():
    from pyhelpers.text.analyser import _find_str_by_rapidfuzz

    lookup_lst = [
        'Anglia',
        'East Coast',
        'East Midlands',
        'North and East',
        'London North Western',
        'Scotland',
        'South East',
        'Wales',
        'Wessex',
        'Western']

    y = find_similar_str(x='angle', lookup_list=lookup_lst)
    assert y == 'Anglia'
    y = find_similar_str(x='angle', lookup_list=lookup_lst, n=2)
    assert y == ['Anglia', 'Wales']

    y = find_similar_str(x='angle', lookup_list=lookup_lst, engine='rapidfuzz')
    assert y == 'Anglia'
    y = find_similar_str('angle', lookup_lst, n=2, engine='rapidfuzz')
    assert y == ['Anglia', 'Wales']

    y = find_similar_str(x='x', lookup_list=lookup_lst)
    assert y is None
    y = find_similar_str(x='x', lookup_list=lookup_lst, cutoff=0.25)
    assert y == 'Wessex'
    y = find_similar_str(x='x', lookup_list=lookup_lst, n=2, cutoff=0.25)
    assert y == 'Wessex'

    y = find_similar_str(x='x', lookup_list=lookup_lst, engine='fuzz')
    assert y == 'Wessex'
    y = find_similar_str(x='x', lookup_list=lookup_lst, n=2, engine='fuzz')
    assert y == ['Wessex', 'Western']

    y = find_similar_str(x='123', lookup_list=lookup_lst, n=1, engine='fuzz')
    assert y is None

    y = find_similar_str(x='anglia', lookup_list=lookup_lst, n=1, engine=_find_str_by_rapidfuzz)
    assert y == 'Anglia'

    y = find_similar_str(x='123', lookup_list=lookup_lst, n=1, engine=_find_str_by_rapidfuzz)
    assert y is None

    with pytest.raises(Exception):
        find_similar_str(x='anglia', lookup_list=lookup_lst, n=1, engine=str)


if __name__ == '__main__':
    pytest.main()
