from utils.utils import read_text_file, count_occurrences, get_entities, search_with_google
import spacy
import json

nlp = spacy.load("it_core_news_sm")

text = read_text_file('assets/test_sentences.txt')

doc = nlp(text)

# Tokenization + POS tagging
# for token in doc:
#     # print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
#     #       token.shape_, token.is_alpha, token.is_stop, token.i, token.idx)

#     print("*" * 30)
#     print(f"Word: {token.text}")
#     print(f"Word index: {token.i}")
#     print(f"Word start character index: {token.idx}")
#     print("*" * 30)

# Opening JSON file
f = open('./assets/italian_cities.json')
italian_cities = json.load(f)

# Count occurrences
counter = count_occurrences(doc, italian_cities, "name")
print(counter)

# Max occurrence
context = max(counter, key=counter.get)
print(context)

# Get entities without duplicates
searchable_entities = get_entities(doc, counter)
print(searchable_entities)

# Search addresses with Google
search_with_google(searchable_entities, context)
