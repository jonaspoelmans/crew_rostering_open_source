import pandas as pd
from ortools.sat.python.cp_model import LinearExpr
from crewrostering.constraints.constraint import Constraint

class NoDutiesOverlapConstraint(Constraint):
    def __init__(self, constraints_data, solver):
        super().__init__(constraints_data, solver)

        self.number_of_interval_vars = 0
        self.number_of_no_overlap_constraints = 0

    def generate_constraint_variables(self):
        """
        Use interval variables for more efficient no-overlap constraints.
        """
        self.add_interval_no_overlap(self.x_captains_to_duties, "Captains")
        self.add_interval_no_overlap(self.x_first_officers_to_duties, "First Officers")
        self.add_interval_no_overlap(self.x_cabin_crew_to_duties, "Cabin Crew")

        print(f"Added {self.number_of_interval_vars} interval decision variables")
        print(f"Added {self.number_of_no_overlap_constraints} no-overlap constraints")

    def add_interval_no_overlap(self, x_crew_to_duties, crew_type_name):
        """
        Create interval variables and add no-overlap constraints.
        """
        crew_ids = set()
        for crew_id, duty_id in x_crew_to_duties.keys():
            crew_ids.add(crew_id)

        for crew_id in crew_ids:
            intervals = []

            for (c_id, duty_id), x_assignment_var in x_crew_to_duties.items():
                if c_id == crew_id:
                    duty = self.duties_for_aircraft_df[self.duties_for_aircraft_df['duty_id'] == duty_id].iloc[0]

                    # Convert times to integers (e.g., minutes since start)
                    start = self.time_to_int(duty['scheduled_departure_utc'])
                    duration = self.time_to_int(duty['scheduled_arrival_utc']) - start

                    # Create optional interval (only active if assigned)
                    self.number_of_interval_vars += 1

                    interval = self.solver.model.NewOptionalIntervalVar(
                        start,
                        duration,
                        start + duration,
                        x_assignment_var,
                        f'interval_{crew_id}_{duty_id}'
                    )
                    intervals.append(interval)

            if intervals:
                self.number_of_no_overlap_constraints += 1
                self.solver.model.AddNoOverlap(intervals)

    def time_to_int(self, time_value):
        """
        Convert pandas datetime to integer minutes since January 1, 2025.
        """
        time_diff = time_value - pd.Timestamp('2025-01-01 00:00:00')
        minutes = int(time_diff.total_seconds() / 60)
        return minutes