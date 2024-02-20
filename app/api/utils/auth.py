import random
import string
from datetime import datetime, timedelta

import jwt

from app.core.config import settings
from app.db.models.accounts import User

ALGORITHM = "HS256"


class Authentication:
    # generate random string
    def get_random(length: int):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    # generate access token based and encode user's id
    async def create_access_token(payload: dict):
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode = {"exp": expire, **payload}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    # generate random refresh token
    async def create_refresh_token():
        expire = datetime.utcnow() + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
        return jwt.encode(
            {"exp": expire, "data": Authentication.get_random(10)},
            settings.SECRET_KEY,
            algorithm=ALGORITHM,
        )

    # deocde access token from header
    async def decode_jwt(token: str):
        try:
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        except:
            decoded = False
        return decoded

    async def decodeAuthorization(token: str):
        token = token[7:]
        decoded = await Authentication.decode_jwt(token)
        if not decoded:
            return None
        user = await User.get_or_none(
            id=decoded["user_id"], access_token=token
        ).select_related("city", "city__region", "city__region__country", "avatar")
        return user
