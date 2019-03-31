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

def make_request(request_type, agencies=None, geo_area=None, routes=None, stops=None):
    if type(agencies) is list:
        agencies = ",".join(agencies)  # convert list of agencies into string
    if type(routes) is list:
        routes = ",".join(routes)  # convert list of stops into string
    if type(stops) is list:
        stops = ",".join(stops)  # convert list of stops into string

    payload = [('format',   'json'),
               ('agencies', agencies) if agencies else None,
               ('geo_area', geo_area) if geo_area else None,
               ('routes', routes) if routes else None,
               ('stops', stops) if stops else None
               ]
    payload = [x for x in payload if x is not None]

    api_url = "https://transloc-api-1-2.p.rapidapi.com/"
    headers = {
      "X-RapidAPI-Key": "49e8d6f922msh58d18d370a3dc27p12e16djsn3eb2f5483f33"
    }

    response = requests.get(api_url + request_type,
                            headers=headers,
                            params=payload)

    if not response.ok:
        print("Request errored with status code", response.status_code)
        print("Reason:", response.reason)

    if not response.json().get('data'):
        print("Request returned no data. Payload:", payload)
        return None

    return response.json()['data']


def build_geo_area(latitude, longitude, radius=10000):
    # latitude, longitude|radius (meters)
    return str(latitude) + "," + str(longitude) + "|" + str(radius)


def uncouple_geo_area(geo):
    return {
        "latitude": float(geo[:geo.find(",")]),
        "longitude": float(geo[geo.find(",")+1:geo.find("|")]),
        "radius": int(geo[geo.find("|")+1:])
    }


def find_by_key(key_id, field, entities):
    if not entities or len(entities) == 0:
        print("find_by_key passed a None value")
        print("key_id:", key_id, "field:", field, "entities:", entities)
        return

    if not key_id:
        print("Trying to find with None key_id")
        print("key_id:", key_id, "field:", field, "entities:", entities)
        return

    for entity in entities:
        if entity[field] == key_id:
            return entity

    print("Couldn't find", key_id)
    print("key_id:", key_id, "field:", field, "entities:", entities)


def get_bus_fullness(vehicle):
    try:
        return "This bus is likely very full. " if (vehicle['passenger_load'] / (vehicle['standing_capacity'] + vehicle['seating_capacity'])) > 0.75 else ""
    except:
        return ""


def get_route(agency_id, route_name, geo_area=None):
    routes = make_request(ROUTES, agencies=agency_id, geo_area=geo_area)
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


def get_route_stops(agency_id, route_id):
    response = make_request(STOPS, agencies=agency_id, routes=[route_id])

    stops = []
    for stop in response:
        if route_id in stop['routes']:
            stops.append(stop)
    return stops


def sort_stops(stops, location):
    if type(location) is str:
        location = uncouple_geo_area(location)
    elif type(location) is not dict:
        print("Invalid location format")
        return None

    closest_stop = sorted(stops, key=lambda x: distance_between(x['location']['lat'], x['location']['lng'], location['latitude'], location['longitude']))
    return closest_stop


def get_vehicle_current_stop(vehicle):
    if len(vehicle['arrival_estimates']) > 0:
        return vehicle['arrival_estimates'][0]
    else:
        return None


def get_arrivals_for_stop(agency_id, stop_id, routes=None):
    print("ROUTES", routes)
    print("STOP_ID", stop_id)

    arrivals = make_request(ARRIVAL_ESTIMATES, agencies=agency_id, routes=routes, stops=stop_id)
    print("ARRIVALS", arrivals)
    stop_arrivals = find_by_key(stop_id, "stop_id", arrivals)
    return stop_arrivals.get('arrivals')


def get_arrival_time_estimates(arrivals):
    now = datetime.now()
    return sorted([dateutil.parser.parse(arrival['arrival_at']).replace(tzinfo=None) - now for arrival in arrivals])


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
        text += " Another bus" + format_time(arrival_times[i]) + "."
    return text


def get_one_bus_arrival_text(arrival_time, bus_line, stop_name):
    text = "The " + bus_line + format_time(arrival_time) + " at " + stop_name + "."
    return text


def convert_address_to_coordinates(address):
    print("ADDRESS:", address)
    api_key = "AIzaSyDWCnuBAOcZHyNDzRTa6JC9PtDRnML6UQI"
    if type(address) is not dict:
        print("Invalid attempt to convert address:", address)
        return None

    try:
        address_string = "+".join([address['addressLine1'],
                                   address['city'], address['stateOrRegion'],
                                   address['postalCode'], address['countryCode']])
    except KeyError:
        address_string = "+".join(address.values())
    response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + address_string + "&key=" + api_key)
    if len(response.json()['results']) == 0:
        print("No location could be determined from this address:", address)
        return None
    else:
        return response.json()['results'][0]['geometry']['location']


