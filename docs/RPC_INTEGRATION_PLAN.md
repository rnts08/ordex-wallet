# OrdexWallet RPC Integration Plan

## Overview
Secure communication between Flask backend and ordexcoind/ordexgoldd daemons via JSON-RPC.

## RPC Connection Management

### 1. Connection Pool
- Maintain separate pools for ordexcoind and ordexgoldd
- Lazy initialization of connections
- Automatic reconnection on failure
- Connection health checks
- Thread-safe access

### 2. Credential Handling
- Credentials auto-generated on first startup
- Stored in environment variables or secure config
- Never hardcoded in source
- Optionally loaded from Docker secrets or vault

### 3. RPC Client Wrapper
```python
class OrdexRPCClient:
    def __init__(self, host, port, user, password, timeout=30):
        self.host = host
        self.port = port
        self.auth = (user, password)
        self.timeout = timeout
        self.session = requests.Session()
        
    def call(self, method, *args):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": list(args),
            "id": 1
        }
        try:
            response = self.session.post(
                f"http://{self.host}:{self.port}",
                json=payload,
                auth=self.auth,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise RPCError(result["error"])
            return result["result"]
        except requests.exceptions.RequestException as e:
            raise RPCConnectionError(f"RPC connection failed: {e}")
```

## Daemon-Specific Integration

### 1. Ordexcoind (Main Network)
- Default ports: RPC 8332, P2P 8333
- Methods needed:
  - `getbalance`, `getnewaddress`, `getaddressesbyaccount`
  - `listtransactions`, `listunspent`, `createrawtransaction`
  - `signrawtransaction`, `sendrawtransaction`
  - `gettransaction`, `getblock`, `getblockcount`
  - `validateaddress`, `getinfo`

### 2. Ordexgoldd (Sidechain/Testnet)
- Configurable ports (different from mainnet)
- Similar method set as ordexcoind
- Separate balance tracking and transaction handling

## Core RPC Operations

### Wallet Operations
- **getbalance\***: Get confirmed balance
- **getnewaddress**: Generate new receiving address
- **getaddressesbyaccount\***: Get all addresses for account
- **validateaddress**: Check if address is valid and get info
- **getaccountaddress\***: Get default address for account

### Transaction Operations
- **listunspent**: Get UTXOs for funding transactions
- **createrawtransaction**: Create unsigned transaction
- **signrawtransaction**: Sign transaction with wallet keys
- **sendrawtransaction**: Broadcast signed transaction
- **gettransaction**: Get transaction details by txid
- **listtransactions**: List wallet transactions

### Blockchain Queries
- **getblockcount**: Get current block height
- **getblockhash**: Get hash of block at height
- **getblock**: Get block details
- **getrawtransaction**: Get raw transaction data
- **gettxout**: Get info about unspent transaction output

## Error Handling and Retry Logic

### 1. Error Classification
- **ConnectionError**: Network issues, daemon unreachable
- **AuthenticationError**: Invalid RPC credentials
- **RPCError**: Daemon returned error (invalid params, etc.)
- **TimeoutError**: Request timed out
- **ValidationError**: Invalid request/response format

### 2. Retry Strategy
- Exponential backoff (1s, 2s, 4s, 8s, max 30s)
- Maximum 5 attempts for transient errors
- No retry for authentication or validation errors
- Circuit breaker pattern to prevent cascading failures

### 3. Fallback Mechanisms
- Cache last known good state
- Allow read-only operations when daemon unavailable
- Queue write operations for retry
- Clear user feedback on connection status

## Security Considerations

### 1. Transport Security
- In production: Use TLS for RPC connections
- Internal network: Restrict to Docker bridge network
- Firewall rules to limit RPC port access
- Consider using UNIX sockets for local daemons

### 2. Authentication
- Strong randomly generated passwords (32+ chars)
- Username/password authentication
- Disable RPC when not needed (configure via firewall)
- Regular credential rotation option

### 3. Input Validation
- Validate all parameters before sending to daemon
- Sanitize inputs to prevent injection
- Check address formats
- Validate amounts and fees

### 4. Rate Limiting
- Limit RPC calls per second per wallet
- Queue excessive requests
- Monitor for abusive patterns
- Differentiate limits for read vs write operations

## Performance Optimization

### 1. Connection Reuse
- Keep-alive HTTP connections
- Connection pooling per daemon
- Reuse sessions for multiple calls

### 2. Batching
- Combine multiple read-only calls where possible
- Implement batch RPC calls for related data
- Cache frequent queries (address validation, balance)

### 3. Caching Strategy
- Short-term cache for balance/UTXO queries (10-30s)
- Medium cache for address info (5-10m)
- Long cache for static data (fee estimates, etc.)
- Cache invalidation on wallet changes

### 4. Async Processing
- Use threading or async for non-blocking RPC calls
- Background processing for transaction monitoring
- Event-driven updates where possible

## Monitoring and Debugging

### 1. RPC Logging
- Log RPC calls (method, params masked, timing)
- Log errors with context
- Performance metrics (call duration, success rates)
- Debug mode for detailed tracing

### 2. Health Checks
- Ping daemon with simple RPC call (getinfo)
- Monitor connection pool status
- Alert on consecutive failures
- Track daemon sync status

### 3. Console/Debug Tools
- RPC console in frontend for manual commands
- Ability to view raw requests/responses
- Testnet/faucet integration for testing
- Mock RPC mode for development

## Implementation Phases

### Phase 1: Basic Connection
- Implement RPC client with connection pooling
- Handle authentication and basic error cases
- Test with getinfo/getbalance calls

### Phase 2: Core Wallet Functions
- Address generation and validation
- Balance checking
- Simple transaction listing

### Phase 3: Transaction Handling
- UTXO selection and transaction creation
- Signing and broadcasting
- Transaction monitoring and confirmation tracking

### Phase 4: Advanced Features
- Batch operations and caching
- Robust error handling and retries
- Performance optimization
- Security hardening

### Phase 5: Monitoring and Tooling
- Health checks and logging
- RPC console implementation
- Diagnostic tools
- Performance benchmarking