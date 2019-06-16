from flask import Flask, jsonify, request
from api import BusRequest

app = Flask(__name__)

api_url = "https://transloc-api-1-2.p.rapidapi.com/"
headers = {
    "X-RapidAPI-Key": "49e8d6f922msh58d18d370a3dc27p12e16djsn3eb2f5483f33"
}





@app.route('/')
def index():
    return jsonify("Welcome to Bus Buddy")


@app.route('/agency/', methods=['GET'])
def get_agency():
    return jsonify("Agency Got.")


@app.route('/route/', methods=['GET'])
def get_route():
    return jsonify("Route Got.")


@app.route('/next_bus/', methods=['GET'])
def get_next_bus():
    stop = request.args.get('stop')
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    radius = request.args.get('radius')
    agency = request.args.get('agency')
    route = request.args.get('route')
    stop = request.args.get('stop')
    vehicle = request.args.get('vehicle')
    br = BusRequest(stop, latitude, longitude, radius, agency, route, stop, vehicle)



