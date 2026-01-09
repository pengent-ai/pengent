import redis
import json
from typing import List
from .memory_storage_interface import MemoryStorageInterface


class RedisMemoryStorage(MemoryStorageInterface):
    """Redisを使用したメモリストレージの実装"""

    def __init__(self, redis_client: redis.Redis, key: str, ttl: int = None):
        """
        :param redis_client: Redisの接続クライアント
        :param key: 会話履歴の保存先キー(例: "memory:user123")
        :param ttl: 有効期限(秒)を設定する場合
        """
        self.redis = redis_client
        self.key = key
        self.ttl = ttl

    def save(self, messages: List[dict]) -> None:
        self.redis.set(self.key, json.dumps(messages))
        if self.ttl:
            self.redis.expire(self.key, self.ttl)

    def load(self) -> List[dict]:
        data = self.redis.get(self.key)
        if data is None:
            return []
        return json.loads(data)
