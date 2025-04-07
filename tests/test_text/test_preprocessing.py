"""
Tests the :mod:`~pyhelpers.text.utils` submodule.
"""

import functools

import pytest

from pyhelpers.text.preprocessing import *
from pyhelpers.text.preprocessing import _english_numerals


@pytest.mark.parametrize('rm_whitespace', [True, False])
@pytest.mark.parametrize('preserve_hyphenated', [True, False])
def test_remove_punctuation(rm_whitespace, preserve_hyphenated):
    raw_text = 'Hello world!\tThis is a test. :-) No hyphenated-word contents.'

    text = remove_punctuation(
        raw_text, rm_whitespace=rm_whitespace, preserve_hyphenated=preserve_hyphenated)
    if rm_whitespace:
        if preserve_hyphenated:
            assert text == 'Hello world This is a test No hyphenated-word contents'
        else:
            assert text == 'Hello world This is a test No hyphenated word contents'
    else:
        if preserve_hyphenated:
            assert text == 'Hello world \tThis is a test      No hyphenated-word contents'
        else:
            assert text == 'Hello world \tThis is a test      No hyphenated word contents'


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
def test_split_on_uppercase(join_with):
    test_inputs = [
        'Network_Waymarks',
        'NetworkRailRetainingWall',
        'BCRRE_Projects',
        'BCRRE-Projects',
        'Version2Update',
        'file_name_with_underscores',
        'some-text-in-kebab-case',
    ]
    test_outputs = map(functools.partial(split_on_uppercase, join_with=join_with), test_inputs)

    if join_with:
        assert list(test_outputs) == [
            'Network Waymarks',
            'Network Rail Retaining Wall',
            'BCRRE Projects',
            'BCRRE Projects',
            'Version 2 Update',
            'file_name_with_underscores',
            'some-text-in-kebab-case',
        ]
    else:
        assert list(test_outputs) == [
            ['Network', 'Waymarks'],
            ['Network', 'Rail', 'Retaining', 'Wall'],
            ['BCRRE', 'Projects'],
            ['BCRRE', 'Projects'],
            ['Version', '2', 'Update'],
            ['file_name_with_underscores'],
            ['some-text-in-kebab-case']]


def test__english_numerals():
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


@pytest.mark.parametrize('lowercase', [False, True])
@pytest.mark.parametrize('ignore_punctuation', [False, True])
@pytest.mark.parametrize('stop_words', [None, True, ['a', 'an', 'is']])
def test_count_words(lowercase, ignore_punctuation, stop_words):
    text = 'This is an apple. That is a pear. Hello world!'

    word_count_dict = count_words(
        text, lowercase=lowercase, ignore_punctuation=ignore_punctuation, stop_words=stop_words)

    if stop_words is None:
        if lowercase is False and ignore_punctuation is False:
            assert word_count_dict == {
                'This': 1, 'is': 2, 'an': 1, 'apple': 1, '.': 2, 'That': 1, 'a': 1, 'pear': 1,
                'Hello': 1, 'world': 1, '!': 1}
        elif lowercase is True and ignore_punctuation is False:
            assert word_count_dict == {
                'this': 1, 'is': 2, 'an': 1, 'apple': 1, '.': 2, 'that': 1, 'a': 1, 'pear': 1,
                'hello': 1, 'world': 1, '!': 1}
        elif lowercase is True and ignore_punctuation is True:
            assert word_count_dict == {
                'this': 1, 'is': 2, 'an': 1, 'apple': 1, 'that': 1, 'a': 1, 'pear': 1,
                'hello': 1, 'world': 1}
        else:
            assert word_count_dict == {
                'This': 1, 'is': 2, 'an': 1, 'apple': 1, 'That': 1, 'a': 1, 'pear': 1,
                'Hello': 1, 'world': 1}

    elif stop_words is True:
        if lowercase is False and ignore_punctuation is False:
            assert word_count_dict == {
                'apple': 1, '.': 2, 'pear': 1, 'Hello': 1, 'world': 1, '!': 1}
        elif lowercase is True and ignore_punctuation is False:
            assert word_count_dict == {
                'apple': 1, '.': 2, 'pear': 1, 'hello': 1, 'world': 1, '!': 1}
        elif lowercase is True and ignore_punctuation is True:
            assert word_count_dict == {'apple': 1, 'pear': 1, 'hello': 1, 'world': 1}
        else:
            assert word_count_dict == {'apple': 1, 'pear': 1, 'Hello': 1, 'world': 1}

    else:
        if lowercase is False and ignore_punctuation is False:
            assert word_count_dict == {
                'This': 1, 'apple': 1, '.': 2, 'That': 1, 'pear': 1, 'Hello': 1, 'world': 1, '!': 1}
        elif lowercase is True and ignore_punctuation is False:
            assert word_count_dict == {
                'this': 1, 'apple': 1, '.': 2, 'that': 1, 'pear': 1, 'hello': 1, 'world': 1, '!': 1}
        elif lowercase is True and ignore_punctuation is True:
            assert word_count_dict == {
                'this': 1, 'apple': 1, 'that': 1, 'pear': 1, 'hello': 1, 'world': 1}
        else:
            assert word_count_dict == {
                'This': 1, 'apple': 1, 'That': 1, 'pear': 1, 'Hello': 1, 'world': 1}


