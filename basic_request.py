import requests
from pprint import pprint
from math import hypot
from datetime import datetime
import dateutil.parser

# request types
AGENCIES = "agencies"
ARRIVAL_ESTIMATES = "arrival-estimates"
ROUTES = "routes"
SEGMENTS = "segments"
VEHICLES = "vehicles"
STOPS = "stops"

api_url = "https://transloc-api-1-2.p.rapidapi.com/"
headers = {
  "X-RapidAPI-Key": "49e8d6f922msh58d18d370a3dc27p12e16djsn3eb2f5483f33"
}


def build_geo_area(longitude, latitude, radius):
    # latitude, longitude|radius (meters)
    return str(longitude) + "," + str(latitude) + "|" + str(radius)


def get_agency(geo_area=None, agencies=None):
    payload = [ ('format',   'json'),
                ('agencies', agencies) if agencies else None,
                ('geo_area', geo_area) if geo_area else None ]
    payload = [x for x in payload if x is not None]

    response = requests.get(api_url + AGENCIES, headers=headers, params=payload)

    if len(response.json()['data']) == 0:
        print("NO AGENCY FOUND")
        exit()

    agency_id = response.json()['data'][0]
    return agency_id


def get_route(agency_id, route_name, geo_area=None):
    payload = [ ('format',   'json'),
                ('agencies', agency_id),
                ('geo_area', geo_area) if geo_area else None
                ]
    payload = [x for x in payload if x is not None]


    response = requests.get(api_url + ROUTES, headers=headers, params=payload)

    routes = response.json()['data'][agency_id]

    route_name = route_name.lower()
    for route in routes:
        if route['long_name'].lower() == route_name:
            return route

    print("couldn't find route")


def get_nearest_stop(agency_id, geo_area):
    payload = [ ('format',   'json'),
                ('agencies', agency_id),
                ('geo_area', geo_area) if geo_area else None
                ]
    payload = [x for x in payload if x is not None]

    response = requests.get(api_url + STOPS, headers=headers, params=payload)
    stops = response.json()['data']

    closest_stop = sorted(stops, key=lambda x: hypot(x['location']['lat'] - latitude, x['location']['lng'] - longitude))[0]

    return closest_stop


def get_arrival_estimates(agency_id, routes=None, stops=None):
    payload = [ ('format',   'json'),
                ('agencies', agency_id),
                ('routes', ",".join(routes)) if routes else None,
                ('stops', ",".join(stops)) if stops else None
                ]
    payload = [x for x in payload if x is not None]

    response = requests.get(api_url + ARRIVAL_ESTIMATES, headers=headers, params=payload)
    return response.json()['data'][0]['arrivals']


def get_arrival_time_estimates(arrivals):
    now = datetime.now()
    return sorted([dateutil.parser.parse(arrival['arrival_at']).replace(tzinfo=None) - now for arrival in arrivals])


# coordinates for Whyburn: 38.0294814,-78.5193463|1000
latitude = 38.0294814
longitude = -78.5193463
radius = 1000
bus_line = "Northline"
geo_area = build_geo_area(latitude, longitude, radius)

agency = get_agency(geo_area=geo_area)
agency_id = agency['agency_id']
# agency_id = '347'
print("Agency id:", agency_id)

route = get_route(agency_id, bus_line)
# route = {'agency_id': 347,
#  'color': 'ef83f2',
#  'description': '',
#  'is_active': True,
#  'is_hidden': False,
#  'long_name': 'Northline',
#  'route_id': '4003286',
#  'segments': [['540416931', 'forward'],
#               ['549906078', 'backward'],
#               ['581170961', 'backward'],
#               ['603002991', 'forward'],
#               ['606885185', 'forward'],
#               ['620186348', 'forward'],
#               ['623754453', 'forward'],
#               ['624430590', 'forward'],
#               ['626981847', 'backward'],
#               ['628961367', 'backward'],
#               ['644727345', 'forward'],
#               ['647516646', 'forward'],
#               ['650597156', 'forward'],
#               ['679296756', 'forward'],
#               ['685478620', 'forward'],
#               ['720756167', 'backward'],
#               ['732168762', 'forward'],
#               ['734413457', 'forward'],
#               ['767465664', 'forward'],
#               ['787155905', 'backward'],
#               ['789247268', 'forward']],
#  'short_name': '',
#  'stops': ['4123890',
#            '4123882',
#            '4123886',
#            '4123994',
#            '4178522',
#            '4229092',
#            '4178524',
#            '4209050',
#            '4209054',
#            '4209058',
#            '4148110',
#            '4137602',
#            '4209066',
#            '4123970',
#            '4123962',
#            '4221190',
#            '4123774',
#            '4123770',
#            '4123978',
#            '4123966',
#            '4124058',
#            '4123982',
#            '4123826',
#            '4123842',
#            '4209056',
#            '4209060',
#            '4209052',
#            '4123990',
#            '4123758',
#            '4123754',
#            '4124042'],
#  'text_color': 'FFFFFF',
#  'type': 'bus',
#  'url': ''}
print("Route:", route['long_name'])

nearest_stop = get_nearest_stop(agency_id, geo_area)
# nearest_stop = {'code': '040', 'description': '', 'url': '', 'parent_station_id': None, 'agency_ids': ['347'], 'station_id': None, 'location_type': 'stop', 'location': {'lat': 38.029349, 'lng': -78.519545}, 'stop_id': '4123890', 'routes': ['4003286', '4011564'], 'name': 'Hereford Dr @ Runk Dining Hall'}
print("Nearest stop:", nearest_stop['name'])

estimates = get_arrival_estimates(agency_id, routes=[route['route_id']], stops=[nearest_stop['stop_id']])
# estimates = [{'arrival_at': '2019-03-23T01:08:16-04:00',
#                 'route_id': '4003286',
#                 'type': 'vehicle-based',
#                 'vehicle_id': '4014853'},
#                {'arrival_at': '2019-03-23T01:33:48-04:00',
#                 'route_id': '4003286',
#                 'type': 'vehicle-based',
#                 'vehicle_id': '4016897'},
#                {'arrival_at': '2019-03-23T01:52:20-04:00',
#                 'route_id': '4003286',
#                 'type': 'vehicle-based',
#                 'vehicle_id': '4014853'}]
arrival_times = get_arrival_time_estimates(estimates)
print("Arrival estimates:")
pprint([int(time.total_seconds()/60) for time in arrival_times])