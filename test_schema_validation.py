"""Test script to verify Pydantic schema validation rules."""
from decimal import Decimal
from api.schemas import (
    SellerApplicationRequest,
    LotCreateRequest,
    LotUpdateRequest,
    CreateReviewRequest,
    WithdrawalRequest,
)


def test_shop_name_validation():
    """Test requirement 3.6: Shop name 3-120 characters."""
    print("\n=== Testing Shop Name Validation (Req 3.6) ===")
    
    # Valid shop name
    try:
        valid = SellerApplicationRequest(
            shop_name="My Game Shop",
            description="A great shop"
        )
        print("✓ Valid shop name (11 chars): PASS")
    except Exception as e:
        print(f"✗ Valid shop name: FAIL - {e}")
    
    # Too short (2 chars)
    try:
        invalid = SellerApplicationRequest(
            shop_name="AB",
            description="A great shop"
        )
        print("✗ Shop name too short (2 chars): FAIL - Should have raised error")
    except Exception as e:
        print(f"✓ Shop name too short (2 chars): PASS - {type(e).__name__}")
    
    # Too long (121 chars)
    try:
        invalid = SellerApplicationRequest(
            shop_name="A" * 121,
            description="A great shop"
        )
        print("✗ Shop name too long (121 chars): FAIL - Should have raised error")
    except Exception as e:
        print(f"✓ Shop name too long (121 chars): PASS - {type(e).__name__}")
    
    # Exactly 3 chars (minimum)
    try:
        valid = SellerApplicationRequest(
            shop_name="ABC",
            description="A great shop"
        )
        print("✓ Shop name minimum length (3 chars): PASS")
    except Exception as e:
        print(f"✗ Shop name minimum length: FAIL - {e}")
    
    # Exactly 120 chars (maximum)
    try:
        valid = SellerApplicationRequest(
            shop_name="A" * 120,
            description="A great shop"
        )
        print("✓ Shop name maximum length (120 chars): PASS")
    except Exception as e:
        print(f"✗ Shop name maximum length: FAIL - {e}")


def test_lot_title_validation():
    """Test requirement 5.9: Lot title 3-255 characters."""
    print("\n=== Testing Lot Title Validation (Req 5.9) ===")
    
    # Valid title
    try:
        valid = LotCreateRequest(
            title="Fortnite V-Bucks",
            description="1000 V-Bucks",
            price=Decimal("99.99"),
            game_id=1,
            category_id=1,
            product_id=1,
            delivery_type="auto"
        )
        print("✓ Valid lot title (16 chars): PASS")
    except Exception as e:
        print(f"✗ Valid lot title: FAIL - {e}")
    
    # Too short (2 chars)
    try:
        invalid = LotCreateRequest(
            title="AB",
            description="1000 V-Bucks",
            price=Decimal("99.99"),
            game_id=1,
            category_id=1,
            product_id=1,
            delivery_type="auto"
        )
        print("✗ Lot title too short (2 chars): FAIL - Should have raised error")
    except Exception as e:
        print(f"✓ Lot title too short (2 chars): PASS - {type(e).__name__}")
    
    # Too long (256 chars)
    try:
        invalid = LotCreateRequest(
            title="A" * 256,
            description="1000 V-Bucks",
            price=Decimal("99.99"),
            game_id=1,
            category_id=1,
            product_id=1,
            delivery_type="auto"
        )
        print("✗ Lot title too long (256 chars): FAIL - Should have raised error")
    except Exception as e:
        print(f"✓ Lot title too long (256 chars): PASS - {type(e).__name__}")
    
    # Exactly 255 chars (maximum)
    try:
        valid = LotCreateRequest(
            title="A" * 255,
            description="1000 V-Bucks",
            price=Decimal("99.99"),
            game_id=1,
            category_id=1,
            product_id=1,
            delivery_type="auto"
        )
        print("✓ Lot title maximum length (255 chars): PASS")
    except Exception as e:
        print(f"✗ Lot title maximum length: FAIL - {e}")


