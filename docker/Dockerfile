FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN mkdir -p /config /data /logs

ENV CONFIG_DIR=/config
ENV DATA_DIR=/data
ENV HOST=0.0.0.0
ENV PORT=5000
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["python", "app.py"]