# OrdexWallet Release Process

This document describes how releases are managed and how users can access specific versions.

## Release Tags

OrdexWallet uses semantic versioning with git tags:

| Tag | Description |
|-----|-------------|
| `v1.0.0` | Initial stable release |
| `v1.0.1` | Bug fix patch |
| `v1.1.0` | New feature release |

## Finding Releases

### Application Releases

Check the git tags for OrdexWallet releases:

```bash
# List all releases
git fetch --tags
git tag -l

# View specific release
git show v1.0.0

# Checkout a release
git checkout v1.0.0
```

### Daemon Releases

The daemon binaries are managed separately:

- **OrdexCoin**: https://github.com/OrdexCoin/Ordexcoin-Core/releases
- **OrdexGold**: https://github.com/OrdexCoin/OrdexGold-Core/releases

### Version Compatibility

| OrdexWallet | OrdexCoin | OrdexGold |
|-------------|-----------|-----------|
| v1.0.0 | V.25.0 | V.0.21.04 |

## Updating to a Specific Release

### Update Application

```bash
# Fetch all tags
git fetch --tags

# List available versions
git tag -l

# Checkout specific version
git checkout v1.0.1

# Rebuild
cd docker
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Update Daemons

```bash
# Stop container
cd docker
docker compose down

# Remove old binaries
rm bin/ordexcoind bin/ordexgoldd

# Download new versions from GitHub:
# - https://github.com/OrdexCoin/Ordexcoin-Core/releases
# - https://github.com/OrdexCoin/OrdexGold-Core/releases

# Make executable
chmod +x bin/ordexcoind bin/ordexgoldd

# Start
docker compose up -d
```

## Release Checklist

When creating a new release:

1. Update version in any documentation
2. Test all functionality
3. Create git tag:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```
4. Update this compatibility table
5. Update README with new daemon versions if needed

## Current Stable Release

- **Version**: v1.0.0
- **OrdexCoin**: V.25.0
- **OrdexGold**: V.0.21.04