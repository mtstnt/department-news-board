import base64
import datetime
from http import HTTPStatus
import mimetypes
from os import stat
from nameko.web.handlers import http
from nameko.rpc import RpcProxy
from requests import head
from werkzeug import Request, Response

from deps.response import ResponseHelper
from deps.jwt import JwtHelper
from deps.redis import RedisProvider

COOKIE_KEY = 'DNB-Auth-Token'
ARCHIVAL_API_KEY = 'r3QCkcsjmspt1KLvWxPq5kkekPcXQ3GK'

class GatewayService:
    """
    HTTP Gateway for the system.
    Will check for authentication.
    """

    name = "gateway_service"

    user_rpc = RpcProxy("user_service")
    news_rpc = RpcProxy("news_service")
    storage_rpc = RpcProxy("storage_service")

    session = RedisProvider()

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

        self.session.whitelist_token(token)

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

        self.session.whitelist_token(token)

        resp = ResponseHelper().success({"token": token, "user": rpc_resp['data']}, HTTPStatus.OK)
        resp.set_cookie(COOKIE_KEY, token)
        return resp

    @http('POST', '/logout')
    def logout(self, request):
        user = self._authenticate(request.cookies)
        if user is None:
            return ResponseHelper().error("Invalid user session", status=HTTPStatus.FORBIDDEN)
        
        token = request.cookies.get(COOKIE_KEY)
        self.session.revoke(token)

        return ResponseHelper().success({})

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
    @http("GET", "/news/<int:news_id>/download")
    def download_news(self, request, news_id: int):
        result = self.news_rpc.download(news_id)
        if result["status"] != HTTPStatus.OK:
            return ResponseHelper().error(result["message"], result["status"])

        filename = result['data']['filename']
        news_title: str = result['data']['news']['title']
        news_date = result['data']['news']['date']

        file_ext = filename.split('.')[-1]

        news_date = datetime.datetime.utcfromtimestamp(news_date).strftime("%d_%m_%Y")

        new_filename = news_title.replace(' ', '_').lower() + "_" + news_date + "." + file_ext
        binary_data = base64.b64decode(result['data']['b'])
        content_type, _ = mimetypes.guess_type(filename)

        if content_type == None:
            content_type = "application/octet-stream" # General purpose

        res = Response(binary_data, HTTPStatus.OK)
        res.headers.add('Content-Type', content_type)
        res.headers.add('Content-Disposition', f'attachment; filename="{new_filename}"')
        return res

    # Manage news
    @http("POST", "/news")
    def create_news(self, request: Request):
        json_req = request.get_json()

        user = self._authenticate(request.cookies)
        if user == None:
            return ResponseHelper().error("Invalid user session", status=HTTPStatus.FORBIDDEN)

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
        user = self._authenticate(request.cookies)
        if user == None:
            return ResponseHelper().error("Invalid user session", status=HTTPStatus.FORBIDDEN)

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
        user = self._authenticate(request.cookies)
        if user == None:
            return ResponseHelper().error("Invalid user session", status=HTTPStatus.FORBIDDEN)

        file = request.files['attachment']

        # Get data from FileStorage
        bytes = file.stream.readlines()

        news = self.news_rpc.upload({
            "content_type": file.content_type,
            "mimetype": file.mimetype,
            "content_data": base64.b64encode(b''.join(bytes)).decode(),
        }, news_id)
        
        if news["status"] != HTTPStatus.OK:
            return ResponseHelper().error(news["message"], news["status"])
            
        return ResponseHelper().success({})

    @http("DELETE", "/news/<int:news_id>")
    def delete_news(self, request, news_id):
        user = self._authenticate(request.cookies)
        if user == None:
            return ResponseHelper().error("Invalid user session", status=HTTPStatus.FORBIDDEN)

        self.news_rpc.delete(news_id)
        return ResponseHelper().success({})

    @http("POST", "/news/archive")
    def archival_job(self, request):
        json = request.get_json()
        if json.get('key') is None:
            return Response("Key not provided", status=HTTPStatus.INTERNAL_SERVER_ERROR)
        
        if json['key'] != ARCHIVAL_API_KEY:
            return Response("Invalid key", status=HTTPStatus.FORBIDDEN)
        
        self.news_rpc.archive()
        
        return Response(status=HTTPStatus.OK)

    def _authenticate(self, cookies: dict) -> dict|None:
        if cookies.get(COOKIE_KEY) == None:
            return None
        
        auth_key = cookies.get(COOKIE_KEY)
        if auth_key == None:
            return None

        if not self.session.check(auth_key):
            return None
            
        auth_vals = JwtHelper().decode(auth_key)

        return auth_vals
