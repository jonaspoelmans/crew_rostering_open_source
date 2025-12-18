from datetime import timedelta
from ortools.sat.python.cp_model import LinearExpr

from crewrostering.constraints.constraint import Constraint


class MinWeeklyRestDaysConstraint(Constraint):
    def __init__(self, constraints_data, solver, min_weekly_rest_days, period_days=14):
        super().__init__(constraints_data, solver)

        self.min_weekly_rest_days = min_weekly_rest_days
        self.period_days = period_days

    def generate_constraint_variables(self):
        """
        EASA: Minimum rest days requirement
        Each crew member must have at least min_rest_days off in any period_days consecutive days

        Example: If min_rest_days=2 and period_days=14, crew must have at least 2 days off
        in every 14-day window
        """

        # Apply constraint for each crew type
        self.add_rest_days_for_crew_type(self.qualified_captains_df, self.x_captains_worked_on_dates)
        self.add_rest_days_for_crew_type(self.qualified_first_officers_df, self.x_first_officers_worked_on_dates)
        self.add_rest_days_for_crew_type(self.qualified_cabin_crew_df, self.x_cabin_crew_worked_on_dates)

        print(f"Added {len(self.constraints_variables_list)} constraints")

        for constraint in self.constraints_variables_list:
            self.solver.model.Add(constraint)

        return len(self.constraints_variables_list)

    def add_rest_days_for_crew_type(self, qualified_crew_df, x_crew_worked_on_dates):
        """
        Ensure each crew member gets minimum rest days in any rolling window

        Args:
            qualified_crew_df: List of crew members
            x_crew_worked_on_dates: Dictionary of (crew_id, date) -> BoolVar (1 if worked that day, 0 if rested)
        """

        # Calculate the maximum number of days a crew member is allowed to work in each rolling window.
        max_work_days = int(self.period_days - self.min_weekly_rest_days)

        # Find the very first date in the schedule (the earliest date we have)
        schedule_start_date = min(self.unique_duty_dates)

        # Make a dictionary that tells us which dates are in each window
        window_dates_lookup = {}

        for start_date in self.unique_duty_dates:
            # Figure out the last date in this window
            end_date = start_date + timedelta(days=self.period_days - 1)

            # Collect all dates that fall between start_date and end_date
            dates_in_window = []
            for date in self.unique_duty_dates:
                if start_date <= date <= end_date:
                    dates_in_window.append(date)

            # Save this list in the dictionary
            window_dates_lookup[start_date] = dates_in_window

        # Make a dictionary to remember which crew worked on which past dates
        historical_work_lookup = {}

        # Go through each row in the historical flights table
        if self.historical_flights_df is not None:
            for index, historical_flight in self.historical_flights_df.iterrows():
                crew_id = historical_flight['crew_id']  # the crew member
                work_date = historical_flight['scheduled_departure_utc'].date()  # the day they worked

                # Mark that this crew worked on this date
                historical_work_lookup[(crew_id, work_date)] = 1

        # Go through each crew member
        for index, crew_member in qualified_crew_df.iterrows():
            crew_id = crew_member['crew_id']

            # Go through each window of dates
            for window_start_date, dates_in_window in window_dates_lookup.items():
                # Count how many historical work days this crew had in this window
                historical_work_days = 0

                # Calculate the historical date range for this window
                historical_start_date = window_start_date - timedelta(days=self.period_days - 1)
                historical_end_date = schedule_start_date - timedelta(days=1)

                # Only check historical dates if the window extends before the schedule start
                if historical_start_date < schedule_start_date:
                    # Count days between historical_start_date and historical_end_date
                    current_date = historical_start_date
                    while current_date <= historical_end_date:
                        if (crew_id, current_date) in historical_work_lookup:
                            historical_work_days += 1
                        current_date += timedelta(days=1)

                # Collect all "worked on date" variables for this crew in this window
                x_days_worked_variables = []
                for date in dates_in_window:
                    if (crew_id, date) in x_crew_worked_on_dates:
                        x_days_worked_variables.append(x_crew_worked_on_dates[crew_id, date])

                # Add the constraint if there is any work recorded
                if x_days_worked_variables or historical_work_days > 0:
                    self.constraints_variables_list.append(
                        historical_work_days + LinearExpr.Sum(x_days_worked_variables) <= max_work_days
                    )