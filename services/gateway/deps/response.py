from http import HTTPStatus
import json
from werkzeug import Response


class ResponseHelper:
    def make(self, data: dict, status: int, message: str = "", headers = {}) -> Response:
        response_data = {
            "error": 0 if status == HTTPStatus.OK else 1,
            "message": message,
            "data": data, 
        }

        response_headers = {
            "Content-Type": "application/json",
            **headers
        }

        return Response(json.dumps(response_data), status, response_headers)

    def error(self, message: str = "Error occurred.", status: int = HTTPStatus.INTERNAL_SERVER_ERROR) -> Response:
        return self.make({}, status, message, {})

    def success(self, data: dict, status: int = HTTPStatus.OK) -> Response: 
        return self.make(data, status, "Success")