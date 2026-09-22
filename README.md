# MyWorld 🌍

MyWorld is a personal life operating system and workspace application that unifies commitments/pursuits tracking, habits, labels, weather forecast strips, and activity dashboards into a clean interface.

---

## 🚀 Features

- **Unified Life Operating System**: Manage daily logs, long-term pursuits, habits, and commitments.
- **Weather & Location Awareness**: Real-time forecast strips and location search.
- **Label System**: Flexible tags and organization across modules.
- **Multi-Environment Support**: Clean separation between `dev`, `staging`, and `prod` configurations.
- **Modular Docker Infrastructure**: Shared PostgreSQL & Redis infrastructure (`docker-compose.infra.yml`), decoupled from environment-specific application containers (`docker-compose.stage.yml`, `docker-compose.prod.yml`).
- **Unified Single-Image Deployment**: Bundling React + Vite frontend and FastAPI backend into a single lightweight multi-stage Docker container.
- **Automated CI/CD**: Automated testing via GitHub Actions and automated Docker image publication to Docker Hub upon release.

---

## 🛠️ Deployment & How to Run

MyWorld can be run locally for development or deployed to staging/production environments using Docker Compose.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

---

### 1. Local Development Stack (`docker-compose.infra.yml`)

In development, PostgreSQL and Redis run inside Docker containers while the FastAPI backend and React Vite frontend run on your host system.

```bash
# Start PostgreSQL (port 5432) and Redis (port 6379)
docker compose -f docker-compose.infra.yml up -d

# Start Backend (in backend/ directory)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload

# Start Frontend (in frontend/ directory)
cd frontend
npm install
npm run dev
```

Visit the app at `http://localhost:5173`.

---

### 2. Building & Pushing the Unified Docker Image Locally

You can bundle both the frontend build assets and the backend API into a single image using the build script:

```bash
# Build image locally
./scripts/build-docker.sh echotrack latest

# Build and push image to Docker Hub
DOCKERHUB_USERNAME="tomaswen" ./scripts/build-docker.sh echotrack latest --push
```

Or directly via Docker:

```bash
docker build -t echotrack:latest .
```

---

### 3. Infrastructure & Shared Database Deployment

The core infrastructure services (`postgres` and `redis`) are defined in `docker-compose.infra.yml`. You can host a single shared PostgreSQL container and point `dev`, `stage`, and `prod` application environments to separate databases (e.g. `echotrack_dev`, `echotrack_stage`, `echotrack_prod`).

Copy `.env.example` to `.env` to configure your environment variables:
```bash
cp .env.example .env
```

#### Shared Infrastructure Variables (`.env`):
- `POSTGRES_CONTAINER_NAME=echotrack-postgres`
- `POSTGRES_USER=echotrack`
- `POSTGRES_PASSWORD=echotrack`
- `POSTGRES_DB=echotrack_dev`
- `POSTGRES_PORT=5432`
- `POSTGRES_DATA_DIR=./data/postgres`
- `REDIS_PORT=6379`
- `REDIS_DATA_DIR=./data/redis`

---

### 4. Running Shared Infrastructure (`docker-compose.infra.yml`)

Start the shared database and Redis instance:

```bash
docker compose --env-file .env -f docker-compose.infra.yml up -d
```

---

### 5. Running Staging Application (`docker-compose.stage.yml`)

Run the staging app connected to `echotrack_stage` database. **Requires shared infrastructure to be running first** (see Step 4).

You can either run them together with combined compose files:
```bash
docker compose -f docker-compose.infra.yml -f docker-compose.stage.yml up -d --build
```

Or start the app separately (if infra is already running):
```bash
APP_IMAGE=tomaswen/echotrack:stage \
APP_CONTAINER_NAME=echotrack-stage-app \
APP_PORT=8001 \
DATABASE_URL=postgresql+asyncpg://echotrack:echotrack@postgres:5432/echotrack_stage \
REDIS_URL=redis://redis:6379 \
STORAGE_PATH=/app/storage \
STORAGE_DATA_DIR=./data/stage/storage \
RESTART_POLICY=unless-stopped \
docker compose -f docker-compose.stage.yml up -d --build
```

Access staging app at `http://localhost:8001`.

---

### 6. Running Production Application (`docker-compose.prod.yml`)

Run the production app connected to `echotrack_prod` database. **Requires shared infrastructure to be running first** (see Step 4).

```bash
docker compose -f docker-compose.infra.yml -f docker-compose.prod.yml up -d --build
```

Or start the app separately (if infra is already running):
```bash
APP_IMAGE=tomaswen/echotrack:latest \
APP_CONTAINER_NAME=echotrack-prod-app \
APP_PORT=8000 \
DATABASE_URL=postgresql+asyncpg://echotrack:echotrack@postgres:5432/echotrack_prod \
REDIS_URL=redis://redis:6379 \
STORAGE_PATH=/app/storage \
STORAGE_DATA_DIR=./data/prod/storage \
CPU_LIMIT=2.0 \
MEMORY_LIMIT=2048M \
RESTART_POLICY=always \
docker compose -f docker-compose.prod.yml up -d --build
```

Access production app at `http://localhost:8000`.

---

## 📦 Automated Release & Docker Hub Publication

When a GitHub Release is published, the GitHub Actions workflow (`.github/workflows/docker-release.yml`) automatically builds the multi-stage Docker image and pushes it to Docker Hub under `${DOCKERHUB_USERNAME}/echotrack:latest` and tagged release versions (e.g. `v1.0.0`).
