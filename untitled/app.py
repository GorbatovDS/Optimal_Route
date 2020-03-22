# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
import urllib.request
import gzip
import time
from lxml import etree
from pyroutelib3 import Router


after_dot = 1000
places_msk = list()

# https://leafletjs.com/examples.html
# http://www.doxygen.nl
# https://www.pythonanywhere.com


def read_map(city: str) -> str:
    '''
    rewrites .osm map on your computer
    :param city: url link from where to take a map (yet to be improved)
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
    file.write('name,lat,lon\n')
    for place in places.keys():
        i += 1
        file.write(str(place).replace(',', '_-_').replace('"', "'") + ',' + str(places[place][0]) + ',' + str(places[place][1]) + '\n')
    file.close()

    print(i, 'names done')

    return names_file


def find_route(names: list, pos: (float, float), file_name: str = 'names.csv') -> dict:
    '''
    creates a file with distance matrix among chosen places
    :param names: names of the places you want to visit
    :param pos: your position at the moment (starting point) ((yet has no use))
    :param file_name: name of a file with name,lat,lon lines
    :return: return a dictionary {1: 'first place', 2: 'second place', ...} (for later in code)
    '''
    global after_dot
    places_number_name = dict()
    places_name_coor = dict()
    name_in = 'SampleIn_1.txt'
    name_out = 'SampleOut.txt'

    places_number_name[1] = 'curr_pos'

    for i in range(1, len(names) + 1):
        places_number_name[i + 1] = names[i - 1]

    file = open(file_name, 'r')

    places_name_coor['curr_pos'] = pos

    for line in file.readlines():
        if line.split(sep=',')[0] in names:
            places_name_coor[line.split(sep=',')[0]] = (float(line.split(sep=',')[1]), float(line.split(sep=',')[2]))

    file.close()

    file_m = open(name_in, 'w', encoding='UTF-8')
    file_m.write(str(len(names) + 1) + '\n')

    router = Router('foot')

    for name_start in places_name_coor.keys():
        to_write = str()
        start = router.findNode(places_name_coor[name_start][0], places_name_coor[name_start][1])
        for name_end in places_name_coor.keys():
            end = router.findNode(places_name_coor[name_end][0], places_name_coor[name_end][1])
            status, route = router.doRoute(start, end)
            # print(status)
            if status == 'success':
                routeLatLons = list(map(router.nodeLatLon, route))

                sum_ = 0

                for i in range(len(routeLatLons) - 1):
                    sum_ += router.distance(routeLatLons[i], routeLatLons[i + 1])
                sum_ *= after_dot
                to_write += ' ' + str(sum_)[:str(sum_).index('.')] + ' '
            elif status == 'no_route':
                to_write += '-1 '
        to_write = to_write.rstrip()
        file_m.write(to_write + '\n')

    file_m.close()
    return places_number_name


def get_cp(name: str = 'Sample_Out1.txt') -> (int, list):
    file = open(name, 'r')

    cost = int()
    path = list()

    for line in file.readlines():
        if line.startswith("Cost:"):
            line = line.replace('Cost', "'Cost'")
            cost_str = '{' + line + '}'
            cost_dict = eval(cost_str)
            cost = cost_dict['Cost']
        if line.startswith("Path:"):
            path_str = line[line.index(':') + 1:].strip()
            for way in path_str.split(sep=' '):
                path.append(eval(way))

    file.close()

    path.sort(key=lambda tup: tup[0])

    path_true = list()
    path_true.append(1)

    for _i in range(len(path)):
        for way in path:
            if (way[0] == path_true[-1]) and (way[1] not in path_true):
                path_true.append(way[1])

    return cost, path_true


clicks = 0  # переменная для подсчета нажатий на кнопку Evaluate Route
places_spb = ['place_1_s', 'place_2_s', 'place_3_s', 'place_4_s', 'place_5_s']

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)  # создаем переменную с которой budem работать

app.layout = html.Div(children=[
    html.H1(children='Route', id='markdown'),  # H1 - заголовочный тег в HTML

    # dropdown - список
    # этот для выбора __города__
    dcc.Dropdown(
        id='city_dropdown',
        options=[
            {'label': 'Snt Petersburg', 'value': 'Snt Petersburg'},
            {'label': 'Moscow', 'value': 'Moscow'},
            {'label': 'Krasnodar', 'value': 'ksd', 'disabled': True},
        ],

        multi=False,  # мнодественные вариант выбора отключили
        searchable=True,  # за покажу
        placeholder='Выберите город',  # что там написано пока не выбрали
    ),

    # этот для выбора __мест__
    dcc.Dropdown(
        id='places_dropdown',  # у него будем меняться

        options=[],  # пока не выбрали город - выриантов нет
        disabled=True,  # пока не выбрали город - не можем выбрать
        multi=True,  # несколько вариантов
        placeholder='Выберите места',
    ),

    html.Button(children='Evaluate route', id='route', n_clicks=0),  # кнопка

    html.Div([
        html.H6(id='names', children=''),
        html.H1(id='path', children=''),

    ]),  # эти два заголовка пока не видны, как только маршрут будет - они появятся


])


@app.callback([dash.dependencies.Output('places_dropdown', 'options'),
               dash.dependencies.Output('places_dropdown', 'disabled'),
               ],
              [dash.dependencies.Input('city_dropdown', 'value')],
              [dash.dependencies.State('places_dropdown', 'options')]
              )
def func(city, curr):
    global places_msk
    global places_spb
    if city == 'Moscow':
        curr.clear()
        for place in places_msk:
            dct = dict()
            dct['label'] = str(place)
            dct['value'] = str(place)
            curr.append(dct)

        return [curr, False]
    elif city == 'Snt Petersburg':
        curr.clear()
        for place in places_spb:
            dct = dict()
            dct['label'] = str(place)
            dct['value'] = str(place)
            curr.append(dct)

        return [curr, False]
    else:
        return [[], True]


@app.callback(dash.dependencies.Output('markdown', 'children'),
              [dash.dependencies.Input('city_dropdown', 'value')]
              )
def func2(value):
    if value is not None:
        return 'Route for %s' % value
    else:
        return 'Route'


@app.callback([dash.dependencies.Output('names', 'children'),
               dash.dependencies.Output('path', 'children')],
              [dash.dependencies.Input('route', 'n_clicks'),
               dash.dependencies.Input('places_dropdown', 'value')])
def print_path(n_click, places):
    global clicks
    cost, path = get_cp()
    line2 = 'current_position, '
    line1 = str()
    if (places is not None) and (places != []):
        if n_click > clicks:

            pnn = find_route(places, (55.788845, 37.613809))
            print(places)
            print(pnn)

            for place in places:
                line2 += place + ', '

            for stretch in path:
                line1 += str(pnn[stretch]) + '->'

            line1 += str(pnn[path[0]])
            clicks = n_click
            return [line2, line1]

    clicks = n_click
    return ['', '']


def main():
    # found this places manually, yet to be updated
    # (it's just a few places, must find other keys and their values that we need)
    keys = ['tourism',
            'amenity',
            'disused:amenity']
    values = ['museum',
              'artwork',
              'theme_park',
              'zoo',
              'gallery',
              'aquarium',
              'attraction',
              'viewpoint',
              'place_of_worship']
    print('hello')
    url_moscow = "https://download.bbbike.org/osm/bbbike/Moscow/Moscow.osm.gz"
    # url_spb = "https://download.bbbike.org/osm/bbbike/SanktPetersburg/SanktPetersburg.osm.gz"
    map_ = read_map(url_moscow)
    pls = get_places(map_, keys, values)
    file = open(pls, 'r', encoding='UTF-8')
    global places_msk
    for line in file.readlines():
        if line == 'name,lat,lon':
            continue
        places_msk.append(line.split(sep=',')[0].replace('_-_', ','))
    file.close()
    places_msk.sort()
    print('end')


# main()
file = open('names.csv', 'r', encoding='UTF-8')
for line in file.readlines():
    if line == 'name,lat,lon':
        continue
    places_msk.append(line.split(sep=',')[0].replace('_-_', ','))
file.close()
places_msk.sort()
app.run_server(debug=True)
