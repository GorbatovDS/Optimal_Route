# -*- coding: UTF-8 -*-
import urllib.request
import gzip
from lxml import etree
# import requests
# import json


def read_map(city: str) -> str:
    webmap = gzip.open(urllib.request.urlopen(city), 'r')  # opening online-archive to get XML map file
    map_name = 'map.osm'
    file = open(map_name, 'w', encoding='UTF-8')

    # rewriting map to the computer
    for line in webmap.readlines():
        file.write(line.decode('UTF-8'))

    file.close()
    print('map done')
    return map_name


def get_places(map_name: str, places_we_need: list) -> dict:
    f = open('names.csv', 'w')
    names = dict()
    root = etree.parse(map_name).getroot()  # got the element tree root of XML file

    # getting places names and their coordinates
    for child in root.getchildren():
        if child.tag == 'node':
            for grandchild in child.getchildren():
                if (grandchild is not None) and (grandchild.tag == 'tag') and (
                        grandchild.attrib['k'] == 'tourism') and (grandchild.attrib['v'] in places_we_need):
                    for c in child.getchildren():
                        if c.attrib['k'] == 'name':
                            names[c.attrib['v']] = (child.attrib['lat'], child.attrib['lon'])

    print(len(names), 'names done')
    f.write('name,lat,lon\n')

    # saving to .csv because i want
    # might delete later on
    for name in names.keys():
        f.write(name + ',' + names[name][0] + ',' + names[name][1] + '\n')

    f.close()
    return names


def main() -> int:
    # found this places manually, yet to be updated
    # (it's only tourism tagged places, must find others keys and their values that we need)
    tourism = ['museum', 'artwork', 'theme_park', 'zoo', 'gallery', 'aquarium', 'attraction', 'viewpoint']
    url_moscow = "https://download.bbbike.org/osm/bbbike/Moscow/Moscow.osm.gz"
    url_spb = "https://download.bbbike.org/osm/bbbike/SanktPetersburg/SanktPetersburg.osm.gz"
    map_ = read_map(url_moscow)
    places = get_places(map_, tourism)
    print(len(places.keys()), 'names returned')
    print('end')
    return 0


if __name__ == '__main__':
    main()









































'''
# ignore this
# s.cpp execute
import os
import subprocess

os.system('/Users/mjlq2/PycharmProjects/untitled/s')
# subprocess.run('/Users/mjlq2/PycharmProjects/untitled/s')
'''


'''
# evaluating route
router = Router('bus')

    start = router.findNode(55.751177, 37.633280)
    end = router.findNode(55.759923, 37.625686)
    print('b')
    status, route = router.doRoute(start, end)
    print('c')
    if status == 'success':
        routeLatLons = list(map(router.nodeLatLon, route))

    sum_ = 0

    for i in range(len(routeLatLons) - 1):
        sum_ += router.distance(routeLatLons[i], routeLatLons[i + 1])

    print(sum_)
'''


'''
# probably useless
data = requests.get('https://apidata.mos.ru/v1/datasets/527/rows/?api_key=da77fc2dc5912ea2890050390f522d99')

dct = json.loads(data.text)

names = list()

for i in range(len(dct)):
    names.append(dct[i]['Cells']['CommonName'].replace('«', '"').replace('»', '"'))


print('names done\n', names)
'''