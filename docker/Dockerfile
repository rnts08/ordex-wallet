FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY bin/ /usr/local/bin/

RUN chmod +x /usr/local/bin/ordexcoind /usr/local/bin/ordexgoldd

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY frontend/ ./frontend/

RUN mkdir -p /config /data /logs

ENV CONFIG_DIR=/data/config
ENV DATA_DIR=/data
ENV HOST=0.0.0.0
ENV PORT=5000
ENV FLASK_ENV=production

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]