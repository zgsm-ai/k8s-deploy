import json
from lib.cache import Cache


cache = Cache()


class ContextHelper:
    CONTEXT_REDIS_PREFIX = "agent_context:"

    @classmethod
    def _make_cache_key(cls, key):
        return f"{cls.CONTEXT_REDIS_PREFIX}{key}"

    @classmethod
    def _get_value_with_key(cls, key):
        key = cls._make_cache_key(key)
        value = cache.get(key)
        return value or {}

    @classmethod
    def get_env_context(cls, key):
        value = cls._get_value_with_key(key)
        return value or {}

    @classmethod
    def clear_env_context(cls, key):
        cache.delete(cls._make_cache_key(key))

    @classmethod
    def update_env_context(cls, key, value):
        if not isinstance(value, dict):
            err_msg = f"value must be a dict, not '{type(value)}'"
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except Exception:
                    err_msg += f", value: {value[:5]}...{value[-5:]}"
                    raise TypeError(err_msg)
            else:
                raise TypeError(err_msg)
        result_value = cls._get_value_with_key(key)
        result_value.update(value)
        cache.set(cls._make_cache_key(key), result_value)
        # 1h 后过期
        cache.expire(cls._make_cache_key(key), 3600)
