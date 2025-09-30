import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context

# Add app/ to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import Base and settings
from app.config.db_connection import Base
from app.config.settings import settings

# Import your models
from app.models import (RegisterUser,BlacklistedToken)

# Set Alembic config manually
config = context.config
config.set_main_option("sqlalchemy.url",settings.database_url_sync)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata

# def include_object(object, name, type_, reflected, compare_to):
#     # Skip this view from autogeneration
#     if type_ == "table" and name == "Brazil Customers": # db table name add after tablename  __table_args__ = {'autoload_with': some_engine}
#         return False
#     return True

def run_migrations_offline():
    context.configure(
        url=settings.database_url_sync,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
        
def run_migrations_online():
    connectable = create_engine(settings.database_url_sync, poolclass=pool.NullPool)
    
    with connectable.connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata) # ,include_object=include_object 
        with context.begin_transaction():
            context.run_migrations()
            
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()