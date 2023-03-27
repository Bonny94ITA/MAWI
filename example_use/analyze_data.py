import json
import os
import matplotlib.pyplot as plt
import numpy as np
import haversine as hs
from sklearn.neighbors import LocalOutlierFactor
from shapely.geometry import Point, Polygon


# leggi il documento torino.json
file_to_read = f"results/extraction_entities_snippet/articles1/it/Torino.geojson"  # TODO: CAMBIARE PATH
with open(file_to_read, 'r', encoding='utf-8') as f: 
    data = json.load(f)

points = data['features']
#points = []
#for point_json in points_json: 
#    coordinate_x = point_json['geometry']['coordinates'][0]
#    coordinate_y = point_json['geometry']['coordinates'][1]
#    points.append(Point(coordinate_x, coordinate_y))

polygon = Polygon([(7.77, 45.08), (7.66, 45.14), (7.58, 45.04), (7.64, 45.01)])

points_in_polygon = []
for point_obj in points:
    point = Point(point_obj['geometry']['coordinates'][0], point_obj['geometry']['coordinates'][1])
    if polygon.contains(point):
        points_in_polygon.append(point_obj)

loc = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            7.773339,
                            45.077873
                        ],
                        [
                            7.664205,
                            45.140217
                        ],
                        [
                            7.577835,
                            45.041828
                        ],
                        [
                            7.644392,
                            45.006792
                        ],
                        [
                            7.773339,
                            45.077873
                        ]
                    ]
                ]
            },
            "properties": {
                "name": "turin"
            }
        }
points_in_polygon.append(loc)

# salva il risultato in un file json
data['features'] = points_in_polygon
file_to_write = f"results/Torino_geojson_cleanSH.geojson"
with open(file_to_write, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
    print("The result cleaned has been saved as a file inside the results folder")