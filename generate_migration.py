from alembic.config import Config
from alembic import command
from pathlib import Path
from app.config.settings import settings

# Create Alembic config object
alembic_cfg = Config()

# Set path to migration scripts
migration_path = str(Path(__file__).resolve().parent / "migration")
alembic_cfg.set_main_option("script_location", migration_path)

# Set the DB URL
alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url_sync)

# Generate new migration with message
command.revision(alembic_cfg, message="Create User model.", autogenerate=True)

print("✅ Migration script generated.")
