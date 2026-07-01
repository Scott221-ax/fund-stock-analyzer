"""简单内存缓存（带 TTL 过期）"""
import time

_store: dict[str, dict] = {}


def get(key: str) -> object | None:
    entry = _store.get(key)
    if entry is None:
        return None
    if time.time() > entry["expires"]:
        del _store[key]
        return None
    return entry["data"]


def set(key: str, data: object, ttl_seconds: int = 300) -> None:
    _store[key] = {"data": data, "expires": time.time() + ttl_seconds}


def clear(pattern: str = "") -> int:
    """清除所有 key，或匹配 pattern 的 key"""
    keys = [k for k in _store if pattern in k] if pattern else list(_store)
    for k in keys:
        _store.pop(k, None)
    return len(keys)


def size() -> int:
    return len(_store)
