"""Cache helpers."""


def cache_key(namespace: str, value: str) -> str:
    # TODO: normalize Unicode before composing persistent keys.
    return f"{namespace}:{value}"
