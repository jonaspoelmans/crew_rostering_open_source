from datetime import timedelta

from crewrostering.constraints.constraint import Constraint


class MaxHoursRollingPeriodConstraint(Constraint):
    def __init__(self, constraints_data, solver, max_duty_or_flight_time_hours_per_window, rolling_days_window_size, duty_or_flight_mode):
        super().__init__(constraints_data, solver)

        self.max_hours_per_window = max_duty_or_flight_time_hours_per_window
        self.rolling_days_window_size = rolling_days_window_size
        self.duty_or_flight_mode = duty_or_flight_mode # flight or duty

        # Pre-compute flight groupings by date
        self.duties_by_date = {}
        for duty_id, date in self.duty_dates_lookup.items():
            if date not in self.duties_by_date:
                self.duties_by_date[date] = []
            self.duties_by_date[date].append(duty_id)

        # Pre-compute historical hours by crew
        self.historical_flights_by_crew = {}
        for crew_id in self.historical_flights_df['crew_id'].unique():
            crew_history = self.historical_flights_df[self.historical_flights_df['crew_id'] == crew_id]
            self.historical_flights_by_crew[crew_id] = crew_history

    def generate_constraint_variables(self):
        """
        EASA: Max y duty or flight hours in x consecutive days
        """

        # Apply constraint for each crew type
        self.add_rolling_constraint_for_crew_type(self.qualified_captains_df, self.x_captains_to_duties)
        self.add_rolling_constraint_for_crew_type(self.qualified_first_officers_df, self.x_first_officers_to_duties)
        self.add_rolling_constraint_for_crew_type(self.qualified_cabin_crew_df, self.x_cabin_crew_to_duties)

        print(f"Added {len(self.constraints_variables_list)} constraints")

        for constraint in self.constraints_variables_list:
            self.solver.model.Add(constraint)

        return len(self.constraints_variables_list)

    def add_rolling_constraint_for_crew_type(self, qualified_crew_df, x_crew_to_duties_assignments):
        """
        Limit duty or flight hours in any x-day period for each crew member

        Args:
            qualified_crew_df: List of crew members (captains, first officers, or cabin crew)
            x_crew_to_duties_assignments: Possible assignments - crew_assignments[crew_id, duty_id] is a 0/1 variable
        """

        # Pre-group assignments by crew_id
        x_assignments_by_crew = {}
        for (crew_id, duty_id), var in x_crew_to_duties_assignments.items():
            if crew_id not in x_assignments_by_crew:
                x_assignments_by_crew[crew_id] = {}
            x_assignments_by_crew[crew_id][duty_id] = var

        # Check each crew member's rolling duty or flight hour limits
        for index, crew_member in qualified_crew_df.iterrows():
            crew_id = crew_member['crew_id']

            if crew_id not in x_assignments_by_crew:
                continue

            crew_assignments = x_assignments_by_crew[crew_id]
            crew_history = self.historical_flights_by_crew.get(crew_id)

            # Check every possible x-day calendar window starting from this month's dates
            for window_start_date in self.unique_duty_dates:
                window_end_date = window_start_date + timedelta(
                    days=self.rolling_days_window_size - 1)  # x calendar days total

                # Step 1: Get historical duty or flight hours from previous month
                historical_start_date = window_start_date - timedelta(days=self.rolling_days_window_size - 1)
                historical_end_date = window_start_date - timedelta(days=1)  # Day before window starts

                # Get historical duty or flight hours for this crew in the days before window starts
                historical_duty_or_flight_time_hours = 0
                if crew_history is not None and len(crew_history) > 0:
                    flights_in_historical_range = crew_history[
                        (crew_history['scheduled_departure_utc'].dt.date >= historical_start_date) &
                        (crew_history['scheduled_departure_utc'].dt.date <= historical_end_date)
                        ]

                    # Sum up duty or flight hours and scale by 100
                    if self.duty_or_flight_mode == 'flight':
                        historical_duty_or_flight_time_hours = flights_in_historical_range['flight_time_hours'].sum()
                    else:
                        historical_duty_or_flight_time_hours = flights_in_historical_range['duty_time_hours'].sum()

                historical_duty_or_flight_time_hours_scaled = int(historical_duty_or_flight_time_hours * 100)

                # Step 2: Find all scheduled duties this crew could work in this window
                x_duties_in_this_window = []
                current_date = window_start_date
                while current_date <= window_end_date:
                    if current_date in self.duties_by_date:
                        for duty_id in self.duties_by_date[current_date]:
                            if duty_id in crew_assignments:
                                x_assignment_variable = crew_assignments[duty_id]
                                x_duties_in_this_window.append((duty_id, x_assignment_variable))
                    current_date += timedelta(days=1)

                # Only add constraint if there are duties OR historical hours
                if x_duties_in_this_window or historical_duty_or_flight_time_hours_scaled > 0:

                    # Step 3: Calculate total duty hours (historical + scheduled) - scaled by 100
                    total_duty_or_flight_time_hours = historical_duty_or_flight_time_hours_scaled
                    for duty_id, x_assignment_variable in x_duties_in_this_window:
                        if self.duty_or_flight_mode == 'flight':
                            duty_or_flight_time_hours_scaled = int(self.flight_time_hours_lookup[duty_id] * 100)
                        else:
                            duty_or_flight_time_hours_scaled = int(self.duty_time_hours_lookup[duty_id] * 100)

                        total_duty_or_flight_time_hours += duty_or_flight_time_hours_scaled * x_assignment_variable

                    # Step 4: Add constraint: duty or flight hours in window <= max hours
                    max_duty_or_flight_time_hours_scaled = int(self.max_hours_per_window * 100)
                    self.constraints_variables_list.append(
                        total_duty_or_flight_time_hours <= max_duty_or_flight_time_hours_scaled)