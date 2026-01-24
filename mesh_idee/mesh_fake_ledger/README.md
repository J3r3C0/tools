# Mesh Fake Ledger

A lightweight off-chain token ledger for compute resources in a mesh network.

## Overview

Mesh Fake Ledger is a simple, deterministic token accounting system that:

- ✅ Runs entirely locally (no blockchain, no consensus)
- ✅ Maintains account balances and transfer history
- ✅ Provides JSON persistence for easy inspection
- ✅ Offers CLI, Python API, and HTTP API interfaces
- ✅ Enables services to implement 402 Payment Required logic

This is "fake" in the sense that there's no real cryptography or distributed consensus—just clean, reliable token counting with JSON storage.

## Installation

```bash
cd c:\mesh_idee\mesh_fake_ledger
pip install -r requirements.txt
```

## Quick Start

### CLI Usage

```bash
# Create accounts
python -m mesh_fake_ledger create-account alice --balance 100
python -m mesh_fake_ledger create-account provider --balance 0

# Check balance
python -m mesh_fake_ledger balance alice

# Transfer tokens
python -m mesh_fake_ledger transfer alice provider 10 --job-id job_123

# View history
python -m mesh_fake_ledger history --limit 10
python -m mesh_fake_ledger history --account alice --limit 5

# List all accounts
python -m mesh_fake_ledger list-accounts

# Credit tokens (admin operation)
python -m mesh_fake_ledger credit alice 50 --reason "Initial grant"
```

### Python API Usage

```python
from mesh_fake_ledger import LedgerService, LedgerConfig

# Initialize service
service = LedgerService()

# Create accounts
service.create_account_if_missing("alice", initial_balance=100)
service.create_account_if_missing("provider", initial_balance=0)

# Check if payment is possible
if service.require_balance("alice", 10):
    # Charge tokens
    record = service.charge(
        payer_id="alice",
        receiver_id="provider",
        amount=10,
        job_id="job_123"
    )
    print(f"Transfer completed: {record['id']}")
else:
    print("Insufficient balance!")

# Get balance
balance = service.get_balance("alice")
print(f"Alice's balance: {balance}")

# View transfer history
transfers = service.get_transfers(account_id="alice", limit=10)
for t in transfers:
    print(f"{t['from_account']} → {t['to_account']}: {t['amount']}")
```

### LedgerClient Usage (Recommended)

The `LedgerClient` provides a unified interface that works in both local and distributed modes:

```python
from mesh_fake_ledger import LedgerClient, PaymentRequiredError

# Local mode - direct JSON access (same process)
ledger = LedgerClient(json_path="ledger.json")

# OR Remote mode - HTTP API (distributed services)
# ledger = LedgerClient(base_url="http://ledger-api:8000")

# Usage is identical regardless of mode
ledger.ensure_account("user1", initial_balance=100)
ledger.ensure_account("provider", initial_balance=0)

# Simple payment check and charge
if ledger.can_pay("user1", 10):
    record = ledger.charge("user1", "provider", 10, job_id="job_123")
    print(f"Charged successfully: {record['id']}")
```

#### Integration in Services

Here's how to use `LedgerClient` in a FastAPI service with proper 402 handling:

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from mesh_fake_ledger import LedgerClient, PaymentRequiredError

app = FastAPI()
ledger = LedgerClient(json_path="ledger.json")

# Handle PaymentRequiredError → HTTP 402
@app.exception_handler(PaymentRequiredError)
async def payment_handler(request: Request, exc: PaymentRequiredError):
    return JSONResponse(
        status_code=402,
        content=exc.to_json()  # Includes required_tokens, current_balance, etc.
    )

@app.post("/scan")
def run_scan_job(job: ScanJob, payer: str, provider: str):
    # Estimate cost
    cost_tokens = estimate_cost(job)
    
    # Check and charge (raises PaymentRequiredError if insufficient)
    if not ledger.can_pay(payer, cost_tokens):
        raise PaymentRequiredError(
            required=cost_tokens,
            balance=ledger.get_balance(payer),
            account_id=payer
        )
    
    # Charge tokens
    ledger.charge(payer, provider, cost_tokens, job_id=job.id)
    
    # Execute work
    results = execute_scan(job)
    return results
```

See [example_service.py](file:///c:/mesh_idee/mesh_fake_ledger/example_service.py) for a complete working example.

```

### HTTP API Usage

Start the API server:

```bash
python -m uvicorn mesh_fake_ledger.api:app --host 0.0.0.0 --port 8000
```

Or use the shorthand:
```bash
cd c:\mesh_idee\mesh_fake_ledger
python api.py
```

#### Example Requests

**Get account balance:**
```bash
curl http://localhost:8000/accounts/alice/balance
```

**Create/ensure account:**
```bash
curl -X POST http://localhost:8000/accounts/bob/ensure \
  -H "Content-Type: application/json" \
  -d '{"initial_balance": 50}'
```

**Execute transfer:**
```bash
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "from_account": "alice",
    "to_account": "provider",
    "amount": 10,
    "job_id": "job_123"
  }'
```

