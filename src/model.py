import spacy
from geopy.geocoders import Nominatim

def create_model(lang: str): 
    """ Create the model with the pipeline of SpaCy and the NER transformer.
    
    Args:
        lang: the language of the text to analyze
    Returns:
        model: the model with the pipeline
    """
    if lang == "it":
        model = spacy.load("it_core_news_sm", exclude=["ner"])

        ner = spacy.load('it_nerIta_trf')

        model.add_pipe("transformer", name="trf_ita", source=ner, last=True)

        model.add_pipe("ner", name="ner_ita", source=ner, last=True)
    
    elif lang == "en":
        model = spacy.load("en_core_web_trf")

    return model

def create_geocoder(): 
    """ Create the geocoder.
    
    Returns:
        geocoder: the geocoder
    """
    geocoder = Nominatim(timeout=100, user_agent="PoI_geocoding")
    return geocoder

