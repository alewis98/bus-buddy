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


def build_geo_area(latitude, longitude, radius=10000):
    # latitude, longitude|radius (meters)
    return str(latitude) + "," + str(longitude) + "|" + str(radius)


# coordinates for Whyburn
# latitude = 38.0294814
# longitude = -78.5193463

# coordinates for William and Mary
latitude = 37.271674
longitude = -76.7155667


def find_by_key(key_id, field, entities):
    if not entities:
        print("find_by_key passed a None value")
        return

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
        return None

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

    for route in routes:
        print(route['long_name'])

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


def get_stops(agency_id, geo_area=None, route_id=None):
    payload = [ ('format',   'json'), \
                ('agencies', agency_id), \
                ('geo_area', geo_area) if geo_area else None \
                ]
    payload = [x for x in payload if x is not None]

    response = requests.get(api_url + STOPS, headers=headers, params=payload)
    if route_id:
        stops = []
        for stop in response.json()['data']:
            if route_id in stop['routes']:
                stops.append(stop)
        return stops
    else:
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

    print([vehicle['vehicle_id'] for vehicle in vehicles])
    print("There are", len(vehicles), "vehicles")

    return vehicles


def get_vehicle_current_stop(vehicle):
    if len(vehicle['arrival_estimates']) > 0:
        return vehicle['arrival_estimates'][0]
    else:
        return None


def get_arrival_estimates(agency_id, routes=None, stops=None):
    payload = [ ('format',   'json'), \
                ('agencies', agency_id), \
                ('routes', ",".join(routes)) if routes else None, \
                ('stops', ",".join(stops)) if stops else None \
                ]
    payload = [x for x in payload if x is not None]

    response = requests.get(api_url + ARRIVAL_ESTIMATES, headers=headers, params=payload)
    print("RESPONSE", response.json())
    return response.json()['data']


def get_arrivals_for_stop(agency_id, stop_id, routes=None):
    print("ROUTES", routes)
    print("STOP_ID", stop_id)
    arrivals = get_arrival_estimates(agency_id, routes=routes, stops=[stop_id])
    print("ARRIVALS", arrivals)
    stop_arrivals = find_by_key(stop_id, "stop_id", arrivals)
    return stop_arrivals['arrivals'] if stop_arrivals else None


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
        return " is arriving now"

    minutes = minutes % 60

    text = " arrives in "
    if hours > 0:
        text += str(hours) + str(" hours " if hours > 1 else " hour")
        if minutes > 0:
            text += "and "

    if minutes > 0:
        text += str(minutes) + str(" minutes" if minutes > 1 else " minute")
    return text


def get_arrival_text(arrival_times, bus_line, stop_name):
    if len(arrival_times) == 0:
        return "There are no buses arriving soon."
    text = "The next " + bus_line + format_time(arrival_times[0]) + " at " + stop_name + "."
    for i in range(1, len(arrival_times)):
        text += " Another bus " + format_time(arrival_times[i]) + "."
    return text


def get_one_bus_arrival_text(arrival_time, bus_line, stop_name):
    text = "The " + bus_line + format_time(arrival_time) + " at " + stop_name + "."
    return text


def convert_address_to_coordinates(address):
    api_key = "AIzaSyDWCnuBAOcZHyNDzRTa6JC9PtDRnML6UQI"
    address_string = " ".join([address['addressLine1'], \
                               address['city'], address['stateOrRegion'], \
                               address['postalCode'], address['countryCode']])
    response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + address_string + "&key=" + api_key)
    return response.json()['results'][0]['geometry']['location']


