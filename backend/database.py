# database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# MySQL connection URL format:
# mysql+pymysql://username:password@host:port/database_name
#
# mysql+pymysql  → use MySQL with pymysql driver
# root           → your MySQL username (default is root)
# your_password  → the password you set during MySQL installation
# localhost      → MySQL is running on your own computer
# 3306           → default MySQL port (like a door number)
# inventorydb    → the database we just created
DATABASE_URL = "mysql+pymysql://root:618507@localhost:3306/inventorydb"

# create_engine sets up the connection to MySQL
# Note: we removed connect_args={"check_same_thread": False}
# because that was SQLite-specific — MySQL doesn't need it
engine = create_engine(DATABASE_URL)

# Exact same as before — this is database-independent
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Exact same as before
Base = declarative_base()

# Exact same as before
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()