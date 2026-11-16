from typing import Optional
from database.connection import DatabaseManager, get_db


class BaseDAO:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()
