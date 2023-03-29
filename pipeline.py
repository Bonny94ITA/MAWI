from src.model import create_model, create_geocoder
from src.preprocessing import get_context, create_directory
from src.entities import get_entities_snippet
from src.location import search_entities_geopy, get_geographic_scope
from src.utils import save_results, get_further_information, read_article

from datetime import datetime

path_articles1_it = f'input/articles1/it/texts/'
path_articles1_en = f'input/articles1/en/texts/'
path_articles2 = f'input/articles2/it/texts/'

path_results = f'results/extraction_entities_snippet/'

titles_articles = [("Atene", "it"), ("Barcellona", "it")]


model_it = create_model("it")
model_en = create_model("en")

geocoder = create_geocoder()

for (title, lang) in titles_articles:
    # Read wiki articles from file
    print("Current article to analyze: ", title)
    if lang == "it":
        path_article = path_articles1_it+title+".txt"
    else:
        path_article = path_articles1_en+title+".txt"
    startTime = datetime.now()
    text = read_article(path_article)
    print("-----------------------read_article : ", str(datetime.now() - startTime))

    path_result_article = create_directory(title, path_results, lang)

    nlp = None
    geographic_scope = ""
    searchable_entities = dict()
    sentence_dict = dict()
    features = list()
    entities_final = list()

    if lang == "it":
        nlp = model_it
    else:
        nlp = model_en

    doc = nlp(text)

    geographic_scope = get_geographic_scope(doc, lang, geocoder) # TODO: controllare che funzioni anche per gli articoli di tipo 2

    # Get entities without duplicates

    startTime = datetime.now()
    searchable_entities, sentence_dict = get_entities_snippet(doc)
    print("----------------------get_entities_snippet : ", str(datetime.now() - startTime))

    #startTime = datetime.now()
    #searchable_entities = get_further_information(searchable_entities, geographic_scope['name'], lang)
    #print("Get_further_information method takes: ", str(datetime.now() - startTime))


    startTime = datetime.now()
    # Search addresses with Google
    features, entities_final = search_entities_geopy(searchable_entities, geographic_scope, path_result_article, lang, geocoder)
    print("----------------------search_entities_geopy : ", str(datetime.now() - startTime)) 

    # Search nearby pages -> TODO: da aggiungere?

    save_results(features, path_result_article, title)

    print("number of entities: ", len(searchable_entities))

    entities_complete = list(searchable_entities.keys())
    entities_complete.sort(key= str.lower)
    file_path_entities_complete = path_result_article+"/"+title+"_entities.txt" 

    with open(file_path_entities_complete, 'w', encoding='utf-8') as f:
        for entity in entities_complete:
            f.write(entity + '\n')

"""
    
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