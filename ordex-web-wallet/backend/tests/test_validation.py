import pytest
from ordex_web_wallet.utils.validation import is_valid_address, is_valid_amount, sanitize_label

def test_address_validation():
    # Valid OXC address
    assert is_valid_address("oxc1q54gunym97g4k0dzazql5jesnuhwux20n7tr4vy", "ordexcoin") == True
    # Valid OXG address
    assert is_valid_address("oxg1q54gunym97g4k0dzazql5jesnuhwux20n7tr4vy", "ordexgold") == True
    # Invalid prefix
    assert is_valid_address("ltc1q54gunym97g4k0dzazql5jesnuhwux20n7tr4vy", "ordexcoin") == False
    # Swapped chain
    assert is_valid_address("oxc1q54gunym97g4k0dzazql5jesnuhwux20n7tr4vy", "ordexgold") == False
    # Malformed Bech32 chars (contains 'o', which is not allowed in Bech32 except as prefix)
    assert is_valid_address("oxc1q54gunyo97g4k0dzazql5jesnuhwux20n7tr4vy", "ordexcoin") == False

def test_amount_validation():
    assert is_valid_amount("1.2345") == True
    assert is_valid_amount(100) == True
    assert is_valid_amount("0") == False
    assert is_valid_amount("-1.5") == False
    assert is_valid_amount("1.12345678") == True
    assert is_valid_amount("1.123456789") == False
    assert is_valid_amount("abc") == False

def test_label_sanitization():
    assert sanitize_label("My Wallet") == "My Wallet"
    assert sanitize_label("<script>alert(1)</script>") == "scriptalert1script"
    assert sanitize_label("A" * 100) == "A" * 64
    assert sanitize_label("   Clean Me   ") == "Clean Me"
