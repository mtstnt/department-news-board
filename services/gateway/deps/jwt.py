from dataclasses import dataclass
from datetime import date
import time
import jwt

KEY = "MANTAP"

class JwtHelper:
    def encode(self, other_data: dict) -> str:
        return jwt.encode({"exp": time.time() + (1 * 3600), **other_data}, KEY)

    def decode(self, token: str) -> dict:
        return jwt.decode(token.encode(), KEY, 'HS256')
