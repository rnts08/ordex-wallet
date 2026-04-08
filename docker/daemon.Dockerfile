FROM debian:unstable-slim

ARG DAEMON_NAME
ARG DAEMON_BIN

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY bin/${DAEMON_BIN} /usr/local/bin/

RUN chmod +x /usr/local/bin/${DAEMON_BIN} \
    && ln -sf /usr/local/bin/${DAEMON_BIN} /usr/bin/ || true

RUN mkdir -p /config /root/.ordexcoin /root/.ordexgold

ENV DAEMON_NAME=${DAEMON_NAME}

EXPOSE 17523 17524 19333 19334

CMD ["echo", "Daemon ${DAEMON_NAME} ready"]