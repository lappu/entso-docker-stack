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


def get_data_for_date(start_date):
    date_start = datetime.datetime.combine(
        start_date, datetime.time(0, 0)
    ).replace(tzinfo=zoneinfo.ZoneInfo(TZ))

    # Convert start time to utc for db access
    date_start = date_start.astimezone(datetime.timezone.utc)

    # Get end time (automatically uses same timezone)
    date_end = date_start + datetime.timedelta(days=1)

    with db.get_session() as session:
        items = session.query(db.Price).filter(
            db.Price.time > date_start).filter(
                db.Price.time <= date_end)

    times, prices = zip(*[(i.time, i.price) for i in items])
        
    series = pd.Series(prices, index=times)

    return series
        
    


__all__ = ['Price', 'engine', 'get_session']
