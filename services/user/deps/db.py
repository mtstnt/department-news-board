from nameko.dependency_providers import DependencyProvider
import psycopg2 as pg

from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

class UserModel:
	def __init__(self, connection) -> None:
		self.conn = connection

	def __get_cursor(self):
		return self.conn.cursor(cursor_factory=RealDictCursor)

	def find_by_username(self, username: str) -> dict:
		cur = self.__get_cursor()
		cur.execute("SELECT * FROM users WHERE username = %s LIMIT 1", (username,))
		if cur.rowcount > 0:
			return cur.fetchone()
		return None

	def create_user(self, username: str, password_hashed: str) -> any:
		try:
			cur = self.__get_cursor()
			cur.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id, username", (username, password_hashed,))
			result = cur.fetchone()
			self.conn.commit()
			return result
		except pg.OperationalError as e:
			print(e.pgcode, e.pgerror)
			return None

class DBProvider(DependencyProvider):
	def setup(self):
		self.conn = ThreadedConnectionPool(
			minconn=5,
			maxconn=10,
			dsn="dbname=dnb_user user=dnb_user password=dnb_user host=user_db"
		)

	def get_dependency(self, worker_ctx):
		return UserModel(self.conn.getconn())