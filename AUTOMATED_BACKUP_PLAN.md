# OrdexWallet Automated Backup System Plan

## Overview
Secure, automated backup system for wallet data with encryption, scheduling, and verification capabilities.

## Backup Scope

### 1. What to Backup
- **Wallet Files**: Encrypted wallet.dat or equivalent
- **Private Keys**: Key pool and HD wallet seed (if applicable)
- **Transaction History**: Complete transaction records
- **Address Book**: Labeled addresses and contacts
- **Configuration**: Non-sensitive wallet settings
- **Metadata**: Creation dates, version info, backup history

### 2. What Not to Backup
- **Blockchain Data**: Available from network
- **Temporary Files**: Cache, logs (unless specifically needed)
- **Sensitive Data in Logs**: Ensure logs don't contain private keys

## Backup Strategy

### 1. Backup Types
- **Full Backup**: Complete wallet data (initial and periodic)
- **Incremental Backup**: Changes since last backup (more complex)
- **Automatic vs Manual**: Scheduled automatic + user-triggered manual

### 2. Backup Locations
- **Local**: Encrypted backups on host system
- **Remote**: Optional cloud storage (encrypted before upload)
- **External**: USB/local network shares (user configurable)

### 3. Backup Frequency
- **Default**: Every 24 hours
- **Configurable**: User-adjustable interval (minimum 1 hour)
- **Event-Based**: After significant transactions or balance changes
- **Manual**: On-demand backup button in UI

## Security Considerations

### 1. Encryption
- **Strong Encryption**: AES-256-GCM or similar authenticated encryption
- **Key Derivation**: PBKDF2 or Argon2 with user-provided passphrase
- **Key Management**: 
  - Option 1: User-provided passphrase (most secure)
  - Option 2: Auto-generated key stored securely (less secure but convenient)
  - Option 3: Hardware wallet/YubiKey integration (advanced)

### 2. Integrity Protection
- **HMAC or AEAD**: Detect tampering
- **Checksums**: Verify backup completeness
- **Versioning**: Detect format corruption

### 3. Access Control
- **File Permissions**: Restrictive permissions on backup files
- **Transport Security**: Encrypted channels for remote backups
- **Authentication**: Required for remote storage access

## Implementation Approach

### 1. Backup Manager Service
```python
class BackupManager:
    def __init__(self, config, wallet_service, encryption_service):
        self.config = config
        self.wallet_service = wallet_service
        self.encryption_service = encryption_service
        self.backup_dir = config.get('backup_dir', './backups')
        self.encryption_key = None  # Set when passphrase provided
        
    def create_backup(self, passphrase=None, label=None):
        """Create encrypted backup of wallet data"""
        # Generate encryption key from passphrase if provided
        if passphrase:
            self.encryption_key = self.encryption_service.derive_key(passphrase)
        elif not self.encryption_key:
            raise BackupError("Encryption key required")
            
        # Collect wallet data
        wallet_data = self.wallet_service.export_data()
        
        # Add metadata
        backup_data = {
            'version': '1.0',
            'timestamp': time.time(),
            'wallet_data': wallet_data,
            'label': label or f"Backup {datetime.now()}",
            'orphaned': False  # Will be set based on wallet state
        }
        
        # Encrypt and serialize
        encrypted_data = self.encryption_service.encrypt(
            json.dumps(backup_data), 
            self.encryption_key
        )
        
        # Write to file with secure permissions
        filename = self._generate_backup_filename(label)
        filepath = os.path.join(self.backup_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(encrypted_data)
            
        # Set restrictive permissions
        os.chmod(filepath, 0o600)
        
        # Clean old backups if needed
        self._cleanup_old_backups()
        
        return filepath
        
    def restore_backup(self, backup_path, passphrase):
        """Restore wallet from encrypted backup"""
        # Derive encryption key
        encryption_key = self.encryption_service.derive_key(passphrase)
        
        # Read and decrypt backup
        with open(backup_path, 'rb') as f:
            encrypted_data = f.read()
            
        decrypted_data = self.encryption_service.decrypt(
            encrypted_data, 
            encryption_key
        )
        
        backup_data = json.loads(decrypted_data)
        
        # Validate backup
        if not self._validate_backup(backup_data):
            raise BackupError("Invalid backup data")
            
        # Restore wallet data
        self.wallet_service.import_data(backup_data['wallet_data'])
        
        return backup_data.get('label', 'Restored backup')
        
    def verify_backup(self, backup_path, passphrase=None):
        """Verify backup integrity without restoring"""
        try:
            # Try to decrypt and validate structure
            data = self._read_backup(backup_path, passphrase)
            return self._validate_backup(data)
        except Exception:
            return False
            
    def _read_backup(self, backup_path, passphrase):
        # Implementation details...
        pass
        
    def _validate_backup(self, backup_data):
        # Check version, required fields, etc.
        pass
        
    def _generate_backup_filename(self, label):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_label = "".join(c for c in label if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return f"ordexwallet_backup_{timestamp}_{safe_label or 'default'}.enc"
        
    def _cleanup_old_backups(self):
        # Remove backups exceeding max_backups setting
        pass
```

