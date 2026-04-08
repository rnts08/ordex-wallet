# OrdexWallet Frontend Plan

## Overview
Single-page application using HTML, CSS, and JavaScript (vanilla or framework-independent) that communicates with the Flask backend API.

## Page Structure

### 1. Landing Page / Dashboard
- Asset overview with total balance (both networks)
- Balance over time chart
- Recent transactions list
- News feed from ordexnetwork homepage
- Quick links: GitHub, Explorer, Pool, Swap, Staking, Discord
- Wallet status indicator (connected/not connected)

### 2. Wallet Setup (First Run)
- Create new wallet button
- Import wallet form (private key input)
- Backup instructions and download
- Wallet verification after creation/import

### 3. Wallet Overview
- Total balance display
- Individual asset balances
- Latest transactions
- Receive/send address buttons

### 4. Address Management
- Receive addresses tab
  - List of receiving addresses
  - QR code display for selected address
  - Copy to clipboard button
  - Generate new address button
- Send addresses tab
  - List of sending addresses (change addresses)
  - Similar functionality to receive addresses

### 5. Transactions
- Transaction list view
  - Filter options (all, sent, received, pending)
  - Search/filter by address or amount
  - Pagination
- Transaction details view
  - Transaction ID/hash
  - Timestamp
  - From/to addresses
  - Amount and fees
  - Confirmations status
  - Raw transaction data (expandable)
  - Block explorer link

### 6. Backup & Security
- Backup wallet button (manual)
- Restore wallet form
- Verify message tool
- Sign message tool
- Change password (if implemented)

### 7. System Console
- RPC console for advanced users
  - Command input
  - Response display
  - Command history
- System stats display
  - Disk usage
  - Network usage
  - Memory usage
  - Uptime
- Audit log viewer
  - Filter by date/type
  - Search capability
  - Export functionality

### 8. Settings
- Exchange selection for price data
- Backup frequency configuration
- Notification preferences
- Theme selection (light/dark)
- Advanced options

## Component Architecture

### Core Services
- `ApiService` - Handles all API calls to backend
- `WalletService` - Manages wallet state and operations
- `TransactionService` - Handles transaction creation and monitoring
- `MarketService` - Fetches and caches price data
- `NotificationService` - Handles user notifications
- `StorageService` - Manages local storage (preferences, cache)

### UI Components
- `Dashboard` - Main overview page
- `WalletSetup` - First-run experience
- `AssetOverview` - Balance and asset display
- `AddressManager` - Address generation and display
- `TransactionList` - List of transactions
- `TransactionDetail` - Detailed transaction view
- `BackupRestore` - Backup and restore interface
- `MessageTools` - Sign/verify message tools
- `SystemConsole` - RPC console and system stats
- `AuditLogViewer` - Log viewing interface
- `SettingsPanel` - Configuration options

### Utilities
- `Formatters` - Currency, date, address formatting
- `Validators` - Input validation (addresses, amounts, etc.)
- `Security` - XSS prevention, input sanitization
- `Helpers` - General utility functions

## Key Features Implementation

### Real-time Updates
- WebSocket or polling for balance updates
- Transaction status monitoring
- Price data refresh intervals

### Offline Support
- Basic caching of last known state
- Queue for offline transactions
- Sync when connection restored

### Security Considerations
- Private keys never leave client-side wallet implementation
- All sensitive operations require confirmation
- Session management
- Secure handling of secrets in memory
- Protection against common web vulnerabilities

### Responsive Design
- Mobile-friendly layouts
- Touch-friendly controls
- Adaptive charts and tables

## Styling Approach
- CSS variables for theming
- Component-based styling
- Accessibility considerations (WCAG)
- Print-friendly views for important data