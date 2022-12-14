import spacy

def create_model(): 
    """ Create the model with the pipeline of SpaCy and the NER transformer.
    
    Returns:
        model: the model with the pipeline
    """

    model = spacy.load("it_core_news_sm", exclude=["ner"])

    ner = spacy.load('it_nerIta_trf')

    model.add_pipe("transformer", name="trf_ita", source=ner, last=True)

    model.add_pipe("ner", name="ner_ita", source=ner, last=True)

    return model
