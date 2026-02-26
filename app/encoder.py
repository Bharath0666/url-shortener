"""
Base62 Encoder / Decoder

Converts a unique auto-increment integer ID into a short alphanumeric code.
62 characters  →  up to 56+ billion unique codes with 6 characters.
O(1) encode / decode complexity.  Collision-free by design.
"""

CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(CHARSET)  # 62


def base62_encode(num: int) -> str:
    """Encode a positive integer to a Base62 string."""
    if num < 0:
        raise ValueError("Only non-negative integers are supported")
    if num == 0:
        return CHARSET[0]

    chars = []
    while num:
        num, remainder = divmod(num, BASE)
        chars.append(CHARSET[remainder])
    return "".join(reversed(chars))


def base62_decode(code: str) -> int:
    """Decode a Base62 string back to an integer."""
    num = 0
    for char in code:
        idx = CHARSET.index(char)
        num = num * BASE + idx
    return num
