# -*- coding: UTF-8 -*-
import urllib.request
import gzip
from lxml import etree
import time


def read_map(city: str) -> str:
    webmap = gzip.open(urllib.request.urlopen(city), 'r')  # opening web-archive to get XML map file
    map_name = 'map.osm'
    file = open(map_name, 'w', encoding='UTF-8')

    # rewriting map to the computer
    for line in webmap.readlines():
        file.write(line.decode('UTF-8'))

    file.close()
    print('map done')
    return map_name


def get_node_coordinates(node: etree._Element, root: etree._Element = None, node_id: str = None) -> (float, float):
    if node.tag == 'node':
        return float(node.attrib['lat']), float(node.attrib['lon'])
    elif node.tag == 'way':
        if node_id is None:
            node_id = node.getchildren()[0].attrib['ref']

        if root is not None:
            for child in root.getchildren():
                if (child.tag == 'node') and (child.attrib['id'] == node_id):
                    return float(child.attrib['lat']), float(child.attrib['lon'])
        else:
            return -2, -2
    else:
        return -1, -1


def get_node_name(node: etree._Element) -> str:
    for child in node.getchildren():
        if ('k' in child.attrib.keys()) and (child.attrib['k'] == 'name'):
            return child.attrib['v']


def get_places(map_name: str, ks: list, vs: list) -> dict:
    places = dict()
    root = etree.parse(map_name).getroot()
    i = 0
    t0 = time.time()
    for child in root.getchildren():
        if child.getchildren() is not None:
            for grandchild in child.getchildren():
                if (grandchild.tag == 'tag') and (grandchild.attrib['k'] in ks) and (grandchild.attrib['v'] in vs):
                    i += 1
                    coors = get_node_coordinates(child, root)
                    if coors == (-1, -1):
                        continue
                    places[str(get_node_name(child)).replace('None', 'None' + str(i))] = coors
                    print(i, time.time() - t0, sep='\n')

    print('dict done')
    i = 0

    file = open('names.csv', 'w', encoding='UTF-8')
    for place in places.keys():
        i += 1
        file.write(str(place).replace(',', '_-_').replace('"', "'") + ',' + str(places[place][0]) + ',' + str(places[place][1]) + '\n')
    file.close()

    print(i)

    return places


def main() -> int:
    # found this places manually, yet to be updated
    # (it's just a few places, must find other keys and their values that we need)
    keys = ['tourism', 'amenity', 'disused:amenity']
    values = ['museum', 'artwork', 'theme_park', 'zoo', 'gallery', 'aquarium', 'attraction', 'viewpoint', 'place_of_worship']
    print('hello')
    url_moscow = "https://download.bbbike.org/osm/bbbike/Moscow/Moscow.osm.gz"
    url_spb = "https://download.bbbike.org/osm/bbbike/SanktPetersburg/SanktPetersburg.osm.gz"
    map_ = 'map.osm'  # read_map(url_moscow)
    pls = get_places(map_, keys, values)
    print('end')
    return 0


if __name__ == '__main__':
    main()
