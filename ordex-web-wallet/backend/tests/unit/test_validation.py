import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAddressValidation:
    """Test address validation for OrdexCoin and OrdexGold."""

    def test_valid_ordexcoin_address(self):
        from ordex_web_wallet.utils.validation import is_valid_address

        valid_addresses = [
            "oxc1q3psft0hvlslddyp8ktr3s737req7q8hrl0rkly",
            "oxc1" + "a" * 38,
            "oxc1" + "q" * 59,
        ]

        for addr in valid_addresses:
            assert is_valid_address(addr, "ordexcoin") is True, f"Failed for {addr}"

    def test_invalid_ordexcoin_address(self):
        from ordex_web_wallet.utils.validation import is_valid_address

        invalid_addresses = [
            "oxc1",
            "oxc1a",
            "oxg1q3psft0hvlslddyp8ktr3s737req7q8hrl0rkly",
            "",
            "invalid",
            "OXC1Q3PSFT0HVL",
            "bc1qkmzc6d49fl0edyeynezwlrfqv486nmk6p5pmta",
        ]

        for addr in invalid_addresses:
            assert is_valid_address(addr, "ordexcoin") is False, (
                f"Should have failed for {addr}"
            )

    def test_valid_ordexgold_address(self):
        from ordex_web_wallet.utils.validation import is_valid_address

        valid_addresses = [
            "oxg1q34apjkn2yc6rsvuua98432ctqdrjh9hdkhpx0t",
            "oxg1" + "a" * 38,
            "oxg1" + "q" * 59,
        ]

        for addr in valid_addresses:
            assert is_valid_address(addr, "ordexgold") is True, f"Failed for {addr}"

    def test_invalid_ordexgold_address(self):
        from ordex_web_wallet.utils.validation import is_valid_address

        invalid_addresses = [
            "oxg1",
            "oxg1a",
            "oxc1q34apjkn2yc6rsvuua98432ctqdrjh9hdkhpx0t",
        ]

        for addr in invalid_addresses:
            assert is_valid_address(addr, "ordexgold") is False, (
                f"Should have failed for {addr}"
            )

    def test_invalid_chain_returns_false(self):
        from ordex_web_wallet.utils.validation import is_valid_address

        assert is_valid_address("oxc1abc", "bitcoin") is False
        assert is_valid_address("oxc1abc", "ethereum") is False
        assert is_valid_address("oxc1abc", "") is False

    def test_non_string_returns_false(self):
        from ordex_web_wallet.utils.validation import is_valid_address

        assert is_valid_address(None, "ordexcoin") is False
        assert is_valid_address(123, "ordexcoin") is False
        assert is_valid_address(["oxc1abc"], "ordexcoin") is False


class TestAmountValidation:
    """Test amount validation."""

    def test_valid_amounts(self):
        from ordex_web_wallet.utils.validation import is_valid_amount

        valid_amounts = ["0.00000001", "1", "100.12345678", "0.1", "999999999.99999999"]

        for amount in valid_amounts:
            assert is_valid_amount(amount) is True, f"Failed for {amount}"

    def test_invalid_amounts(self):
        from ordex_web_wallet.utils.validation import is_valid_amount

        invalid_amounts = ["0", "-1", "-0.00000001", "0.000000001", "", "abc", None]

        for amount in invalid_amounts:
            assert is_valid_amount(amount) is False, f"Should have failed for {amount}"


class TestLabelSanitization:
    """Test label sanitization."""

    def test_sanitize_label_basic(self):
        from ordex_web_wallet.utils.validation import sanitize_label

        assert sanitize_label("test") == "test"
        assert sanitize_label("Test Label") == "Test Label"
        assert sanitize_label("Test@Label") == "Test@Label"

    def test_sanitize_label_removes_special_chars(self):
        from ordex_web_wallet.utils.validation import sanitize_label

        result = sanitize_label("Test<script>alert('xss')</script>Label")
        assert "<script>" not in result
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_label_truncates(self):
        from ordex_web_wallet.utils.validation import sanitize_label

        long_label = "a" * 100
        result = sanitize_label(long_label)

        assert len(result) <= 64

    def test_sanitize_label_empty_input(self):
        from ordex_web_wallet.utils.validation import sanitize_label

        assert sanitize_label("") == ""
        assert sanitize_label(None) == ""


class TestAddressValidationEdgeCases:
    """Test edge cases in address validation."""

    def test_case_insensitive(self):
        from ordex_web_wallet.utils.validation import is_valid_address

        lowercase = "oxc1q3psft0hvlslddyp8ktr3s737req7q8hrl0rkly"
        uppercase = "OXC1Q3PSFT0HVLSDDYP8KTR3S737REQ7Q8HRL0RKLY"
        mixed = "OxC1Q3pSFT0hVlsLDdYp8kTR3S737reQ7q8hrl0RkLy"

        assert is_valid_address(lowercase, "ordexcoin") is True
        assert is_valid_address(uppercase, "ordexcoin") is True
        assert is_valid_address(mixed, "ordexcoin") is True

    def test_excluded_bech32_chars(self):
        from ordex_web_wallet.utils.validation import is_valid_address

        invalid_with_excluded = "oxc1qip8ktr3s737req7q8hrl0rkly"

        assert is_valid_address(invalid_with_excluded, "ordexcoin") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
