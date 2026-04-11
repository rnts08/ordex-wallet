import re


def is_valid_address(address, chain="ordexcoin"):
    """
    Validate OrdexCoin (oxc1...) and OrdexGold (oxg1...) addresses.
    These are typically Bech32 strings.
    """
    if not isinstance(address, str):
        return False

    # Standard Bech32 characters: a-z, 0-9 except 'i', 'o', 'b'
    # Base regex for Bech32 part
    bech32_chars = "[023456789acdefghjklmnpqrstuvwxyz]"

    if chain == "ordexcoin":
        pattern = f"^oxc1{bech32_chars}{{38,59}}$"
    elif chain == "ordexgold":
        pattern = f"^oxg1{bech32_chars}{{38,59}}$"
    else:
        return False

    return bool(re.match(pattern, address.lower()))


def is_valid_amount(amount):
    """
    Ensure amount is a positive number with max 8 decimal places.
    """
    try:
        val = float(amount)
        if val <= 0:
            return False

        # Check decimal places
        s = str(amount)
        if "." in s:
            decimals = len(s.split(".")[1])
            if decimals > 8:
                return False

        return True
    except (ValueError, TypeError):
        return False


def sanitize_label(label, max_length=64):
    """
    Sanitize and truncate labels.
    """
    if not label:
        return ""

    # Remove any non-printable characters or potential script tags
    # Keep alphanumeric, spaces, and basic punctuation
    label = re.sub(r"[^\w\s\-\.\@\$\#\&\!]", "", str(label))

    return label[:max_length].strip()
