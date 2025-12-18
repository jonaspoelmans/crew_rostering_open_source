from crewrostering.constraints.constraint import Constraint


class MaxFlightDutyPeriodHoursConstraint(Constraint):
    def __init__(self, constraints_data, solver, max_flight_duty_period_hours):
        super().__init__(constraints_data, solver)

        self.max_flight_duty_period_hours = max_flight_duty_period_hours

    def generate_constraint_variables(self):
        """
        EASA: Maximum Flight Duty Period (FDP)
        Each crew member's shift (continuous work period) cannot exceed max_shift_hours

        Example: If max is 13 hours, a pilot working multiple duties in one day
        cannot have those duties total more than 13 hours of duty time
        """

        # Apply constraint for each crew type
        self.add_max_shift_hours_for_crew_type(self.qualified_captains_df, self.x_captains_to_duties)
        self.add_max_shift_hours_for_crew_type(self.qualified_first_officers_df, self.x_first_officers_to_duties)
        self.add_max_shift_hours_for_crew_type(self.qualified_cabin_crew_df, self.x_cabin_crew_to_duties)

        print(f"Added {len(self.constraints_variables_list)} constraints")

        for constraint in self.constraints_variables_list:
            self.solver.model.Add(constraint)

        return len(self.constraints_variables_list)

    def add_max_shift_hours_for_crew_type(self, qualified_crew_df, x_crew_to_duties_assignments):
        """
        Limit total work hours per shift for each crew member

        Args:
            qualified_crew_df: List of crew members
            x_crew_to_duties_assignments: Possible assignments - crew_assignments[crew_id, duty_id] is 0/1 variable
        """

        max_shift_hours_scaled = int(self.max_flight_duty_period_hours * 100)

        # Pre-group assignments by (crew_id, date)
        x_assignments_by_crew_date = {}
        for (crew_id, duty_id), x_assignment_variable in x_crew_to_duties_assignments.items():
            date = self.duty_dates_lookup[duty_id]
            if (crew_id, date) not in x_assignments_by_crew_date:
                x_assignments_by_crew_date[(crew_id, date)] = []
            x_assignments_by_crew_date[(crew_id, date)].append((duty_id, x_assignment_variable))

        # Check each crew member's shift limits
        for index, crew_member in qualified_crew_df.iterrows():
            crew_id = crew_member['crew_id']

            # Check each unique date
            for date in self.duty_dates_lookup.values():

                # Step 1: Find all duties this crew member could work on this date
                x_duties_on_this_date = x_assignments_by_crew_date.get((crew_id, date), [])

                # Only add constraint if there are duties on this date
                if x_duties_on_this_date:

                    # Step 2: Calculate total duty hours for this shift - scaled by 100 to avoid decimals
                    total_shift_hours = 0
                    for duty_id, x_assignment_variable in x_duties_on_this_date:
                        shift_hours_scaled = int(self.duty_time_hours_lookup[duty_id] * 100)
                        total_shift_hours += shift_hours_scaled * x_assignment_variable

                    # Step 3: Add constraint: shift hours cannot exceed maximum
                    self.constraints_variables_list.append(total_shift_hours <= max_shift_hours_scaled)