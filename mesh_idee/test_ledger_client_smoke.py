"""
Smoke test for LedgerClient - verifies basic functionality.
"""

from mesh_fake_ledger.client import LedgerClient, PaymentRequiredError


def main():
    print("=" * 60)
    print("LedgerClient Smoke Test")
    print("=" * 60)
    
    # Initialize client with fresh ledger
    ledger = LedgerClient(json_path="ledger_smoke_test.json")
    print(f"\n✓ Client initialized")
    print(f"  Mode: {ledger.mode}")
    
    # Ensure accounts exist
    ledger.ensure_account("alice", initial_balance=100)
    ledger.ensure_account("provider", initial_balance=0)
    print(f"\n✓ Accounts created")
    
    # Check balance
    bal = ledger.get_balance("alice")
    print(f"\n✓ Alice balance: {bal}")
    # Alice might already exist from previous runs, so just verify she has enough
    if bal < 100:
        print(f"  Warning: Alice has less than 100, crediting...")
        from mesh_fake_ledger import LedgerService, LedgerConfig
        from pathlib import Path
        svc = LedgerService(LedgerConfig(ledger_path=Path("ledger_smoke_test.json")))
        svc.credit("alice", 100 - bal, "smoke test setup")
    
    # Check can_pay
    can_pay = ledger.can_pay("alice", 10)
    print(f"✓ Alice can pay 10? {can_pay}")
    assert can_pay is True, "Alice should be able to pay 10"
    
    # Successful charge
    print(f"\n✓ Charging 10 tokens from alice to provider...")
    record = ledger.charge("alice", "provider", 10, job_id="job_test_1")
    print(f"  Transfer ID: {record['id'][:8]}...")
    
    new_bal = ledger.get_balance("alice")
    print(f"✓ Alice new balance: {new_bal}")
    assert new_bal == 90, f"Expected 90, got {new_bal}"
    
    provider_bal = ledger.get_balance("provider")
    print(f"✓ Provider balance: {provider_bal}")
    assert provider_bal == 10, f"Expected 10, got {provider_bal}"
    
    # Test PaymentRequiredError
    print(f"\n✓ Testing PaymentRequiredError with amount 10,000,000...")
    try:
        ledger.charge("alice", "provider", 10_000_000, job_id="job_test_2")
        print("✗ FAILED: Should have raised PaymentRequiredError!")
        exit(1)
    except PaymentRequiredError as e:
        print(f"✓ Caught PaymentRequiredError as expected")
        error_json = e.to_json()
        print(f"  Error JSON: {error_json}")
        assert error_json["required_tokens"] == 10_000_000
        assert error_json["current_balance"] == 90
        assert error_json["shortfall"] == 10_000_000 - 90
        assert error_json["account_id"] == "alice"
    
    print("\n" + "=" * 60)
    print("✓ ALL SMOKE TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
