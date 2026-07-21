"""SQLite persistence for users and their multiplayer statistics."""

from dataclasses import dataclass
from contextlib import closing
import os
import sqlite3


@dataclass(frozen=True)
class User:
    id: int
    username: str
    password_hash: str
    password_salt: str
    rating: int
    wins: int
    losses: int
    draws: int


class UserRepository:
    """Only SQL and user persistence; no password or ELO calculations."""

    def __init__(self, database_path: str):
        self.database_path = database_path

    def initialize(self) -> None:
        directory = os.path.dirname(self.database_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    wins INTEGER NOT NULL DEFAULT 0,
                    losses INTEGER NOT NULL DEFAULT 0,
                    draws INTEGER NOT NULL DEFAULT 0
                )
            """)

    def create(self, username: str, password_hash: str, password_salt: str, rating: int) -> User:
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                "INSERT INTO users(username, password_hash, password_salt, rating) VALUES (?, ?, ?, ?)",
                (username, password_hash, password_salt, rating),
            )
            return self.get_by_id(cursor.lastrowid, connection)

    def get_by_username(self, username: str) -> User | None:
        with closing(self._connect()) as connection, connection:
            row = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return self._to_user(row)

    def update_game_result(self, first: User, second: User, first_rating: int, second_rating: int,
                           first_outcome: str, second_outcome: str) -> None:
        with closing(self._connect()) as connection, connection:
            self._update_player(connection, first.id, first_rating, first_outcome)
            self._update_player(connection, second.id, second_rating, second_outcome)

    def get_by_id(self, user_id: int, connection=None) -> User:
        if connection is not None:
            return self._to_user(connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
        with closing(self._connect()) as own_connection, own_connection:
            return self.get_by_id(user_id, own_connection)

    @staticmethod
    def _update_player(connection, user_id, rating, outcome):
        column = {"win": "wins", "loss": "losses", "draw": "draws"}[outcome]
        connection.execute(f"UPDATE users SET rating = ?, {column} = {column} + 1 WHERE id = ?", (rating, user_id))

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _to_user(row) -> User | None:
        return None if row is None else User(**dict(row))
