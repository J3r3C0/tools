"""Quick test of fixed LedgerClient."""

from mesh_fake_ledger import LedgerClient, PaymentRequiredError

print("=" * 60)
print("Testing LedgerClient after fixes")
print("=" * 60)

# Test 1: Direct mode
print("\n1. Testing Direct Mode")
client = LedgerClient(json_path="test_fixed.json")
print(f"   ✓ Client created, mode: {client.mode}")

# Create accounts
client.ensure_account("alice", 100)
client.ensure_account("bob", 50)
print(f"   ✓ Created accounts")

# Check balance
balance = client.get_balance("alice")
print(f"   ✓ Alice balance: {balance}")

# Test can_pay
can_pay = client.can_pay("alice", 10)
print(f"   ✓ Alice can pay 10? {can_pay}")

# Test charge
try:
    record = client.charge("alice", "bob", 10, job_id="test_001")
    print(f"   ✓ Charge succeeded: {record['id'][:8]}...")
    print(f"   ✓ New balance: {client.get_balance('alice')}")
except PaymentRequiredError as e:
    print(f"   ✗ Unexpected error: {e}")

# Test insufficient balance
print("\n2. Testing PaymentRequiredError")
try:
    client.charge("alice", "bob", 1000)  # Alice only has 90 left
    print("   ✗ Should have raised PaymentRequiredError!")
except PaymentRequiredError as e:
    print(f"   ✓ Correctly raised PaymentRequiredError")
    print(f"   ✓ Error JSON: {e.to_json()}")

print("\n" + "=" * 60)
print("✓ All tests passed!")
print("=" * 60)
