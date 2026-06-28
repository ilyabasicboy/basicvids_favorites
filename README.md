# BasicVids Favorites

Favorites microservice for BasicVids.

## Stack

- Gunicorn
- FastAPI
- SQLModel
- Redis

## Development

Use a virtual environment:

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Run locally:

```bash
uvicorn basicvids_favorites.main:app --reload
```

## Container

```bash
mkdir -p data
cp .env.example data/.env
docker compose up -d --build
```

The service is available through the shared gateway at:

```text
http://localhost:8080/api/v1/favorites/
```

## Configuration

Project environment is loaded from:

```text
./data/.env
```

Start from:

```text
./.env.example
```

Database examples:

```env
# SQLite default
# DATABASE_URL=sqlite:///./data/database.db

# PostgreSQL example
DATABASE_URL=postgresql://basicvids_favorites_user:change_me@host.docker.internal:5432/basicvids_favorites
```

Important variables:

| Variable | Default | Description |
| --- | --- | --- |
| `DATA_PATH` | `./data` | Data directory mounted in container |
| `DATABASE_URL` | `sqlite:///./data/database.db` | Metadata database URL |
| `REDIS_URL` | `redis://localhost:6379/5` | Redis connection |
| `AUTH_CURRENT_USER_URL` | `http://basicvids_auth:8000/api/v1/users/detail/` | Auth service current-user endpoint |

## Healthcheck

```text
http://localhost:8080/favorites/health
```
