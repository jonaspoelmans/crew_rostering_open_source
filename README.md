# Crew Rostering Open Source

Airline crew scheduling system using Google OR-Tools CP-SAT solver with EASA regulation compliance.

## Prerequisites

- Python 3.8+
- FlightEra API key (required for flight data)

## Installation

```bash
git clone https://github.com/jonaspoelmans/crew_rostering_open_source.git
cd CrewRosteringOpenSource
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install pandas ortools requests python-dotenv
```

## Quick Start

### 1. Get Flight Data (Required)

Sign up at RapidAPI FlightEra and get your API key.

Create `.env` file:
```env
FLIGHT_ERA_API_TOKEN=your_api_key_here
```

Edit `data/retrieval/flight_era.py`:
```python
self.airline = "LG"  # Your airline IATA code
self.start_time = "2025-10-01"
self.end_time = "2025-10-31"
```

Retrieve flights:
```bash
python data/retrieval/flight_era.py
```

### 2. Generate Synthetic Crew & Historical Data

```bash
# Generate crew members
python data/generators/crew_generator.py

# Generate historical flights (update schedule_start_date first to match your flight data)
python data/generators/historical_flight_generator.py
```

### 3. Create Configuration Files

Modify these in `assets/resources/`: **aircraft_fleet.csv**, **crew_requirements.csv**, **regulations.csv**, **time_off_requests.csv** (optional)

### 4. Run Scheduler

```bash
python crew_rostering/crew_scheduler.py
```

Results saved to: `assets/output/crew_schedule_output.csv`

## Troubleshooting

**No solution found?**
- Increase crew numbers in `crew_generator.py`
- Reduce historical workload in `historical_flight_generator.py`
- Ensure aircraft types match across all files

**Check aircraft types match:**
```bash
python -c "import pandas as pd; df=pd.read_csv('assets/simulated/flightera_flights.csv'); print(df['aircraft_type'].unique())"
```

## Customization

Edit crew numbers in `data/generators/crew_generator.py`:
```python
captains_per_aircraft = {
    'B738': 17,
    'DH8D': 63,
}
```

Adjust workload in `data/generators/historical_flight_generator.py`:
```python
avg_flights_per_week_captain=4
```

## Disclaimer

⚠️ For educational purposes only. Not certified for production use. Consult aviation safety experts before using in real operations.

## Contact

Jonas Poelmans - [@jonaspoelmans](https://github.com/jonaspoelmans)
