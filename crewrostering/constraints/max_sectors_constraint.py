from ortools.sat.python.cp_model import LinearExpr

from crewrostering.constraints.constraint import Constraint


class MaxSectorsConstraint(Constraint):
    def __init__(self, constraints_data, solver, max_sectors_day):
        super().__init__(constraints_data, solver)

        # Pre-compute flight groupings by date
        self.duties_by_date = {}
        for duty_id, date in self.duty_dates_lookup.items():
            if date not in self.duties_by_date:
                self.duties_by_date[date] = []
            self.duties_by_date[date].append(duty_id)

        # Maximum flights allowed per crew member per day
        self.max_sectors_day = max_sectors_day

    def generate_constraint_variables(self):
        """
        EASA: Maximum 6 sectors (takeoffs/landings) per day
        Simplified: each flight = 1 sector
        """

        # Apply constraint for each crew type
        self.add_max_sectors_for_crew_type(self.qualified_captains_df, self.x_captains_to_duties)
        self.add_max_sectors_for_crew_type(self.qualified_first_officers_df, self.x_first_officers_to_duties)
        self.add_max_sectors_for_crew_type(self.qualified_cabin_crew_df, self.x_cabin_crew_to_duties)

        print(f"Added {len(self.constraints_variables_list)} constraints")

        for constraint in self.constraints_variables_list:
            self.solver.model.Add(constraint)

        return len(self.constraints_variables_list)

    def add_max_sectors_for_crew_type(self, qualified_crew_df, x_crew_to_duties_assignments):
        """
        Limit how many flights each crew member can do per day

        Example: If max_sectors=3, a pilot can do at most 3 flights on any single day

        Args:
            qualified_crew_df: List of all crew members (pilots, cabin crew, etc.)
            x_crew_to_duties_assignments: Possible assignments - crew_assignments[crew_id, duty_id] is a 0/1 variable
        """

        # Pre-group assignments by crew_id
        x_assignments_by_crew = {}
        for (crew_id, duty_id), var in x_crew_to_duties_assignments.items():
            if crew_id not in x_assignments_by_crew:
                x_assignments_by_crew[crew_id] = {}
            x_assignments_by_crew[crew_id][duty_id] = var

        # Process each crew member
        for index, crew_member in qualified_crew_df.iterrows():
            crew_id = crew_member['crew_id']

            if crew_id not in x_assignments_by_crew:
                continue

            crew_assignments = x_assignments_by_crew[crew_id]

            # For each date, constrain this crew member
            for date, duty_ids_on_date in self.duties_by_date.items():
                # Find duties this crew could do on this date
                x_possible_duties_on_date = []
                for duty_id in duty_ids_on_date:
                    if duty_id in crew_assignments:
                        x_possible_duties_on_date.append(crew_assignments[duty_id])

                # Only add constraint if needed
                if len(x_possible_duties_on_date) > self.max_sectors_day:
                    self.constraints_variables_list.append(
                        LinearExpr.Sum(x_possible_duties_on_date) <= int(self.max_sectors_day / 2)
                    )