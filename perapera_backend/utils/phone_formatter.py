import re


def normalize_phone(phone: str) -> str:
    """
    Convert any Japanese mobile format to +81 storage format.

    Accepted inputs:
        090-1234-5678   →  +819012345678
        09012345678     →  +819012345678
        +819012345678   →  +819012345678  (already normalised)
    """
    digits = re.sub(r"[\s\-]", "", phone)

    if digits.startswith("+81"):
        return digits

    if digits.startswith("0"):
        return "+81" + digits[1:]

    # Fallback: return as-is (validation catches bad formats upstream)
    return digits