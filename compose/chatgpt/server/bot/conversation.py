import uuid


CONVERSATION_CACHE_PREFIX_KEY = "conversation:"


def get_cache_key(app_conversation_id):
    return ":".join([CONVERSATION_CACHE_PREFIX_KEY, str(app_conversation_id)])


def get_conversation(redis, app_conversation_id):
    """
    return: conversation_id, parent_id
    """
    cache_key = get_cache_key(app_conversation_id)
    cache_result = redis.get(cache_key)
    if not cache_result:
        return None, str(uuid.uuid4())
    else:
        split = cache_result.split(":")
        conversation_id = split[0]
        parent_id = split[1]
        if conversation_id.lower() == "none":
            conversation_id = None
        if parent_id.lower() == "none":
            parent_id = None
        return conversation_id, parent_id


def save_conversation(redis, app_conversation_id, conversation_id, parent_id):
    cache_key = get_cache_key(app_conversation_id)
    cache_result = ":".join([str(conversation_id), str(parent_id)])
    return redis.set(cache_key, cache_result)
