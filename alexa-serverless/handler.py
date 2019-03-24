import requests
import json
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

use_cached_requests = True



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

    print("STOPS:", stops)
    print("There are", len(stops), "stops")

    closest_stop = sorted(stops, key=lambda x: hypot(x['location']['lat'] - latitude, x['location']['lng'] - longitude))[0]
    return closest_stop


def get_arrival_estimates(agency_id, routes=None, stops=None):
    payload = [ ('format',   'json'),
                ('agencies', agency_id),
                ('routes', ",".join(routes)) if routes else None,
                ('stops', ",".join(stops)) if stops else None
                ]
    payload = [x for x in payload if x is not None]

    print("Arrival Payload", payload)

    response = requests.get(api_url + ARRIVAL_ESTIMATES, headers=headers, params=payload)
    print("Arrival Response:", response)
    return response.json()['data'][0]['arrivals']


def get_arrival_time_estimates(arrivals):
    now = datetime.now()
    return sorted([dateutil.parser.parse(arrival['arrival_at']).replace(tzinfo=None) - now for arrival in arrivals])


def format_time(arrival):
    seconds = int(arrival.total_seconds())
    minutes = int(seconds // 60)
    hours   = int(minutes // 60)
    if minutes == 0:
        return "is arriving now"

    minutes = minutes % 60

    text = "arrives in "
    if hours > 0:
        text += str(hours) + " hours " if hours > 1 else " hour "
        if minutes > 0:
            text += "and "

    if minutes > 0:
        text += str(minutes) + " minutes" if minutes > 1 else " minute"
    return text


def get_arrival_text(arrival_times):
    text = "The next bus " + format_time(arrival_times[0]) + ". "
    for i in range(1, len(arrival_times)):
        text += "\nAnother bus " + format_time(arrival_times[i])
    return text


def run_test():
    bus_line = "Northline"
    geo_area = build_geo_area(latitude, longitude, radius)
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


def build_response_alexa(text):
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


def build_permission_card_response_alexa(permissions):
    response = {
        'version': '1.0',
        'response': {
            'card':{
                'type': 'AskForPermissionsConsent',
                'permissions': permissions
            }
        }
    }
    return response


def on_launch_alexa(intent_request, session):
    return build_response_alexa("Welcome to Bus Buddy")


def on_intent_alexa(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]
    if intent_name == "GetNextBus":
        values = intent["slots"]["bus_line"]["resolutions"]["resolutionsPerAuthority"][0]["values"]
        geo_area = build_geo_area(latitude, longitude, radius)
        agency_id = get_agency(geo_area)['agency_id']
        matched_route = None
        for value in values:
            route = get_route(agency_id=agency_id, route_name=value['value']['name'])
            if route and route['agency_id'] == int(agency_id):
                matched_route = route
                break
        if matched_route:
            nearest_stop = get_nearest_stop(agency_id, geo_area)
            print("Nearest stop:", nearest_stop)
            estimates = get_arrival_estimates(agency_id, routes=[matched_route['route_id']], stops=[nearest_stop['stop_id']])
            print("Esimates:", estimates)
            arrival_times = get_arrival_time_estimates(estimates)
            text = get_arrival_text(arrival_times)
        else:
            text = "No bus found"
    else:
        raise ValueError("Invalid intent")
    return build_response_alexa(text)


def build_response_google(text):
    return {'fulfillmentText': text}


def on_intent_google(intent_request):
    intent = intent_request["queryResult"]["intent"]
    if intent['displayName'] == "GetNextBus":
        params = intent_request["queryResult"]["parameters"]
        bus_line = params['bus_line']
        print("Bus line:", bus_line)
        geo_area = build_geo_area(latitude, longitude, radius)
        try:
            agency = get_agency(geo_area=geo_area)
            print("AGENCY:", agency)
            agency_id = agency['agency_id']
        except:
            agency_id = '347'
        print("Agency ID:", agency_id)
        route = get_route(agency_id=agency_id, route_name=bus_line)
        print("Route:", route)
        matched_route = route if route and route['agency_id'] == int(agency_id) else None
        print("Matched route:", matched_route)
        if matched_route:
            nearest_stop = get_nearest_stop(agency_id, geo_area)
            print("Nearest stop:", nearest_stop)
            estimates = get_arrival_estimates(agency_id, routes=[matched_route['route_id']], stops=[nearest_stop['stop_id']])
            print("Esimates:", estimates)
            arrival_times = get_arrival_time_estimates(estimates)
            text = get_arrival_text(arrival_times)
        else:
            text = "No bus found"
    else:
        raise ValueError("Invalid intent")
    return build_response_google(text)


def get_postal_addr_alexa(event):
    system = event["context"]["System"]
    user = system["user"]
    api_token = system["apiAccessToken"]
    host = system["apiEndpoint"]
    device_id = system["device"]["deviceId"]
    endpoint = "/v1/devices/" + str(device_id) + "/settings/address"
    headers = {
        "Authorization": "Bearer " + api_token
    }
    response = requests.get(host + endpoint, headers=headers)
    return response.json()
    


def lambda_handler(event, context):  
    pprint(event)
    supported_interfaces = event["context"]["System"]["device"]["supportedInterfaces"]
    user = event["context"]["System"]["user"]
    gps_permission_status = user["permissions"]["scopes"]["alexa::devices:all:geolocation:read"]["status"]
    if supported_interfaces.get("Geolocation") != None:
        if gps_permission_status == "DENIED":
            return build_permission_card_response_alexa(["alexa::devices:all:geolocation:read"])
        else:
            if event["context"].get("Geolocation"):
                geo = event["context"]["Geolocation"]
                latitude = geo["coordinate"]["latitudeInDegrees"]
                longitude = geo["coordinate"]["longitudeInDegrees"]
                return build_response_alexa("Your latitude is :" + str(latitude))
            else:
                return build_response_alexa("GPS info not available. Please enable location services and try again.")
    else:
        response = get_postal_addr_alexa(event)
        pprint(response)
        if response.get("code") and response["code"] == "ACCESS_DENIED":
            return build_permission_card_response_alexa(["read::alexa:device:all:address"])
        else:
            return build_response_alexa(response["addressLine1"])
    if event["request"]["type"] == "IntentRequest":
        return on_intent_alexa(event["request"], event["session"])
    elif event["request"]["type"] == "LaunchRequest":
        return on_launch_alexa(event["request"], event["session"])
    else:
        return build_response_alexa("I think an error occurred")


def results(request):
    request_json = request.get_json()
    params = request_json.get('queryResult').get('parameters')
    if params['request_type'] == "where":
        return {'fulfillmentText': 'WHERE YOU AT ' + params['bus_line']}
    elif params['request_type'] == "when":
        return on_intent_google(request_json)
    else:
        return build_response_google("We've lost the " + params['bus_line'])


def handler(request):
    # return response
    return json.dumps(results(request))
