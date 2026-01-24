"""
Service layer for the mesh fake ledger.

This module provides a high-level business API for ledger operations,
managing state persistence and providing convenient wrapper functions.
"""

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Optional

from mesh_fake_ledger.ledger_store import (
    LedgerState,
    TransferRecord,
    load_state,
    save_state,
    ensure_account,
    get_balance,
    can_pay,
    transfer,
    get_transfers,
    AccountNotFoundError,
    InsufficientBalanceError,
    LedgerError,
)


@dataclass
class LedgerConfig:
    """Configuration for the ledger service."""
    ledger_path: Path = Path("ledger.json")
    default_provider_account: str = "mesh_provider"
    auto_create_accounts: bool = True


class LedgerService:
    """
    High-level service for ledger operations.
    
    This service manages the ledger state, handles persistence,
    and provides thread-safe access to ledger operations.
    """
    
    def __init__(self, config: Optional[LedgerConfig] = None):
        """
        Initialize the ledger service.
        
        Args:
            config: Optional configuration (uses defaults if not provided)
        """
        self.config = config or LedgerConfig()
        self._state: LedgerState = load_state(self.config.ledger_path)
        self._lock = Lock()
        
        # Ensure default provider account exists
        if self.config.default_provider_account:
            with self._lock:
                ensure_account(self._state, self.config.default_provider_account, 0)
                self._save()
    
    def _save(self) -> None:
        """Save current state to disk (internal, assumes lock is held)."""
        save_state(self._state, self.config.ledger_path)
    
    def create_account_if_missing(
        self,
        account_id: str,
        initial_balance: int = 0
    ) -> bool:
        """
        Create an account if it doesn't exist.
        
        Args:
            account_id: Account identifier
            initial_balance: Initial balance for new accounts
            
        Returns:
            True if account was created, False if it already existed
        """
        with self._lock:
            existed = account_id in self._state["accounts"]
            ensure_account(self._state, account_id, initial_balance)
            if not existed:
                self._save()
            return not existed
    
    def get_balance(self, account_id: str) -> int:
        """
        Get account balance.
        
        Args:
            account_id: Account identifier
            
        Returns:
            Account balance
            
        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        with self._lock:
            return get_balance(self._state, account_id)
    
    def require_balance(self, payer_id: str, amount: int) -> bool:
        """
        Check if an account has sufficient balance.
        
        Args:
            payer_id: Payer account identifier
            amount: Required amount
            
        Returns:
            True if payer has sufficient balance, False otherwise
        """
        with self._lock:
            return can_pay(self._state, payer_id, amount)
    
    def charge(
        self,
        payer_id: str,
        receiver_id: str,
        amount: int,
        job_id: Optional[str] = None,
        note: Optional[str] = None
    ) -> TransferRecord:
        """
        Charge tokens from payer to receiver.
        
        Args:
            payer_id: Payer account identifier
            receiver_id: Receiver account identifier
            amount: Amount to charge
            job_id: Optional job identifier
            note: Optional note
            
        Returns:
            TransferRecord of the completed transfer
            
        Raises:
            AccountNotFoundError: If either account doesn't exist
            InsufficientBalanceError: If payer has insufficient balance
        """
        with self._lock:
            # Auto-create accounts if configured
            if self.config.auto_create_accounts:
                ensure_account(self._state, payer_id, 0)
                ensure_account(self._state, receiver_id, 0)
            
            record = transfer(self._state, payer_id, receiver_id, amount, job_id, note)
            self._save()
            return record
    
    def credit(
        self,
        account_id: str,
        amount: int,
        reason: Optional[str] = None
    ) -> TransferRecord:
        """
        Credit tokens to an account (admin/god mode).
        
        This creates tokens from a special 'system' account.
        
        Args:
            account_id: Account to credit
            amount: Amount to credit
            reason: Optional reason for the credit
            
        Returns:
            TransferRecord of the completed transfer
        """
        system_account = "system"
        
        with self._lock:
            # Ensure system account exists with unlimited balance
            if system_account not in self._state["accounts"]:
                ensure_account(self._state, system_account, 10**18)  # Effectively unlimited
            
            # Ensure target account exists
            if self.config.auto_create_accounts:
                ensure_account(self._state, account_id, 0)
            
            # Give system account enough balance if needed
            if self._state["accounts"][system_account]["balance"] < amount:
                self._state["accounts"][system_account]["balance"] = 10**18
            
            record = transfer(self._state, system_account, account_id, amount, None, reason)
            self._save()
            return record
    
    def get_transfers(
        self,
        account_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list[TransferRecord]:
        """
        Get transfer history.
        
        Args:
            account_id: Optional account to filter by
            limit: Optional limit on number of records
            
        Returns:
            List of transfer records, newest first
        """
        with self._lock:
            return get_transfers(self._state, account_id, limit)
    
    def account_exists(self, account_id: str) -> bool:
        """
        Check if an account exists.
        
        Args:
            account_id: Account identifier
            
        Returns:
            True if account exists, False otherwise
        """
        with self._lock:
            return account_id in self._state["accounts"]
    
    def list_accounts(self) -> dict[str, int]:
        """
        List all accounts and their balances.
        
        Returns:
            Dictionary mapping account IDs to balances
        """
        with self._lock:
            return {
                account_id: account["balance"]
                for account_id, account in self._state["accounts"].items()
            }
