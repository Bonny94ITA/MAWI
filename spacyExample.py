import spacy
from spacy.lang.it.examples import sentences
from spacy.pipeline.ner import DEFAULT_NER_MODEL
from spacy import displacy

nlp = spacy.load("it_core_news_sm")
# config = {
#     "moves": None,
#     "update_with_oracle_cut_size": 100,
#     "model": DEFAULT_NER_MODEL,
#     "incorrect_spans_key": "incorrect_spans",
# }
# nlp.add_pipe("ner", config=config)

print("Initial sentence: ", sentences[0])
doc = nlp(sentences[0])
print("Tagged sentence: ", doc.text)

# doc = nlp("In zona San Donato, oltre alla vistosissima Casa Fenoglio, in via Piffetti[N 15] vi sono due esempi databili 1908, opera di Giovanni Gribodo e poco distante vi sono altri esemplari di edifici liberty in via Durandi, via Cibrario e ancora in via Piffetti, al civico 35; mentre di Giovan Battista Benazzo sono Casa Tasca (1903), che ostenta decori floreali, motivi geometrici circolari e ricche decorazioni in ferro battuto per ringhiere e finestre.")
# for token in doc:
#     print(token.text, token.pos_, token.dep_)

for ent in doc.ents:
    print(ent.text, ent.start_char, ent.end_char,
          ent.label_, spacy.explain(ent.label_))

# displacy.serve(doc, style="ent")
# displacy.serve(doc, style="dep")
