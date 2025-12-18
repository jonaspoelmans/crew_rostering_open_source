import pandas as pd


class FeasibleAssignmentsFilter():
    def __init__(self,
                 aircraft_type,
                 duties_for_aircraft_df,
                 crew_df,
                 time_off_df,
                 regulations_dict):

        # Data for analysis
        self.aircraft_type = aircraft_type
        self.crew_df = crew_df
        self.time_off_df = time_off_df
        self.duties_for_aircraft_df = duties_for_aircraft_df
        self.regulations_dict = regulations_dict

        # Qualified staff
        self.qualified_captains_df = None
        self.qualified_first_officers_df = None
        self.qualified_cabin_crew_df = None
        self.qualified_crew_ids_df = None
        self.time_off_for_aircraft_df = None

        # Track feasible pairs
        self.feasible_captains = []
        self.feasible_first_officers = []
        self.feasible_cabin_crew = []

        # Regulations
        self.max_flight_time_hours_year = regulations_dict['max_flight_time_hours_year'] * 0.95
        self.max_flight_time_hours_12_months = regulations_dict['max_flight_time_hours_12_months'] * 0.95
        self.max_flight_time_hours_28_days = regulations_dict['max_flight_time_hours_28_days'] * 0.95
        self.max_duty_time_hours_28_days = regulations_dict['max_duty_time_hours_28_days'] * 0.95

    def filter_qualified_crew_members(self):
        """
        Filter crew qualified for this aircraft type
        """

        if self.aircraft_type is not None:
            self.qualified_captains_df = self.crew_df[
                (self.crew_df['role'] == 'Captain') & (
                        self.crew_df['qualifications'].str.contains(self.aircraft_type) |
                        (self.crew_df['qualifications'] == 'ALL')
                )].copy()

            self.qualified_first_officers_df = self.crew_df[
                (self.crew_df['role'] == 'First Officer') & (
                        self.crew_df['qualifications'].str.contains(self.aircraft_type) |
                        (self.crew_df['qualifications'] == 'ALL')
                )].copy()

            self.qualified_cabin_crew_df = self.crew_df[
                (self.crew_df['role'] == 'Flight Attendant') & (
                        self.crew_df['qualifications'].str.contains(self.aircraft_type) |
                        (self.crew_df['qualifications'] == 'ALL')
                )].copy()
        else:
            self.qualified_captains_df = self.crew_df[(self.crew_df['role'] == 'Captain')].copy()
            self.qualified_first_officers_df = self.crew_df[(self.crew_df['role'] == 'First Officer')].copy()
            self.qualified_cabin_crew_df = self.crew_df[(self.crew_df['role'] == 'Flight Attendant')].copy()

        # Filter time-off requests for qualified crew only
        self.qualified_crew_ids_df = pd.concat([
            self.qualified_captains_df['crew_id'],
            self.qualified_first_officers_df['crew_id'],
            self.qualified_cabin_crew_df['crew_id']
        ])

        self.time_off_for_aircraft_df = self.time_off_df[
            self.time_off_df['crew_id'].isin(self.qualified_crew_ids_df)
        ].copy()

    def filter_feasible_assignments(self):
        """
        Create variables for feasible crew-flight pairs for each role
        """

        self.feasible_captains = self.filter_feasible_for_role(self.qualified_captains_df)
        self.feasible_first_officers = self.filter_feasible_for_role(self.qualified_first_officers_df)
        self.feasible_cabin_crew = self.filter_feasible_for_role(self.qualified_cabin_crew_df)

    def filter_feasible_for_role(self, crew_df):
        """
        Filter feasible crew-duty pairs for a specific role
        """

        feasible = []

        for index, crew in crew_df.iterrows():
            crew_id = crew['crew_id']

            # Skip crew very close to yearly limit
            if crew['current_calendar_year_flight_time_hours'] >= self.max_flight_time_hours_year:
                continue

            if crew['last_11_calendar_months_flight_time_hours'] >= self.max_flight_time_hours_12_months:
                continue

            # Skip crew close to 28-day limit
            if crew['current_month_flight_time_hours'] >= self.max_flight_time_hours_28_days:
                continue

            if crew['current_month_duty_time_hours'] >= self.max_duty_time_hours_28_days:
                continue

            for index2, duty in self.duties_for_aircraft_df.iterrows():
                duty_id = duty['duty_id']

                # Check if crew has enough hours left for this duty
                if crew['current_calendar_year_flight_time_hours'] + duty['flight_time_hours'] > self.max_flight_time_hours_year:
                    continue

                if crew['last_11_calendar_months_flight_time_hours'] + duty['flight_time_hours'] > self.max_flight_time_hours_12_months:
                    continue

                if crew['current_month_flight_time_hours'] + duty['flight_time_hours'] > self.max_flight_time_hours_28_days:
                    continue

                if crew['current_month_duty_time_hours'] + duty['duty_time_hours'] > self.max_duty_time_hours_28_days:
                    continue

                # Check time-off conflicts
                if self.has_time_off_conflict(crew_id, duty):
                    continue

                feasible.append((crew_id, duty_id))

        return feasible

    def has_time_off_conflict(self, crew_id, flight):
        """
        Check if crew member has time-off request that conflicts with flight
        """

        crew_time_offs = self.time_off_for_aircraft_df[self.time_off_for_aircraft_df['crew_id'] == crew_id]

        for index, time_off in crew_time_offs.iterrows():
            if time_off['start_date'] <= flight['scheduled_departure_utc'] <= time_off['end_date']:
                return True

        return False
