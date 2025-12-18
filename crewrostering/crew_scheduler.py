import time

import pandas as pd

from crewrostering.constraints.flight_coverage_constraint import FlightCoverageConstraint
from crewrostering.constraints.max_hours_rolling_period_constraint import MaxHoursRollingPeriodConstraint
from crewrostering.constraints.max_flight_duty_period_hours_constraint import MaxFlightDutyPeriodHoursConstraint
from crewrostering.constraints.flight_time_hours_period_constraint import FlightTimeHoursPeriodConstraint
from crewrostering.constraints.max_sectors_constraint import MaxSectorsConstraint
from crewrostering.constraints.min_weekly_rest_days_constraint import MinWeeklyRestDaysConstraint
from crewrostering.constraints.no_duties_overlap_constraint import NoDutiesOverlapConstraint
from crewrostering.preprocessing.flight_data_preprocessor import FlightDataPreprocessor
from crewrostering.solvers.aircraft_sat_solver import AircraftSatSolver
from crewrostering.preprocessing.feasible_assignments_filter import FeasibleAssignmentsFilter
from crewrostering.preprocessing.pairing_duties_generator import PairingDutiesGenerator


class CrewScheduler:
    """
    Crew Scheduling with EASA Constraints using Google OR-Tools CP-SAT
    """

    def __init__(self):
        # Data for analysis
        self.pairing_duties_df = None
        self.historical_flights_df = None
        self.crew_df = None
        self.time_off_df = None
        self.crew_requirements_df = None
        self.regulations_df = None

        self.captains_required_dict = []
        self.first_officers_required_dict = []
        self.cabin_crew_required_dict = []
        self.regulations_dict = []

        # Store assignments results (populated after solving)
        self.assignments = []
        self.final_assignments = None

    def preprocess_data(self):
        # Load scheduled flights, crew, regulations and offtime
        flight_data_preprocessor = FlightDataPreprocessor()
        flight_data_preprocessor.load_data()

        # Store processed results
        self.historical_flights_df = flight_data_preprocessor.historical_flights_df
        self.crew_df = flight_data_preprocessor.crew_df
        self.time_off_df = flight_data_preprocessor.time_off_df
        self.crew_requirements_df = flight_data_preprocessor.crew_requirements_df
        self.regulations_df = flight_data_preprocessor.regulations_df

        self.captains_required_dict = flight_data_preprocessor.captains_required_dict
        self.first_officers_required_dict = flight_data_preprocessor.first_officers_required_dict
        self.cabin_crew_required_dict = flight_data_preprocessor.cabin_crew_required_dict
        self.regulations_dict = flight_data_preprocessor.regulations_dict

        # Generate pairings
        pairing_duties_generator = PairingDutiesGenerator(flight_data_preprocessor.flights_df, self.regulations_dict['max_flight_duty_period_hours'])
        pairing_duties_generator.generate_pairings()
        pairing_duties_generator.print_assignments_to_csv()

        self.pairing_duties_df = pairing_duties_generator.pairing_duties_df

    def apply_flight_coverage_constraint(self, solver, constraints_data):
        t = time.time()
        flight_coverage_constraint = FlightCoverageConstraint(constraints_data, solver)
        flight_coverage_constraint.generate_constraint_variables()
        print(f"Apply flight coverage constraints: {time.time() - t:.2f}s")

    def apply_max_sectors_constraint(self, solver, constraints_data):
        t = time.time()
        max_sectors_constraint = MaxSectorsConstraint(constraints_data, solver,
                                                      max_sectors_day=self.regulations_dict['max_sectors_day'])
        max_sectors_constraint.generate_constraint_variables()
        print(f"Apply max sectors constraints: {time.time() - t:.2f}s")

    def apply_max_flight_time_hours_period_constraints(self, solver, constraints_data):
        t = time.time()
        max_flight_time_hours_year_constraint = FlightTimeHoursPeriodConstraint(constraints_data, solver,
                                                                                max_hours_per_period=self.regulations_dict[
                                                                            'max_flight_time_hours_year'],
                                                                                period_type='year')
        max_flight_time_hours_year_constraint.generate_constraint_variables()
        print(f"Apply max flight hours year constraints: {time.time() - t:.2f}s")

        t = time.time()
        max_flight_time_hours_12_months_constraint = FlightTimeHoursPeriodConstraint(constraints_data, solver,
                                                                                     max_hours_per_period=self.regulations_dict[
                                                                           'max_flight_time_hours_12_months'],
                                                                                     period_type='months')
        max_flight_time_hours_12_months_constraint.generate_constraint_variables()
        print(f"Apply max flight hours 12 months constraints: {time.time() - t:.2f}s")

    def apply_max_duty_and_flight_time_hours_constraints(self, solver, constraints_data):
        t = time.time()
        max_duty_time_hours_7_days_constraint = MaxHoursRollingPeriodConstraint(constraints_data, solver,
                                                                           max_duty_or_flight_time_hours_per_window=
                                                                                     self.regulations_dict[
                                                                                         'max_duty_time_hours_7_days'],
                                                                           rolling_days_window_size=7,
                                                                           duty_or_flight_mode='duty')
        max_duty_time_hours_7_days_constraint.generate_constraint_variables()
        print(f"Apply max duty hours 7 days constraints: {time.time() - t:.2f}s")

        t = time.time()
        max_duty_time_hours_28_days_constraint = MaxHoursRollingPeriodConstraint(constraints_data, solver,
                                                                            max_duty_or_flight_time_hours_per_window=
                                                                                     self.regulations_dict[
                                                                                         'max_duty_time_hours_28_days'],
                                                                            rolling_days_window_size=28,
                                                                            duty_or_flight_mode='duty')
        max_duty_time_hours_28_days_constraint.generate_constraint_variables()
        print(f"Apply max duty hours 28 days constraints: {time.time() - t:.2f}s")

        t = time.time()
        max_flight_time_hours_28_days_constraint = MaxHoursRollingPeriodConstraint(constraints_data, solver,
                                                                              max_duty_or_flight_time_hours_per_window=
                                                                                      self.regulations_dict[
                                                                                          'max_flight_time_hours_28_days'],
                                                                              rolling_days_window_size=28,
                                                                              duty_or_flight_mode='flight')
        max_flight_time_hours_28_days_constraint.generate_constraint_variables()
        print(f"Apply max flight hours 28 days constraints: {time.time() - t:.2f}s")

    def apply_flight_duty_period_hours_constraint(self, solver, constraints_data):
        t = time.time()
        flight_duty_period_hours_constraint = MaxFlightDutyPeriodHoursConstraint(constraints_data, solver,
                                                                                 max_flight_duty_period_hours=
                                                                                 self.regulations_dict[
                                                                                     'max_flight_duty_period_hours'])
        flight_duty_period_hours_constraint.generate_constraint_variables()
        print(f"Apply max flight duty period hours constraints: {time.time() - t:.2f}s")

    def apply_min_weekly_rest_days_constraint(self, solver, constraints_data):
        t = time.time()
        min_weekly_rest_days_constraint = MinWeeklyRestDaysConstraint(constraints_data, solver,
                                                                      min_weekly_rest_days=
                                                                      self.regulations_dict[
                                                                          'min_weekly_rest_days'])
        min_weekly_rest_days_constraint.generate_constraint_variables()
        print(f"Apply min weekly rest days constraints: {time.time() - t:.2f}s")

    def no_duties_overlap_constraint(self, solver, constraints_data):
        t = time.time()
        no_duties_overlap_constraint = NoDutiesOverlapConstraint(constraints_data, solver)
        no_duties_overlap_constraint.generate_constraint_variables()
        print(f"Apply min weekly rest days constraints: {time.time() - t:.2f}s")

    def package_solver_data_for_constraints(self, solver):
        data = {
            'duties_for_aircraft_df': solver.duties_for_aircraft_df,
            'historical_flights_df': solver.historical_flights_df,
            'duty_dates_lookup': solver.duty_dates_lookup,
            'unique_duty_dates': solver.unique_duty_dates,
            'duty_time_hours_lookup': solver.duty_time_hours_lookup,
            'flight_time_hours_lookup': solver.flight_time_hours_lookup,
            'x_captains_to_duties': solver.x_captains_to_duties,
            'x_first_officers_to_duties': solver.x_first_officers_to_duties,
            'x_cabin_crew_to_duties': solver.x_cabin_crew_to_duties,
            'x_captains_worked_on_dates': solver.x_captains_worked_on_dates,
            'x_first_officers_worked_on_dates': solver.x_first_officers_worked_on_dates,
            'x_cabin_crew_worked_on_dates': solver.x_cabin_crew_worked_on_dates,
            'qualified_captains_df': solver.qualified_captains_df,
            'qualified_first_officers_df': solver.qualified_first_officers_df,
            'qualified_cabin_crew_df': solver.qualified_cabin_crew_df
        }

        return data

    def solve_full(self):
        # Generate rostering on all aircraft types at once
        aircraft_type = None
        duties_for_aircraft_df = self.pairing_duties_df.copy()

        # Process the data
        self.process_aircraft(aircraft_type, duties_for_aircraft_df)

        # Store results
        self.final_assignments = pd.concat(self.assignments, ignore_index=True)
        self.print_assignments_to_csv()

    def process_aircraft(self, aircraft_type, duties_for_aircraft_df):
        # Filter qualified staff to create feasible assignments of crew members to duties
        t = time.time()
        feasible_assignments_filter = FeasibleAssignmentsFilter(aircraft_type,
                                                                duties_for_aircraft_df,
                                                                self.crew_df,
                                                                self.time_off_df,
                                                                self.regulations_dict)
        feasible_assignments_filter.filter_qualified_crew_members()
        feasible_assignments_filter.filter_feasible_assignments()
        print(f"Identify feasible crew to aircraft assignments: {time.time() - t:.2f}s")

        ## Create scheduler and solve
        solver = AircraftSatSolver(aircraft_type, self.historical_flights_df)
        solver.initialize_data(feasible_assignments_filter)

        # Add variables
        solver.create_variables()

        # Add objective
        solver.add_objective_balance_workload()

        # Add all constraints
        constraints_data = self.package_solver_data_for_constraints(solver)

        self.no_duties_overlap_constraint(solver, constraints_data)
        self.apply_flight_coverage_constraint(solver, constraints_data)
        self.apply_max_sectors_constraint(solver, constraints_data)
        self.apply_max_duty_and_flight_time_hours_constraints(solver, constraints_data)
        self.apply_max_flight_time_hours_period_constraints(solver, constraints_data)
        self.apply_flight_duty_period_hours_constraint(solver, constraints_data)
        self.apply_min_weekly_rest_days_constraint(solver, constraints_data)

        # Solve
        t = time.time()
        status, assignments = solver.solve()
        print(f"Total solver time spent: {time.time() - t:.2f}s")

        if status in ['Optimal', 'Feasible']:
            self.assignments.append(assignments)

            # Update crew hours for next iteration
            for index, assignment in assignments.iterrows():
                crew_idx = self.crew_df[self.crew_df['crew_id'] == assignment['crew_id']].index[0]

                self.crew_df.loc[crew_idx, 'current_month_flight_time_hours'] += assignment['duty_flight_time_hours']
                self.crew_df.loc[crew_idx, 'last_11_calendar_months_flight_time_hours'] += assignment['duty_flight_time_hours']
                self.crew_df.loc[crew_idx, 'current_calendar_year_flight_time_hours'] += assignment['duty_flight_time_hours']

                self.crew_df.loc[crew_idx, 'current_month_duty_time_hours'] += assignment['duty_time_hours']
        else:
            print(f"WARNING: Could not find solution for {aircraft_type}")

    def print_assignments_to_csv(self):
        self.final_assignments.to_csv('../assets/output/crew_schedule_output.csv', index=False)


if __name__ == "__main__":
    t = time.time()
    scheduler = CrewScheduler()
    scheduler.preprocess_data()
    scheduler.solve_full()
    print(f"Total time spent: {time.time() - t:.2f}s")
