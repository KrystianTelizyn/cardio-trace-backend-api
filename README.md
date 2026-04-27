# cardio-trace-backend-api

Core domain service for the Cardio Trace platform — owns all business data and write endpoints. Built with Django REST Framework and PostgreSQL.

## Tech Stack

- Python 3.13
- Django + Django REST Framework
- PostgreSQL 17
- uv (package manager)

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Docker (for PostgreSQL)
- Docker Compose (for full app + database)

## Getting Started

```bash
# Clone the repo
git clone git@github.com:KrystianTelizyn/cardio-trace-backend-api.git
cd cardio-trace-backend-api

# Install dependencies
uv sync

# Copy env file and fill in values
cp .env.example .env

# Start PostgreSQL
make db-start

# Run migrations
make migrate

# Start the dev server
make runserver
```

## Run with Docker Compose

```bash
# Copy env file and fill in values
cp .env.example .env

# Build and start API + PostgreSQL
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## Available Make Targets

| Target      | Description                              |
|-------------|------------------------------------------|
| `db-start`  | Start PostgreSQL in Docker               |
| `db-stop`   | Stop PostgreSQL container                |
| `db-reset`  | Remove PostgreSQL volume (destroys data) |
| `db-status` | Show container status                    |
| `migrate`   | Run Django migrations                    |
| `runserver`  | Start Django development server          |

## Project Structure

```
config/          # Django settings, root URL conf, WSGI
accounts/        # Users, tenants, profiles
docs/            # Architecture overview, API spec, ADRs
```

## Architecture

This service is the **write side** of a read/write split — it handles all mutations through DRF endpoints while [Hasura](https://hasura.io/) serves reads via GraphQL over the same PostgreSQL database.

Authentication is handled externally by the gateway, which forwards trusted headers (`X-User-Id`, `X-Tenant-Id`, `X-Roles`). Internal callers (sensor-hub, workers) are trusted by network origin.

See `docs/backend-api-overview.md` for full details.

## License

Proprietary — all rights reserved.
