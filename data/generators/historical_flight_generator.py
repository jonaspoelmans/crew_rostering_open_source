import random
import pandas as pd
from datetime import datetime, timedelta


class HistoricalFlightGenerator:
    def __init__(self, crew_df, schedule_start_date):
        """
        Generate historical flight data for crew members

        Args:
            crew_df: DataFrame with crew members (must have 'crew_id' and 'role' columns)
            schedule_start_date: The start date of your schedule (datetime object)
        """
        self.crew_df = crew_df
        self.schedule_start_date = schedule_start_date
        self.historical_flights = []

        # Historical period: 30 days before schedule (covers all rolling windows)
        self.historical_start_date = schedule_start_date - timedelta(days=30)
        self.historical_end_date = schedule_start_date - timedelta(days=1)

    def generate_historical_flights(self,
                                    avg_flights_per_week_captain=4,
                                    avg_flights_per_week_fo=4,
                                    avg_flights_per_week_cabin=5):
        """
        Generate historical flights for all crew members

        Args:
            avg_flights_per_week_captain: Average flights per week for captains
            avg_flights_per_week_fo: Average flights per week for first officers
            avg_flights_per_week_cabin: Average flights per week for cabin crew
        """

        for _, crew_member in self.crew_df.iterrows():
            crew_id = crew_member['crew_id']
            role = crew_member['role']

            # Determine average flights per week based on role
            if role == 'Captain':
                avg_flights_per_week = avg_flights_per_week_captain
            elif role == 'First Officer':
                avg_flights_per_week = avg_flights_per_week_fo
            else:  # Flight Attendant
                avg_flights_per_week = avg_flights_per_week_cabin

            # Generate flights for this crew member over 28 days (4 weeks)
            total_flights = random.randint(
                int(avg_flights_per_week * 3),  # Min: 3 weeks worth
                int(avg_flights_per_week * 4)  # Max: 4 weeks worth
            )

            # Generate random flight dates in the historical period
            for _ in range(total_flights):
                # Random date in historical period
                days_offset = random.randint(0, 27)
                flight_date = self.historical_start_date + timedelta(days=days_offset)

                # Add realistic flight time (6 AM to 10 PM)
                flight_datetime = self.generate_random_flight_time(flight_date)

                # Generate realistic flight and duty hours
                flight_time_hours = round(random.uniform(1.0, 5.5), 1)  # 1-5.5 hours
                duty_time_hours = round(flight_time_hours + random.uniform(1.5, 3.0), 1)  # Add pre/post flight time

                self.historical_flights.append({
                    'crew_id': crew_id,
                    'scheduled_departure_utc': flight_datetime,
                    'flight_time_hours': flight_time_hours,
                    'duty_time_hours': duty_time_hours
                })

    def generate_random_flight_time(self, base_date):
        """
        Generate a realistic flight departure time
        Most flights between 6 AM and 10 PM
        """
        # Random hour between 6 and 22 (6 AM to 10 PM)
        hour = random.randint(6, 22)
        # Random minute
        minute = random.randint(0, 59)
        # Random second
        second = random.randint(0, 59)

        return base_date.replace(hour=hour, minute=minute, second=second)

    def generate_dataframe(self):
        """Convert historical flights to DataFrame"""
        df = pd.DataFrame(self.historical_flights)

        if len(df) > 0:
            # Sort by crew and date
            df = df.sort_values(['crew_id', 'scheduled_departure_utc']).reset_index(drop=True)

        return df

    def save_to_csv(self, path):
        """Save historical flights to CSV"""
        df = self.generate_dataframe()
        df.to_csv(path, index=False)
        return df

if __name__ == "__main__":
    # Load crew data
    crew_df = pd.read_csv('../../assets/simulated/crew_members.csv')

    # Set schedule start date (e.g., January 1, 2025)
    schedule_start_date = datetime(2025, 10, 1)

    # Generate historical flights
    historical_generator = HistoricalFlightGenerator(crew_df, schedule_start_date)

    # Generate flights with typical workload
    historical_generator.generate_historical_flights(
        avg_flights_per_week_captain=4,  # Captains: ~4 flights/week
        avg_flights_per_week_fo=4,  # First Officers: ~4 flights/week
        avg_flights_per_week_cabin=5  # Cabin Crew: ~5 flights/week
    )

    # Save to CSV
    df = historical_generator.save_to_csv('../../assets/simulated/historical_flights.csv')

    print("Historical flights saved to 'historical_flights.csv'")