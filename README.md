# ONTOLOGY POC

This sample Flask web app uses Python's built‑in `sqlite3` module to store data.
The schema follows the ontology tables and is created automatically on startup.
웹 브라우저에서 기본 CRUD 화면을 제공하며,
또한 각 테이블을 조회할 수 있는 간단한 `GET` API도 제공합니다.

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

The server now listens on all network interfaces (0.0.0.0) so you can
access it from other machines as long as the port is open. The
application uses the `db/onai_route.db` file for its database.

## Tariff table

The application now contains a **Tariff** table that holds pricing
information for each route. Tariffs represent the costs that are
applied when a shipment uses a specific route and are used when
recommending a plan. A new `/tariffs` page lists all tariffs in the
web interface so you can review and edit them.

## Plan recommendation

The **Plan Recommendation** page (`/plan`) suggests a series of routes
between two locations. When planning, you select the desired start
date and the system automatically computes the end date based on the
lead times of each chosen route. The total cost shown for each plan is
calculated using the tariffs associated with those routes.

## Available endpoints

- `GET /carriers`
- `GET /locations`
- `GET /routes`
- `GET /schedules`
- `GET /shipments`
- `GET /costitems`
- `GET /locationcoverage`
- `GET /tariffs`

