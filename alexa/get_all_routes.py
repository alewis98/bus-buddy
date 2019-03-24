import requests
import json
import wordninja
from pprint import pprint
import regex as re

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

parens = re.compile(r"\(.*\)")
slashes = re.compile(r"\/")
for agency_id, routes in response.json()['data'].items():
    for route in routes:

        # TODO other string manipulating synonym-finding logic here
        short_name = parens.sub("", route["short_name"])
        short_name = slashes.sub(" ", short_name).strip()
        long_name = parens.sub("", route["long_name"])
        long_name = slashes.sub(" ", long_name).strip()

        synonyms = [ short_name.lower() ] if short_name != "" else []
        synonyms.append(long_name.lower())
        compound = " ".join(wordninja.split(long_name.lower()))  # northline -> north line
        if compound not in synonyms:
            synonyms.append(compound)

        alexa_name = {
            "name": {
                "value": long_name,
                "synonyms": synonyms
            }
        }

        # Google needs the "name" to be included as a synonym
        synonyms.append(long_name)

        google_name = {
            "value": long_name,
            "synonyms": synonyms
        }

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