def get_bus_line_info(intent_request, agency_id="", matched_route=None, geo_area=None, where=False):
    if agency_id == "":  # this is Google
        params = intent_request["queryResult"]["parameters"]
        bus_line = params['bus_line']
        print("Bus line:", bus_line)
        geo_area = build_geo_area(latitude, longitude)
        try:
            agency = get_agency(geo_area=geo_area)
            if not agency:
                return "That route is very far from your location"

            print("AGENCY:", agency)
            agency_id = agency['agency_id']
        except:
            agency_id = '347'
        print("Agency ID:", agency_id)
        route = get_route(agency_id=agency_id, route_name=bus_line)
        matched_route = route if route and route['agency_id'] == int(agency_id) else None
    else:  # this is Alexa
        bus_line = matched_route['long_name']
    if matched_route:
        print("Matched route:", matched_route.get('route_id'))
        stops = sort_stops(agency_id, geo_area=geo_area)

        nearest_stop = None
        for stop in stops:
            if matched_route['route_id'] in stop['routes']:
                nearest_stop = stop
                break
        if not nearest_stop:
            return "I couldn't find any stops near you for the " + bus_line

        print("Nearest stop:", nearest_stop['stop_id'])
        estimates = get_arrivals_for_stop(agency_id, stop_id=nearest_stop['stop_id'], routes=[matched_route['route_id']])
        print("Esimates:", estimates)
        if not estimates or len(estimates) == 0:
            return "There are no upcoming " + matched_route['long_name'] + " buses near you."

        arrival_time_deltas = get_arrival_time_estimates(estimates)
        print("Arrival time deltas", arrival_time_deltas)

        if where:
            your_bus_id = estimates[0]['vehicle_id']
            print("YOUR BUS:", your_bus_id)
            print("MATCHED ROUTE:", matched_route)
            current_stop = get_where_is_next_bus(agency_id, matched_route['route_id'], your_bus_id, stops=stops)
            if not current_stop:
                return "Can't find that bus right now"
            text = "The next bus is currently at " + str(current_stop.get('name')) + ". "
            text += get_one_bus_arrival_text(arrival_time_deltas[0], bus_line, nearest_stop['name'])
        else:
            text = get_arrival_text(arrival_time_deltas, bus_line, nearest_stop['name'])

    else:
        text = "Couldn't find any buses running that route right now"

    return text


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


def on_intent_alexa(intent_request, session, addr=None):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]
    bus_lines = intent["slots"]["bus_line"]["resolutions"]["resolutionsPerAuthority"][0].get("values")
    if not bus_lines:
        print("No bus lines, ok to panic.")
    geo_area = build_geo_area(addr["lat"], addr["lng"])
    agency_id = get_agency(geo_area)['agency_id']
    matched_route = None
    text = ""
    for bus_line in bus_lines:
        route = get_route(agency_id=agency_id, route_name=bus_line['value']['name'])
        if route and route['agency_id'] == int(agency_id):
            matched_route = route
            break
    if intent_name == "GetNextBus":
        text = get_bus_line_info(intent_request, agency_id=agency_id, matched_route=matched_route, geo_area=geo_area, where=False)
    elif intent_name == "WhereIsBus":
        text = get_bus_line_info(intent_request, agency_id=agency_id, matched_route=matched_route, geo_area=geo_area, where=True)
    else:
        return build_response_alexa("Invalid Intent")
    return build_response_alexa(text)


def build_response_google(text):
    return {'fulfillmentText': text}


def on_intent_google(intent_request):
    intent = intent_request["queryResult"]["intent"]

    params = intent_request.get('queryResult').get('parameters')
    print("PARAMS:", params)
    request_type = params['request_type']

    if intent['displayName'] == "GetNextBus":
        if request_type == "when":
            text = get_bus_line_info(intent_request, where=False)
        elif request_type == "where":
            text = get_bus_line_info(intent_request, where=True)
        else:
            raise ValueError("Invalid request")
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
    addr = {
        "lat": None,
        "lng": None
    }
    supported_interfaces = event["context"]["System"]["device"]["supportedInterfaces"]
    user = event["context"]["System"]["user"]
    gps_permission_status = user["permissions"]["scopes"]["alexa::devices:all:geolocation:read"]["status"]
    if supported_interfaces.get("Geolocation") != None:
        if gps_permission_status == "DENIED":
            return build_permission_card_response_alexa(["alexa::devices:all:geolocation:read"])
        else:
            if event["context"].get("Geolocation"):
                geo = event["context"]["Geolocation"]
                addr["lat"] = geo["coordinate"]["latitudeInDegrees"]
                addr["lng"] = geo["coordinate"]["longitudeInDegrees"]
            else:
                return build_response_alexa("GPS info not available. Please enable location services and try again.")
    else:
        response = get_postal_addr_alexa(event)
        pprint(response)
        if response.get("code") and response["code"] == "ACCESS_DENIED":
            return build_permission_card_response_alexa(["read::alexa:device:all:address"])
        else:
            addr = convert_address_to_coordinates(response)
    if event["request"]["type"] == "IntentRequest":
        return on_intent_alexa(event["request"], event["session"], addr)
    elif event["request"]["type"] == "LaunchRequest":
        return on_launch_alexa(event["request"], event["session"])
    else:
        return build_response_alexa("I think an error occurred")


def handler(request):
    # return response
<<<<<<< HEAD
    return json.dumps(on_intent_google(request.get_json()))

print(on_intent_google({
  "responseId": "9d2ade87-8ae9-46e7-94df-55d7f7134670",
  "queryResult": {
    "queryText": "when is the next northline",
    "parameters": {
      "bus_line": "Carrboro Weaver Street",
      "request_type": "when"
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
=======
    return json.dumps(on_intent_google(request.get_json()))
>>>>>>> c9cc9473712db1bfd55a6cc59b732f04023ed686
