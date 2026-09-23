FROM python:3.12-slim

WORKDIR /app

# System deps for building bcrypt/cryptography wheels if a prebuilt wheel
# isn't available for the target platform.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite lives here by default (DATABASE_URL=sqlite:////data/netpulse.db in
# production so it survives container restarts on platforms with a
# persistent disk/volume mount, e.g. Render/Fly.io). Swap DATABASE_URL to a
# managed Postgres/Supabase connection string for anything beyond a demo.
RUN mkdir -p /data
ENV DATABASE_URL=sqlite:////data/netpulse.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
