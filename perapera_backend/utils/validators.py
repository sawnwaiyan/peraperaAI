import re


def is_email(identifier: str) -> bool:
    """True if identifier looks like an email address."""
    return "@" in identifier


def is_phone(identifier: str) -> bool:
    """True if identifier looks like a Japanese mobile number (with or without +81)."""
    digits = re.sub(r"[\s\-+]", "", identifier)
    return digits.isdigit() and len(digits) >= 10


def detect_identifier_type(identifier: str) -> str:
    """
    Return "email" or "phone".
    Used in login so the user can type either without a separate field.
    """
    if is_email(identifier):
        return "email"
    return "phone"