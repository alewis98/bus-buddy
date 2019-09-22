import requests
import math
from datetime import datetime
import dateutil.parser

# request types
AGENCIES = "agencies"
ARRIVAL_ESTIMATES = "arrival-estimates"
ROUTES = "routes"
SEGMENTS = "segments"
VEHICLES = "vehicles"
STOPS = "stops"


def build_geo_area(latitude, longitude, radius=10000):
    # latitude,longitude|radius (meters)
    return str(latitude) + "," + str(longitude) + "|" + str(radius)


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


def make_request(request_type, latitude=None, longitude=None, radius=10000, agency_ids=None, route_id=None, stop_id=None):
    payload = [('format',   'json'),
               ('agencies', ",".join([str(id) for id in agency_ids])) if agency_ids else None,
               ('geo_area', build_geo_area(latitude, longitude, radius)) if latitude and longitude else None,
               ('routes', str(route_id)) if route_id else None,
               ('stops', str(stop_id)) if stop_id else None
               ]
    payload = [x for x in payload if x is not None]

    # TODO throw this in a config file
    api_url = "https://transloc-api-1-2.p.rapidapi.com/"
    headers = {
      "X-RapidAPI-Key": "49e8d6f922msh58d18d370a3dc27p12e16djsn3eb2f5483f33"
    }

    response = requests.get(api_url + request_type,
                            headers=headers,
                            params=payload)

    # TODO handle radius too small
    # TODO handle timeouts
    if not response.ok:
        print("Request errored with status code", response.status_code)
        print("Reason:", response.reason)
        raise Exception("Request response was not OK")

    return response


def get_arrival_time_estimates(arrivals):
    if type(arrivals) is not list:
        arrivals = [arrivals]
    now = datetime.now()
    return sorted([dateutil.parser.parse(arrival['arrival_at']).replace(tzinfo=None) - now for arrival in arrivals])


def get_vehicle_current_stop(vehicle):
    if len(vehicle['arrival_estimates']) > 0:
        return vehicle['arrival_estimates'][0]
    else:
        return None


def get_route(route_name, agency_ids):
    response = make_request(ROUTES, agency_ids=agency_ids)

    bus_routes_by_agency = response.json().get('data')

    route = None
    for routes in bus_routes_by_agency.values():
        route = find_by_key(route_name, 'long_name', routes)
        if route:
            break

    if not route:
        raise Exception("Couldn't find route", route_name, "in agencies", agency_ids)

    return route


def get_agency_ids(latitude, longitude):
    response = make_request(AGENCIES, latitude=latitude, longitude=longitude)
    agencies = response.json().get('data')
    agency_ids = [int(agency.get('agency_id')) for agency in agencies]
    return agency_ids


def get_nearest_stop(latitude, longitude, route_name=None):
    agency_ids = get_agency_ids(latitude, longitude)
    if len(agency_ids) == 0:
        return None  # TODO return json with appropriate error message

    route_id = None
    if route_name:
        route = get_route(route_name, agency_ids)
        route_id = route.get('route_id')

    response = make_request(STOPS, agency_ids=agency_ids, latitude=latitude, longitude=longitude)

    stops = response.json().get('data')

    sorted_stops = sorted(stops, key=lambda x: math.hypot(float(x['location']['lat']) - latitude, float(x['location']['lng']) - longitude))

    closest_stop = None
    if route_id is None and len(sorted_stops) > 0:
        closest_stop = sorted_stops[0]
    else:
        for stop in sorted_stops:
            if str(route_id) in stop.get('routes'):
                closest_stop = stop
                break

    if not closest_stop:
        raise Exception("Couldn't find nearby stop" + ("on route " + str(route_id) if route_id else ""))

    return {
        'closest_stop': closest_stop,
    }


def get_next_bus(latitude, longitude, route_name=None):
    agency_ids = get_agency_ids(latitude, longitude)
    route = get_route(route_name, agency_ids)
    route_id = route.get('route_id')
    nearest_stop = get_nearest_stop(latitude, longitude, route_name)

    response = make_request(VEHICLES, agency_ids=agency_ids, route_id=route_id)
    vehicles_by_agency_id = response.json().get('data')

    closest_bus_stops_away = 100  # this is very arbitrary
    closest_bus = None
    for vehicles in vehicles_by_agency_id.values():
        for vehicle in vehicles:
            print("VEHICLE:", vehicle.get('vehicle_id'))
            arrival_estimates = vehicle.get("arrival_estimates")
            for i, estimate in enumerate(arrival_estimates):
                if estimate.get("stop_id") == nearest_stop.get("stop_id"):
                    if i < closest_bus_stops_away:
                        closest_bus_stops_away = i
                        print("closest_bus_stops_away", closest_bus_stops_away)
                        closest_bus = vehicle
                    break

    if closest_bus is None:
        return None

    arrival = find_by_key(nearest_stop.get('stop_id'), 'stop_id', closest_bus.get("arrival_estimates"))

    arrival_time = get_arrival_time_estimates(arrival)[0]

    vehicle_current_stop = get_vehicle_current_stop(closest_bus)

    # TODO use database mapping to get stop from stop_id
    response = make_request(STOPS, agency_ids=agency_ids, latitude=latitude, longitude=longitude, route_id=route_id)
    stops = response.json().get('data')
    current_stop = find_by_key(vehicle_current_stop.get('stop_id'), 'stop_id', stops)

    return {
        'arrival_estimate': arrival_time,
        'closest_bus': closest_bus,
        'current_stop': current_stop
    }


# print(get_nearest_stop(38.029421, -78.519554, 4013078))
# print(get_nearest_stop(38.029162, -78.516443))
