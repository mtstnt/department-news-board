from nameko.dependency_providers import DependencyProvider
import psycopg2 as pg

from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool


class NewsModel:
    def __init__(self, connection) -> None:
        self.conn = connection

    def __get_cursor(self):
        return self.conn.cursor(cursor_factory=RealDictCursor)

    def get_all_news(self, include_archived=False) -> list[dict]:
        cur = self.__get_cursor()
        sql = "SELECT * FROM news WHERE status = true"
        if not include_archived:
            sql += " AND archived = false"
        sql += " ORDER BY date DESC"
        cur.execute(sql)
        result = cur.fetchall()
        return result

    def get_news(self, id: int, include_archived=False) -> dict:
        cur = self.__get_cursor()
        sql = "SELECT * FROM news WHERE id = %s AND status = true"
        if not include_archived:
            sql += " AND archived = false"
        cur.execute(sql, (id,))
        result = cur.fetchone()
        return result

    def create(self, data: dict) -> list[dict]:
        try:
            cur = self.__get_cursor()
            cur.execute(
                "INSERT INTO news (date, title, description, author) VALUES (%s, %s, %s, %s) RETURNING id, date, title, description, author",
                (data['date'], data["title"], data["description"], data['author']),
            )
            self.conn.commit()
            return cur.fetchone()
        except pg.OperationalError as e:
            print("pg operational err:", e.pgcode, e.pgerror, flush=True)
            return e
        except Exception as e:
            print("err:", e, flush=True)
            return e

    def update(self, data: dict, id: int) -> dict:
        try:
            cur = self.__get_cursor()
            updates, params = [], []
            for cols in ['date', 'title', 'description']:
                if data.get(cols) != None:
                    updates.append(f"{cols} = %s")
                    params.append(data[cols])
            cur.execute(
                f"UPDATE news SET {','.join(updates)} WHERE id = %s RETURNING id, date, title, description, filename, author",
                (*params, id),
            )
            self.conn.commit()
            return cur.fetchone()
        except pg.OperationalError as e:
            print("pg operational err:", e.pgcode, e.pgerror, flush=True)
            return e
        except Exception as e:
            print("err:", e, flush=True)
            return e

    def update_filename(self, filename: str, id: int):
        try:
            cur = self.__get_cursor()
            cur.execute("UPDATE news SET filename = %s WHERE id = %s RETURNING id, title, description, filename, author", (filename, id,))
            self.conn.commit()
            return cur.fetchone()
        except pg.OperationalError as e:
            print("pg operational err:", e.pgcode, e.pgerror, flush=True)
            return e
        except Exception as e:
            print("err:", e, flush=True)
            return e
        

    def delete(self, id: int) -> None:
        try:
            cur = self.__get_cursor()
            cur.execute("UPDATE news SET status = false WHERE id = %s", (id,))
            self.conn.commit()
        except pg.OperationalError as e:
            print("pg operational err:", e.pgcode, e.pgerror, flush=True)
            return e
        except Exception as e:
            print("err:", e, flush=True)
            return e

class DBProvider(DependencyProvider):
    def setup(self):
        self.conn = ThreadedConnectionPool(
            minconn=5,
            maxconn=10,
            dsn="dbname=dnb_news user=dnb_news password=dnb_news host=news_db",
        )

    def get_dependency(self, worker_ctx):
        return NewsModel(self.conn.getconn())
