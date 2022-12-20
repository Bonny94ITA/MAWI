from utils.utils import get_entities_snippet, search_entities_geopy, wiki_content, get_nearby_pages, save_results, get_further_information
import spacy


nlp = spacy.load("it_core_news_sm", exclude=["ner"])

ner_nlp = spacy.load('it_nerIta_trf')

nlp.add_pipe("transformer", name="trf_ita", source=ner_nlp, last=True)

nlp.add_pipe("ner", name="ner_ita", source=ner_nlp, last=True)

#cities = ["Torino", "Roma", "Bologna", "Milano", "Liberty a Torino", "Barocco a Milano"]

cities = ["Torino"]

for city in cities:
    # Read wiki pages
    text, context = wiki_content(city, True)

    doc = nlp(text)

    print(context)

    # Get entities without duplicates
    searchable_entities, sentence_dict = get_entities_snippet(doc)

    print("number of entities: ", len(searchable_entities))

    entities_complete = list(searchable_entities.keys())
    entities_complete.sort(key= str.lower)
    name_context = context['name']
    file_path_entities_complete = f'response/spacy_pipeline/{name_context}_entities.txt'

    with open(file_path_entities_complete, 'w', encoding='utf-8') as f:
        for entity in entities_complete:
            f.write(entity + '\n')

    # Search addresses with Google
    features, entities_final = search_entities_geopy(searchable_entities, context, city)

    # nearby pages

    nearby_pages = get_nearby_pages(city)

    print(nearby_pages)
    """
    for page in nearby_pages:
        text = wiki_content(page)
        doc = nlp(text)

        searchable_entities = get_entities_snippet(doc, searchable_entities)

        features = search_entities(searchable_entities, context, city, features)
    
    """
    save_results(features, context)

    ## Further analysis

    snippet_ent = get_further_information(entities_final)

    file_path_snippet_ent = f'response/spacy_pipeline/Snippet_entities.txt'

    with open(file_path_snippet_ent, 'w', encoding='utf-8') as f:
        for key, snippet in snippet_ent.items():
            f.write(key +'\n')
            if snippet is None: 
                f.write('No snippet available' + '\n')
            else: 
                f.write(snippet + '\n')

