# Umbriel App Publishing Guide

This guide covers how to build, push, and publish OrdexWallet to the Umbriel App Store.

## Prerequisites

- Docker with buildx enabled for multi-arch builds
- Docker Hub account
- Fork of [getumbrel/umbrel-apps](https://github.com/getumbrel/umbrel-apps)

---

## Step 1: Build Docker Image

### Option A: Single Architecture (x86/x64 only)

```bash
cd ordex-wallet

# Build the image
docker build -t ordexnetwork/ordex-wallet:1.0.0 .
```

### Option B: Multi-Architecture (x86/x64 + ARM64)

> **Note**: ARM64 requires manual daemon compilation. See [PLATFORM_SUPPORT.md](./PLATFORM_SUPPORT.md)

```bash
cd ordex-wallet

# Enable docker buildx
docker buildx create --name ordexbuilder
docker buildx use ordexbuilder

# Build and push multi-arch image
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ordexnetwork/ordex-wallet:1.0.0 \
  --push .
```

---

## Step 2: Get Image Digest

The digest ensures an immutable, verified image:

```bash
# Pull and inspect
docker pull ordexnetwork/ordex-wallet:1.0.0
docker inspect ordexnetwork/ordex-wallet:1.0.0 --format='{{index .RepoDigests 0}}'
```

Output example:
```
ordexnetwork/ordex-wallet@sha256:a1b2c3d4e5f6...
```

---

## Step 3: Update docker-compose.yml

Replace the image tag with the digest:

```yaml
# Before
image: ordex-wallet:1.0.0

# After
image: ordexnetwork/ordex-wallet:1.0.0@sha256:a1b2c3d4e5f6...
```

---

## Step 4: Fork and Prepare umbrel-apps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/umbrel-apps.git
cd umbrel-apps

# Create branch
git checkout -b add-ordex-wallet

# Copy app directory
cp -r /path/to/ordex-wallet ordex-wallet/

# Commit
git add .
git commit -m "Add OrdexWallet v1.0.0"
git push -u origin add-ordex-wallet
```

---

## Step 5: Submit Pull Request

1. Open PR at: https://github.com/getumbrel/umbrel-apps/pull/new
2. Use this template:

```markdown
# App Submission

### App name
OrdexWallet - Self-hosted web wallet for OrdexCoin and OrdexGold

### 256x256 SVG icon
_(Upload icon with no rounded corners - will be rounded with CSS)_

### Gallery images
_(Upload 3-5 screenshots at 1440x900px)_

### I have tested my app on:
- [x] umbrelOS on an Umbrel Home (x86/x64)
- [x] umbrelOS on Linux VM (x86/x64)
- [ ] umbrelOS on Raspberry Pi (ARM64 - requires manual daemon compilation)
```

---

## Step 6: Testing Before Submitting

### Using umbrel-dev (recommended)

```bash
# Start umbrel dev environment
git clone https://github.com/getumbrel/umbrel.git
cd umbrel
npm run dev

# In another terminal, copy app to app store
rsync -av --exclude=".gitkeep" \
  /path/to/ordex-wallet \
  umbrel@umbrel-dev.local:/home/umbrel/umbrel/app-stores/getumbrel-umbrel-apps-github-53f74447/

# Install via CLI
npm run dev client -- apps.install.mutate -- --appId ordex-wallet
```

Access at: http://umbrel-dev.local:15000

---

## Version Updates

When releasing a new version:

1. Build and push new image with new tag
2. Update `umbrel-app.yml` version and releaseNotes
3. Update `docker-compose.yml` with new digest
4. Submit PR to umbrel-apps

---

## Architecture Support

| Platform | Status | Notes |
|----------|--------|-------|
| x86/x64 | Full | Pre-compiled daemons included |
| ARM64 | Limited | Requires manual daemon compilation |

For ARM64 compilation, see [PLATFORM_SUPPORT.md](./PLATFORM_SUPPORT.md).

---

## Troubleshooting

### Daemon won't start
- Check logs: `docker logs ordex-wallet`
- Verify volumes mounted correctly
- Ensure daemons have execute permissions

### RPC connection failed
- Verify RPC port matches: 25173 (OXC), 25466 (OXG)
- Check generated configs: `/data/config/*.conf`

### Image pull failed
- Ensure image is public on Docker Hub
- Verify digest is correct (not platform-specific)

---

## Files Reference

| File | Purpose |
|------|---------|
| `umbrel-app.yml` | App manifest (name, version, port) |
| `docker-compose.yml` | Umbriel service config with volumes |
| `Dockerfile` | Container build instructions |
| `exports.sh` | Environment variable exports |
| `docker/entrypoint.sh` | Startup script with daemon init |
| `bin/` | Daemon binaries (x86/x64) |
| `PLATFORM_SUPPORT.md` | ARM64 compilation guide |