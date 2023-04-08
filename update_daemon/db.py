import os

from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import sessionmaker

DB_USER = os.environ.get('DB_USER', 'entso')
DB_PASS = os.environ.get('DB_PASS', 'entso')
DB_HOST = os.environ.get('DB_HOST', 'mysql')
DB_NAME = os.environ.get('DB_NAME', 'entso')

# Define the database connection
engine = create_engine(f'mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}', echo=False)

# Define a session factory
#Session = sessionmaker(bind=engine)

# Declare a base for declarative class definitions
Base = declarative_base()

# Define the Price model
class Price(Base):
    __tablename__ = 'price'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime, unique=True, nullable=False)
    price = Column(Float, nullable=False)

# Create the table schema
Base.metadata.create_all(engine)


def get_session():
    return sessionmaker(bind=engine)()


__all__ = ['Price', 'engine', 'get_session']
