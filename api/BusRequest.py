class BusRequest:
    
    def __init__(self, latitude=None, longitude=None, radius=None, agency=None, route=None, stop=None, vehicle=None):
        self.latitude = latitude
        self.longitude = longitude
        self.radius = radius
        self.agency = agency
        self.route = route
        self.vehicle = vehicle
        
        if stop:
            # TODO get stop id from string location
            pass
        self.stop = stop




