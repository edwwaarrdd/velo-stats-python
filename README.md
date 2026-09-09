# Velo Stats

Django app for tracking Velo Antwerp bike-share stations, ride history, and routing between stations.

## Setup

```
docker compose up -d --build
```

This starts five services:
- `api` – Django app served by gunicorn on port `8000`
- `redis` – broker/result backend for Celery
- `worker` – Celery worker for background tasks
- `worker-ride-distance` – Celery worker consuming the `ride_distance_checks` queue one task at a time, so calls to the free routing API are never made concurrently
- `worker-ride-weather` – Celery worker consuming the `ride_weather_checks` queue one task at a time, so calls to the free Open-Meteo API are never made concurrently

Verify the app is up and running:

```
curl http://localhost:8000/_healthcheck
```

Should return a 200 OK response.

Stop everything with:

```
docker compose down
```

### Configuration

Environment variables (set in `docker-compose.yml`):

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | `insecure-dev-key-change-me` | Django secret key |
| `DJANGO_DEBUG` | `false` | Enable Django debug mode |
| `DJANGO_ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Celery result backend URL |

Data is persisted to a SQLite database at `data/db.sqlite3`.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/_healthcheck` | Returns `{"message": "ok"}` with a 200 status if the app is up |
| `GET` | `/rides/` | Returns every ride with its basic info, distance (from the cached station route), speed (distance ÷ duration), and cached weather, most recent first |
| `GET` | `/rides/summary` | Returns aggregate stats across all rides: total rides, total/average/longest/shortest duration, and total/average distance |
| `GET` | `/rides/cost` | Returns the cost per ride, using the € 58/year subscription price prorated over the date range from the first to the last ride, plus the equivalent cost and money saved versus paying with day passes (€ 5) or week passes (€ 12) instead |

## Console Commands

Run against the running `api` container:

```
docker compose exec api python manage.py <command>
```

| Command | Description |
|---|---|
| `load_stations` | Fetches Velo Antwerp station information from the public GBFS feed and upserts it into the database |
| `load_rides [--path PATH]` | Loads ride history from a JSON export (defaults to `data/rides.json`) and upserts it into the database |
| `dispatch_test_task [--message MSG]` | Dispatches a test Celery task that logs a message from the worker, useful for verifying the Celery/Redis setup |
| `check_ride_distances` | Dispatches a Celery task per unchecked ride to calculate and cache the distance between its origin and destination stations, one at a time via the `ride_distance_checks` queue |
| `check_ride_weather [--force]` | Dispatches a Celery task per ride to fetch and cache the biking-relevant weather (temperature, precipitation, wind, cloud cover, humidity, weather code) at its origin station and checkin time from the free Open-Meteo API, one at a time via the `ride_weather_checks` queue. Only unchecked rides are dispatched by default; pass `--force` to re-fetch weather for every ride |

### Verifying the Celery setup

Dispatch a test "hello world" task through the `api` container:

```
docker compose exec api python manage.py dispatch_test_task --message "hello world"
```

Then check the `worker` container's logs to confirm the message was picked up and processed:

```
docker compose logs worker
```

You should see a log line containing `hello world` from the worker.
