# Docker Setup for OrdexWallet

## Prerequisites

Before running the Docker stack, you need to obtain the Ordex network daemon binaries:

1. Download `ordexcoind` and `ordexgoldd` from the OrdexCoin GitHub:
   - https://github.com/OrdexCoin/Ordexcoin-Core
   - https://github.com/OrdexCoin/OrdexGold-Core

2. Place the binaries in this directory:
   ```
   bin/ordexcoind
   bin/ordexgoldd
   ```

3. Make them executable:
   ```bash
   chmod +x bin/ordexcoind bin/ordexgoldd
   ```

## Building

Once binaries are in place:

```bash
docker-compose build
```

## Running

```bash
docker-compose up -d
```

The application will be available at `http://localhost:5000`

## Notes

- The blockchain data is persisted in Docker volumes (`ordexcoin_data`, `ordexgold_data`)
- Configuration is auto-generated on first startup in the `config_data` volume
- Logs are stored in the `logs` volume