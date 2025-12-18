import json


class FlightFE():
    def __init__(self):
        self.flnr = None
        self.date = None
        self.journey_id = None
        self.scheduled_departure_utc = None
        self.actual_departure_utc = None
        self.scheduled_departure_local = None
        self.actual_departure_local = None
        self.actual_departure_is_estimated = None
        self.departure_ident = None
        self.departure_icao = None
        self.departure_iata = None
        self.departure_name = None
        self.departure_city = None
        self.departure_terminal = None
        self.departure_gate = None
        self.arrival_ident = None
        self.arrival_icao = None
        self.arrival_iata = None
        self.arrival_name = None
        self.arrival_city = None
        self.arrival_terminal = None
        self.scheduled_arrival_utc = None
        self.actual_arrival_utc = None
        self.scheduled_arrival_local = None
        self.actual_arrival_local = None
        self.actual_arrival_is_estimated = None
        self.status = None
        self.reg = None
        self.model = None
        self.family = None
        self.airline_iata = None
        self.airline_icao = None
        self.airline_name = None

    def load_from_json(self, data: json):
        self.flnr = data.get('flnr')
        self.date = data.get('date')
        self.departure_ident = data.get('departure_ident')
        self.arrival_ident = data.get('arrival_ident')
        self.status = data.get('status')
        self.journey_id = data.get('journey_id')

        if not 'scheduled_departure_utc' in data:
            return

        self.scheduled_departure_utc = data.get('scheduled_departure_utc')
        self.actual_departure_utc = data.get('actual_departure_utc')
        self.scheduled_departure_local = data.get('scheduled_departure_local')
        self.actual_departure_local = data.get('actual_departure_local')
        self.actual_departure_is_estimated = data.get('actual_departure_is_estimated')
        self.departure_icao = data.get('departure_icao')
        self.departure_iata = data.get('departure_iata')
        self.departure_name = data.get('departure_name')
        self.departure_city = data.get('departure_city')
        self.departure_terminal = data.get('departure_terminal')
        self.departure_gate = data.get('departure_gate')
        self.arrival_icao = data.get('arrival_icao')
        self.arrival_iata = data.get('arrival_iata')
        self.arrival_name = data.get('arrival_name')
        self.arrival_city = data.get('arrival_city')
        self.arrival_terminal = data.get('arrival_terminal')
        self.scheduled_arrival_utc = data.get('scheduled_arrival_utc')
        self.actual_arrival_utc = data.get('actual_arrival_utc')
        self.scheduled_arrival_local = data.get('scheduled_arrival_local')
        self.actual_arrival_local = data.get('actual_arrival_local')
        self.actual_arrival_is_estimated = data.get('actual_arrival_is_estimated')
        self.reg = data.get('reg')
        self.model = data.get('model')
        self.family = data.get('family')
        self.airline_iata = data.get('airline_iata')
        self.airline_icao = data.get('airline_icao')
        self.airline_name = data.get('airline_name')