@pytest.mark.parametrize('lowercase', [True, False])
@pytest.mark.parametrize('ignore_punctuation', [True, False])
def test_calculate_idf(lowercase, ignore_punctuation):
    documents = [
        'This is an apple.',
        'That is a pear.',
        'It is human being.',
        'Hello world!']

    docs_tf, corpus_idf = calculate_idf(
        documents, lowercase=lowercase, ignore_punctuation=ignore_punctuation)

    if lowercase and ignore_punctuation:
        assert docs_tf == [
            {'this': 1, 'is': 1, 'an': 1, 'apple': 1},
            {'that': 1, 'is': 1, 'a': 1, 'pear': 1},
            {'it': 1, 'is': 1, 'human': 1, 'being': 1},
            {'hello': 1, 'world': 1}]
        assert corpus_idf == {
            'this': 0.6931471805599453,
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

    elif not lowercase and ignore_punctuation:
        assert docs_tf == [
            {'This': 1, 'is': 1, 'an': 1, 'apple': 1},
            {'That': 1, 'is': 1, 'a': 1, 'pear': 1},
            {'It': 1, 'is': 1, 'human': 1, 'being': 1},
            {'Hello': 1, 'world': 1}]
        assert corpus_idf == {
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

    elif not lowercase and not ignore_punctuation:
        assert docs_tf == [
            {'This': 1, 'is': 1, 'an': 1, 'apple': 1, '.': 1},
            {'That': 1, 'is': 1, 'a': 1, 'pear': 1, '.': 1},
            {'It': 1, 'is': 1, 'human': 1, 'being': 1, '.': 1},
            {'Hello': 1, 'world': 1, '!': 1}]
        assert corpus_idf == {
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
        assert docs_tf == [
            {'this': 1, 'is': 1, 'an': 1, 'apple': 1, '.': 1},
            {'that': 1, 'is': 1, 'a': 1, 'pear': 1, '.': 1},
            {'it': 1, 'is': 1, 'human': 1, 'being': 1, '.': 1},
            {'hello': 1, 'world': 1, '!': 1}]
        assert corpus_idf == {
            'this': 0.6931471805599453,
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


@pytest.mark.parametrize('lowercase', [True, False])
def test_calculate_tfidf(lowercase):
    documents = [
        'This is an apple.',
        'That is a pear.',
        'It is human being.',
        'Hello world!']

    tfidf = calculate_tfidf(documents, lowercase=lowercase, ignore_punctuation=True)
    if lowercase:
        assert tfidf == {
            'this': 0.6931471805599453,
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
    else:
        assert tfidf == {
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


if __name__ == '__main__':
    pytest.main()
