FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build deterministic demo data/model artifacts into the image so startup is fast.
RUN python scripts/bootstrap_demo.py --force-data --force-models

EXPOSE 8000

CMD ["sh", "scripts/docker_start.sh"]
