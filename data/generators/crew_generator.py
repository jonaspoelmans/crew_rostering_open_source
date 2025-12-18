import random
import pandas as pd

captains_per_aircraft = {
    'B738': 17,
    'DH8D': 63,
    'B38M': 9,
    'B737': 21
}

first_officers_per_aircraft = {
    'B738': 17,
    'DH8D': 63,
    'B38M': 9,
    'B737': 21
}

total_flight_attendants = 330


class CrewGenerator():
    def __init__(self):
        self.columns = [
            'crew_id',
            'role',
            'qualifications',
            'purser',
            'seniority',
            'monthly_hours_limit',
            'yearly_hours_limit',
            'current_month_flight_time_hours',
            'current_month_duty_time_hours',
            'last_11_calendar_months_flight_time_hours',
            'current_calendar_year_flight_time_hours'
        ]

        self.captains = []
        self.first_officers = []
        self.cabin_crew = []

        self.df_captains = None
        self.df_first_officers = None
        self.df_cabin_crew = None
        self.df_combined = None

    def generate_records(self,
                         number_of_records,
                         role,
                         qualifications,
                         purser=False,
                         seniority=None,
                         monthly_hours_limit=90,
                         yearly_hours_limit=900,
                         current_month_flight_time_hours=0,
                         current_month_duty_time_hours=0,
                         last_11_calendar_months_flight_time_hours=0,
                         current_calendar_year_flight_time_hours=0):
        if seniority is None:
            seniority = [5, 15]

        for i in range(number_of_records):
            if purser:
                purser_val = random.choices(["YES", "NO"], weights=[0.25, 0.75])[0]
            else:
                purser_val = 'NO'

            row = [
                self.generate_id_prefix(role),
                role,
                ','.join(qualifications),
                purser_val,
                random.randint(seniority[0], seniority[1]),
                monthly_hours_limit,
                yearly_hours_limit,
                current_month_flight_time_hours,
                current_month_duty_time_hours,
                last_11_calendar_months_flight_time_hours,
                current_calendar_year_flight_time_hours
            ]

            if role == 'Captain':
                self.captains.append(row)
            elif role == 'First Officer':
                self.first_officers.append(row)
            elif role == 'Flight Attendant':
                self.cabin_crew.append(row)

    def generate_id_prefix(self, role):
        id_prefix = ''

        if role == 'Captain':
            id_prefix = 'C' + str(len(self.captains) + 1)
        elif role == 'First Officer':
            id_prefix = 'FO' + str(len(self.first_officers) + 1)
        elif role == 'Flight Attendant':
            id_prefix = 'FA' + str(len(self.cabin_crew) + 1)

        return id_prefix

    def generate_data_frame(self):
        self.df_captains = pd.DataFrame(self.captains, columns=self.columns)
        self.df_first_officers = pd.DataFrame(self.first_officers, columns=self.columns)
        self.df_cabin_crew = pd.DataFrame(self.cabin_crew, columns=self.columns)

        self.df_combined = pd.concat([self.df_captains, self.df_first_officers, self.df_cabin_crew], ignore_index=True)

    def save_to_csv(self, path):
        self.df_combined.to_csv(path, index=False)


if __name__ == "__main__":
    crew_generator = CrewGenerator()

    for qualification, pilot_count in captains_per_aircraft.items():
        crew_generator.generate_records(
            number_of_records=pilot_count,
            role='Captain',
            qualifications=[qualification],
            purser=False,
            seniority=[14, 23]
        )

    for qualification, pilot_count in first_officers_per_aircraft.items():
        crew_generator.generate_records(
            number_of_records=pilot_count,
            role='First Officer',
            qualifications=[qualification],
            purser=False,
            seniority=[4, 15]
        )

    # Cabin Crew
    crew_generator.generate_records(
        number_of_records=total_flight_attendants,
        role='Flight Attendant',
        qualifications=['ALL'],
        purser=True,
        seniority=[1, 25]
    )

    # Generate DataFrames and save to CSV
    crew_generator.generate_data_frame()
    crew_generator.save_to_csv('../../assets/simulated/crew_members.csv')

    print(f"Generated {len(crew_generator.df_combined)} crew records")
    print(crew_generator.df_combined.groupby('role')['crew_id'].count())
