# Platform Support

## Supported Platforms
- **x86/x64 (Intel/AMD)**: Full support with pre-compiled daemon binaries
- **ARM64**: Not currently supported due to lack of pre-compiled daemon binaries

## ARM64 Support Requirements

For ARM64 platforms, you'll need to compile the daemon binaries manually:

### 1. Install Dependencies
```bash
# Install Go for ordexcoind compilation
sudo apt-get update
sudo apt-get install -y golang build-essential git

# Install build dependencies for ordexgoldd
sudo apt-get install -y libssl-dev libgmp-dev
```

### 2. Compile ordexcoind
```bash
cd ~
git clone https://github.com/OrdexCoin/Ordexcoin-Core.git
cd Ordexcoin-Core
git checkout V.25.0
make
cp src/ordexcoind /path/to/ordex-wallet/ordex-wallet/bin/ordexcoind
chmod +x /path/to/ordex-wallet/ordex-wallet/bin/ordexcoind
```

### 3. Compile ordexgoldd
```bash
cd ~
git clone https://github.com/OrdexCoin/OrdexGold-Core.git
cd OrdexGold-Core
git checkout V.0.21.04
make
cp src/ordexgoldd /path/to/ordex-wallet/ordex-wallet/bin/ordexgoldd
chmod +x /path/to/ordex-wallet/ordex-wallet/bin/ordexgoldd
```

### 4. Rebuild Docker Image
```bash
cd /path/to/ordex-wallet/ordex-wallet
docker build -t ordex-wallet:1.0.0-arm64 .
```

## Limitations

- **ARM64 Support**: Manual compilation required for daemon binaries
- **Performance**: ARM64 may have different performance characteristics
- **Testing**: ARM64 platforms require additional testing

## Future Plans

We plan to add official ARM64 support once the ordexnetwork project provides pre-compiled ARM binaries or when we have sufficient resources to maintain our own ARM builds.