def get_next_bus(intent_request, bus_lines, geo_area, where=False):
    text = ""

    if type(bus_lines) is str:
        bus_lines = [bus_lines]  # we want to loop through bus routes, not characters of a string

    agencies = make_request(AGENCIES, geo_area=geo_area)
    if not agencies:
        return "We can't find any routes near you"
    print("AGENCIES:", agencies)
    matched_route = None

    for ag in agencies:
        ag_id = ag['agency_id']
        for bus_line in bus_lines:
            routes = make_request(ROUTES, agencies=ag_id).get(ag_id)
            route = find_by_key(bus_line, 'long_name', routes)
            if not route:
                print("Couldn't find route", bus_line, "in agency", ag_id)
                continue
            matched_route = route
            route_name = matched_route['long_name']
            agency = ag
            agency_id = ag_id
            break

    if not matched_route:
        return "I couldn't find any routes by that name near you"

    print("AGENCY:", agency.get('long_name'))
    print("MATCHED ROUTE:", matched_route.get('route_id'))

    stops = make_request(STOPS, agencies=agency_id, geo_area=geo_area, routes=matched_route['route_id'])
    sorted_stops = sort_stops(stops, geo_area)

    nearest_stop = None
    for stop in sorted_stops:
        if matched_route['route_id'] in stop['routes']:
            nearest_stop = stop
            break
    if not nearest_stop:
        return "I couldn't find any stops near you for the " + bus_line

    print("Nearest stop:", nearest_stop['stop_id'])
    estimates = get_arrivals_for_stop(agency_id, stop_id=nearest_stop['stop_id'], routes=matched_route['route_id'])

    print("ESTIMATES:", estimates)
    if not estimates:
        return "There are no upcoming " + route_name + " buses near you."

    arrival_time_deltas = get_arrival_time_estimates(estimates)

    if where:
        your_bus_id = estimates[0]['vehicle_id']
        print("YOUR BUS ID:", your_bus_id)
        response = make_request(VEHICLES, agencies=agency_id, routes=matched_route['route_id'])
        vehicles = response.get(agency_id)

        your_bus = find_by_key(your_bus_id, "vehicle_id", vehicles)
        vehicle_current_stop = get_vehicle_current_stop(your_bus)
        current_stop = find_by_key(vehicle_current_stop.get('stop_id'), 'stop_id', sorted_stops)

        if not current_stop:
            return "Can't find that bus right now"
        text = "The next bus is currently at " + str(current_stop.get('name')) + ". "
        text += get_bus_fullness(your_bus)
        text += get_one_bus_arrival_text(arrival_time_deltas[0], bus_line, nearest_stop['name'])
    else:
        text = get_arrival_text(arrival_time_deltas, bus_line, nearest_stop['name'])

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


def on_intent_alexa(intent_request, session, addr):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]
    bus_lines = intent["slots"]["bus_line"]["resolutions"]["resolutionsPerAuthority"][0].get("values")
    geo_area = build_geo_area(addr["lat"], addr["lng"])

    bus_names = [bus['value']['name'] for bus in bus_lines]

    if intent_name == "GetNextBus":
        text = get_next_bus(intent_request, bus_names, geo_area=geo_area, where=False)
    elif intent_name == "WhereIsBus":
        text = get_next_bus(intent_request, bus_names, geo_area=geo_area, where=True)
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

    # coordinates for Whyburn: latitude=38.0294814, longitude=-78.5193463
    #                          geo_area='38.0294814,-78.5193463|10000'
    latitude = 38.0294814
    longitude = -78.5193463
    if "location" in params.keys():
        location = params['location']
        print("ADDRESS DETECTED:", location)

        location = convert_address_to_coordinates(location)
        print("ADDRESS RESOLVED TO:", location)
        if location:
            latitude = location['lat']
            longitude = location['lng']
        else:
            print("Could not convert address to coordinates. Using default coordinates")

    geo_area = build_geo_area(latitude, longitude)

    if intent['displayName'] == "GetNextBus":
        if request_type == "when":
            text = get_next_bus(intent_request, [params['bus_line']], geo_area=geo_area, where=False)
        elif request_type == "where":
            text = get_next_bus(intent_request, [params['bus_line']], geo_area=geo_area, where=True)
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
    if supported_interfaces.get("Geolocation") is not None:
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


def google_handler(request):
    return json.dumps(on_intent_google(request.get_json()))
