import pandas as pd


class FlightDataPreprocessor():
    def __init__(self):
        self.flights_df = None
        self.historical_flights_df = None

        self.crew_df = None
        self.time_off_df = None
        self.crew_requirements_df = None
        self.regulations_df = None

        self.captains_required_dict = []
        self.first_officers_required_dict = []
        self.cabin_crew_required_dict = []
        self.regulations_dict = []

        self.flights_datetime_cols = [
            'scheduled_departure_utc',
            'scheduled_arrival_utc',
            'actual_departure_utc',
            'actual_arrival_utc'
        ]

    def load_data(self):
        print("Loading data...")

        # Load scheduled flights and historical flights
        self.flights_df = pd.read_csv('../assets/simulated/flightera_flights.csv')
        self.historical_flights_df = pd.read_csv('../assets/simulated/historical_flights.csv')

        # Load crew, regulations and offtime
        self.crew_df = pd.read_csv('../assets/simulated/crew_members.csv')
        self.time_off_df = pd.read_csv('../assets/simulated/time_off_requests.csv')
        self.crew_requirements_df = pd.read_csv('../assets/resources/crew_requirements.csv')
        self.regulations_df = pd.read_csv('../assets/resources/regulations.csv')

        # Create mapping dictionaries where relevant
        self.captains_required_dict = self.crew_requirements_df.set_index('model')['captains'].to_dict()
        self.first_officers_required_dict = self.crew_requirements_df.set_index('model')['first_officers'].to_dict()
        self.cabin_crew_required_dict = self.crew_requirements_df.set_index('model')['cabin_crew'].to_dict()

        self.regulations_dict = self.regulations_df.set_index('constraint_name')['value'].astype(int).to_dict()

        # Process the data
        self.clean_data()
        self.preprocess_flights_data()
        self.preprocess_crew_data()

        print("Successfully loaded and preprocessed all data")

    def clean_data(self):
        # Remove rows where flight_time, scheduled_departure_utc or scheduled_arrival_utc is literally "NULL" or empty
        self.flights_df = self.flights_df[
            (self.flights_df['scheduled_departure_utc'].notnull()) &
            (self.flights_df['scheduled_arrival_utc'].notnull()) &
            (self.flights_df['aircraft_registration'].notnull()) &
            (self.flights_df['scheduled_departure_utc'] != "NULL") &
            (self.flights_df['scheduled_arrival_utc'] != "NULL") &
            (self.flights_df['aircraft_registration'] != "NULL") &
            (self.flights_df['scheduled_departure_utc'] != "") &
            (self.flights_df['scheduled_arrival_utc'] != "") &
            (self.flights_df['aircraft_registration'] != "")
            ]

    def preprocess_flights_data(self):
        # Convert datetime columns to datetime objects
        for col in self.flights_datetime_cols:
            self.flights_df[col] = pd.to_datetime(self.flights_df[col])

        # Calculate scheduled flight time (time between scheduled departure and arrival)
        self.flights_df['flight_time_seconds'] = self.flights_df['scheduled_arrival_utc'] - self.flights_df['scheduled_departure_utc']
        self.flights_df['flight_time_hours'] = (self.flights_df['flight_time_seconds'].dt.total_seconds() / 3600).round(2)

        # Add crew requirement columns to flights_df
        self.flights_df['captains_required'] = self.flights_df['aircraft_type'].map(self.captains_required_dict)
        self.flights_df['first_officers_required'] = self.flights_df['aircraft_type'].map(self.first_officers_required_dict)
        self.flights_df['cabin_crew_required'] = self.flights_df['aircraft_type'].map(self.cabin_crew_required_dict)

        # Preprocess historical flights data
        self.historical_flights_df['scheduled_departure_utc'] = pd.to_datetime(self.historical_flights_df['scheduled_departure_utc'])

    def preprocess_crew_data(self):
        self.time_off_df['start_date'] = pd.to_datetime(self.time_off_df['start_date'])
        self.time_off_df['end_date'] = pd.to_datetime(self.time_off_df['end_date'])


