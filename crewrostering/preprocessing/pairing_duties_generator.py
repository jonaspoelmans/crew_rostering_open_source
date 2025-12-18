import pandas as pd


class PairingDutiesGenerator:
    def __init__(self, flights_for_aircraft_df, max_flight_duty_period_hours):
        # Duty hours buffer constant
        self.duty_buffer_hours = 1.5

        # Daily duty hours constraint
        self.max_flight_duty_period_hours = max_flight_duty_period_hours

        # Flight input data for generating pairings
        self.flights_for_aircraft_df = flights_for_aircraft_df

        # Supporting data structures containing pairings, paired and unpaired flight ids
        self.pairings = []
        self.paired_flight_ids = []
        self.unpaired_flight_ids = []

        # Output: generated pairing duties
        columns = [
            "duty_id",
            "outbound_flight_id",
            "inbound_flight_id",
            "outbound_departure_icao",
            "outbound_arrival_icao",
            "inbound_departure_icao",
            "inbound_arrival_icao",
            "aircraft_type",
            "aircraft_registration",
            "flight_time_hours",
            "duty_time_hours",
            "scheduled_departure_utc",
            "scheduled_arrival_utc",
            'sector_count',
            'captains_required',
            'first_officers_required',
            'cabin_crew_required'
        ]

        self.pairing_duties_df = pd.DataFrame([], columns=columns)

    def generate_pairings(self):
        # Step 1: make all pairings where possible
        self.find_return_flights(self.flights_for_aircraft_df)

        # Step 2: find unpaired flights and filter to only unpaired flights
        self.find_unpaired_flights()
        unpaired_flights_df = self.flights_for_aircraft_df[
            self.flights_for_aircraft_df['flight_id'].isin(self.paired_flight_ids) == False
        ]

        # Call the pairing method without aircraft requirement
        self.find_return_flights(unpaired_flights_df, require_same_aircraft=False)

        # Update the list of unpaired flights
        self.find_unpaired_flights()

        # Step 3: generate duties for all pairings
        self.generate_duties_for_pairings()
        self.generate_duties_for_unpaired_flights()

    def print_assignments_to_csv(self):
        self.pairing_duties_df.to_csv('../assets/output/pairings_output.csv', index=False)

    def generate_duties_for_pairings(self):
        for outbound_flight_id, inbound_flight_id in self.pairings:
            outbound_flight = self.flights_for_aircraft_df[self.flights_for_aircraft_df['flight_id'] == outbound_flight_id].iloc[0]
            inbound_flight = self.flights_for_aircraft_df[self.flights_for_aircraft_df['flight_id'] == inbound_flight_id].iloc[0]

            # Compute the delta in hours between departure and arrival
            flight_time_hours = outbound_flight["flight_time_hours"] + inbound_flight["flight_time_hours"]
            duty_time_hours = round(self.duty_buffer_hours + (inbound_flight["scheduled_arrival_utc"] - outbound_flight["scheduled_departure_utc"]).total_seconds() / 3600, 2)

            new_row = pd.DataFrame([{
                "duty_id": len(self.pairing_duties_df),
                "outbound_flight_id": outbound_flight_id,
                "inbound_flight_id": inbound_flight_id,
                "outbound_departure_icao": outbound_flight['departure_icao'],
                "outbound_arrival_icao": outbound_flight['arrival_icao'],
                "inbound_departure_icao": inbound_flight['departure_icao'],
                "inbound_arrival_icao": inbound_flight['arrival_icao'],
                "aircraft_type": outbound_flight['aircraft_type'],
                "aircraft_registration": outbound_flight['aircraft_registration'],
                "flight_time_hours": flight_time_hours,
                "duty_time_hours": duty_time_hours,
                "scheduled_departure_utc": outbound_flight["scheduled_departure_utc"],
                "scheduled_outbound_arrival_utc": outbound_flight["scheduled_arrival_utc"],
                "scheduled_inbound_departure_utc": outbound_flight["scheduled_departure_utc"],
                "scheduled_arrival_utc": inbound_flight["scheduled_arrival_utc"],
                'sector_count': 2,
                'captains_required': inbound_flight["captains_required"],
                'first_officers_required': inbound_flight["first_officers_required"],
                'cabin_crew_required': inbound_flight["cabin_crew_required"]
            }])

            self.pairing_duties_df = pd.concat([self.pairing_duties_df, new_row], ignore_index=True)

    def generate_duties_for_unpaired_flights(self):
        for flight_id in self.unpaired_flight_ids:
            flight = self.flights_for_aircraft_df[self.flights_for_aircraft_df['flight_id'] == flight_id].iloc[0]

            # Compute the delta in hours between departure and arrival
            flight_time_hours = flight["flight_time_hours"]
            duty_time_hours = self.duty_buffer_hours + flight["flight_time_hours"]

            new_row = pd.DataFrame([{
                "duty_id": len(self.pairing_duties_df),
                "outbound_flight_id": flight_id,
                "inbound_flight_id": None,
                "outbound_departure_icao": flight['departure_icao'],
                "outbound_arrival_icao": flight['arrival_icao'],
                "inbound_departure_icao": flight['departure_icao'],
                "inbound_arrival_icao": flight['arrival_icao'],
                "aircraft_type": flight['aircraft_type'],
                "aircraft_registration": flight['aircraft_registration'],
                "flight_time_hours": flight_time_hours,
                "duty_time_hours": duty_time_hours,
                "scheduled_departure_utc": flight['scheduled_departure_utc'],
                "scheduled_arrival_utc": flight['scheduled_arrival_utc'],
                'sector_count': 1,
                'captains_required': flight["captains_required"],
                'first_officers_required': flight["first_officers_required"],
                'cabin_crew_required': flight["cabin_crew_required"]
            }])

            self.pairing_duties_df = pd.concat([self.pairing_duties_df, new_row], ignore_index=True)

    def find_return_flights(self, flights_df, require_same_aircraft=True):
        """
        Find flights that are return legs.
        Returns: List of (outbound_flight_id, inbound_flight_id)
        """
        max_turnaround_hours = 4  # Maximum time between landing and return departure

        for index, outbound_flight in flights_df.iterrows():
            # Only consider flights that start from home base (LUX)
            if outbound_flight['departure_icao'] != 'ELLX':
                continue

            # Calculate the latest possible departure time for return flight
            max_scheduled_departure_utc = outbound_flight['scheduled_arrival_utc'] + pd.Timedelta(hours=max_turnaround_hours)

            # Find return flights that:
            return_flights = flights_df[
                # Start from where the outbound_flight flight ended
                (flights_df['departure_icao'] == outbound_flight['arrival_icao']) &

                # Go back to where the outbound_flight flight started
                (flights_df['arrival_icao'] == outbound_flight['departure_icao']) &

                # Depart after the outbound_flight flight arrives
                (flights_df['scheduled_departure_utc'] > outbound_flight['scheduled_arrival_utc']) &

                # Depart within the turnaround time window
                (flights_df['scheduled_departure_utc'] <= max_scheduled_departure_utc) &

                # Dont pair an already paired flight
                (flights_df['flight_id'].isin(self.paired_flight_ids) == False)
            ]

            # Only add aircraft condition if needed
            if require_same_aircraft:
                return_flights = return_flights[
                    # Use the same aircraft type
                    (return_flights['aircraft_type'] == outbound_flight['aircraft_type']) &

                    # Use the aircraft with the same registration number
                    (return_flights['aircraft_registration'] == outbound_flight['aircraft_registration'])
                ]

            if len(return_flights) > 0:
                # Take the first chronological return flight
                inbound_flight = return_flights.sort_values('scheduled_departure_utc').iloc[0]

                # Check total duty period is not exceeded for the combination nof both flights
                combined_flight_time_hours = outbound_flight["flight_time_hours"] + inbound_flight["flight_time_hours"]
                combined_duty_time_hours = self.duty_buffer_hours + combined_flight_time_hours

                # Save paired flight ids to array
                if combined_duty_time_hours < self.max_flight_duty_period_hours:
                    self.pairings.append((outbound_flight['flight_id'], inbound_flight['flight_id']))
                    self.paired_flight_ids.append(outbound_flight['flight_id'])
                    self.paired_flight_ids.append(inbound_flight['flight_id'])

    def find_unpaired_flights(self):
        self.unpaired_flight_ids.clear()

        for index, flight in self.flights_for_aircraft_df.iterrows():
            if flight['flight_id'] not in self.paired_flight_ids:
                self.unpaired_flight_ids.append(flight['flight_id'])
