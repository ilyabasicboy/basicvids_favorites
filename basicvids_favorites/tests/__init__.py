from basicvids_favorites.db import create_db_and_tables, engine
from basicvids_favorites.main import app

create_db_and_tables()

__all__ = ["app", "engine"]
