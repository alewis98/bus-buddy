import requests
import json
from pprint import pprint

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

payload = [ ('format',   'json') ]
response = requests.get(api_url + AGENCIES, headers=headers, params=payload)
agency_ids = [x['agency_id'] for x in response.json()['data']]

payload = (('format',   'json'), ('agencies', ",".join(agency_ids)))
response = requests.get(api_url + ROUTES, headers=headers, params=payload)

all_routes = []

for agency_id, routes in response.json()['data'].items():
    for route in routes:
        name = {
            "name": {
                "value": route["long_name"],
            }
        }

        if route["short_name"] != "" :
            name["name"]["synonyms"] = [ route["short_name"] ]

        all_routes.append(name)

file_path = 'BusBuddy/models/en-US.json'
data = json.load(open(file_path, 'r'))

for i in range(len(data['interactionModel']['languageModel']['types'])):
    if data['interactionModel']['languageModel']['types'][i]['name'] == "BusLine":
        data['interactionModel']['languageModel']['types'][i]['values'] = all_routes

with open(file_path, 'w') as outfile:
    json.dump(data, outfile)
