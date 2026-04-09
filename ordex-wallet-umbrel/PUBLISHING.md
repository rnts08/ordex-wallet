# OrdexWallet Umbrel Publishing Guide

✅ **The app is already fully prepared. Just follow these 3 simple steps:**

---

## Step 1: Push Docker Image to Docker Hub

```bash
# 1. Login to your Docker Hub account
docker login

# 2. Build and push the image
cd ..
docker buildx build --platform linux/amd64 --tag rnts08vn/ordexnetwork-umbrel:1.1.0 -f ordex-wallet-umbrel/Dockerfile --push .

# 3. Get the immutable image digest
docker inspect rnts08vn/ordexnetwork-umbrel:1.1.0 --format='{{index .RepoDigests 0}}'
```

✅ You will get output like:
```
rnts08vn/ordexnetwork-umbrel@sha256:abc123def456...
```

---

## Step 2: Update Configuration

Edit `ordex-wallet-umbrel/docker-compose.yml` line 13:

```yaml
# Replace this:
image: ordex-wallet:1.0.0

# With your full digest:
image: rnts08vn/ordexnetwork-umbrel:1.1.0@sha256:abc123def456...
```

---

## Step 3: Submit to Umbrel App Store

1.  Go to https://github.com/getumbrel/umbrel-apps
2.  Click **Fork** in the top right
3.  Clone your fork:
    ```bash
    git clone https://github.com/YOUR_USERNAME/umbrel-apps.git
    cd umbrel-apps
    ```

4.  Copy the app:
    ```bash
    cp -r /path/to/ordex-wallet-umbrel ./ordex-wallet
    ```

✅ **Note**: Only the `ordex-wallet-umbrel/` folder needs to be copied. All source code is already built into the Docker image hosted on Docker Hub. No other project files are required for submission.

5.  Commit and push:
    ```bash
    git checkout -b add-ordex-wallet
    git add .
    git commit -m "Add OrdexWallet v1.1.0"
    git push -u origin add-ordex-wallet
    ```

6.  **Open Pull Request** at https://github.com/getumbrel/umbrel-apps/pull/new

    Use this PR description:
    ```markdown
    # App Submission

    ### App name
    OrdexWallet - Self-hosted web wallet for OrdexCoin and OrdexGold

    ### 256x256 SVG icon
    ✅ Included in app package

    ### Gallery images
    ✅ 3 screenshots included

    ### I have tested my app on:
    - [x] umbrelOS on an Umbrel Home (x86/x64)
    - [x] umbrelOS on Linux VM (x86/x64)
    - [ ] umbrelOS on Raspberry Pi (ARM64)
    ```

---

## ✅ Done!

That's it. The Umbrel team will review your submission.

---

### Need to update later?
When releasing new versions:
1.  Build and push new image with incremented tag
2.  Update `umbrel-app.yml` version and releaseNotes
3.  Update `docker-compose.yml` with new digest
4.  Submit new PR

---

## Troubleshooting
- Build issues? Check Docker is running and buildx is enabled
- Push denied? Make sure you are logged in to Docker Hub
- Digest not found? Wait 1 minute for Docker Hub to process the image