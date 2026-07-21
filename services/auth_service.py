"""Registration, password verification and server-side session tokens."""

import hashlib
import hmac
import secrets


class AuthError(ValueError):
    pass


class AuthService:
    def __init__(self, repository, settings):
        self.repository = repository
        self.settings = settings
        self._sessions: dict[str, object] = {}

    def register(self, username: str, password: str):
        self._validate(username, password)
        if self.repository.get_by_username(username) is not None:
            raise AuthError("username_taken")
        salt = secrets.token_bytes(self.settings.password.salt_bytes)
        password_hash = self._hash(password, salt)
        return self.repository.create(username, password_hash.hex(), salt.hex(), self.settings.elo.starting_rating)

    def login(self, username: str, password: str) -> tuple[object, str]:
        user = self.repository.get_by_username(username)
        if user is None or not hmac.compare_digest(user.password_hash, self._hash(password, bytes.fromhex(user.password_salt)).hex()):
            raise AuthError("invalid_credentials")
        token = secrets.token_urlsafe(self.settings.session_token_bytes)
        self._sessions[token] = user
        return user, token

    def user_for_token(self, token: str):
        return self._sessions.get(token)

    def _hash(self, password: str, salt: bytes) -> bytes:
        p = self.settings.password
        return hashlib.pbkdf2_hmac(p.algorithm, password.encode("utf-8"), salt, p.iterations, p.derived_key_bytes)

    @staticmethod
    def _validate(username: str, password: str) -> None:
        if not username.strip() or not password:
            raise AuthError("username_and_password_required")
