from http import HTTPStatus
import json
from os import stat
from nameko.web.handlers import http
from nameko.rpc import RpcProxy
from requests import head
from werkzeug import Request, Response

from deps.response import ResponseHelper
from deps.jwt import JwtHelper

COOKIE_KEY = 'DNB-Auth-Token'

class GatewayService:
    """
    HTTP Gateway for the system.
    Will check for authentication.
    """

    name = "gateway_service"

    user_rpc = RpcProxy("user_service")
    news_rpc = RpcProxy("news_service")
    storage_rpc = RpcProxy("storage_service")

    # Users
    @http("POST", "/login")
    def login(self, request: Request):
        json_request = request.get_json()

        username = json_request["username"]
        password = json_request["password"]

        rpc_resp = self.user_rpc.login(username, password)
        if rpc_resp['status'] != HTTPStatus.OK:
            return ResponseHelper().error(
                "Invalid login credentials", HTTPStatus.UNAUTHORIZED
            )

        token = JwtHelper().encode(
            {"user_id": rpc_resp['data']['id'], "username": rpc_resp['data']['username']}
        )
        resp = ResponseHelper().success({"token": token})
        resp.set_cookie(COOKIE_KEY, token)
        return resp

    @http("POST", "/register")
    def register(self, request: Request):
        json_request = request.get_json()

        username = json_request["username"]
        password = json_request["password"]

        rpc_resp = self.user_rpc.register(username, password)
        if rpc_resp['status'] != HTTPStatus.OK:
            return ResponseHelper().error(
                "Invalid registration request", HTTPStatus.BAD_REQUEST
            )

        token = JwtHelper().encode(
            {"user_id": rpc_resp['data']["id"], "username": rpc_resp['data']["username"]}
        )
        resp = ResponseHelper().success({"token": token, "user": rpc_resp['data']}, HTTPStatus.OK)
        resp.set_cookie(COOKIE_KEY, token)
        return resp

    # News
    @http("GET", "/news")
    def get_all_news(self, request):
        result = self.news_rpc.get_all_news()
        if result["status"] != HTTPStatus.OK:
            return ResponseHelper().error(result["message"], result["status"])

        return ResponseHelper().success({"news": result["data"]})

    @http("GET", "/news/<int:news_id>")
    def get_news(self, request, news_id: int):
        result = self.news_rpc.get_news(news_id)
        if result["status"] != HTTPStatus.OK:
            return ResponseHelper().error(result["message"], result["status"])

        return ResponseHelper().success({"news": result["data"]})

    # Storage
    # TODO: Fix
    @http("GET", "/news/<int:news_id>/download")
    def download_news(self, request, news_id: int):
        result = self.news_rpc.download(news_id)
        if result["status"] != HTTPStatus.OK:
            return ResponseHelper().error(result["message"], result["status"])

        return ResponseHelper().make(result["data"], HTTPStatus.OK)

    ### Requires auth
    # Manage news
    @http("POST", "/news")
    def create_news(self, request: Request):
        json_req = request.get_json()

        user = self._authenticate(request.cookies)
        if user == None:
            return ResponseHelper().error(status=HTTPStatus.UNAUTHORIZED)

        data = {
            "date": json_req["date"],
            "title": json_req["title"],
            "description": json_req["description"],
        }

        news = self.news_rpc.create(data, user['user_id'])
        if news["status"] != HTTPStatus.OK:
            return ResponseHelper().error(news["message"], news["status"])

        return ResponseHelper().success({"news": news["data"]})

    @http("PUT", "/news/<int:news_id>")
    def update_news(self, request: Request, news_id: int):
        json_req: dict = request.get_json()
        data = {}

        if json_req.get('date') != None:
            data['date'] = json_req['date']
        if json_req.get('title') != None:
            data['title'] = json_req['title']
        if json_req.get('description') != None:
            data['description'] = json_req["description"]

        news = self.news_rpc.update(data, news_id)

        if news["status"] != HTTPStatus.OK:
            return ResponseHelper().error(news["message"], news["status"])
            
        return ResponseHelper().success({"news": news["data"]})

    @http("PUT", "/news/<int:news_id>/upload")
    def upload_news_attachment(self, request: Request, news_id: int):
        file = request.files['attachment']

        news = self.news_rpc.upload(file, news_id)
        
        if news["status"] != HTTPStatus.OK:
            return ResponseHelper().error(news["message"], news["status"])
            
        return ResponseHelper().success({})

    @http("DELETE", "/news/<int:news_id>")
    def delete_news(self, request, news_id):
        self.news_rpc.delete(news_id)
        return ResponseHelper().success({})

    def _authenticate(self, cookies: dict) -> dict|None:
        print(cookies, flush=True)
        if cookies.get(COOKIE_KEY) == None:
            return None
        
        auth_key = cookies.get(COOKIE_KEY)
        auth_vals = JwtHelper().decode(auth_key)

        return auth_vals