import math
import json
import requests
from pprint import pprint
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


def build_geo_area(latitude, longitude, radius=1000):
    # latitude, longitude|radius (meters)
    return str(latitude) + "," + str(longitude) + "|" + str(radius)


# coordinates for Whyburn: 38.0294814,-78.5193463|1000
latitude = 38.0294814
longitude = -78.5193463
radius = 1000

use_cached_requests = True


def find_by_key(key_id, field, entities):
    # pprint(entities)
    for entity in entities:
        if entity[field] == key_id:
            return entity
    print("couldn't find", key_id)


def get_agency(geo_area=None, agencies=None):
    payload = [ ('format',   'json'), \
                ('agencies', agencies) if agencies else None, \
                ('geo_area', geo_area) if geo_area else None \
                ]
    payload = [x for x in payload if x is not None]

    response = requests.get(api_url + AGENCIES, headers=headers, params=payload)

    if len(response.json()['data']) == 0:
        print("NO AGENCY FOUND")
        exit()

    agency = response.json()['data'][0]  # assume this is the right one
    return agency


def get_route(agency_id, route_name, geo_area=None):
    payload = [ ('format',   'json'), \
                ('agencies', agency_id),
                \
                ('geo_area', geo_area) if geo_area else None \
                ]
    payload = [x for x in payload if x is not None]

    response = requests.get(api_url + ROUTES, headers=headers, params=payload)
    routes = response.json()['data'][agency_id]

    return find_by_key(route_name, 'long_name', routes)


def distance_between(lat_1, lon_1, lat_2, lon_2):
    '''Uses the "great circle distance" formula and the circumference of the earth
    to convert two GPS coordinates to the miles separating them'''
    lat_1, lon_1 = math.radians(lat_1), math.radians(lon_1)
    lat_2, lon_2 = math.radians(lat_2), math.radians(lon_2)
    theta = lon_1 - lon_2
    dist = math.sin(lat_1)*math.sin(lat_2) + math.cos(lat_1)*math.cos(lat_2)*math.cos(theta)
    dist = math.acos(dist)
    dist = math.degrees(dist)
    dist = dist * 69.06         # 69.09 = circumference of earth in miles / 360 degrees

    return dist


def get_stops(agency_id, geo_area=None):
    payload = [ ('format',   'json'), \
                ('agencies', agency_id), \
                ('geo_area', geo_area) if geo_area else None \
                ]
    payload = [x for x in payload if x is not None]

    response = requests.get(api_url + STOPS, headers=headers, params=payload)
    return response.json()['data']


def sort_stops(agency_id, stops=None, geo_area=None):
    if not stops:
        stops = get_stops(agency_id, geo_area)

    closest_stop = sorted(stops, key=lambda x: distance_between(x['location']['lat'], x['location']['lng'], latitude, longitude))
    return closest_stop


def get_vehicles(agency_id, routes=None, geo_area=None):
    payload = [ ('format',   'json'), \
                ('agencies', agency_id), \
                ('geo_area', geo_area) if geo_area else None, \
                ('routes', ",".join(routes)) if routes else None \
                ]
    payload = [x for x in payload if x is not None]

    response = requests.get(api_url + VEHICLES, headers=headers, params=payload)
    vehicles = response.json()['data'][agency_id]

    print("There are", len(vehicles), "vehicles")
    return vehicles


def get_vehicle_current_stop(vehicle):
    return vehicle['arrival_estimates'][0]


def get_arrival_estimates(agency_id, routes=None, stops=None):
    payload = [ ('format',   'json'), \
                ('agencies', agency_id), \
                ('routes', ",".join(routes)) if routes else None, \
                ('stops', ",".join(stops)) if stops else None \
                ]
    payload = [x for x in payload if x is not None]

    response = requests.get(api_url + ARRIVAL_ESTIMATES, headers=headers, params=payload)
    return response.json()['data']


def get_arrivals_for_stop(agency_id, stop_id, routes=None):
    arrivals = get_arrival_estimates(agency_id, routes=routes, stops=[stop_id])
    return find_by_key(stop_id, "stop_id", arrivals)['arrivals']


def get_arrival_time_estimates(arrivals):
    now = datetime.now()
    return sorted([dateutil.parser.parse(arrival['arrival_at']).replace(tzinfo=None) - now for arrival in arrivals])


def get_where_is_next_bus(agency_id, route_id, vehicle_id, stops=None, geo_area=None):
    if not stops:
        stops = sort_stops(agency_id, geo_area=geo_area)

    vehicles = get_vehicles(agency_id, routes=[route_id])
    your_bus = find_by_key(vehicle_id, "vehicle_id", vehicles)

    current_stop = get_vehicle_current_stop(your_bus)
    return find_by_key(current_stop['stop_id'], 'stop_id', stops)


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


