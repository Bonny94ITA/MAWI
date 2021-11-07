# https://www.machinelearningplus.com/nlp/training-custom-ner-model-in-spacy/
# Load a spacy model and chekc if it has ner
from pathlib import Path
from spacy.util import minibatch, compounding
from spacy.lang.it.examples import sentences
from spacy.pipeline.ner import DEFAULT_NER_MODEL
from spacy import displacy
import random
import spacy
from spacy.training import Example

# nlp = spacy.load('it_core_news_sm')
nlp = spacy.load('en_core_web_sm')

# config = {
#     "moves": None,
#     "update_with_oracle_cut_size": 100,
#     "model": DEFAULT_NER_MODEL,
#     "incorrect_spans_key": "incorrect_spans",
# }
# nlp.add_pipe("ner", config=config)

# print("Initial sentence: ", sentences[0])
# doc = nlp(sentences[0])
# print("Tagged sentence: ", doc.text)

# ['tok2vec', 'morphologizer', 'tagger', 'parser', 'attribute_ruler', 'lemmatizer', 'ner']
print(nlp.pipe_names)

# Getting the pipeline component
ner = nlp.get_pipe("ner")

# training data
TRAIN_DATA = [
    ("Walmart is a leading e-commerce company", {"entities": [(0, 7, "ORG")]}),
    ("I reached Chennai yesterday.", {
        "entities": [(10, 17, "GPE")]}),
    ("I recently ordered a book from Amazon", {"entities": [(24, 32, "ORG")]}),
    ("I was driving a BMW", {"entities": [(16, 19, "PRODUCT")]}),
    ("I ordered this from ShopClues", {"entities": [(20, 29, "ORG")]}),
    ("Fridge can be ordered in Amazon ", {"entities": [(0, 6, "PRODUCT")]}),
    ("I bought a new Washer", {"entities": [(16, 22, "PRODUCT")]}),
    ("I bought a old table", {"entities": [(16, 21, "PRODUCT")]}),
    ("I bought a fancy dress", {"entities": [(18, 23, "PRODUCT")]}),
    ("I rented a camera", {"entities": [(12, 18, "PRODUCT")]}),
    ("I rented a tent for our trip", {"entities": [(12, 16, "PRODUCT")]}),
    ("I rented a screwdriver from our neighbour",
     {"entities": [(12, 22, "PRODUCT")]}),
    ("I repaired my computer", {"entities": [(15, 23, "PRODUCT")]}),
    ("I got my clock fixed", {"entities": [(16, 21, "PRODUCT")]}),
    ("I got my truck fixed", {"entities": [(16, 21, "PRODUCT")]}),
    ("Flipkart started it's journey from zero", {"entities": [(0, 8, "ORG")]}),
    ("I recently ordered from Max", {"entities": [(24, 27, "ORG")]}),
    ("Flipkart is recognized as leader in market",
     {"entities": [(0, 8, "ORG")]}),
    ("I recently ordered from Swiggy", {"entities": [(24, 29, "ORG")]})
]

for text, annotations in TRAIN_DATA:
    tags = spacy.training.offsets_to_biluo_tags(
        nlp.make_doc(text), annotations.get("entities"))
    print(text, tags)
    for ent in annotations.get("entities"):
        ner.add_label(ent[2])

# Disable pipeline components you dont need to change
pipe_exceptions = ["ner"]
unaffected_pipes = [
    pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
print(unaffected_pipes)

# TRAINING THE MODEL
with nlp.disable_pipes(*unaffected_pipes):
    # Training for 30 iterations
    for iteration in range(60):

        # shuufling examples  before every iteration
        random.shuffle(TRAIN_DATA)
        losses = {}
        # batch up the examples using spaCy's minibatch
        batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.001))
        for batch in batches:
            texts, annotations = zip(*batch)

            example = []
            # Update the model with iterating each text
            for i in range(len(texts)):
                doc = nlp.make_doc(texts[i])
                example.append(Example.from_dict(doc, annotations[i]))

            # Update the model
            nlp.update(example, drop=0.5, losses=losses)

        # print("Losses", losses)

# Testing the model
doc = nlp("I repaired my computer")
print(doc.ents)
print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
