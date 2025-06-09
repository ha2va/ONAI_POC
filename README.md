# ONTOLOGY POC

This proof of concept implements basic CRUD APIs for an ontology-based forwarding solution using Flask and SQLAlchemy.

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

- `/carriers`
- `/locations`
- `/routes`
- `/schedules`
- `/shipments`
- `/costitems`

Each endpoint supports standard `POST`, `GET`, `PUT`, and `DELETE` operations.
