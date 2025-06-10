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

애플리케이션은 `db/onai_route.db` 파일을 사용합니다.

## Available endpoints

- `GET /carriers`
- `GET /locations`
- `GET /routes`
- `GET /schedules`
- `GET /shipments`
- `GET /costitems`
- `GET /locationcoverage`

