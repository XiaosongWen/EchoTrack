# Backend-only production image — used when the frontend is served
# separately (e.g. Cloudflare Pages) and only the FastAPI service
# needs to run on Google Cloud Run.

FROM python:3.12-slim

# Keeps Python from generating .pyc files and enables unbuffered stdout/stderr
# so Cloud Run log collection works correctly.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

# Cloud Run injects $PORT at runtime (default 8080).
# The entrypoint reads it so the service binds on the correct port.
EXPOSE 8080

CMD ["./entrypoint.sh"]
