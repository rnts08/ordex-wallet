FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ordex-web-wallet/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ordex-web-wallet/backend /app/ordex_web_wallet
COPY ordex-web-wallet/scripts /app/scripts
COPY ordex-web-wallet/frontend /app/frontend

RUN mkdir -p /data/{blocks,chainstate,wallets,backups,logs}

COPY ordex-web-wallet/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "flask", "--app", "ordex_web_wallet.app:create_app()", "run", "--host", "0.0.0.0", "--port", "5000"]