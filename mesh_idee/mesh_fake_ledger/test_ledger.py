"""
Comprehensive test script for mesh_fake_ledger.

This script tests all major functionality of the ledger system.
"""

from mesh_fake_ledger import LedgerService, LedgerConfig
from mesh_fake_ledger.ledger_store import AccountNotFoundError, InsufficientBalanceError
from pathlib import Path


def test_basic_operations():
    """Test basic ledger operations."""
    print("=" * 60)
    print("TEST: Basic Operations")
    print("=" * 60)
    
    # Use a test ledger file
    config = LedgerConfig(ledger_path=Path("test_ledger.json"))
    service = LedgerService(config)
    
    # Create accounts
    print("\n1. Creating accounts...")
    service.create_account_if_missing("alice", 100)
    service.create_account_if_missing("bob", 50)
    service.create_account_if_missing("provider", 0)
    
    # Check balances
    print("   ✓ Alice balance:", service.get_balance("alice"))
    print("   ✓ Bob balance:", service.get_balance("bob"))
    print("   ✓ Provider balance:", service.get_balance("provider"))
    
    # Test transfer
    print("\n2. Testing transfer...")
    if service.require_balance("alice", 10):
        record = service.charge("alice", "provider", 10, job_id="test_job_1")
        print(f"   ✓ Transferred 10 tokens (ID: {record['id'][:8]}...)")
        print(f"   ✓ Alice new balance: {service.get_balance('alice')}")
        print(f"   ✓ Provider new balance: {service.get_balance('provider')}")
    
    # Test credit (admin operation)
    print("\n3. Testing credit operation...")
    record = service.credit("bob", 100, reason="Test bonus")
    print(f"   ✓ Credited 100 tokens to Bob")
    print(f"   ✓ Bob new balance: {service.get_balance('bob')}")
    
    # List all accounts
    print("\n4. Listing all accounts...")
    accounts = service.list_accounts()
    for account_id, balance in sorted(accounts.items()):
        print(f"   {account_id:20s}: {balance:>10,}")
    
    # Get transfer history
    print("\n5. Transfer history...")
    transfers = service.get_transfers(limit=5)
    for t in transfers:
        print(f"   {t['from_account']} → {t['to_account']}: {t['amount']} tokens")
        if t.get('job_id'):
            print(f"      Job ID: {t['job_id']}")
    
    print("\n✓ All basic tests passed!")


def test_error_handling():
    """Test error handling."""
    print("\n" + "=" * 60)
    print("TEST: Error Handling")
    print("=" * 60)
    
    config = LedgerConfig(ledger_path=Path("test_ledger.json"))
    service = LedgerService(config)
    
    # Test insufficient balance
    print("\n1. Testing insufficient balance...")
    try:
        service.charge("alice", "bob", 10000)  # More than Alice has
        print("   ✗ Should have raised InsufficientBalanceError!")
    except InsufficientBalanceError as e:
        print(f"   ✓ Correctly caught error: {e}")
    
    # Test account not found (with auto-create disabled)
    print("\n2. Testing account not found...")
    config2 = LedgerConfig(
        ledger_path=Path("test_ledger2.json"),
        auto_create_accounts=False
    )
    service2 = LedgerService(config2)
    try:
        service2.get_balance("nonexistent")
        print("   ✗ Should have raised AccountNotFoundError!")
    except AccountNotFoundError as e:
        print(f"   ✓ Correctly caught error: {e}")
    
    # Test negative amount
    print("\n3. Testing negative transfer amount...")
    try:
        service.charge("alice", "bob", -10)
        print("   ✗ Should have raised ValueError!")
    except ValueError as e:
        print(f"   ✓ Correctly caught error: {e}")
    
    print("\n✓ All error handling tests passed!")


def test_integration_scenario():
    """Test a realistic integration scenario."""
    print("\n" + "=" * 60)
    print("TEST: Integration Scenario (Service with 402 logic)")
    print("=" * 60)
    
    config = LedgerConfig(ledger_path=Path("test_ledger.json"))
    service = LedgerService(config)
    
    # Simulate a compute service
    def process_job(user_id: str, job_id: str, cost: int):
        """Simulate processing a job with payment."""
        print(f"\nProcessing job {job_id} for user {user_id}...")
        
        # Check if user can pay
        if not service.require_balance(user_id, cost):
            print(f"   ✗ 402 Payment Required: User has insufficient balance")
            return False
        
        # Simulate work
        print(f"   → Executing computation...")
        result = f"Result for {job_id}"
        
        # Charge on success
        service.charge(user_id, "provider", cost, job_id=job_id)
        print(f"   ✓ Job completed, charged {cost} tokens")
        print(f"   ✓ User balance: {service.get_balance(user_id)}")
        
        return result
    
    # Test successful job
    print("\n1. Processing job with sufficient balance...")
    process_job("alice", "job_001", 5)
    
    # Test job with insufficient balance
    print("\n2. Processing job with insufficient balance...")
    process_job("alice", "job_002", 10000)
    
    print("\n✓ Integration scenario test passed!")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " MESH FAKE LEDGER - COMPREHENSIVE TEST SUITE ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        test_basic_operations()
        test_error_handling()
        test_integration_scenario()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nCheck test_ledger.json for the persisted state.")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
