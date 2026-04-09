FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libgomp1 \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Create umbrel user and directories with proper permissions
RUN useradd -m -u 1000 umbrel && \
    mkdir -p /data /config /logs /backend && \
    chown -R umbrel:umbrel /data /config /logs /backend

# Copy daemon binaries from build context if available, otherwise download
COPY bin/ /usr/local/bin/

# Download daemon binaries if not present
RUN if [ ! -f /usr/local/bin/ordexcoind ]; then \
    echo "Downloading OrdexCoin daemon..." && \
    wget -q https://github.com/OrdexCoin/Ordexcoin-Core/releases/download/V.25.0/ordexcoin-25.0-linux.tar.gz -O /tmp/ordexcoin.tar.gz && \
    tar -xzf /tmp/ordexcoin.tar.gz -C /tmp && \
    mv /tmp/ordexcoin-25.0/bin/ordexcoind /usr/local/bin/ && \
    rm -rf /tmp/ordexcoin*; \
    fi

RUN if [ ! -f /usr/local/bin/ordexgoldd ]; then \
    echo "Downloading OrdexGold daemon..." && \
    wget -q https://github.com/OrdexCoin/OrdexGold-Core/releases/download/V.0.21.04/ordexgold-0.21.4-linux.tar.gz -O /tmp/ordexgold.tar.gz && \
    tar -xzf /tmp/ordexgold.tar.gz -C /tmp && \
    mv /tmp/ordexgold-0.21.4/bin/ordexgoldd /usr/local/bin/ && \
    rm -rf /tmp/ordexgold*; \
    fi

RUN chmod +x /usr/local/bin/ordexcoind /usr/local/bin/ordexgoldd || true

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .
COPY frontend/ ./frontend/

# Create directories for data (owned by umbrel)
RUN mkdir -p /data/config /data/blockchain/ordexcoin /data/blockchain/ordexgold /data/logs /data/backups && \
    chown -R umbrel:umbrel /data

ENV CONFIG_DIR=/data/config
ENV DATA_DIR=/data
ENV HOST=0.0.0.0
ENV PORT=5000
ENV FLASK_ENV=production

# Copy entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]