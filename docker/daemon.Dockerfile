FROM debian:bookworm-slim

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

EXPOSE 25173 25466 9333 9334

CMD ["echo", "Daemon ${DAEMON_NAME} ready. Use docker-compose to start the full application."]