### 2. Encryption Service
Handles cryptographic operations for backup security.

### 3. Scheduler
- **Internal Scheduler**: Background thread/process for timed backups
- **System Integration**: Option to use system cron (Linux) or Task Scheduler (Windows)
- **Persistence**: Survives application restarts
- **Missed Backup Handling**: Run backup on startup if schedule was missed

## Backup Workflow

### 1. Initial Setup
- User sets backup encryption passphrase (or accepts auto-generated)
- Backup directory configured (default: ./backups)
- Schedule set (default: daily)

### 2. Regular Operation
- Background scheduler triggers backup at intervals
- Before backup: 
  - Ensure wallet is not mid-transaction
  - Flush any pending writes
  - Take consistent snapshot
- During backup:
  - Export wallet data
  - Encrypt with current key
  - Write to timestamped file
  - Set secure file permissions
- After backup:
  - Verify backup integrity (optional)
  - Clean up old backups per retention policy
  - Log backup completion

### 3. User-Initiated Backup
- Backup button in UI
- Option to label backup
- Progress indication
- Success/error feedback

### 4. Backup Restoration
- Restore wizard in UI
- Select backup file
- Enter encryption passphrase
- Verify backup before restoring
- Confirm restoration (wallet will be replaced)
- Post-restore verification

## Key Management Options

### Option 1: User-Managed Passphrase
- Most secure
- User must remember passphrase
- Key derived using PBKDF2/Argon2
- No key storage (only in memory during operations)
- Backup unusable without passphrase

### Option 2: Auto-Generated Key
- Convenient but less secure
- Key generated on first run
- Stored encrypted with system/DPAPI protection
- Requires securing the host system
- Recovery possible if host is compromised

### Option 3: Hybrid Approach
- Auto-generated master key
- Encrypted with user passphrase for export
- Allows both convenience and security

## Backup File Format
```
{
  "version": "1.0",                    # Backup format version
  "timestamp": 1234567890,             # Unix timestamp
  "label": "User-defined label",       # Optional descriptive label
  "wallet_format": "ordexwallet_v1",   # Indicates wallet data format
  "wallet_data": {                     # Actual wallet export data
    # ... wallet-specific structure ...
  },
  "orphaned": false,                   # True if wallet was deleted after backup
  "checksum": "abc123..."              # SHA-256 of wallet_data for verification
}
```

## Implementation Phases

### 1. Core Backup Functionality
- Basic export/import of wallet data
- Encryption/decryption with passphrase
- File I/O with secure permissions
- Basic scheduling mechanism

### 2. Enhanced Security
- Strong encryption (AEAD modes)
- Key derivation functions
- Integrity checks
- Secure memory handling

### 3. Scheduler Improvements
- Robust background scheduling
- Missed backup detection
- System integration options
- Logging and monitoring

### 4. User Interface
- Backup settings page
- Manual backup controls
- Backup browser/restore wizard
- Passphrase management

### 5. Advanced Features
- Incremental backups (complex)
- Remote backup options
- Backup verification tools
- Multi-signature backup approval (advanced)

## Configuration Options

```yaml
backup:
  enabled: true
  interval_hours: 24
  retention_count: 7          # Keep last N backups
  retention_days: 30          # OR keep backups from last N days
  directory: ./backups
  encrypt: true
  # encryption_key_management: user_passphrase | auto_generated | hybrid
  compression: true           # Compress before encrypting
  verify_after_create: true   # Verify backup after creation
  notify_on_failure: true     # Alert user if backup fails
  min_free_space_mb: 100      # Minimum space required
```

## Error Handling and Recovery

### 1. Backup Failures
- Retry mechanism with exponential backoff
- Alert user after multiple failures
- Fallback to manual backup reminder
- Log detailed error information

### 2. Restore Failures
- Validate backup before restore
- Clear error messages for common issues
  - Wrong passphrase
  - Corrupted backup
  - Incompatible version
  - Missing required data
- Option to try different passphrases
- Partial recovery options if possible

### 3. Disk Space Issues
- Check available space before backup
- Clean oldest backups if space low
- Fail gracefully with clear message
- Suggest increasing retention or freeing space

### 4. Key Management Issues
- Handle lost passphrase (with warnings)
- Key rotation capability
- Emergency recovery documentation
- Secure key deletion when needed

## Monitoring and Maintenance

### 1. Backup Verification
- Periodic verification of existing backups
- Automated integrity checks
- Verification on restore attempt
- User-initiated verification tool

### 2. Logging and Auditing
- Log backup successes/failures
- Track backup sizes and frequencies
- Audit backup access and restoration
- Monitor for suspicious backup patterns

### 3. Performance Considerations
- Minimize wallet lock duration during backup
- Efficient serialization formats
- Background encryption to avoid blocking
- Incremental backup consideration for large wallets

### 4. Compliance and Auditing
- Backup retention policy enforcement
- Audit trail for backup/restore operations
- Option for encrypted backup manifests
- Compatibility with enterprise backup solutions

This automated backup system will provide OrdexWallet users with reliable protection against data loss while maintaining strong security practices for their cryptocurrency assets.