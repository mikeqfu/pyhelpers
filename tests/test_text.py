# text.py

from pyhelpers.text import find_matched_str, find_similar_str

string = 'ang'

lookup_list = ['Anglia',
               'East Coast',
               'East Midlands',
               'North and East',
               'London North Western',
               'Scotland',
               'South East',
               'Wales',
               'Wessex',
               'Western']

# Use 'fuzzywuzzy'
result_1 = find_similar_str(string, lookup_list, processor='fuzzywuzzy')
print(result_1)

# Use 'nltk'
result_2 = find_similar_str(string, lookup_list, processor='nltk', substitution_cost=100)
print(result_2)

result_3 = find_matched_str(string, lookup_list)
print(result_3)
