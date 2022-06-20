from datetime import datetime
from http import HTTPStatus
import re
import time
from nameko.rpc import rpc, RpcProxy
import psycopg2
from deps.db import DBProvider


class NewsService:
    name = "news_service"

    news_model = DBProvider()

    user_rpc = RpcProxy('user_service')

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
        dt = None
        try:
            dt = datetime.strptime(data['date'], '%d/%m/%Y')
        except ValueError as e:
            return self._response(HTTPStatus.BAD_REQUEST, msg="Invalid date format, should be: DD/MM/YYYY")

        unixtime = time.mktime(dt.timetuple())

        data['date'] = int(unixtime)
        data['author'] = user_id
        
        news = self.news_model.create(data)
        if news is Exception:
            return self._response(HTTPStatus.INTERNAL_SERVER_ERROR, msg=news)

        author = self.user_rpc.get_user(news['author'])
        if author == None:
            news['author'] = { "error": "Deleted User" }
        else:
            news['author'] = author
        
        return self._response(HTTPStatus.OK, news)

    @rpc
    def update(self, data: dict, id: int) -> dict | None:
        if data.get('date') != None: 
            dt = None
            try:
                dt = datetime.strptime(data['date'], '%d/%m/%Y')
            except ValueError as e:
                return self._response(HTTPStatus.BAD_REQUEST, msg="Invalid date format, should be: DD/MM/YYYY")
            unixtime = time.mktime(dt.timetuple())
            data['date'] = int(unixtime)

        news = self.news_model.update(data, id)
        if news == None:
            return self._response(HTTPStatus.INTERNAL_SERVER_ERROR)

        return self._response(HTTPStatus.OK, news)

    @rpc
    def delete(self, id: int) -> None:
        self.news_model.delete(id)
