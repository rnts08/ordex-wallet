FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ../../../bin/ordexcoind /usr/local/bin/ordexcoind
COPY ../../../bin/ordexcoin-cli /usr/local/bin/ordexcoin-cli

RUN chmod +x /usr/local/bin/ordexcoind /usr/local/bin/ordexcoin-cli && \
    useradd -m -s /bin/false ordex && \
    mkdir -p /data /config && \
    chown -R ordex:ordex /data /config

USER ordex
WORKDIR /data

EXPOSE 5332

CMD ["ordexcoind", "-server", "-rpcbind=0.0.0.0:5332", "-rpcallowip=172.16.0.0/12", "-txindex=1"]