def test_price_validation():
    """Test requirement 5.10: Price positive with 2 decimal places."""
    print("\n=== Testing Price Validation (Req 5.10) ===")
    
    # Valid price with 2 decimals
    try:
        valid = LotCreateRequest(
            title="Valid Product",
            description="Description",
            price=Decimal("99.99"),
            game_id=1,
            category_id=1,
            product_id=1,
            delivery_type="auto"
        )
        print(f"✓ Valid price (99.99): PASS - Stored as {valid.price}")
    except Exception as e:
        print(f"✗ Valid price: FAIL - {e}")
    
    # Price with 3 decimals (should be rounded)
    try:
        valid = LotCreateRequest(
            title="Valid Product",
            description="Description",
            price=Decimal("99.999"),
            game_id=1,
            category_id=1,
            product_id=1,
            delivery_type="auto"
        )
        print(f"✓ Price with 3 decimals (99.999): PASS - Rounded to {valid.price}")
        if valid.price == Decimal("100.00"):
            print("  ✓ Correctly rounded to 2 decimal places")
        else:
            print(f"  ✗ Unexpected rounding result: {valid.price}")
    except Exception as e:
        print(f"✗ Price with 3 decimals: FAIL - {e}")
    
    # Negative price
    try:
        invalid = LotCreateRequest(
            title="Valid Product",
            description="Description",
            price=Decimal("-10.00"),
            game_id=1,
            category_id=1,
            product_id=1,
            delivery_type="auto"
        )
        print("✗ Negative price: FAIL - Should have raised error")
    except Exception as e:
        print(f"✓ Negative price: PASS - {type(e).__name__}")
    
    # Zero price
    try:
        invalid = LotCreateRequest(
            title="Valid Product",
            description="Description",
            price=Decimal("0.00"),
            game_id=1,
            category_id=1,
            product_id=1,
            delivery_type="auto"
        )
        print("✗ Zero price: FAIL - Should have raised error")
    except Exception as e:
        print(f"✓ Zero price: PASS - {type(e).__name__}")
    
    # Very small positive price
    try:
        valid = LotCreateRequest(
            title="Valid Product",
            description="Description",
            price=Decimal("0.01"),
            game_id=1,
            category_id=1,
            product_id=1,
            delivery_type="auto"
        )
        print(f"✓ Minimum positive price (0.01): PASS - Stored as {valid.price}")
    except Exception as e:
        print(f"✗ Minimum positive price: FAIL - {e}")


def test_rating_validation():
    """Test requirement 11.10: Rating 1-5 integer."""
    print("\n=== Testing Rating Validation (Req 11.10) ===")
    
    # Valid ratings
    for rating in [1, 2, 3, 4, 5]:
        try:
            valid = CreateReviewRequest(
                rating=rating,
                text="Great product!"
            )
            print(f"✓ Valid rating ({rating}): PASS")
        except Exception as e:
            print(f"✗ Valid rating ({rating}): FAIL - {e}")
    
    # Rating too low (0)
    try:
        invalid = CreateReviewRequest(
            rating=0,
            text="Great product!"
        )
        print("✗ Rating too low (0): FAIL - Should have raised error")
    except Exception as e:
        print(f"✓ Rating too low (0): PASS - {type(e).__name__}")
    
    # Rating too high (6)
    try:
        invalid = CreateReviewRequest(
            rating=6,
            text="Great product!"
        )
        print("✗ Rating too high (6): FAIL - Should have raised error")
    except Exception as e:
        print(f"✓ Rating too high (6): PASS - {type(e).__name__}")


def test_review_text_validation():
    """Test requirement 11.10: Review text max 2000 characters."""
    print("\n=== Testing Review Text Validation (Req 11.10) ===")
    
    # Valid review text
    try:
        valid = CreateReviewRequest(
            rating=5,
            text="Great product! " * 50  # 800 chars
        )
        print(f"✓ Valid review text (800 chars): PASS")
    except Exception as e:
        print(f"✗ Valid review text: FAIL - {e}")
    
    # Exactly 2000 chars
    try:
        valid = CreateReviewRequest(
            rating=5,
            text="A" * 2000
        )
        print(f"✓ Review text maximum length (2000 chars): PASS")
    except Exception as e:
        print(f"✗ Review text maximum length: FAIL - {e}")
    
    # Too long (2001 chars)
    try:
        invalid = CreateReviewRequest(
            rating=5,
            text="A" * 2001
        )
        print("✗ Review text too long (2001 chars): FAIL - Should have raised error")
    except Exception as e:
        print(f"✓ Review text too long (2001 chars): PASS - {type(e).__name__}")
    
    # No text (optional)
    try:
        valid = CreateReviewRequest(
            rating=5,
            text=None
        )
        print(f"✓ Review without text (optional): PASS")
    except Exception as e:
        print(f"✗ Review without text: FAIL - {e}")


def test_withdrawal_amount_validation():
    """Test withdrawal amount validation (2 decimal places)."""
    print("\n=== Testing Withdrawal Amount Validation ===")
    
    # Valid amount
    try:
        valid = WithdrawalRequest(
            amount=Decimal("100.00"),
            payment_method="card",
            payment_details="1234-5678-9012-3456"
        )
        print(f"✓ Valid withdrawal amount (100.00): PASS - Stored as {valid.amount}")
    except Exception as e:
        print(f"✗ Valid withdrawal amount: FAIL - {e}")
    
    # Amount with 3 decimals (should be rounded)
    try:
        valid = WithdrawalRequest(
            amount=Decimal("100.555"),
            payment_method="card",
            payment_details="1234-5678-9012-3456"
        )
        print(f"✓ Amount with 3 decimals (100.555): PASS - Rounded to {valid.amount}")
    except Exception as e:
        print(f"✗ Amount with 3 decimals: FAIL - {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("PYDANTIC SCHEMA VALIDATION TESTS")
    print("Testing Requirements: 3.6, 5.9, 5.10, 11.10")
    print("=" * 70)
    
    test_shop_name_validation()
    test_lot_title_validation()
    test_price_validation()
    test_rating_validation()
    test_review_text_validation()
    test_withdrawal_amount_validation()
    
    print("\n" + "=" * 70)
    print("VALIDATION TESTS COMPLETED")
    print("=" * 70)
