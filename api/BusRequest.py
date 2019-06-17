import requests

# request types
AGENCIES = "agencies"
ARRIVAL_ESTIMATES = "arrival-estimates"
ROUTES = "routes"
SEGMENTS = "segments"
VEHICLES = "vehicles"
STOPS = "stops"


def find_by_key(key, value, dict_list):
    if not dict_list or len(dict_list) == 0:
        print("find_by_key passed a None value")
        print("value:", value, "key:", key, "dict_list:", dict_list)
        return

    if not value:
        print("Trying to find with None value")
        print("value:", value, "key:", key, "dict_list:", dict_list)
        return

    for entity in dict_list:
        if entity.get(key) == value:
            return entity

    print("Couldn't find", value)
    print("value:", value, "key:", key, "dict_list:", dict_list)


class BusRequest:

    def __init__(self, latitude=None, longitude=None, radius=10000, agency_ids=None, agency_name=None, route_name=None, route_id=None, stop_name=None, stop_id=None):
        self.latitude = latitude
        self.longitude = longitude
        self.radius = radius
        self.agency_ids = agency_ids if agency_ids else []
        self.route_id = int(route_id)
        self.route_name = route_name
        self.stop_id = int(stop_id)
        self.stop_name = stop_name

        # figure out location
        # give stop_name priority over user's coordinates when determining agency_id
        # TODO if we had a database, we could use the stop_id or agency_name to look up locations
        if stop_name:
            # TODO make Google Maps API call to get coordinates
            if not self.latitude or not self.longitude:
                raise Exception("Where you at? Please include your coordinates or a stop name.")

        if len(agency_ids) == 0:
            # TODO get agency id from location

            agencies = self.make_request(AGENCIES)

            self.agency_ids = [int(agency.get('agency_id')) for agency in agencies]

            # TODO get agency_id from agency_name by looping through agencies
            if agency_name:
                # TODO handle casing
                for name in ['name', 'short_name', 'long_name']:
                    agency = find_by_key(agency_name, name, agencies)
                    if agency:
                        self.agency_ids = [int(agency.get('agency_id'))]
                        break

            if len(agency_ids) == 0:
                raise Exception("Could not find a bus agency near you")

        if route_id is None and route_name:
            # TODO get route id from agency_id and route_name
            pass

        if stop_id is None and stop_name:
            # TODO get stop id from agency_id, location, stop_name, and/or route_id
            pass

    def build_geo_area(self):
        # latitude,longitude|radius (meters)
        return str(self.latitude) + "," + str(self.longitude) + "|" + str(self.radius)

    def make_request(self, request_type):
        payload = [('format',   'json'),
                   ('agencies', ",".join(self.agency_ids)) if self.agency_ids else None,
                   ('geo_area', self.build_geo_area()) if self.latitude and self.longitude else None,
                   ('routes', str(self.route_id)) if self.route_id else None,
                   ('stops', str(self.stop_id)) if self.stop_id else None
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

        return response.json().get('data')
