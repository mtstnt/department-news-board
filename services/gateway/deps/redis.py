from nameko.dependency_providers import DependencyProvider
import redis
import time


class RedisSession:
    conn: redis.Redis = None

    def __get_expiration_time(self) -> int:
        return 1 * 3600

    def __init__(self, conn) -> None:
        self.conn = conn

    def whitelist_token(self, token: str) -> None:
        self.conn.set(token, 1, ex=self.__get_expiration_time())

    def extend(self, token: str) -> None:
        return self.conn.expire(token, self.__get_expiration_time())

    def revoke(self, token: str) -> None:
        self.conn.delete(token)

    def check(self, token: str) -> bool:
        print(self.conn.get(token), flush=True)
        if self.conn.get(token) is None or self.conn.get(token) == 0:
            return False
        return True


class RedisProvider(DependencyProvider):
    def __init__(self) -> None:
        super().__init__()

    def setup(self):
        self.conn = redis.ConnectionPool(host="redis", max_connections=10)

    def get_dependency(self, worker_ctx):
        return RedisSession(redis.Redis(connection_pool=self.conn))