**Get transfer history:**
```bash
# All transfers
curl http://localhost:8000/transfers?limit=20

# Transfers for specific account
curl http://localhost:8000/transfers?account=alice&limit=10
```

**List all accounts:**
```bash
curl http://localhost:8000/accounts
```

## Architecture

### Components

1. **`ledger_store.py`** - Core ledger logic
   - State management with JSON persistence
   - Account and transfer operations
   - Validation and error handling

2. **`ledger_service.py`** - Business logic layer
   - High-level API wrapper
   - Thread-safe operations
   - Auto-save on mutations

3. **`cli.py`** - Command-line interface
   - Account management commands
   - Transfer operations
   - History queries

4. **`api.py`** - HTTP REST API
   - FastAPI-based endpoints
   - JSON request/response
   - Standard HTTP error codes

### Data Model

The ledger state is stored as JSON:

```json
{
  "accounts": {
    "alice": {
      "balance": 90,
      "created_at": "2025-12-07T04:20:00Z",
      "meta": {}
    },
    "provider": {
      "balance": 10,
      "created_at": "2025-12-07T04:20:00Z",
      "meta": {}
    }
  },
  "transfers": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2025-12-07T04:21:00Z",
      "from_account": "alice",
      "to_account": "provider",
      "amount": 10,
      "job_id": "job_123",
      "note": null
    }
  ]
}
```

## Integration Guide

### Implementing 402 Payment Required

The ledger itself doesn't return 402 responses—that's the job of your service. Here's how to integrate:

```python
from fastapi import FastAPI, HTTPException
from mesh_fake_ledger import LedgerService

app = FastAPI()
ledger = LedgerService()

@app.post("/compute/run")
def run_computation(request: ComputeRequest, user_id: str):
    # Define cost
    cost = calculate_cost(request)
    
    # Check if user can pay
    if not ledger.require_balance(user_id, cost):
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient balance. Required: {cost}"
        )
    
    # Execute computation
    result = execute_compute_job(request)
    
    # Charge tokens on success
    ledger.charge(
        payer_id=user_id,
        receiver_id="mesh_provider",
        amount=cost,
        job_id=request.job_id
    )
    
    return {"result": result, "charged": cost}
```

### Best Practices

1. **Check before charging**: Always use `require_balance()` before starting work
2. **Charge after completion**: Only call `charge()` after successful work
3. **Use job IDs**: Always pass `job_id` for traceability
4. **Handle errors**: Catch `InsufficientBalanceError` and `AccountNotFoundError`
5. **Inspect ledger**: Regularly check `ledger.json` for debugging

## Configuration

The ledger can be configured via `LedgerConfig`:

```python
from pathlib import Path
from mesh_fake_ledger import LedgerService, LedgerConfig

config = LedgerConfig(
    ledger_path=Path("custom_ledger.json"),
    default_provider_account="my_provider",
    auto_create_accounts=True  # Auto-create accounts on transfer
)

service = LedgerService(config)
```

For the HTTP API, set environment variables:

```bash
export LEDGER_PATH=/path/to/ledger.json
python -m uvicorn mesh_fake_ledger.api:app
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `create-account <id> [--balance N]` | Create a new account |
| `balance <id>` | Get account balance |
| `transfer <from> <to> <amount> [--job-id ID]` | Transfer tokens |
| `history [--account ID] [--limit N]` | Show transfer history |
| `list-accounts` | List all accounts |
| `credit <id> <amount> [--reason TEXT]` | Credit tokens (admin) |

All commands accept `--ledger <path>` to use a custom ledger file.

## Testing

### Manual CLI Testing

```bash
# Setup
python -m mesh_fake_ledger create-account alice --balance 100
python -m mesh_fake_ledger create-account bob --balance 50
python -m mesh_fake_ledger create-account provider --balance 0

# Transfers
python -m mesh_fake_ledger transfer alice provider 10
python -m mesh_fake_ledger transfer bob provider 5

# Verify
python -m mesh_fake_ledger list-accounts
python -m mesh_fake_ledger history

# Test error case
python -m mesh_fake_ledger transfer alice provider 1000  # Should fail
```

### API Testing with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Ensure accounts
requests.post(f"{BASE_URL}/accounts/alice/ensure", json={"initial_balance": 100})
requests.post(f"{BASE_URL}/accounts/provider/ensure", json={"initial_balance": 0})

# Transfer
response = requests.post(f"{BASE_URL}/transfers", json={
    "from_account": "alice",
    "to_account": "provider",
    "amount": 10,
    "job_id": "test_job"
})
print(response.json())

# Check balance
response = requests.get(f"{BASE_URL}/accounts/alice/balance")
print(response.json())
```

## License

This is a utility component for the mesh project. Use freely within your mesh infrastructure.

## Future Enhancements

Potential features for future versions:

- **Rate limiting**: Per-account transfer rate limits
- **Quotas**: Daily/monthly spending limits
- **Webhooks**: Notifications on balance changes
- **Audit log**: Immutable append-only transfer log
- **Multi-currency**: Support different token types
- **Refunds**: Reversal operations for failed jobs

## Support

For questions or issues, refer to the main mesh project documentation.
