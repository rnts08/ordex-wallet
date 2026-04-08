# OrdexWallet Config Auto-Generation Plan

## Overview
Automatic generation of configuration files with randomized passwords for RPC daemons on first startup.

## Configuration Files to Generate

### 1. Daemon RPC Configuration
- **ordexcoin.conf**: For ordexcoind RPC settings
- **ordexgold.conf**: For ordexgoldd RPC settings

### 2. Application Configuration
- **config.json**: Main application settings
- **.env**: Environment variables (if used)

### 3. Backup Encryption
- **backup.key**: Encryption key for wallet backups (if separate from wallet encryption)

## Auto-Generation Process

### 1. First Startup Detection
- Check for existence of config directory/files
- If missing, initiate auto-generation sequence
- Create necessary directory structure

### 2. Secure Random Generation
- Use cryptographically secure random number generators
- Generate passwords with sufficient entropy (32+ characters)
- Include uppercase, lowercase, numbers, and special characters
- Ensure no ambiguous characters if needed for manual entry

### 3. Password Generation Algorithm
```python
import secrets
import string

def generate_secure_password(length=32):
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    # Remove ambiguous characters if desired: 'Il1O0S5'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_rpc_credentials():
    return {
        'rpcuser': generate_secure_password(16),
        'rpcpassword': generate_secure_password(32)
    }
```

### 4. Configuration Template Population
- Use Jinja2 or string templates for config files
- Insert generated credentials into appropriate fields
- Set other configuration values to safe defaults

### 5. File Permissions
- Set restrictive permissions on config files (600)
- Ensure only the application user can read sensitive files
- Directory permissions set appropriately (700)

## Specific Configurations

### 1. ordexcoin.conf
```
rpcuser=[GENERATED_USER]
rpcpassword=[GENERATED_PASSWORD]
rpcallowip=127.0.0.1
rpcbind=127.0.0.1
rpclisten=1
server=1
daemon=1
listen=1
```

### 2. ordexgold.conf
```
rpcuser=[GENERATED_USER_GOLD]
rpcpassword=[GENERATED_PASSWORD_GOLD]
rpcallowip=127.0.0.1
rpcbind=127.0.0.1
rpclisten=1
server=1
daemon=1
listen=1
[Additional testnet/specific settings if needed]
```

### 3. config.json
```json
{
  "daemons": {
    "ordexcoind": {
      "host": "localhost",
      "port": 8332,
      "username": "[GENERATED_USER]",
      "password": "[GENERATED_PASSWORD]"
    },
    "ordexgoldd": {
      "host": "localhost",
      "port": 18332,
      "username": "[GENERATED_USER_GOLD]",
      "password": "[GENERATED_PASSWORD_GOLD]"
    }
  },
  "wallet": {
    "encrypt_backups": true,
    "backup_frequency_hours": 24,
    "max_backups": 7
  },
  "api": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  },
  "market": {
    "default_exchange": "nestex",
    "update_interval_minutes": 5
  },
  "system": {
    "stats_interval_seconds": 30,
    "log_retention_days": 30
  }
}
```

### 4. .env (Alternative)
```
FLASK_ENV=production
SECRET_KEY=[GENERATED_SECRET_KEY]
ORDEXCOIND_RPC_USER=[GENERATED_USER]
ORDEXCOIND_RPC_PASSWORD=[GENERATED_PASSWORD]
ORDEXGOLD_RPC_USER=[GENERATED_USER_GOLD]
ORDEXGOLD_RPC_PASSWORD=[GENERATED_PASSWORD_GOLD]
BACKUP_ENCRYPTION_KEY=[GENERATED_BACKUP_KEY]
```

## Security Considerations

### 1. Entropy Sources
- Use `secrets` module (Python 3.6+) or `os.urandom`
- Avoid predictable random number generators
- Consider system entropy sources if available

### 2. Password Storage
- Never log generated passwords
- Store only in memory when needed
- Use environment variables or secure config files
- Consider keyring or vault solutions for production

### 3. File Security
- Set file ownership to non-root user
- Use `chmod 600` on config files
- Consider encrypting sensitive config values
- Audit file access logs if possible

### 4. Regeneration Protection
- Only run auto-generation on first start
- Detect existing configs and skip generation
- Provide manual regeneration option (with warnings)
- Backup existing configs before regeneration

## Implementation Steps

### 1. Detection Mechanism
```python
import os
from pathlib import Path

def is_first_startup(config_dir):
    required_files = [
        'ordexcoin.conf',
        'ordexgold.conf', 
        'config.json'
    ]
    config_path = Path(config_dir)
    return not all((config_path / f).exists() for f in required_files)
```

### 2. Generation Functions
- Separate functions for each config type
- Centralized generator orchestrator
- Error handling and rollback capability

### 3. Template System
- String.Template or Jinja2 for flexibility
- Default templates embedded in code
- Option to override with custom templates

### 4. Post-Generation Validation
- Verify files were created correctly
- Test RPC connections with generated credentials
- Validate config file syntax/format
- Log success/failure appropriately

### 5. Integration with Startup Sequence
- Run before daemon startup
- Run before Flask app initialization
- Fail gracefully if generation fails
- Provide clear error messages to user

## Backup and Recovery

### 1. Configuration Backup
- Automatically backup existing configs before regeneration
- Timestamped backup files
- Option to restore from backup
- Clear documentation on backup location

### 2. Migration Path
- Handle config format changes over time
- Provide upgrade scripts if needed
- Maintain backward compatibility where possible
- Document breaking changes

## Testing Strategy

### 1. Unit Tests
- Test password generation entropy
- Validate template population
- Check file permission settings
- Verify first-start detection logic

### 2. Integration Tests
- Test full auto-generation sequence
- Verify daemon connectivity with generated creds
- Test configuration file parsing
- Validate application startup with generated config

### 3. Security Tests
- Check for password leakage in logs/debug output
- Verify file permissions are set correctly
- Test resistance to common attacks
- Validate entropy of generated passwords

## Deployment Considerations

### 1. Docker Integration
- Run generation in entrypoint script
- Mount volumes for persistent config storage
- Handle first-run vs subsequent runs
- Provide mechanism for manual regeneration

### 2. Manual Override
- Allow specifying configs via environment variables
- Provide command-line flags to skip generation
- Document manual configuration process
- Offer config examples/templates

### 3. Monitoring
- Log when auto-generation occurs
- Alert on generation failures
- Track config file ages
- Monitor for unexpected config changes

## Edge Cases and Error Handling

### 1. Partial Generation
- Rollback on failure during generation
- Clean up partially created files
- Clear error messages indicating what failed

### 2. Permission Issues
- Check directory writability before generation
- Provide helpful error messages for permission problems
- Suggest solutions (run as correct user, fix permissions)

### 3. Disk Space
- Check available space before writing files
- Handle disk full conditions gracefully
- Provide recovery instructions

### 4. Concurrent Startup
- Use file locking to prevent race conditions
- Handle multiple instances trying to generate configs
- Ensure only one generation occurs