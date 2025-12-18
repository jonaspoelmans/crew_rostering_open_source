from crewrostering.constraints.constraint import Constraint


class FlightTimeHoursPeriodConstraint(Constraint):
    def __init__(self, constraints_data, solver, max_hours_per_period, period_type):
        super().__init__(constraints_data, solver)

        self.max_hours_per_period = max_hours_per_period
        self.period_type = period_type # year or months

    def generate_constraint_variables(self):
        """
        EASA: Max 900 flight hours per calendar year
        """

        # Apply constraint for each crew type
        self.add_period_hours_constraint_for_crew_type(self.qualified_captains_df, self.x_captains_to_duties)
        self.add_period_hours_constraint_for_crew_type(self.qualified_first_officers_df, self.x_first_officers_to_duties)
        self.add_period_hours_constraint_for_crew_type(self.qualified_cabin_crew_df, self.x_cabin_crew_to_duties)

        print(f"Added {len(self.constraints_variables_list)} constraints")

        for constraint in self.constraints_variables_list:
            self.solver.model.Add(constraint)

        return len(self.constraints_variables_list)

    def add_period_hours_constraint_for_crew_type(self, qualified_crew_df, x_crew_to_duties_assignments):
        """
        Limit how many hours each crew member can fly in a calendar year

        Example: If max is 900 hours/year and they've flown 850, they can only do 50 more

        Args:
            qualified_crew_df: List of crew members (captains, first officers, or cabin crew)
            x_crew_to_duties_assignments: Possible assignments - crew_assignments[crew_id, duty_id] is a 0/1 variable
        """

        # Pre-group assignments by crew_id
        x_assignments_by_crew = {}
        for (crew_id, duty_id), var in x_crew_to_duties_assignments.items():
            if crew_id not in x_assignments_by_crew:
                x_assignments_by_crew[crew_id] = []
            x_assignments_by_crew[crew_id].append((duty_id, var))

        # Check each crew member's yearly hour limits
        for index, crew_member in qualified_crew_df.iterrows():
            crew_id = crew_member['crew_id']

            if self.period_type == 'year':
                hours_already_flown = crew_member['current_calendar_year_flight_time_hours']
            else:
                hours_already_flown = crew_member['last_11_calendar_months_flight_time_hours']

            # Step 1: Find all duties this crew member could be assigned to
            x_possible_duty_assignments = x_assignments_by_crew.get(crew_id, [])

            # Only add constraint if this crew member has possible duties
            if x_possible_duty_assignments:

                # Step 2: Calculate total hours from all possible assignments - scaled by 100 to avoid decimals
                total_scheduled_hours = 0
                for duty_id, x_assignment_variable in x_possible_duty_assignments:
                    flight_time_hours_scaled = int(self.flight_time_hours_lookup[duty_id] * 100)
                    total_scheduled_hours += flight_time_hours_scaled * x_assignment_variable

                # Step 3: Calculate how many hours this crew member has left this year
                hours_remaining = self.max_hours_per_period - hours_already_flown
                max_hours_allowed_scaled = int(hours_remaining * 100)

                # Step 4: Add constraint: scheduled hours must not exceed remaining yearly hours
                self.constraints_variables_list.append(total_scheduled_hours <= max_hours_allowed_scaled)