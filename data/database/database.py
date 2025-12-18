import psycopg2, os

from general.flight import FlightFR24, FlightFE


class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host = os.getenv("DB_HOST", "localhost"),
            database = os.getenv("DB_NAME", "crew_scheduling"),
            user = os.getenv("DB_USER", "XXXX"),
            password = os.getenv("DB_PASSWORD", "XXXX"),
            port = int(os.getenv("DB_PORT", "5432"))
        )
        self.create_flightera_table()

    def create_flightera_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS flightera_flights (
            id SERIAL PRIMARY KEY,
            flnr TEXT NOT NULL,
            date TIMESTAMP NOT NULL,
            journey_id TEXT,
            scheduled_departure_utc TIMESTAMP,
            actual_departure_utc TIMESTAMP,
            scheduled_departure_local TIMESTAMP,
            actual_departure_local TIMESTAMP,
            actual_departure_is_estimated BOOLEAN,
            departure_ident TEXT,
            departure_icao TEXT,
            departure_iata TEXT,
            departure_name TEXT,
            departure_city TEXT,
            departure_terminal TEXT,
            departure_gate TEXT,
            arrival_ident TEXT,
            arrival_icao TEXT,
            arrival_iata TEXT,
            arrival_name TEXT,
            arrival_city TEXT,
            arrival_terminal TEXT,
            scheduled_arrival_utc TIMESTAMP,
            actual_arrival_utc TIMESTAMP,
            scheduled_arrival_local TIMESTAMP,
            actual_arrival_local TIMESTAMP,
            actual_arrival_is_estimated BOOLEAN,
            status TEXT,
            reg TEXT,
            model TEXT,
            family TEXT,
            airline_iata TEXT,
            airline_icao TEXT,
            airline_name TEXT
        );
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()
        cursor.close()

    def create_flight_fe_if_not_exists(self, flight: FlightFE) -> bool:
        # Check if exists based on flight number and date
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 1 FROM flightera_flights 
            WHERE flnr = %s AND date = %s
        """, (flight.flnr, flight.date))
        exists = cursor.fetchone() is not None

        if exists:
            cursor.close()
            return False

        # Insert flight using object attributes directly
        cursor.execute("""
            INSERT INTO flightera_flights (
                flnr, date, journey_id, scheduled_departure_utc, actual_departure_utc,
                scheduled_departure_local, actual_departure_local, actual_departure_is_estimated,
                departure_ident, departure_icao, departure_iata, departure_name, departure_city,
                departure_terminal, departure_gate, arrival_ident, arrival_icao, arrival_iata,
                arrival_name, arrival_city, arrival_terminal, scheduled_arrival_utc,
                actual_arrival_utc, scheduled_arrival_local, actual_arrival_local,
                actual_arrival_is_estimated, status, reg, model, family, airline_iata,
                airline_icao, airline_name
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            flight.flnr, flight.date, flight.journey_id, flight.scheduled_departure_utc,
            flight.actual_departure_utc, flight.scheduled_departure_local,
            flight.actual_departure_local, flight.actual_departure_is_estimated,
            flight.departure_ident, flight.departure_icao, flight.departure_iata,
            flight.departure_name, flight.departure_city, flight.departure_terminal,
            flight.departure_gate, flight.arrival_ident, flight.arrival_icao,
            flight.arrival_iata, flight.arrival_name, flight.arrival_city,
            flight.arrival_terminal, flight.scheduled_arrival_utc, flight.actual_arrival_utc,
            flight.scheduled_arrival_local, flight.actual_arrival_local,
            flight.actual_arrival_is_estimated, flight.status, flight.reg, flight.model,
            flight.family, flight.airline_iata, flight.airline_icao, flight.airline_name
        ))
        self.conn.commit()
        cursor.close()
        return True

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    database = Database()
