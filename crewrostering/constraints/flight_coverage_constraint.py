from ortools.sat.python.cp_model import LinearExpr

from crewrostering.constraints.constraint import Constraint


class FlightCoverageConstraint(Constraint):
    def __init__(self, constraints_data, solver):
        super().__init__(constraints_data, solver)

    def generate_constraint_variables(self):
        """
        Each flight must have exactly the required number of crew for each position:
        - Required Captains
        - Required First Officers
        - Required Cabin Crew
        """

        for duty_id in self.duties_for_aircraft_df['duty_id']:
            duty_data = self.duties_for_aircraft_df[self.duties_for_aircraft_df['duty_id'] == duty_id].iloc[0]

            self.require_crew_for_flight(duty_id, self.x_captains_to_duties, duty_data['captains_required'])
            self.require_crew_for_flight(duty_id, self.x_first_officers_to_duties, duty_data['first_officers_required'])
            self.require_crew_for_flight(duty_id, self.x_cabin_crew_to_duties, duty_data['cabin_crew_required'])

            self.require_purser_for_flight(duty_id, self.x_cabin_crew_to_duties)

        print(f"Added {len(self.constraints_variables_list)} constraints")

        for constraint in self.constraints_variables_list:
            self.solver.model.Add(constraint)

        return len(self.constraints_variables_list)

    def require_crew_for_flight(self, duty_id, x_crew_to_duties_assignments, required_count):
        """
        Add constraint that a flight must have exactly the required number of crew

        Args:
            duty_id: The flight that needs crew
            x_crew_to_duties_assignments: Dictionary of (crew_id, duty_id) -> BoolVar assignments
            required_count: Number of crew members required
        """
        x_crew_assigned_to_this_duty = []

        for crew_id, pair_duty_id in x_crew_to_duties_assignments.keys():
            if pair_duty_id == duty_id:
                x_assignment_variable = x_crew_to_duties_assignments[crew_id, pair_duty_id]
                x_crew_assigned_to_this_duty.append(x_assignment_variable)

        if x_crew_assigned_to_this_duty:
            self.constraints_variables_list.append(LinearExpr.Sum(x_crew_assigned_to_this_duty) == required_count)

    def require_purser_for_flight(self, duty_id, x_crew_to_duties_assignments):
        """
        Add constraint that a flight must have at least one purser assigned.

        Args:
            duty_id: The flight that needs crew
            x_crew_to_duties_assignments: Dictionary of (crew_id, duty_id) -> BoolVar assignments
        """
        x_total_pursers_assigned_this_duty = []

        for crew_id, pair_duty_id in x_crew_to_duties_assignments.keys():
            if pair_duty_id == duty_id:
                x_assignment_variable = x_crew_to_duties_assignments[crew_id, pair_duty_id]

                # Look up crew info once
                crew_info = self.qualified_cabin_crew_df[self.qualified_cabin_crew_df['crew_id'] == crew_id].iloc[0]

                if crew_info['purser'] == 'YES':
                    x_total_pursers_assigned_this_duty.append(x_assignment_variable)

        if x_total_pursers_assigned_this_duty:
            self.constraints_variables_list.append(LinearExpr.Sum(x_total_pursers_assigned_this_duty) >= 1)
