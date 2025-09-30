from alembic.config import Config
from alembic import command
from pathlib import Path
from app.config.settings import settings

# Create Alembic config object
alembic_cfg = Config()

# Set the path to migration/env.py
migration_path = str(Path(__file__).resolve().parent / "migration")
alembic_cfg.set_main_option("script_location", migration_path)

# Set the DB URL (you can hardcode or read from environment/settings)
alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url_sync)

# Run the upgrade
command.upgrade(alembic_cfg, "head")
