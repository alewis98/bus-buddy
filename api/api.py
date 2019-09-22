from flask import Flask, jsonify, request

import basics

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify("Welcome to Bus Buddy")


# @app.route('/next_bus/', methods=['GET'])
# def get_next_bus():
#     stop = request.args.get('stop')
#     latitude = request.args.get('latitude')
#     longitude = request.args.get('longitude')
#     radius = request.args.get('radius')
#     agency = request.args.get('agency')
#     route = request.args.get('route')
#     vehicle = request.args.get('vehicle')
#     br = BusRequest(stop, latitude, longitude, radius, agency, route, stop, vehicle)

@app.route('/nearest_stop/', methods=['GET'])
def get_nearest_stop():
    latitude = float(request.args.get('latitude'))
    longitude = float(request.args.get('longitude'))
    # agency = request.args.get('agency')
    route_name = request.args.get('route_name')
    if latitude is None or longitude is None:
        return jsonify("INVALID REQUEST: please specify a location")

    return jsonify(basics.get_nearest_stop(latitude, longitude, route_name))


@app.route('/next_bus/', methods=['GET'])
def get_next_bus():
    latitude = float(request.args.get('latitude'))
    longitude = float(request.args.get('longitude'))
    # agency = request.args.get('agency')
    route_name = request.args.get('route_name')

    if latitude is None or longitude is None:
        return jsonify("INVALID REQUEST: please specify a location")

    return jsonify(basics.get_next_bus(latitude, longitude, route_name))
