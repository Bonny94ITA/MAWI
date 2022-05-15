import json

filtered_cities = []

"""
    Read json file with the cities to filter, the goal is to have a json with only
    italian cities. In addiction is useful to clean all the cities with 'Provincia di' 
    and 'Città metropolitana di'. 
"""
with open(f'assets/cities.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

    for element in data:
        if element['country_code'] == 'IT':
            if element['name'].__contains__("Provincia di"): 
                element['name'] = element['name'].replace("Provincia di", '') 
            elif element['name'].__contains__("Città metropolitana di"):
                element['name'] = element['name'].replace("Città metropolitana di", '')
            filtered_cities.append(element)

with open(f'assets/italian_cities.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_cities, f, indent=4)
