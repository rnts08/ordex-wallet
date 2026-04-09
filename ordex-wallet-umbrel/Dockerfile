FROM python:3.12-slim

# Install system dependencies (as root)
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libgomp1 \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Create required directories (data volumes will be mounted at /data)
RUN mkdir -p /app/config /app/frontend /app/bin

# Create non-root user
RUN useradd -m -u 1000 umbrel
RUN chown -R umbrel:umbrel /app
USER umbrel

# Copy daemon binaries from parent (local dev) or download if not present
COPY ../bin/ /app/bin/

# Download daemon binaries if not present
RUN if [ ! -f /app/bin/ordexcoind ]; then \
    echo "Downloading OrdexCoin daemon..." && \
    wget -q https://github.com/OrdexCoin/Ordexcoin-Core/releases/download/V.25.0/ordexcoin-25.0-linux.tar.gz -O /tmp/ordexcoin.tar.gz && \
    tar -xzf /tmp/ordexcoin.tar.gz -C /tmp && \
    mv /tmp/ordexcoin-25.0/bin/ordexcoind /app/bin/ && \
    rm -rf /tmp/ordexcoin*; \
    fi

RUN if [ ! -f /app/bin/ordexgoldd ]; then \
    echo "Downloading OrdexGold daemon..." && \
    wget -q https://github.com/OrdexCoin/OrdexGold-Core/releases/download/V.0.21.04/ordexgold-0.21.4-linux.tar.gz -O /tmp/ordexgold.tar.gz && \
    tar -xzf /tmp/ordexgold.tar.gz -C /tmp && \
    mv /tmp/ordexgold-0.21.4/bin/ordexgoldd /app/bin/ && \
    rm -rf /tmp/ordexgold*; \
    fi

RUN chmod +x /app/bin/ordexcoind /app/bin/ordexgoldd || true

# Copy application code from parent
COPY ../backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../backend/ /app/
COPY ../frontend/ /app/frontend/

# Copy entrypoint (as root before switching user)
USER root
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
USER umbrel

# Set environment variables (data comes from mounted volumes at /data)
ENV CONFIG_DIR=/data/config
ENV DATA_DIR=/data
ENV HOST=0.0.0.0
ENV PORT=15000
ENV FLASK_ENV=production

# Expose port
EXPOSE 15000

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]