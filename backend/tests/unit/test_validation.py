"""
Unit tests for Input Validation Module.
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from validation import (
    ValidationService,
    AddressValidator,
    AmountValidator,
    PrivateKeyValidator,
    TransactionValidator,
    ConfigValidator,
    MessageValidator,
    ValidationResult,
)


class TestAddressValidator(unittest.TestCase):
    """Test cases for AddressValidator."""

    def test_is_valid_base58_valid(self):
        """Test valid Base58 addresses."""
        valid_addresses = [
            "M123456789abcdefghijkmnpqrstu",
            "N5W6X7Y8Z9ABCDEF1EFGH2aKLM3NPa4a",
            "PQRSTUVWXYZaefghijkmnpqrst",
        ]
        for addr in valid_addresses:
            self.assertTrue(
                AddressValidator.is_valid_base58(addr), f"Failed for {addr}"
            )

    def test_is_valid_base58_invalid(self):
        """Test invalid Base58 addresses."""
        invalid_addresses = ["", "0", "I", "O", "l", "123", "abc!@#"]
        for addr in invalid_addresses:
            self.assertFalse(AddressValidator.is_valid_base58(addr))

    def test_is_valid_ordexcoin_valid(self):
        """Test valid OrdexCoin addresses."""
        result = AddressValidator.is_valid_ordexcoin("M123456789abcdefghijkmnopqrstuvw")
        self.assertTrue(result.valid)

    def test_is_valid_ordexcoin_invalid(self):
        """Test invalid OrdexCoin addresses."""
        result = AddressValidator.is_valid_ordexcoin("")
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0].code, "required")

        result = AddressValidator.is_valid_ordexcoin("123456789abcdefghijkmnopqrstuvw")
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0].code, "prefix")

    def test_is_valid_ordexgold_valid(self):
        """Test valid OrdexGold addresses."""
        result = AddressValidator.is_valid_ordexgold("a123456789bcdefghijkmnopqrstuvw")
        self.assertTrue(result.valid)

        result = AddressValidator.is_valid_ordexgold("G123456789bcdefghijkmnopqrstuvw")
        self.assertTrue(result.valid)

    def test_is_valid_ordexgold_invalid(self):
        """Test invalid OrdexGold addresses."""
        result = AddressValidator.is_valid_ordexgold("")
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0].code, "required")


class TestAmountValidator(unittest.TestCase):
    """Test cases for AmountValidator."""

    def test_is_valid_positive_amount(self):
        """Test valid positive amounts."""
        valid_amounts = ["0.00000001", "1.0", "100.12345678", "1000"]
        for amount in valid_amounts:
            result = AmountValidator.is_valid(amount)
            self.assertTrue(result.valid, f"Failed for {amount}")

    def test_is_valid_zero(self):
        """Test zero amount validation."""
        result = AmountValidator.is_valid("0")
        self.assertFalse(result.valid)

        result = AmountValidator.is_valid("0", allow_zero=True)
        self.assertTrue(result.valid)

    def test_is_valid_negative(self):
        """Test negative amount validation."""
        result = AmountValidator.is_valid("-1.0")
        self.assertFalse(result.valid)

    def test_is_valid_excessive_decimals(self):
        """Test amount with more than 8 decimal places."""
        result = AmountValidator.is_valid("0.000000011")
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0].code, "precision")

    def test_is_valid_invalid_format(self):
        """Test invalid amount format."""
        result = AmountValidator.is_valid("abc")
        self.assertFalse(result.valid)

        result = AmountValidator.is_valid("1.2.3")
        self.assertFalse(result.valid)

    def test_validate_fee_valid(self):
        """Test valid fee."""
        result = AmountValidator.validate_fee("0.001", tx_amount=1.0)
        self.assertTrue(result.valid)

    def test_validate_fee_excessive(self):
        """Test excessive fee."""
        result = AmountValidator.validate_fee("0.5", tx_amount=1.0, max_percentage=10.0)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0].code, "excessive")


class TestPrivateKeyValidator(unittest.TestCase):
    """Test cases for PrivateKeyValidator."""

    def test_is_valid_wif_valid(self):
        """Test valid WIF keys (51 chars)."""
        valid_keys = [
            "5HueCGU8rjmpVHX2cZa174r7iRStC9C5eT5q7h4h8K5L6M7N8oP",
            "5HueCGU8rjmpVHX2cZa174r7iRStC9C5eT5q7h4h8K5L6M7N8oQA",
            "L3rN8rN9rN8rN9rN8rN9rN8rN9rN8rN9rN8rN9rN8rN9rN8rpQa",
        ]
        for key in valid_keys:
            result = PrivateKeyValidator.is_valid_wif(key)
            self.assertTrue(result.valid, f"Failed for {key}, len={len(key)}")

    def test_is_valid_wif_invalid(self):
        """Test invalid WIF keys."""
        invalid_keys = ["", "0", "123", "invalid_key_here"]
        for key in invalid_keys:
            result = PrivateKeyValidator.is_valid_wif(key)
            self.assertFalse(result.valid)

    def test_is_valid_hex_valid(self):
        """Test valid hex private key."""
        result = PrivateKeyValidator.is_valid_hex("0" * 64)
        self.assertTrue(result.valid)

        result = PrivateKeyValidator.is_valid_hex("a" * 64 + "f" * 64)
        self.assertFalse(result.valid)

    def test_is_valid_hex_invalid(self):
        """Test invalid hex private key."""
        result = PrivateKeyValidator.is_valid_hex("xyz" * 20)
        self.assertFalse(result.valid)


class TestTransactionValidator(unittest.TestCase):
    """Test cases for TransactionValidator."""

    def test_is_valid_hex_valid(self):
        """Test valid hex string."""
        result = TransactionValidator.is_valid_hex("deadbeef" * 10)
        self.assertTrue(result.valid)

    def test_is_valid_hex_invalid(self):
        """Test invalid hex string."""
        result = TransactionValidator.is_valid_hex("")
        self.assertFalse(result.valid)

        result = TransactionValidator.is_valid_hex("xyz")
        self.assertFalse(result.valid)

        result = TransactionValidator.is_valid_hex("abcdeg")
        self.assertFalse(result.valid)

    def test_is_valid_txid_valid(self):
        """Test valid transaction ID."""
        result = TransactionValidator.is_valid_txid("a" * 64)
        self.assertTrue(result.valid)

    def test_is_valid_txid_invalid(self):
        """Test invalid transaction ID."""
        result = TransactionValidator.is_valid_txid("")
        self.assertFalse(result.valid)

        result = TransactionValidator.is_valid_txid("abc" * 20)
        self.assertFalse(result.valid)

    def test_validate_inputs_valid(self):
        """Test valid inputs."""
        inputs = [{"txid": "a" * 64, "vout": 0}, {"txid": "b" * 64, "vout": 1}]
        result = TransactionValidator.validate_inputs(inputs)
        self.assertTrue(result.valid)

    def test_validate_inputs_invalid(self):
        """Test invalid inputs."""
        inputs = [{"vout": 0}, {"txid": "abc"}]
        result = TransactionValidator.validate_inputs(inputs)
        self.assertFalse(result.valid)


class TestConfigValidator(unittest.TestCase):
    """Test cases for ConfigValidator."""

    def test_validate_port_valid(self):
        """Test valid ports."""
        valid_ports = [1, 80, 443, 25173, 25466, 65535]
        for port in valid_ports:
            result = ConfigValidator.validate_port(port)
            self.assertTrue(result.valid, f"Failed for {port}")

    def test_validate_port_invalid(self):
        """Test invalid ports."""
        result = ConfigValidator.validate_port(0)
        self.assertFalse(result.valid)

        result = ConfigValidator.validate_port(65536)
        self.assertFalse(result.valid)

        result = ConfigValidator.validate_port("abc")
        self.assertFalse(result.valid)

    def test_validate_host_valid(self):
        """Test valid hosts."""
        valid_hosts = ["localhost", "127.0.0.1", "192.168.1.1", "example.com"]
        for host in valid_hosts:
            result = ConfigValidator.validate_host(host)
            self.assertTrue(result.valid, f"Failed for {host}")

    def test_validate_dbcache(self):
        """Test dbcache validation."""
        result = ConfigValidator.validate_dbcache(512)
        self.assertTrue(result.valid)

        result = ConfigValidator.validate_dbcache(10)
        self.assertFalse(result.valid)


class TestMessageValidator(unittest.TestCase):
    """Test cases for MessageValidator."""

    def test_validate_message_valid(self):
        """Test valid messages."""
        result = MessageValidator.validate_message("Test message")
        self.assertTrue(result.valid)

        result = MessageValidator.validate_message("")
        self.assertFalse(result.valid)

    def test_validate_signature_valid(self):
        """Test valid signatures."""
        result = MessageValidator.validate_signature(
            "H6+nPWu7CGCwVaBvvK3+y6Y7+1V+5w+V9q3J+r5P5mG9kYJ8r2mQd6eN5tU3sV1wX4yZ0aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4"
        )
        self.assertTrue(result.valid)


class TestValidationService(unittest.TestCase):
    """Test cases for ValidationService."""

    def setUp(self):
        self.service = ValidationService()

    def test_validate_address_ordexcoin(self):
        result = self.service.validate_address(
            "M123456789abcdefghijkmnopqrstuvw", "ordexcoin"
        )
        self.assertTrue(result.valid)

    def test_validate_address_ordexgold(self):
        result = self.service.validate_address(
            "a123456789bcdefghijkmnopqrstuvw", "ordexgold"
        )
        self.assertTrue(result.valid)

    def test_validate_amount(self):
        result = self.service.validate_amount("1.0")
        self.assertTrue(result.valid)

    def test_validate_private_key_wif(self):
        result = self.service.validate_private_key(
            "5HueCGU8rjmpVHX2cZa174r7iRStC9C5eT5q7h4h8K5L6M7N8oP", "wif"
        )
        self.assertTrue(result.valid)

    def test_validate_config(self):
        config = {"port": 25173, "dbcache": 512, "maxconnections": 16}
        result = self.service.validate_config(config)
        self.assertTrue(result.valid)


class TestValidationResult(unittest.TestCase):
    """Test cases for ValidationResult."""

    def test_success(self):
        result = ValidationResult.success("test_value")
        self.assertTrue(result.valid)
        self.assertEqual(result.value, "test_value")

    def test_failure(self):
        result = ValidationResult.failure("field", "Error message", "error_code")
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0].field, "field")


if __name__ == "__main__":
    unittest.main()
