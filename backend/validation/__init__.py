"""
Input Validation Module for OrdexWallet.

Provides validation for addresses, amounts, private keys, and other inputs.
"""

import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Validation error details."""

    field: str
    message: str
    code: str

    def __str__(self):
        return f"{self.field}: {self.message}"


@dataclass
class ValidationResult:
    """Result of validation operation."""

    valid: bool
    errors: List[ValidationError]
    value: Any = None

    @staticmethod
    def success(value: Any = None) -> "ValidationResult":
        return ValidationResult(valid=True, errors=[], value=value)

    @staticmethod
    def failure(field: str, message: str, code: str = "invalid") -> "ValidationResult":
        return ValidationResult(
            valid=False, errors=[ValidationError(field, message, code)]
        )

    @staticmethod
    def failures(errors: List[ValidationError]) -> "ValidationResult":
        return ValidationResult(valid=False, errors=errors)


class AddressValidator:
    """Validates cryptocurrency addresses."""

    BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    @classmethod
    def is_valid_base58(cls, address: str) -> bool:
        """Check if address matches Base58 pattern."""
        if not address:
            return False
        if len(address) < 26 or len(address) > 35:
            return False
        return all(c in cls.BASE58_ALPHABET for c in address)

    @classmethod
    def is_valid_ordexcoin(cls, address: str) -> ValidationResult:
        """Validate OrdexCoin (OXC) address."""
        if not address:
            return ValidationResult.failure(
                "address", "Address is required", "required"
            )

        if not cls.is_valid_base58(address):
            return ValidationResult.failure(
                "address", "Invalid Base58 address format", "format"
            )

        first_char = address[0]
        if first_char not in [
            "M",
            "N",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
        ]:
            return ValidationResult.failure(
                "address", "OrdexCoin addresses must start with M-N or P-Z", "prefix"
            )

        return ValidationResult.success(address)

    @classmethod
    def is_valid_ordexgold(cls, address: str) -> ValidationResult:
        """Validate OrdexGold (OXG) address."""
        if not address:
            return ValidationResult.failure(
                "address", "Address is required", "required"
            )

        if not cls.is_valid_base58(address):
            return ValidationResult.failure(
                "address", "Invalid Base58 address format", "format"
            )

        first_char = address[0]
        if first_char not in [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
            "m",
            "n",
            "o",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "v",
            "w",
            "x",
            "y",
            "z",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
        ]:
            return ValidationResult.failure(
                "address", "OrdexGold addresses must start with a-z or G-R", "prefix"
            )

        return ValidationResult.success(address)

    @classmethod
    def validate(cls, address: str, network: str = "ordexcoin") -> ValidationResult:
        """Validate address for specified network."""
        if network == "ordexcoin":
            return cls.is_valid_ordexcoin(address)
        elif network == "ordexgold":
            return cls.is_valid_ordexgold(address)
        else:
            return ValidationResult.failure(
                "network", f"Unknown network: {network}", "unknown_network"
            )


class AmountValidator:
    """Validates cryptocurrency amounts."""

    AMOUNT_PATTERN = r"^\d+(\.\d{1,8})?$"
    AMOUNT_REGEX = re.compile(AMOUNT_PATTERN)

    MIN_AMOUNT = 0.00000001
    MAX_AMOUNT = 2100000000000000

    @classmethod
    def is_valid(cls, amount: Any, allow_zero: bool = False) -> ValidationResult:
        """Validate amount."""
        if amount is None:
            return ValidationResult.failure("amount", "Amount is required", "required")

        try:
            amount_float = float(amount)
        except (TypeError, ValueError):
            return ValidationResult.failure(
                "amount", "Amount must be a valid number", "type"
            )

        if not cls.AMOUNT_REGEX.match(str(amount)):
            return ValidationResult.failure(
                "amount", "Amount can have maximum 8 decimal places", "precision"
            )

        if amount_float < 0:
            return ValidationResult.failure(
                "amount", "Amount must be positive", "negative"
            )

        if not allow_zero and amount_float == 0:
            return ValidationResult.failure(
                "amount", "Amount must be greater than zero", "zero"
            )

        if amount_float > cls.MAX_AMOUNT:
            return ValidationResult.failure(
                "amount", "Amount exceeds maximum allowed", "max"
            )

        return ValidationResult.success(amount_float)

    @classmethod
    def validate_fee(
        cls,
        amount: Any,
        tx_amount: Optional[float] = None,
        max_percentage: float = 10.0,
    ) -> ValidationResult:
        """Validate transaction fee."""
        result = cls.is_valid(amount, allow_zero=True)
        if not result.valid:
            return result

        fee = float(amount)

        if tx_amount is not None and tx_amount > 0:
            fee_percentage = (fee / tx_amount) * 100
            if fee_percentage > max_percentage:
                return ValidationResult.failure(
                    "fee",
                    f"Fee exceeds {max_percentage}% of transaction amount",
                    "excessive",
                )

        return ValidationResult.success(fee)


class PrivateKeyValidator:
    """Validates private keys in WIF format."""

    BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    WIF_PREFIXES = ("5", "K", "L")

    @classmethod
    def is_valid_wif(cls, private_key: str) -> ValidationResult:
        """Validate WIF format private key."""
        if not private_key:
            return ValidationResult.failure(
                "private_key", "Private key is required", "required"
            )

        if not isinstance(private_key, str):
            return ValidationResult.failure(
                "private_key", "Private key must be a string", "type"
            )

        if len(private_key) not in (51, 52):
            return ValidationResult.failure(
                "private_key",
                "Invalid WIF format. Must be 51 or 52 characters",
                "format",
            )

        if not private_key[0] in cls.WIF_PREFIXES:
            return ValidationResult.failure(
                "private_key", "WIF key must start with 5, K, or L", "prefix"
            )

        if not all(c in cls.BASE58_ALPHABET for c in private_key):
            return ValidationResult.failure(
                "private_key", "Invalid WIF format. Invalid characters", "format"
            )

        return ValidationResult.success(private_key)

        if not isinstance(private_key, str):
            return ValidationResult.failure(
                "private_key", "Private key must be a string", "type"
            )

        if cls.WIF_REGEX.match(private_key) or cls.WIF_COMPRESSED_REGEX.match(
            private_key
        ):
            return ValidationResult.success(private_key)

        return ValidationResult.failure(
            "private_key",
            "Invalid WIF format. Must be 51 or 52 Base58 characters starting with 5, K, or L",
            "format",
        )

    @classmethod
    def is_valid_hex(cls, private_key: str) -> ValidationResult:
        """Validate hex format private key."""
        if not private_key:
            return ValidationResult.failure(
                "private_key", "Private key is required", "required"
            )

        if not isinstance(private_key, str):
            return ValidationResult.failure(
                "private_key", "Private key must be a string", "type"
            )

        if not re.match(r"^[0-9a-fA-F]{64}$", private_key):
            return ValidationResult.failure(
                "private_key", "Invalid hex format. Must be 64 hex characters", "format"
            )

        return ValidationResult.success(private_key)

    @classmethod
    def validate(cls, private_key: str, format: str = "wif") -> ValidationResult:
        """Validate private key in specified format."""
        if format == "wif":
            return cls.is_valid_wif(private_key)
        elif format == "hex":
            return cls.is_valid_hex(private_key)
        else:
            return ValidationResult.failure(
                "format", f"Unknown format: {format}", "unknown_format"
            )


class TransactionValidator:
    """Validates transaction data."""

    HEX_PATTERN = r"^[0-9a-fA-F]+$"
    HEX_REGEX = re.compile(HEX_PATTERN)

    TXID_PATTERN = r"^[0-9a-fA-F]{64}$"
    TXID_REGEX = re.compile(TXID_PATTERN)

    @classmethod
    def is_valid_hex(cls, hex_string: str, min_length: int = 10) -> ValidationResult:
        """Validate hex string."""
        if not hex_string:
            return ValidationResult.failure("hex", "Hex string is required", "required")

        if not cls.HEX_REGEX.match(hex_string):
            return ValidationResult.failure("hex", "Invalid hex format", "format")

        if len(hex_string) < min_length:
            return ValidationResult.failure(
                "hex", f"Hex string too short (min {min_length} chars)", "min_length"
            )

        if len(hex_string) % 2 != 0:
            return ValidationResult.failure(
                "hex", "Hex string must have even length", "odd_length"
            )

        return ValidationResult.success(hex_string)

    @classmethod
    def is_valid_txid(cls, txid: str) -> ValidationResult:
        """Validate transaction ID."""
        if not txid:
            return ValidationResult.failure(
                "txid", "Transaction ID is required", "required"
            )

        if not cls.TXID_REGEX.match(txid):
            return ValidationResult.failure(
                "txid", "Invalid transaction ID format", "format"
            )

        return ValidationResult.success(txid)

    @classmethod
    def validate_inputs(cls, inputs: List[Dict[str, Any]]) -> ValidationResult:
        """Validate transaction inputs."""
        if not inputs:
            return ValidationResult.failure(
                "inputs", "At least one input is required", "required"
            )

        errors = []

        for i, inp in enumerate(inputs):
            if "txid" not in inp:
                errors.append(
                    ValidationError(f"inputs[{i}]", "Missing txid", "missing_txid")
                )
            elif not cls.TXID_REGEX.match(inp["txid"]):
                errors.append(
                    ValidationError(
                        f"inputs[{i}]", "Invalid txid format", "invalid_txid"
                    )
                )

            if "vout" not in inp:
                errors.append(
                    ValidationError(f"inputs[{i}]", "Missing vout", "missing_vout")
                )
            elif not isinstance(inp["vout"], int) or inp["vout"] < 0:
                errors.append(
                    ValidationError(
                        f"inputs[{i}]", "Invalid vout value", "invalid_vout"
                    )
                )

        if errors:
            return ValidationResult.failures(errors)

        return ValidationResult.success(inputs)

    @classmethod
    def validate_outputs(cls, outputs: Dict[str, float]) -> ValidationResult:
        """Validate transaction outputs."""
        if not outputs:
            return ValidationResult.failure(
                "outputs", "At least one output is required", "required"
            )

        errors = []

        for address, amount in outputs.items():
            addr_result = AddressValidator.is_valid_ordexcoin(address)
            if not addr_result.valid:
                errors.append(
                    ValidationError(
                        f"outputs[{address}]",
                        addr_result.errors[0].message,
                        "invalid_address",
                    )
                )

            amount_result = AmountValidator.is_valid(amount)
            if not amount_result.valid:
                errors.append(
                    ValidationError(
                        f"outputs[{address}]",
                        amount_result.errors[0].message,
                        "invalid_amount",
                    )
                )

        if errors:
            return ValidationResult.failures(errors)

        return ValidationResult.success(outputs)


class ConfigValidator:
    """Validates configuration values."""

    PORT_RANGE = (1, 65535)

    @classmethod
    def validate_port(cls, port: Any) -> ValidationResult:
        """Validate port number."""
        try:
            port_int = int(port)
        except (TypeError, ValueError):
            return ValidationResult.failure("port", "Port must be a number", "type")

        if port_int < cls.PORT_RANGE[0] or port_int > cls.PORT_RANGE[1]:
            return ValidationResult.failure(
                "port",
                f"Port must be between {cls.PORT_RANGE[0]} and {cls.PORT_RANGE[1]}",
                "range",
            )

        return ValidationResult.success(port_int)

    @classmethod
    def validate_host(cls, host: str) -> ValidationResult:
        """Validate hostname or IP address."""
        if not host:
            return ValidationResult.failure("host", "Host is required", "required")

        ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        hostname_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"

        if not (re.match(ipv4_pattern, host) or re.match(hostname_pattern, host)):
            return ValidationResult.failure(
                "host", "Invalid hostname or IP address", "format"
            )

        return ValidationResult.success(host)

    @classmethod
    def validate_positive_int(
        cls, value: Any, field_name: str = "value"
    ) -> ValidationResult:
        """Validate positive integer."""
        try:
            value_int = int(value)
        except (TypeError, ValueError):
            return ValidationResult.failure(field_name, "Must be an integer", "type")

        if value_int <= 0:
            return ValidationResult.failure(field_name, "Must be positive", "positive")

        return ValidationResult.success(value_int)

    @classmethod
    def validate_dbcache(cls, dbcache: int) -> ValidationResult:
        """Validate database cache size (MB)."""
        if dbcache < 16:
            return ValidationResult.failure(
                "dbcache", "Minimum dbcache is 16 MB", "min"
            )
        if dbcache > 16384:
            return ValidationResult.failure(
                "dbcache", "Maximum dbcache is 16384 MB", "max"
            )
        return ValidationResult.success(dbcache)

    @classmethod
    def validate_maxconnections(cls, connections: int) -> ValidationResult:
        """Validate max connections."""
        if connections < 0:
            return ValidationResult.failure(
                "maxconnections", "Cannot be negative", "negative"
            )
        if connections > 1000:
            return ValidationResult.failure("maxconnections", "Maximum is 1000", "max")
        return ValidationResult.success(connections)


class MessageValidator:
    """Validates message signing operations."""

    MESSAGE_MAX_LENGTH = 65536

    @classmethod
    def validate_message(cls, message: str) -> ValidationResult:
        """Validate message text."""
        if not message:
            return ValidationResult.failure(
                "message", "Message is required", "required"
            )

        if not isinstance(message, str):
            return ValidationResult.failure(
                "message", "Message must be a string", "type"
            )

        if len(message) > cls.MESSAGE_MAX_LENGTH:
            return ValidationResult.failure(
                "message",
                f"Message exceeds maximum length of {cls.MESSAGE_MAX_LENGTH} characters",
                "max_length",
            )

        return ValidationResult.success(message)

    @classmethod
    def validate_signature(cls, signature: str) -> ValidationResult:
        """Validate signature format."""
        if not signature:
            return ValidationResult.failure(
                "signature", "Signature is required", "required"
            )

        if not isinstance(signature, str):
            return ValidationResult.failure(
                "signature", "Signature must be a string", "type"
            )

        if len(signature) < 64 or len(signature) > 520:
            return ValidationResult.failure(
                "signature", "Invalid signature length", "length"
            )

        return ValidationResult.success(signature)


class ValidationService:
    """Central validation service for all input types."""

    def __init__(self):
        self.address_validator = AddressValidator()
        self.amount_validator = AmountValidator()
        self.private_key_validator = PrivateKeyValidator()
        self.transaction_validator = TransactionValidator()
        self.config_validator = ConfigValidator()
        self.message_validator = MessageValidator()

    def validate_address(
        self, address: str, network: str = "ordexcoin"
    ) -> ValidationResult:
        """Validate address for network."""
        return self.address_validator.validate(address, network)

    def validate_amount(
        self, amount: Any, allow_zero: bool = False
    ) -> ValidationResult:
        """Validate amount."""
        return self.amount_validator.is_valid(amount, allow_zero)

    def validate_fee(
        self, amount: Any, tx_amount: Optional[float] = None
    ) -> ValidationResult:
        """Validate fee."""
        return self.amount_validator.validate_fee(amount, tx_amount)

    def validate_private_key(
        self, private_key: str, format: str = "wif"
    ) -> ValidationResult:
        """Validate private key."""
        return self.private_key_validator.validate(private_key, format)

    def validate_tx_hex(self, hex_string: str) -> ValidationResult:
        """Validate transaction hex."""
        return self.transaction_validator.is_valid_hex(hex_string)

    def validate_txid(self, txid: str) -> ValidationResult:
        """Validate transaction ID."""
        return self.transaction_validator.is_valid_txid(txid)

    def validate_message(self, message: str) -> ValidationResult:
        """Validate message."""
        return self.message_validator.validate_message(message)

    def validate_signature(self, signature: str) -> ValidationResult:
        """Validate signature."""
        return self.message_validator.validate_signature(signature)

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate daemon configuration."""
        errors = []

        if "port" in config:
            result = self.config_validator.validate_port(config["port"])
            if not result.valid:
                errors.append(result.errors[0])

        if "host" in config:
            result = self.config_validator.validate_host(config["host"])
            if not result.valid:
                errors.append(result.errors[0])

        if "dbcache" in config:
            result = self.config_validator.validate_dbcache(config["dbcache"])
            if not result.valid:
                errors.append(result.errors[0])

        if "maxconnections" in config:
            result = self.config_validator.validate_maxconnections(
                config["maxconnections"]
            )
            if not result.valid:
                errors.append(result.errors[0])

        if errors:
            return ValidationResult.failures(errors)

        return ValidationResult.success(config)
