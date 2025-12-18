import time

from ortools.sat.python import cp_model
import pandas as pd

class AircraftSatSolver():
    def __init__(self, aircraft_type, historical_flights_df):
        self.aircraft_type = aircraft_type

        # Flight data arrays
        self.duties_for_aircraft_df = []
        self.historical_flights_df = historical_flights_df
        self.time_off_for_aircraft_df = None

        # Dictionary to look up when each flight departs
        self.duty_dates_lookup = {}

        # Unique flight dates sorted chronologically
        self.unique_duty_dates = []

        # Dictionary to look up how many duty hours each flight takes
        self.duty_time_hours_lookup = {}

        # Dictionary to look up how many hours each flight takes
        self.flight_time_hours_lookup = {}

        # Qualified staff for aircraft type
        self.qualified_captains_df = None
        self.qualified_first_officers_df = None
        self.qualified_cabin_crew_df = None

        # Track feasible pairs
        self.feasible_captains = []
        self.feasible_first_officers = []
        self.feasible_cabin_crew = []

        # Create the CP-SAT model
        self.model = cp_model.CpModel()

        # Decision variables will be stored here
        self.x_captains_to_duties = {}
        self.x_first_officers_to_duties = {}
        self.x_cabin_crew_to_duties = {}

        self.x_captains_worked_on_dates = {}
        self.x_first_officers_worked_on_dates = {}
        self.x_cabin_crew_worked_on_dates = {}

        # Store assignments results (populated after solving)
        self.assignments = []
        self.final_assignments = None

        # Store solver status
        self.status = None

    def initialize_data(self, feasible_assignments_filter):
        """
        Initialize crew scheduler
        """
        # Flight data arrays
        self.duties_for_aircraft_df = feasible_assignments_filter.duties_for_aircraft_df
        self.time_off_for_aircraft_df = feasible_assignments_filter.time_off_df

        # Qualified staff for aircraft type
        self.qualified_captains_df = feasible_assignments_filter.qualified_captains_df
        self.qualified_first_officers_df = feasible_assignments_filter.qualified_first_officers_df
        self.qualified_cabin_crew_df = feasible_assignments_filter.qualified_cabin_crew_df

        # Feasible crew to duties assignments
        self.feasible_captains = feasible_assignments_filter.feasible_captains
        self.feasible_first_officers = feasible_assignments_filter.feasible_first_officers
        self.feasible_cabin_crew = feasible_assignments_filter.feasible_cabin_crew

        # Create a dictionary to quickly look up when each flight departs
        self.duty_dates_lookup = self.duties_for_aircraft_df.set_index('duty_id')['scheduled_departure_utc'].dt.date.to_dict()

        # Get unique dates sorted chronologically
        self.unique_duty_dates = sorted(self.duties_for_aircraft_df['scheduled_departure_utc'].dt.date.unique())

        # Create a dictionary to quickly look up how many duty hours each flight takes
        self.duty_time_hours_lookup = self.duties_for_aircraft_df.set_index('duty_id')['duty_time_hours'].to_dict()

        # Create a dictionary to quickly look up how many hours each flight takes
        self.flight_time_hours_lookup = self.duties_for_aircraft_df.set_index('duty_id')['flight_time_hours'].to_dict()

    def create_variables(self):
        """
        Create binary decision variables for feasible assignments
        x[crew_id, duty_id] = 1 if crew assigned to flight, 0 otherwise
        """

        t = time.time()

        # Pre-convert DataFrames to dictionaries for O(1) lookup
        captains_dict = self.qualified_captains_df.set_index('crew_id').to_dict('index')
        first_officers_dict = self.qualified_first_officers_df.set_index('crew_id').to_dict('index')
        cabin_crew_dict = self.qualified_cabin_crew_df.set_index('crew_id').to_dict('index')
        duties_dict = self.duties_for_aircraft_df.set_index('duty_id').to_dict('index')

        # Create variables for captain assignments
        for captain_id, duty_id in self.feasible_captains:
            captain = captains_dict[captain_id]
            duty = duties_dict[duty_id]

            if duty['aircraft_type'] in captain['qualifications'] or 'ALL' in captain['qualifications']:
                self.x_captains_to_duties[captain_id, duty_id] = self.model.NewBoolVar(f'capt_{captain_id}_f_{duty_id}')

        # Create variables for first officer assignments
        for first_officer_id, duty_id in self.feasible_first_officers:
            first_officer = first_officers_dict[first_officer_id]
            duty = duties_dict[duty_id]

            if duty['aircraft_type'] in first_officer['qualifications'] or 'ALL' in first_officer['qualifications']:
                self.x_first_officers_to_duties[first_officer_id, duty_id] = self.model.NewBoolVar(f'fo_{first_officer_id}_f_{duty_id}')

        # Create variables for cabin crew assignments
        for cabin_crew_id, duty_id in self.feasible_cabin_crew:
            cabin_crew = cabin_crew_dict[cabin_crew_id]
            duty = duties_dict[duty_id]

            if duty['aircraft_type'] in cabin_crew['qualifications'] or 'ALL' in cabin_crew['qualifications']:
                self.x_cabin_crew_to_duties[cabin_crew_id, duty_id] = self.model.NewBoolVar(f'cc_{cabin_crew_id}_f_{duty_id}')

        # Create "worked on date" variables for captains
        for captain_id in self.qualified_captains_df['crew_id'].unique():
            for date in self.unique_duty_dates:
                self.x_captains_worked_on_dates[captain_id, date] = self.model.NewBoolVar(f'worked_{captain_id}_{date}')

        # Create "worked on date" variables for first officers
        for first_officer_id in self.qualified_first_officers_df['crew_id'].unique():
            for date in self.unique_duty_dates:
                self.x_first_officers_worked_on_dates[first_officer_id, date] = self.model.NewBoolVar(f'worked_{first_officer_id}_{date}')

        # Create "worked on date" variables for cabin crew
        for cabin_crew_id in self.qualified_cabin_crew_df['crew_id'].unique():
            for date in self.unique_duty_dates:
                self.x_cabin_crew_worked_on_dates[cabin_crew_id, date] = self.model.NewBoolVar(f'worked_{cabin_crew_id}_{date}')

        print(f"Added {len(self.x_captains_to_duties) + len(self.x_first_officers_to_duties) + len(self.x_cabin_crew_to_duties) +
            len(self.x_captains_worked_on_dates) + len(self.x_first_officers_worked_on_dates) + len(self.x_cabin_crew_worked_on_dates)} "
            f"decision variables")
        print(f"Create variables: {time.time() - t:.2f}s")

    def add_objective_balance_workload(self):
        """
        Objective: indirectly balances workload by preferring solutions with fewer total assignments
        """
        total_assignments = (sum(self.x_captains_to_duties.values()) + sum(self.x_first_officers_to_duties.values()) + sum(self.x_cabin_crew_to_duties.values()))

        self.model.Minimize(total_assignments)

    def solve(self):
        """
        Solve the optimization problem
        """

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 3600
        solver.parameters.log_search_progress = True
        solver.parameters.num_search_workers = 8  # Use multiple cores

        status = solver.Solve(self.model)

        # Status mapping
        status_map = {
            cp_model.OPTIMAL: 'Optimal',
            cp_model.FEASIBLE: 'Feasible',
            cp_model.INFEASIBLE: 'Infeasible',
            cp_model.MODEL_INVALID: 'Invalid',
            cp_model.UNKNOWN: 'Unknown'
        }

        status_string = status_map.get(status, cp_model.UNKNOWN)

        # Extract solution
        all_assignments = []

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Extract captain assignments
            all_assignments.extend(
                self._extract_assignments_for_crew_type(
                    solver, self.x_captains_to_duties, self.qualified_captains_df, 'Captain'
                )
            )

            # Extract first officer assignments
            all_assignments.extend(
                self._extract_assignments_for_crew_type(
                    solver, self.x_first_officers_to_duties, self.qualified_first_officers_df, 'First Officer'
                )
            )

            # Extract cabin crew assignments
            all_assignments.extend(
                self._extract_assignments_for_crew_type(
                    solver, self.x_cabin_crew_to_duties, self.qualified_cabin_crew_df, 'Cabin Crew'
                )
            )

        assignments_dataframe = pd.DataFrame(all_assignments)

        return status_string, assignments_dataframe

    def _extract_assignments_for_crew_type(self, solver, x_crew_assignments, crew_dataframe, crew_role):
        """
        Extract assigned duties for a specific crew type from the solved model

        Args:
            solver: The solved CP-SAT solver
            x_crew_assignments: Dictionary of (crew_id, duty_id) -> BoolVar assignments
            crew_dataframe: DataFrame of crew members for this type
            crew_role: String describing the role (e.g., 'Captain', 'First Officer', 'Cabin Crew')

        Returns:
            List of assignment dictionaries
        """

        assignments = []

        for (crew_id, duty_id), assignment_variable in x_crew_assignments.items():
            if solver.Value(assignment_variable) == 1:
                crew_info = crew_dataframe[crew_dataframe['crew_id'] == crew_id].iloc[0]
                duty_info = self.duties_for_aircraft_df[self.duties_for_aircraft_df['duty_id'] == duty_id].iloc[0]

                assignments.append({
                    'crew_id': crew_id,
                    'duty_id': duty_id,
                    'crew_role': crew_role,
                    'crew_purser': crew_info['purser'],
                    'duty_scheduled_departure_utc': duty_info['scheduled_departure_utc'],
                    'duty_scheduled_outbound_arrival_utc': duty_info['scheduled_outbound_arrival_utc'],
                    'duty_scheduled_inbound_departure_utc': duty_info['scheduled_inbound_departure_utc'],
                    "duty_scheduled_arrival_utc": duty_info["scheduled_arrival_utc"],
                    'duty_aircraft_type': duty_info['aircraft_type'],
                    'duty_flight_time_hours': duty_info['flight_time_hours'],
                    'duty_time_hours': duty_info['duty_time_hours'],
                    "duty_outbound_flight_id": duty_info['outbound_flight_id'],
                    "duty_inbound_flight_id": duty_info['inbound_flight_id'],
                    "duty_outbound_departure_icao": duty_info['outbound_departure_icao'],
                    "duty_outbound_arrival_icao": duty_info['outbound_arrival_icao'],
                    "duty_inbound_departure_icao": duty_info['inbound_departure_icao'],
                    "duty_inbound_arrival_icao": duty_info['inbound_arrival_icao'],
                    "duty_aircraft_registration": duty_info['aircraft_registration'],
                    'duty_sector_count': duty_info['sector_count'],
                    'duty_captains_required': duty_info["captains_required"],
                    'duty_first_officers_required': duty_info["first_officers_required"],
                    'duty_cabin_crew_required': duty_info["cabin_crew_required"],
                    'crew_qualifications': crew_info['qualifications'],
                    'crew_seniority': crew_info['seniority']
                })

        return assignments
