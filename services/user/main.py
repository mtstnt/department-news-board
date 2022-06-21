from http import HTTPStatus
import bcrypt
from nameko.rpc import rpc

from deps.db import DBProvider


class UserService:
    name = "user_service"

    user_model = DBProvider()

    def _response(self, status, data=None, msg=""):
        return {"status": status, "data": data, "message": msg}

    @rpc
    def login(self, username: str, password: str) -> dict:
        user = self.user_model.find_by_username(username)

        if user == None:
            return self._response(HTTPStatus.UNAUTHORIZED, msg="Invalid credentials")

        if not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return self._response(HTTPStatus.UNAUTHORIZED, msg="Invalid credentials")

        return self._response(HTTPStatus.OK, user)

    @rpc
    def register(self, username: str, password: str) -> dict:
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user = self.user_model.create_user(username, hashed_pw.decode())

        if user is None:
            return self._response(HTTPStatus.UNAUTHORIZED, msg="Invalid credentials")

        return self._response(HTTPStatus.OK, user)

    @rpc 
    def get_user(self, user_id: int) -> dict:
        user = self.user_model.find_by_id(user_id)
        if user == None:
            return None
        return user