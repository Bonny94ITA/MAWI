from spacy.tokens import Doc

def find_indexes(doc: Doc, ch): 
    """ Find the index of the character ch in the doc.

    Args:
        doc: spacy doc where to search
        ch: character to search
    
    Returns:
        list of the indexes of the character ch
    """

    indexes = []
    end = 0
    for i, token in enumerate(doc):
        if token.text == ch:
            indexes.append(i)
        end = i
    indexes.append(end)
    return indexes