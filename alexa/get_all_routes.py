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

alexa_all_routes = []
google_all_routes = []

for agency_id, routes in response.json()['data'].items():
    for route in routes:
        alexa_name = {
            "name": {
                "value": route["long_name"],
            }
        }

        if route["short_name"] != "" :
            alexa_name["name"]["synonyms"] = [ route["short_name"] ]

        google_name = {
            "value": route["long_name"],
        }

        if route["short_name"] != "" :
            google_name["synonyms"] = [ route["short_name"] ]

        alexa_all_routes.append(alexa_name)
        google_all_routes.append(google_name)

alexa_file_path = 'BusBuddy/models/en-US.json'
google_file_path = '../BusLine.json'

# write out Alexa json
data = json.load(open(alexa_file_path, 'r'))
for i in range(len(data['interactionModel']['languageModel']['types'])):
    if data['interactionModel']['languageModel']['types'][i]['name'] == "BusLine":
        data['interactionModel']['languageModel']['types'][i]['values'] = alexa_all_routes
with open(alexa_file_path, 'w') as outfile:
    json.dump(data, outfile)

# write out Google json
data = json.load(open(google_file_path, 'r'))
if data['name'] == "BusLine":
    data['entries'] = google_all_routes

    with open(google_file_path, 'w') as outfile:
        json.dump(data, outfile)
else:
    print("You've got the wrong Google json file")
