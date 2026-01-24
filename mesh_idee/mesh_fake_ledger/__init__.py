"""
Mesh Fake Ledger - Lightweight off-chain token ledger.

This package provides a simple token accounting system for compute resources
in a mesh network. It includes JSON persistence, account management, and
transfer operations.

Example usage:
    from mesh_fake_ledger import LedgerService, LedgerConfig
    
    # Create service
    service = LedgerService()
    
    # Create accounts
    service.create_account_if_missing("alice", 100)
    service.create_account_if_missing("provider", 0)
    
    # Check and charge
    if service.require_balance("alice", 10):
        service.charge("alice", "provider", 10, job_id="job_123")
"""

from .ledger_service import LedgerService, LedgerConfig
from .ledger_store import (
    LedgerError,
    AccountNotFoundError,
    InsufficientBalanceError,
    TransferRecord,
    LedgerState,
)
from .client import LedgerClient, PaymentRequiredError

__version__ = "1.0.0"

__all__ = [
    "LedgerService",
    "LedgerConfig",
    "LedgerClient",
    "PaymentRequiredError",
    "LedgerError",
    "AccountNotFoundError",
    "InsufficientBalanceError",
    "TransferRecord",
    "LedgerState",
]
