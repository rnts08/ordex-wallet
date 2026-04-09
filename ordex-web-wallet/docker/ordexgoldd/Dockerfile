FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ../../../bin/ordexgoldd /usr/local/bin/ordexgoldd
COPY ../../../bin/ordexgold-cli /usr/local/bin/ordexgold-cli

RUN chmod +x /usr/local/bin/ordexgoldd /usr/local/bin/ordexgold-cli && \
    useradd -m -s /bin/false ordex && \
    mkdir -p /data /config && \
    chown -R ordex:ordex /data /config

USER ordex
WORKDIR /data

EXPOSE 5333

CMD ["ordexgoldd", "-server", "-rpcbind=0.0.0.0:5333", "-rpcallowip=172.16.0.0/12", "-txindex=1"]