from .errors import ZotlocalError


def require_positive_limit(n: int) -> int:
    if int(n) <= 0:
        raise ZotlocalError("--limit must be a positive integer")
    return int(n)
