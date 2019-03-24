import math
import json
import requests
from pprint import pprint
from datetime import datetime
import dateutil.parser
from beautifultable import BeautifulTable

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


def get_routes(agency_id):
	payload = [ ('format',   'json'), ('agencies', agency_id)]
	payload = [x for x in payload if x is not None]
	response = requests.get(api_url + ROUTES, headers=headers, params=payload)
	return response.json()['data'].get(agency_id)


payload = [ ('format', 'json') ]
response = requests.get(api_url + AGENCIES, headers=headers, params=payload)
data = response.json()['data']

routes = []
for d in data:
	if d:
		r = get_routes(d.get('agency_id'))
		if r:
			routes += r

active_routes = [route for route in routes if route.get('is_active')]
active_agency_ids = set([ar['agency_id'] for ar in active_routes])

table = BeautifulTable()
table.column_headers = ["id", "name", "location"]
for d in data:
    if d['agency_id'] in str(active_agency_ids):
        table.append_row([d.get('agency_id'), d.get('long_name'), d.get('position')])

print(table)

while True:
    print(table)
    print('Type "exit" to exit')
    agency = input("Input ID to see routes: ")
    if agency != 'exit':
        routes = get_routes(agency)
        pprint([r['long_name'] for r in routes])
    else:
        break

