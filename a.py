# -*- coding: UTF-8 -*-
import urllib.request
import gzip
from lxml import etree
from pyroutelib3 import Router


def read_map(city: str) -> str:
    '''
    rewrites .osm map on your computer
    :param city: url link from where to take a map (yet to be imoroved)
    :return: file name, where map was rewritten
    '''
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
    '''
    finding a node coordinates
    :param node: etree node for which to get coordinates
    :param root: etree root (optional, needed only for <way /> tags)
    :param node_id: optional parameter, the <node /> id reference from where to look for coordinates
    :return: returns a tuple (lat, lon)
    '''
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
    '''
    finding a node name
    :param node: etree node for wich to find a name (of a place)
    :return: returns a name
    '''
    for child in node.getchildren():
        if ('k' in child.attrib.keys()) and (child.attrib['k'] == 'name'):
            return child.attrib['v']


def get_places(map_name: str, ks: list, vs: list) -> str:
    '''
    finding all fitting places
    # --------------------------
    # in each element of etree finds child:
    # <tag k="__key__" v="__value__">
    # --------------------------
    :param map_name: file name where .osm map is
    :param ks: keys to find
    :param vs: values to find
    :return: returns a .csv file name where lies name,lat,lon lines of found objects
    '''
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

    names_file = 'names.csv'

    file = open(names_file, 'w', encoding='UTF-8')
    file.write('name,lat,lon')
    for place in places.keys():
        i += 1
        file.write(str(place).replace(',', '_-_').replace('"', "'") + ',' + str(places[place][0]) + ',' + str(places[place][1]) + '\n')
    file.close()

    print(i)

    return names_file


def find_route(names: list, pos: (float, float), file_name: str = 'names.csv') -> dict:
    '''
    creates a file with distance matrix among chosen places
    :param names: names of the places you want to visit
    :param pos: your position at the moment (starting point) ((yet has no use))
    :param file_name: name of a file with name,lat,lon lines
    :return: return a dictionary {1: 'first place', 2: 'second place', ...} (for later in code)
    '''
    places_number_name = dict()
    places_name_coor = dict()
    name_in = 'SampleIn_1.txt'
    name_out = 'SampleOut.txt'

    for i in range(len(names)):
        places_number_name[i + 1] = names[i]

    file = open(file_name, 'r')

    for line in file.readlines():
        if line.split(sep=',')[0] in names:
            places_name_coor[line.split(sep=',')[0]] = (float(line.split(sep=',')[1]), float(line.split(sep=',')[2]))

    file.close()

    file_m = open(name_in, 'w', encoding='UTF-8')
    file_m.write(str(len(names)) + '\n')

    router = Router('car')

    for name_start in places_name_coor.keys():
        start = router.findNode(places_name_coor[name_start][0], places_name_coor[name_start][1])
        for name_end in places_name_coor.keys():
            end = router.findNode(places_name_coor[name_end][0], places_name_coor[name_end][1])
            if name_start == name_end:
                file_m.write('-1 ')
                continue
            status, route = router.doRoute(start, end)
            print(status)
            if status == 'success':
                routeLatLons = list(map(router.nodeLatLon, route))

                sum_ = 0

                for i in range(len(routeLatLons) - 1):
                    sum_ += router.distance(routeLatLons[i], routeLatLons[i + 1])
                file_m.write(' ' + str(sum_)[:5] + ' ')
        file_m.write('\n')

    file_m.close()
    return places_number_name


def main() -> int:
    # found this places manually, yet to be updated
    # (it's just a few places, must find other keys and their values that we need)
    keys = ['tourism', 'amenity', 'disused:amenity']
    values = ['museum', 'artwork', 'theme_park', 'zoo', 'gallery', 'aquarium', 'attraction', 'viewpoint', 'place_of_worship']
    print('hello')
    url_moscow = "https://download.bbbike.org/osm/bbbike/Moscow/Moscow.osm.gz"
    url_spb = "https://download.bbbike.org/osm/bbbike/SanktPetersburg/SanktPetersburg.osm.gz"
    map_ = 'map.osm'  # read_map(url_moscow)
    pls = 'names.csv'  # get_places(map_, keys, values)
    file = open(pls, 'r', encoding='UTF-8')
    names = list()
    for line in file.readlines():
        names.append(line.split(sep=',')[0].replace('_-_', ','))
    file.close()
    names.sort()
    print(find_route(names[:5], (0, 0)))
    print('end')
    return 0


if __name__ == '__main__':
    main()
