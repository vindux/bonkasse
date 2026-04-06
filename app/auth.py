import bcrypt
import secrets
from fastapi import Cookie, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DBSession

from .database import get_db
from .models import AppConfig

_valid_tokens: set[str] = set()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_admin_token() -> str:
    token = secrets.token_urlsafe(32)
    _valid_tokens.add(token)
    return token


def revoke_admin_token(token: str):
    _valid_tokens.discard(token)


class AdminRequired:
    """Callable dependency that redirects to login if not authenticated."""

    async def __call__(
        self,
        request: Request,
        admin_token: str | None = Cookie(default=None),
        db: DBSession = Depends(get_db),
    ):
        config = db.get(AppConfig, 1)
        if config and config.password_hash:
            if admin_token is None or admin_token not in _valid_tokens:
                raise _AdminRedirectException()


class _AdminRedirectException(Exception):
    pass


require_admin = AdminRequired()
