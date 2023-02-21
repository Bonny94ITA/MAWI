import spacy
from langdetect import detect

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

def get_lang(text: str) -> str:
    """ Get the language of the text.
    
    Args:
        text: the text to analyze
    
    Returns:
        lang: the language of the text
    """
    lang = detect(text[:100])

    print(lang)

    return lang


