import spacy

nlp = spacy.load('it_core_news_sm')
nlp.add_pipe('sentencizer')


text = "Per il successo di questa corrente stilistica e la tipologia di edifici che sorse nei primi decenni del Novecento, Torino divenne una delle capitali del liberty tanto che si percepiscono ancora oggi cospicue testimonianze architettoniche di quel periodo. In Italia, e particolarmente a Torino, la nuova corrente si affermò inizialmente come «arte nuova», declinando il termine direttamente dal francese. nel capoluogo piemontese insediarono nuovi e numerosi stabilimenti proprio negli anni a ridosso tra Ottocento e Novecento."
doc = nlp(text)

sents_list = []
for sent in doc.sents:
    sents_list.append(sent.text)

# print(sents_list)
# print([token.text for token in doc])

for elem in sents_list:
    print(elem)
    print("\n")