def convert_address_to_coordinates(address):
    api_key = "AIzaSyDWCnuBAOcZHyNDzRTa6JC9PtDRnML6UQI"
    address_string = " ".join([address['addressLine1'], \
                               address['city'], address['stateOrRegion'], \
                               address['postalCode'], address['countryCode']])
    response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + address_string + "&key=" + api_key)
    return response.json()['results'][0]['geometry']['location']


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
        nearest_stop = sort_stops(agency_id, geo_area=geo_area)[0]
        estimates = get_arrivals_for_stop(agency_id, stop_id=nearest_stop['stop_id'], routes=[route['route_id']])
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
<<<<<<< HEAD:basic_request.py
            nearest_stop = sort_stops(agency_id, geo_area=geo_area)[0]
            estimates = get_arrivals_for_stop(agency_id, routes=matched_route['route_id'], stops=[nearest_stop['stop_id']])
=======
            nearest_stop = get_nearest_stop(agency_id, geo_area)
            print("Nearest stop:", nearest_stop)
            estimates = get_arrival_estimates(agency_id, routes=[matched_route['route_id']], stops=[nearest_stop['stop_id']])
            print("Esimates:", estimates)
>>>>>>> 3838908db83e6679da41fe2fe508c7d76771606d:alexa-serverless/handler.py
            arrival_times = get_arrival_time_estimates(estimates)
            text = get_arrival_text(arrival_times)
        else:
            text = "No bus found"
    else:
        raise ValueError("Invalid intent")
    return build_response_alexa(text)


def build_response_google(text):
    return {'fulfillmentText': text}


def when_is_bus_coming(intent_request):
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
    matched_route = route if route and route['agency_id'] == int(agency_id) else None
    print("Matched route:", matched_route.get('route_id'))
    if matched_route:
        nearest_stop = sort_stops(agency_id, geo_area=geo_area)[0]
        print("Nearest stop:", nearest_stop.get('stop_id'))
        estimates = get_arrivals_for_stop(agency_id, stop_id=nearest_stop['stop_id'], routes=[matched_route['route_id']])
        print("Esimates:", estimates)
        arrival_times = get_arrival_time_estimates(estimates)
        text = get_arrival_text(arrival_times)
    else:
        text = "Couldn't find any buses running that route right now"

    return text


def where_is_next_bus(intent_request):
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
    matched_route = route if route and route['agency_id'] == int(agency_id) else None
    print("Matched route:", matched_route.get('route_id'))
    if matched_route:
        stops = sort_stops(agency_id, geo_area=geo_area)
        nearest_stop = stops[0]
        estimates = get_arrivals_for_stop(agency_id, stop_id=nearest_stop['stop_id'], routes=[matched_route['route_id']])
        your_bus = estimates[0]['vehicle_id']
        print("YOUR BUS:", your_bus)
        current_stop = get_where_is_next_bus(agency_id, route['route_id'], your_bus, stops=stops)
        text = "The next bus is currently at " + current_stop.get('name')
    else:
        text = "Couldn't find any buses running that route right now"

    return text


def on_intent_google(intent_request):
    intent = intent_request["queryResult"]["intent"]

    params = intent_request.get('queryResult').get('parameters')
    request_type = params['request_type'].lower()

    if intent['displayName'] == "GetNextBus":
        if request_type == "when":
            text = when_is_bus_coming(intent_request)
        elif request_type == "where":
            text = where_is_next_bus(intent_request)
        else:
            raise ValueError("Invalid request")
    else:
        raise ValueError("Invalid intent")
    return build_response_google(text)


<<<<<<< HEAD:basic_request.py
def lambda_handler(event):
=======
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
>>>>>>> 3838908db83e6679da41fe2fe508c7d76771606d:alexa-serverless/handler.py
    if event["request"]["type"] == "IntentRequest":
        return on_intent_alexa(event["request"], event["session"])
    elif event["request"]["type"] == "LaunchRequest":
        return on_launch_alexa(event["request"], event["session"])
    else:
        return build_response_alexa("I think an error occurred")


def results(request):
    # request_json = request.get_json() # TODO CHANGE THIS BACK
    request_json = request
    params = request_json.get('queryResult').get('parameters')
    request_type = params['request_type'].lower()
    return on_intent_google(request_json)


def handler(request):
    # return response
    return json.dumps(results(request))

print(handler({
  "responseId": "9d2ade87-8ae9-46e7-94df-55d7f7134670",
  "queryResult": {
    "queryText": "when is the next northline",
    "parameters": {
      "bus_line": "Northline",
      "request_type": "where"
    },
    "allRequiredParamsPresent": True,
    "fulfillmentText": "The Northline is on its way",
    "fulfillmentMessages": [
      {
        "text": {
          "text": [
            "The Northline is on its way"
          ]
        }
      }
    ],
    "intent": {
      "name": "projects/busbuddy-64e11/agent/intents/d6f859df-fae2-4c6c-aba6-e2ffdc637fc2",
      "displayName": "GetNextBus"
    },
    "intentDetectionConfidence": 1,
    "languageCode": "en"
  },
  "originalDetectIntentRequest": {
    "payload": {}
  },
  "session": "projects/busbuddy-64e11/agent/sessions/53f2ad62-d27f-3a50-f7b1-4b8c9b358028"
}))