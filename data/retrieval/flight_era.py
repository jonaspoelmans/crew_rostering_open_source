from time import sleep

import requests
import os
from dotenv import load_dotenv
from datetime import datetime

from data.database.database import Database
from general.flight.FlightFE import FlightFE

load_dotenv()

class FlightEra():
    def __init__(self):
        self.database = Database()

        self.flights_list_url = "https://flightera-flight-data.p.rapidapi.com/airline/flights"
        self.flight_details_url = "https://flightera-flight-data.p.rapidapi.com/flight/info"

        self.airline = "XXX" # TODO: set your airline code here, e.g. LG
        self.start_time = "2025-10-01"
        self.end_time = "2025-10-31"

        self.end_date = datetime.fromisoformat(self.end_time).date()

        self.headers = {
            "x-rapidapi-key": os.getenv("FLIGHT_ERA_API_TOKEN", ""),
            "x-rapidapi-host": "flightera-flight-data.p.rapidapi.com"
        }

        self.all_flight_recs = {}
        self.current_flight_recs = {}

    def retrieve_flights_with_details(self, time=None):
        # Step 1: Retrieve the next batch of flights and the new timestamp cursor
        next_page = self.retrieve_flights_list(time)

        # Step 2: Enrich the current batch of flights
        self.enrich_flights()

        # Step 3: Save the current batch of flights
        self.save_flights()

        # Step 4: Retrieve next batch of flights
        flight_date = datetime.fromisoformat(next_page).date()

        if next_page and flight_date <= self.end_date:
            print("Retrieving flight records from starting point timestamp: " + next_page)
            self.retrieve_flights_with_details(next_page)

    def retrieve_flights_list(self, time = None):
        # Step 1: Retrieve the 10 flights after the given start time
        querystring = {"ident": self.airline, "time": time}
        response = requests.get(self.flights_list_url, headers=self.headers, params=querystring)
        response_json = response.json()

        # Process the flights
        flights = response_json.get("flights")

        if not flights:
            return None

        # Step 2: Save all flights for further processing
        for flight in flights:
            flight_rec = FlightFE()
            flight_rec.load_from_json(flight)

            self.current_flight_recs[(flight['flnr'], flight['date'])] = flight_rec
            self.all_flight_recs[(flight['flnr'], flight['date'])] = flight_rec

        # Return the start timestamp for the next batch if available
        return response_json.get('next_time')

    def enrich_flights(self):
        for key, flight_rec in self.current_flight_recs.items():
            # Enrich the current flight record
            flight_rec_with_details = self.retrieve_flight_details(flight_rec.flnr, flight_rec.date)

            # If the flight record has been enriched
            if flight_rec_with_details:
                self.current_flight_recs[key] = flight_rec_with_details
                self.all_flight_recs[key] = flight_rec_with_details

            sleep(2)

    def retrieve_flight_details(self, flight_number = None, date = None):
        # Retrieve the flight data
        querystring = {"flnr": flight_number, "date": date}
        response = requests.get(self.flight_details_url, headers=self.headers, params=querystring)
        response_json = response.json()
        print(response_json)

        if len(response_json) == 0:
            return None

        flight = response_json[0]

        flight_rec = self.all_flight_recs[(flight['flnr'], flight['date'])]
        flight_rec.load_from_json(flight)

        return flight_rec

    def save_flights(self):
        for key, flight_rec in self.current_flight_recs.items():
            self.database.create_flight_fe_if_not_exists(flight_rec)

        self.current_flight_recs.clear()

if __name__ == "__main__":
    flightEra = FlightEra()
    flightEra.retrieve_flights_with_details(time = flightEra.start_time)