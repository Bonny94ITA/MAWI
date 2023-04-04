from src.model import create_model, create_geocoder
from src.preprocessing import create_directory
from src.entities import get_entities_snippet
from src.location import search_entities_geopy, get_geographic_scope
from src.utils import save_results, read_article, read_titles

import logging

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

trf = True
type = 1
lang = "it"

path_articles1_it = f'input/articles1/it/texts/'
path_articles1_en = f'input/articles1/en/texts/'
path_articles2 = f'input/articles2/it/texts/'

path_articles1_titles = f'input/articles1/articles1_title.txt'
path_articles2_titles = f'input/articles2/articles2_title.txt'

path_results = f'results/extraction_entities_snippet/'

titles_articles = read_titles(path_articles1_titles, lang) 

model = create_model(lang, trf)

geocoder = create_geocoder()

for title in titles_articles:
    # Read wiki articles from file
    print("Current article to analyze: ", title)
    if lang == "it":
        path_article = path_articles1_it+title+".txt"
    else:
        path_article = path_articles1_en+title+".txt"
    
    text = read_article(path_article)
    logging.info('read_article')

    path_result_article = create_directory(title, path_results, lang, type, trf)

    nlp = None
    geographic_scope = ""
    searchable_entities = dict()
    sentence_dict = dict()
    features = list()
    entities_final = list()

    nlp = model

    doc = nlp(text)

    geographic_scope = get_geographic_scope(doc, lang, geocoder) # TODO: controllare che funzioni anche per gli articoli di tipo 2

    # Get entities without duplicates

    searchable_entities, sentence_dict = get_entities_snippet(doc)
    logging.info('get_entities_snippet')

    
    # Search addresses with Google
    features, entities_final = search_entities_geopy(searchable_entities, geographic_scope, path_result_article, lang, geocoder)
    logging.info('search_entities_geopy')

    save_results(features, path_result_article, title)

    print("number of entities: ", len(searchable_entities))

    entities_complete = list(searchable_entities.keys())
    entities_complete.sort(key= str.lower)
    file_path_entities_complete = path_result_article+"/"+title+"_entities.txt" 

    with open(file_path_entities_complete, 'w', encoding='utf-8') as f:
        for entity in entities_complete:
            f.write(entity + '\n')

"""

    startTime = datetime.now()
    searchable_entities = get_further_information(searchable_entities, geographic_scope['name'], lang)
    print("Get_further_information method takes: ", str(datetime.now() - startTime))
    
    nearby_pages = get_nearby_pages(city)


    print(nearby_pages)
    
    for page in nearby_pages:
        print("Current page to analyze: ", page)
        text = wiki_content(page)
        doc = nlp(text)

        searchable_entities, _ = get_entities_snippet(doc, searchable_entities)

        searchable_entities = get_further_information(searchable_entities, city)

        features, _ = search_entities_geopy(searchable_entities, context, city, features)
"""