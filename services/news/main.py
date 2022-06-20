from datetime import datetime
from http import HTTPStatus
import re
import time
from nameko.rpc import rpc
import psycopg2

from deps.db import DBProvider


class NewsService:
    name = "news_service"

    news_model = DBProvider()

    def _response(self, status, data=None, msg=""):
        return {"status": status, "data": data, "message": msg}

    @rpc
    def get_all_news(self, include_archived=False) -> list[dict]:
        news_list = self.news_model.get_all_news(include_archived)
        return self._response(HTTPStatus.OK, news_list)

    @rpc
    def download(self, id: int) -> dict:
        news = self.news_model.get_news(id)

        if news == None:
            return self._response(HTTPStatus.NOT_FOUND, msg="Not found")

        filename = news["filename"]
        filecontent = self.storage_rpc.download(filename)

        if filecontent == None:
            return self._response(HTTPStatus.NOT_FOUND, msg="Not found")

        return self._response(HTTPStatus.OK, filecontent)

    @rpc
    def get_news(self, id: int) -> dict | None:
        news = self.news_model.get_news(id)

        if news == None:
            return self._response(HTTPStatus.NOT_FOUND, msg="Not found")

        return self._response(HTTPStatus.OK, news)

    @rpc
    def create(self, data: dict, user_id: int) -> dict | None:
        string_date = data['date']
        if re.match('^\d{2}/\d{2}/\d{4}$', string_date) == None:
            return self._response(HTTPStatus.BAD_REQUEST, msg="Invalid date string")

        date_elements = string_date.split('/')
        date, month, year = date_elements[0], date_elements[1], date_elements[2]
        d = datetime(int(year), int(month), int(date))
        unixtime = time.mktime(d.timetuple())

        data['date'] = int(unixtime)
        data['author'] = user_id
        
        news = self.news_model.create(data)
        if news is psycopg2.Error:
            return self._response(HTTPStatus.INTERNAL_SERVER_ERROR, msg=news)
        news.pop('author')
        return self._response(HTTPStatus.OK, news)

    @rpc
    def update(self, data: dict, id: int) -> dict | None:
        news = self.news_model.update(data, id)

        if news == None:
            return self._response(HTTPStatus.INTERNAL_SERVER_ERROR)

        return self._response(HTTPStatus.OK, news)

    @rpc
    def delete(self, id: int) -> None:
        self.news_model.delete(id)
