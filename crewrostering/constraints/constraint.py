
class Constraint():
    def __init__(self, constraints_data, solver):
        # The solver model
        self.solver = solver

        # Data for analysis
        self.duties_for_aircraft_df = constraints_data['duties_for_aircraft_df']

        # Historical flights
        self.historical_flights_df = constraints_data['historical_flights_df']

        # Dictionary to quickly look up how many duty hours each flight takes
        self.duty_time_hours_lookup = constraints_data['duty_time_hours_lookup']

        # Dictionary to quickly look up how many hours each flight takes
        self.flight_time_hours_lookup = constraints_data['flight_time_hours_lookup']

        # Dictionary to quickly look up which date each flight departs
        self.duty_dates_lookup = constraints_data['duty_dates_lookup']

        # Unique flight dates sorted chronologically
        self.unique_duty_dates = constraints_data['unique_duty_dates']

        # Decision variables will be stored here
        self.x_captains_to_duties = constraints_data['x_captains_to_duties']
        self.x_first_officers_to_duties = constraints_data['x_first_officers_to_duties']
        self.x_cabin_crew_to_duties = constraints_data['x_cabin_crew_to_duties']

        self.x_captains_worked_on_dates = constraints_data['x_captains_worked_on_dates']
        self.x_first_officers_worked_on_dates = constraints_data['x_first_officers_worked_on_dates']
        self.x_cabin_crew_worked_on_dates = constraints_data['x_cabin_crew_worked_on_dates']

        # Qualified staff
        self.qualified_captains_df = constraints_data['qualified_captains_df']
        self.qualified_first_officers_df = constraints_data['qualified_first_officers_df']
        self.qualified_cabin_crew_df = constraints_data['qualified_cabin_crew_df']

        # Output: list of constraint variables
        self.constraints_variables_list = []

    def generate_constraint_variables(self):
        pass