import json
import csv

filtered_cities = []

"""
    Read json file with the cities to filter, the goal is to have a json with only
    italian cities. In addiction is useful to clean all the cities with 'Provincia di' 
    and 'Città metropolitana di'. 
"""
with open(f'assets/cities.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

    for element in data:
        #if element['country_code'] == 'IT':
        if element['name'].__contains__("Provincia di "): 
            element['name'] = element['name'].replace("Provincia di ", '') 
        elif element['name'].__contains__("Città metropolitana di "):
            element['name'] = element['name'].replace("Città metropolitana di ", '')
        filtered_cities.append(element)

with open(f'assets/cities1.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_cities, f, ensure_ascii=False, indent=4)
        

with open(f'assets/worldcitiespop.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    filtered_cities = []
    for row in reader:
        #if row['Country'] == 'it':
        filtered_cities.append(row)


with open(f'assets/cities2.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_cities, f, ensure_ascii=False, indent=4)
