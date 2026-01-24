"""
HTTP API for the mesh fake ledger.

Provides REST endpoints for account and transfer operations using FastAPI.
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .ledger_service import LedgerService, LedgerConfig
from .ledger_store import (
    AccountNotFoundError,
    InsufficientBalanceError,
    LedgerError,
    TransferRecord,
)
from .ledger_client import PaymentRequiredError
try:
    ledger.charge(
except PaymentRequiredError as e:
    raise e.to_http_exception(
        status_code=402, detail=e.to_http_detail(HTTPException))
    def to_http_exception(self):
        from fastapi import HTTPException
        return HTTPException(status_code=402, detail=self.to_json(
            response = requests.post(
                f"{self.base_url}/accounts/{account_id}/ensure",
                json={"initial_balance": initial_balance}
            )
            response.raise_for_status()
            data = response.json()
            return bool(data.get("created", False))))
)

# Pydantic models for request/response
class EnsureAccountRequest(BaseModel):
    """Request to ensure account exists."""
    initial_balance: int = Field(default=0, ge=0)


class TransferRequest(BaseModel):
    """Request to execute a transfer."""
    from_account: str = Field(..., min_length=1)
    to_account: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0)
    job_id: Optional[str] = None
    note: Optional[str] = None


class BalanceResponse(BaseModel):
    """Response for balance query."""
    account: str
    balance: int


class TransferResponse(BaseModel):
    """Response for transfer operation."""
    ok: bool
    transfer: TransferRecord
    balances: dict[str, int]


class EnsureAccountResponse(BaseModel):
    """Response for ensure account operation."""
    account: str
    created: bool
    balance: int


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None


# Create FastAPI app
app = FastAPI(
    title="Mesh Fake Ledger API",
    description="Off-chain token ledger for compute resources",
    version="1.0.0"
)

# Initialize ledger service
# This could be configured via environment variables
_service: Optional[LedgerService] = None


def get_service() -> LedgerService:
    """Get or create the ledger service instance."""
    global _service
    if _service is None:
        config = LedgerConfig()
        # You can customize the path via environment variable
        import os
        ledger_path = os.getenv("LEDGER_PATH", "ledger.json")
        config.ledger_path = Path(ledger_path)
        _service = LedgerService(config)
    return _service


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "name": "Mesh Fake Ledger API",
        "version": "1.0.0",
        "endpoints": {
            "get_balance": "GET /accounts/{account_id}/balance",
            "ensure_account": "POST /accounts/{account_id}/ensure",
            "transfer": "POST /transfers",
            "get_transfers": "GET /transfers",
            "list_accounts": "GET /accounts"
        }
    }


@app.get("/accounts/{account_id}/balance", response_model=BalanceResponse)
def get_balance(account_id: str):
    """
    Get the balance of an account.
    
    Args:
        account_id: Account identifier
        
    Returns:
        Account balance information
        
    Raises:
        404: Account not found
    """
    service = get_service()
    
    try:
        balance = service.get_balance(account_id)
        return BalanceResponse(account=account_id, balance=balance)
    except AccountNotFoundError:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")


@app.post("/accounts/{account_id}/ensure", response_model=EnsureAccountResponse)
def ensure_account(account_id: str, request: EnsureAccountRequest):
    """
    Ensure an account exists, creating it if necessary.
    
    Args:
        account_id: Account identifier
        request: Request body with initial_balance
        
    Returns:
        Account information including whether it was created
    """
    service = get_service()
    
    try:
        created = service.create_account_if_missing(account_id, request.initial_balance)
        balance = service.get_balance(account_id)
        
        return EnsureAccountResponse(
            account=account_id,
            created=created,
            balance=balance
        )
    except LedgerError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transfers", response_model=TransferResponse)
def create_transfer(request: TransferRequest):
    """
    Execute a transfer between two accounts.
    
    Args:
        request: Transfer request with from/to accounts and amount
        
    Returns:
        Transfer record and updated balances
        
    Raises:
        404: Account not found
        400: Insufficient balance or invalid request
    """
    service = get_service()
    
    try:
        record = service.charge(
            request.from_account,
            request.to_account,
            request.amount,
            request.job_id,
            request.note
        )
        
        # Get updated balances
        from_balance = service.get_balance(request.from_account)
        to_balance = service.get_balance(request.to_account)
        
        return TransferResponse(
            ok=True,
            transfer=record,
            balances={
                request.from_account: from_balance,
                request.to_account: to_balance
            }
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LedgerError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transfers", response_model=list[TransferRecord])
def get_transfers(
    account: Optional[str] = Query(None, description="Filter by account ID"),
    limit: Optional[int] = Query(50, ge=1, le=1000, description="Number of records to return")
):
    """
    Get transfer history.
    
    Args:
        account: Optional account filter
        limit: Maximum number of records to return
        
    Returns:
        List of transfer records, newest first
    """
    service = get_service()
    
    try:
        return service.get_transfers(account, limit)
    except LedgerError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/accounts", response_model=dict[str, int])
def list_accounts():
    """
    List all accounts and their balances.
    
    Returns:
        Dictionary mapping account IDs to balances
    """
    service = get_service()
    
    try:
        return service.list_accounts()
    except LedgerError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/accounts/{account_id}/credit")
def credit_account(account_id: str, amount: int = Query(..., gt=0), reason: Optional[str] = None):
    """
    Credit tokens to an account (admin operation).
    
    Args:
        account_id: Account to credit
        amount: Amount to credit
        reason: Optional reason
        
    Returns:
        Transfer record
    """
    service = get_service()
    
    try:
        record = service.credit(account_id, amount, reason)
        balance = service.get_balance(account_id)
        
        return {
            "ok": True,
            "transfer": record,
            "new_balance": balance
        }
    except LedgerError as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
