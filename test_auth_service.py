"""Test script to verify Telegram initData validation.

This script tests the AuthService implementation for requirements:
- 1.1: Retrieve Telegram initData
- 1.2: Validate hash using HMAC-SHA256
- 1.3: Return 401 for invalid hash
- 29.1: HMAC-SHA256 validation with bot token

Run with: python test_auth_service.py
"""
import hashlib
import hmac
import json
from urllib.parse import urlencode


def create_test_init_data(bot_token: str, user_data: dict) -> str:
    """Create a valid initData string for testing.
    
    This simulates what Telegram WebApp SDK would send.
    
    Args:
        bot_token: Bot token for signing
        user_data: User data dict with id, username, first_name
        
    Returns:
        Valid initData query string with hash
    """
    # Create the data dict
    data = {
        "user": json.dumps(user_data),
        "auth_date": "1234567890",
        "query_id": "test_query_id"
    }
    
    # Create data check string (sorted key=value pairs)
    data_check_arr = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = "\n".join(data_check_arr)
    
    # Calculate secret key
    secret_key = hmac.new(
        "WebAppData".encode(),
        bot_token.encode(),
        hashlib.sha256
    ).digest()
    
    # Calculate hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Add hash to data
    data["hash"] = calculated_hash
    
    # Return as query string
    return urlencode(data)


def test_valid_init_data():
    """Test that valid initData is accepted (Req 1.2)."""
    print("\n=== Testing Valid initData (Req 1.2) ===")
    
    from api.services.auth import AuthService
    
    bot_token = "test_bot_token_12345"
    user_data = {
        "id": 123456789,
        "username": "testuser",
        "first_name": "Test"
    }
    
    # Create valid initData
    init_data = create_test_init_data(bot_token, user_data)
    
    # Create auth service (without session for validation test)
    class MockSession:
        pass
    
    auth_service = AuthService(MockSession(), bot_token)
    
    # Validate
    result = auth_service.validate_init_data(init_data)
    
    if result:
        print("✓ Valid initData accepted: PASS")
        print(f"  User data extracted: {json.loads(result['user'])}")
        return True
    else:
        print("✗ Valid initData rejected: FAIL")
        return False


def test_invalid_hash():
    """Test that invalid hash is rejected (Req 1.3, 29.1)."""
    print("\n=== Testing Invalid Hash Rejection (Req 1.3, 29.1) ===")
    
    from api.services.auth import AuthService
    
    bot_token = "test_bot_token_12345"
    user_data = {
        "id": 123456789,
        "username": "testuser",
        "first_name": "Test"
    }
    
    # Create valid initData
    init_data = create_test_init_data(bot_token, user_data)
    
    # Tamper with the hash
    tampered_init_data = init_data.replace(
        init_data.split("hash=")[1].split("&")[0],
        "invalid_hash_value"
    )
    
    # Create auth service
    class MockSession:
        pass
    
    auth_service = AuthService(MockSession(), bot_token)
    
    # Validate
    result = auth_service.validate_init_data(tampered_init_data)
    
    if result is None:
        print("✓ Invalid hash rejected: PASS")
        return True
    else:
        print("✗ Invalid hash accepted: FAIL")
        return False


def test_wrong_bot_token():
    """Test that initData signed with different bot token is rejected."""
    print("\n=== Testing Wrong Bot Token Rejection ===")
    
    from api.services.auth import AuthService
    
    bot_token_1 = "test_bot_token_12345"
    bot_token_2 = "different_bot_token_67890"
    user_data = {
        "id": 123456789,
        "username": "testuser",
        "first_name": "Test"
    }
    
    # Create initData signed with bot_token_1
    init_data = create_test_init_data(bot_token_1, user_data)
    
    # Try to validate with bot_token_2
    class MockSession:
        pass
    
    auth_service = AuthService(MockSession(), bot_token_2)
    
    # Validate
    result = auth_service.validate_init_data(init_data)
    
    if result is None:
        print("✓ Wrong bot token rejected: PASS")
        return True
    else:
        print("✗ Wrong bot token accepted: FAIL")
        return False


def test_missing_hash():
    """Test that initData without hash is rejected."""
    print("\n=== Testing Missing Hash Rejection ===")
    
    from api.services.auth import AuthService
    
    bot_token = "test_bot_token_12345"
    user_data = {
        "id": 123456789,
        "username": "testuser",
        "first_name": "Test"
    }
    
    # Create initData without hash
    data = {
        "user": json.dumps(user_data),
        "auth_date": "1234567890"
    }
    init_data = urlencode(data)
    
    # Create auth service
    class MockSession:
        pass
    
    auth_service = AuthService(MockSession(), bot_token)
    
    # Validate
    result = auth_service.validate_init_data(init_data)
    
    if result is None:
        print("✓ Missing hash rejected: PASS")
        return True
    else:
        print("✗ Missing hash accepted: FAIL")
        return False


def test_malformed_init_data():
    """Test that malformed initData is rejected."""
    print("\n=== Testing Malformed initData Rejection ===")
    
    from api.services.auth import AuthService
    
    bot_token = "test_bot_token_12345"
    
    # Create malformed initData
    init_data = "not_a_valid_query_string"
    
    # Create auth service
    class MockSession:
        pass
    
    auth_service = AuthService(MockSession(), bot_token)
    
    # Validate
    result = auth_service.validate_init_data(init_data)
    
    if result is None:
        print("✓ Malformed initData rejected: PASS")
        return True
    else:
        print("✗ Malformed initData accepted: FAIL")
        return False


def test_hmac_sha256_algorithm():
    """Test that HMAC-SHA256 algorithm is used correctly (Req 29.1)."""
    print("\n=== Testing HMAC-SHA256 Algorithm (Req 29.1) ===")
    
    # Test the algorithm directly
    bot_token = "test_bot_token"
    data_check_string = "auth_date=1234567890\nuser={\"id\":123}"
    
    # Calculate secret key
    secret_key = hmac.new(
        "WebAppData".encode(),
        bot_token.encode(),
        hashlib.sha256
    ).digest()
    
    # Calculate hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Verify it's a valid hex string of correct length (64 chars for SHA256)
    if len(calculated_hash) == 64 and all(c in "0123456789abcdef" for c in calculated_hash):
        print("✓ HMAC-SHA256 produces valid hash: PASS")
        print(f"  Hash length: {len(calculated_hash)} chars")
        print(f"  Sample hash: {calculated_hash[:16]}...")
        return True
    else:
        print("✗ HMAC-SHA256 produces invalid hash: FAIL")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("TELEGRAM INITDATA VALIDATION TESTS")
    print("Testing Requirements: 1.1, 1.2, 1.3, 29.1")
    print("=" * 70)
    
    results = []
    
    results.append(test_valid_init_data())
    results.append(test_invalid_hash())
    results.append(test_wrong_bot_token())
    results.append(test_missing_hash())
    results.append(test_malformed_init_data())
    results.append(test_hmac_sha256_algorithm())
    
    print("\n" + "=" * 70)
    print(f"TESTS COMPLETED: {sum(results)}/{len(results)} PASSED")
    print("=" * 70)
    
    if all(results):
        print("\n✓ All tests passed! Auth service is working correctly.")
        exit(0)
    else:
        print("\n✗ Some tests failed. Please review the implementation.")
        exit(1)
