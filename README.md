# ONTOLOGY POC

This sample Flask web app uses Python's built‑in `sqlite3` module to store data.
The schema follows the ontology tables and is created automatically on startup.
Only simple `GET` endpoints are provided to list rows from each table.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the application

```bash
python app.py
```

The application uses SQLite (`poc.db`) in the project directory.

## Available endpoints

- `GET /carriers`
- `GET /locations`
- `GET /routes`
- `GET /schedules`
- `GET /shipments`
- `GET /costitems`
- `GET /locationcoverage`

