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

def build_geo_area(latitude, longitude, radius):
    # latitude, longitude|radius (meters)
    return str(latitude) + "," + str(longitude) + "|" + str(radius)

# coordinates for Whyburn: 38.0294814,-78.5193463|1000
latitude = 38.0294814
longitude = -78.5193463
radius = 1000
bus_line = "Northline"
geo_area = build_geo_area(latitude, longitude, radius)

use_cached_requests = True


def get_agency(geo_area=None, agencies=None):
    print('geo:', geo_area)
    print('agencies', agencies)
    payload = [ ('format',   'json'),
                ('agencies', agencies) if agencies else None,
                ('geo_area', geo_area) if geo_area else None ]
    payload = [x for x in payload if x is not None]
    print('payload', payload)
    response = requests.get(api_url + AGENCIES, headers=headers, params=payload)
    print('response', response.json()['data'])
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
    print('routes', routes)
    route_name = route_name.lower()
    for route in routes:
        print('route', route)
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
    print('arrival estimates response', response.json()['data'])

    return response.json()['data'][0]['arrivals']


def get_arrival_time_estimates(arrivals):
    now = datetime.now()
    return sorted([dateutil.parser.parse(arrival['arrival_at']).replace(tzinfo=None) - now for arrival in arrivals])



def run_test():
    if use_cached_requests:
        agency_id = '347'
        route = {'agency_id': 347,
        'color': 'ef83f2',
        'description': '',
        'is_active': True,
        'is_hidden': False,
        'long_name': 'Northline',
        'route_id': '4003286',
        'segments': [['540416931', 'forward'],
                    ['549906078', 'backward'],
                    ['581170961', 'backward'],
                    ['603002991', 'forward'],
                    ['606885185', 'forward'],
                    ['620186348', 'forward'],
                    ['623754453', 'forward'],
                    ['624430590', 'forward'],
                    ['626981847', 'backward'],
                    ['628961367', 'backward'],
                    ['644727345', 'forward'],
                    ['647516646', 'forward'],
                    ['650597156', 'forward'],
                    ['679296756', 'forward'],
                    ['685478620', 'forward'],
                    ['720756167', 'backward'],
                    ['732168762', 'forward'],
                    ['734413457', 'forward'],
                    ['767465664', 'forward'],
                    ['787155905', 'backward'],
                    ['789247268', 'forward']],
        'short_name': '',
        'stops': ['4123890',
                '4123882',
                '4123886',
                '4123994',
                '4178522',
                '4229092',
                '4178524',
                '4209050',
                '4209054',
                '4209058',
                '4148110',
                '4137602',
                '4209066',
                '4123970',
                '4123962',
                '4221190',
                '4123774',
                '4123770',
                '4123978',
                '4123966',
                '4124058',
                '4123982',
                '4123826',
                '4123842',
                '4209056',
                '4209060',
                '4209052',
                '4123990',
                '4123758',
                '4123754',
                '4124042'],
        'text_color': 'FFFFFF',
        'type': 'bus',
        'url': ''}
        nearest_stop = {'code': '040', 'description': '', 'url': '', 'parent_station_id': None, 'agency_ids': ['347'], 'station_id': None, 'location_type': 'stop', 'location': {'lat': 38.029349, 'lng': -78.519545}, 'stop_id': '4123890', 'routes': ['4003286', '4011564'], 'name': 'Hereford Dr @ Runk Dining Hall'}
        estimates = [{'arrival_at': '2019-03-23T01:08:16-04:00',
        'route_id': '4003286',
        'type': 'vehicle-based',
        'vehicle_id': '4014853'},
        {'arrival_at': '2019-03-23T01:33:48-04:00',
        'route_id': '4003286',
        'type': 'vehicle-based',
        'vehicle_id': '4016897'},
        {'arrival_at': '2019-03-23T01:52:20-04:00',
        'route_id': '4003286',
        'type': 'vehicle-based',
        'vehicle_id': '4014853'}]
    else:
        agency = get_agency(geo_area=geo_area)
        agency_id = agency['agency_id']
        route = get_route(agency_id, bus_line)
        nearest_stop = get_nearest_stop(agency_id, geo_area)
        estimates = get_arrival_estimates(agency_id, routes=[route['route_id']], stops=[nearest_stop['stop_id']])
        arrival_times = get_arrival_time_estimates(estimates)

    print("Agency id:", agency_id)
    print("Route:", route['long_name'])
    print("Nearest stop:", nearest_stop['name'])
    print("Arrival estimates:", [int(time.total_seconds()/60) for time in arrival_times])


def build_response(text):
    response = {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': text,
            }
        }
    }
    return response


def on_launch(intent_request, session):
    return build_response("Welcome to Bus Buddy")


def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]
    if intent_name == "GetNextBus":
        values = intent["slots"]["bus_line"]["resolutions"]["resolutionsPerAuthority"][0]["values"]
        geo_area = build_geo_area(latitude, longitude, radius)
        agency_id = get_agency(geo_area)['agency_id']
        print('agency id', agency_id)
        matched_route = None
        for value in values:
            print('agency id', agency_id)
            print('value', value['value']['name'])
            route = get_route(agency_id=agency_id, route_name=value['value']['name'])
            print("Route:", route)
            if route and route['agency_id'] == int(agency_id):
                matched_route = route
                break
        if matched_route:
            nearest_stop = get_nearest_stop(agency_id, geo_area)
            print("nearest stop:", nearest_stop)
            estimates = get_arrival_estimates(agency_id, routes=[matched_route['route_id']], stops=[nearest_stop['stop_id']])
            print("Estimates:", estimates)
            arrival_times = get_arrival_time_estimates(estimates)
            text = "The next bus arrives in " + str(arrival_times[0]) + " minutes."
            for i in range(1, len(arrival_times)):
                text += "\nAnother bus will be arriving in " + str(arrival_times[i].total_seconds()//60) + " minutes."
        else:
            text = "No bus found"
    else:
        raise ValueError("Invalid intent")
    return build_response(text)


def lambda_handler(event, context):  
    pprint(event)
    if event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    else:
        return build_response("I think an error occurred")