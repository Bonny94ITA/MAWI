# MAWI: Mapping the Unmapped in Wikipedia Texts through Geographic Information Extraction

## SpaCy setup

`pip install -U pip setuptools wheel`

`pip install -U spacy`

`python -m spacy download it_core_news_sm`

`python -m spacy download en_core_web_sm`

`python -m spacy download en_core_web_trf`


# SpaCy utils

https://spacy.io/api

https://spacy.io/usage/linguistic-features

**Token attributes:**
https://spacy.io/api/token#attributes

**Entity attributes:**
https://spacy.io/usage/linguistic-features#named-entities

```
PERSON:      People, including fictional.
NORP:        Nationalities or religious or political groups.
FAC:         Buildings, airports, highways, bridges, etc.
ORG:         Companies, agencies, institutions, etc.
GPE:         Countries, cities, states.
LOC:         Non-GPE locations, mountain ranges, bodies of water.
PRODUCT:     Objects, vehicles, foods, etc. (Not services.)
EVENT:       Named hurricanes, battles, wars, sports events, etc.
WORK_OF_ART: Titles of books, songs, etc.
LAW:         Named documents made into laws.
LANGUAGE:    Any named language.
DATE:        Absolute or relative dates or periods.
TIME:        Times smaller than a day.
PERCENT:     Percentage, including ”%“.
MONEY:       Monetary values, including unit.
QUANTITY:    Measurements, as of weight or distance.
ORDINAL:     “first”, “second”, etc.
CARDINAL:    Numerals that do not fall under another type.
```

## Italian NER - trf-based

https://huggingface.co/bullmount/it_nerIta_trf

## BeautifulSoup setup and utils

https://pypi.org/project/beautifulsoup4/

`pip install beautifulsoup4`
`pip install html5lib`

## Geojson setup

https://pypi.org/project/geojson/

`pip install geojson`

http://geojson.io


## Nominatim setup and utils -> geopy library

https://github.com/geopy/geopy

`pip install geopy`



