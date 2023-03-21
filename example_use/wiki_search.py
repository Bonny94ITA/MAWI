
import wikipediaapi

wiki_wiki = wikipediaapi.Wikipedia('it')
wiki_page = wiki_wiki.page("Torino")

#print(wiki_page.links)

links = wiki_page.links
keys = list(links.keys())

print(keys)
