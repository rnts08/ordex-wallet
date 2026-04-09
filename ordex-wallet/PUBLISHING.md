# Publishing Instructions

## Prerequisites

1. **Docker Hub Account**: Create a Docker Hub account
2. **GitHub Fork**: Fork the umbrel-apps repository

## Steps to Publish

### 1. Build and Push Docker Images

For x86/x64 platforms:
```bash
# Build x86/x64 image
docker build -t rnts08/ordex-wallet:1.0.0 .

# Push to Docker Hub
docker push rnts08/ordex-wallet:1.0.0
```

For ARM64 (when available):
```bash
# Build multi-architecture image
docker buildx build --platform linux/amd64,linux/arm64 \
  --tag rnts08/ordex-wallet:1.0.0 \
  --push .
```

### 2. Get Docker Image Digest

```bash
# Get the digest for verification
docker pull rnts08/ordex-wallet:1.0.0
docker inspect rnts08/ordex-wallet:1.0.0 --format='{{index .RepoDigests 0}}'
```

Example output:
```
rnts08/ordex-wallet@sha256:abc123def456...
```

### 3. Update docker-compose.yml

Replace the image reference with the digest:
```yaml
web:
  image: rnts08/ordex-wallet:1.0.0@sha256:abc123def456...
```

### 4. Submit Pull Request

1. Fork the umbrel-apps repository
2. Create a new branch: `git checkout -b add-ordex-wallet`
3. Copy the ordex-wallet directory to your fork
4. Update the umbrel-app.yml with correct dependencies and information
5. Update docker-compose.yml with the correct image digest
6. Commit changes: `git commit -m "Add OrdexWallet app"`
7. Push to your fork: `git push origin add-ordex-wallet`
8. Open a pull request to umbrel-apps repository

### 5. Testing

Test the app on umbrelOS using the development environment:
```bash
# Copy app to umbrel-dev
rsync -av --exclude=".gitkeep" ordex-wallet umbrel@umbrel-dev.local:/home/umbrel/umbrel/app-stores/getumbrel-umbrel-apps-github-53f74447/

# Install via CLI
npm run dev client -- apps.install.mutate -- --appId ordex-wallet
```

### 6. Required Files

Ensure all required files are included:
- `umbrel-app.yml` - App manifest
- `docker-compose.yml` - Docker configuration
- `exports.sh` - Environment variables
- `Dockerfile` - Build instructions
- `PLATFORM_SUPPORT.md` - Platform documentation
- `README.md` - App-specific documentation

### 7. App Store Submission Requirements

For the pull request description:

```
# App Submission

### App name
OrdexWallet - Self-hosted web wallet for OrdexCoin and OrdexGold

### 256x256 SVG icon
_(Upload an icon with no rounded corners as it will be dynamically rounded with CSS.)_

### Gallery images
_(Upload 3 to 5 high-quality gallery images of the app)_

### I have tested my app on:
- [x] umbrelOS on a Raspberry Pi (ARM64 - manual compilation required)
- [x] umbrelOS on an Umbrel Home (x86/x64)
- [x] umbrelOS on Linux VM (x86/x64)
```

### 8. Version Management

- **Version Format**: Use semantic versioning (e.g., 1.0.0)
- **Dependencies**: Update docker-compose.yml when new versions are available
- **Breaking Changes**: Increment major version number
- **Features**: Increment minor version number  
- **Bug Fixes**: Increment patch version number

## Publishing Checklist

- [ ] Docker Hub account created and authenticated
- [ ] Docker images built and pushed for supported platforms
- [ ] Image digests obtained and verified
- [ ] docker-compose.yml updated with digests
- [ ] All required files included
- [ ] App tested on umbrelOS
- [ ] Fork created and branch pushed
- [ ] Pull request opened with proper description
- [ ] Documentation updated for new version