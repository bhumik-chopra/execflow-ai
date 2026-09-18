"""Lazy, shared PyMongo Atlas connection."""

from threading import Lock

from pymongo import MongoClient, timeout
from pymongo.database import Database
from pymongo.errors import PyMongoError

from config import Settings


class DatabaseUnavailable(RuntimeError):
    """Safe error that never includes connection strings or credentials."""


class MongoDB:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: MongoClient | None = None
        self._lock = Lock()

    def get_database(self) -> Database:
        uri = self._settings.mongodb_uri.get_secret_value().strip()
        if not uri or uri == "your_mongodb_atlas_connection_string":
            raise DatabaseUnavailable("MongoDB Atlas is not configured.")
        try:
            with self._lock:
                if self._client is None:
                    self._client = MongoClient(
                        uri,
                        connect=False,
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=5000,
                        socketTimeoutMS=15000,
                        timeoutMS=15000,
                        appname="execflow-ai",
                    )
            return self._client[self._settings.mongodb_db]
        except (PyMongoError, ValueError, OSError):
            raise DatabaseUnavailable("MongoDB Atlas is currently unavailable.") from None

    def ping(self) -> bool:
        try:
            with timeout(3):
                self.get_database().command("ping")
            return True
        except (DatabaseUnavailable, PyMongoError, ValueError, OSError):
            return False

    def close(self) -> None:
        with self._lock:
            if self._client is not None:
                self._client.close()
                self._client = None
