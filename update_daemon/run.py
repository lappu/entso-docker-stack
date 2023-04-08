import datetime
import json
import os
import time
import zoneinfo

import pytz

from loguru import logger

import schedule

import paho.mqtt.client as mqtt

from entsoe import EntsoePandasClient

import pandas as pd

import db


ENTSO_API_KEY = os.environ['ENTSO_API_KEY']
MQTT_BROKER_HOST= os.enivron.get("MQTT_BROKER_HOST")

TZ = 'Europe/Helsinki'

MQTT_TOPIC_TODAY = "electricity/price/today"
MQTT_TOPIC_TOMORROW = "electricity/price/tomorrow"
MQTT_TOPIC_HOURLY = "electricity/price/current_hour"

client = EntsoePandasClient(api_key=KEY)

def today():
    return datetime.date.today()

def tomorrow():
    return today() + datetime.timedelta(days=1)

def day_after():
    return tomorrow() + datetime.timedelta(days=2)


@logger.catch
def update_prices(start, end, country_code='FI'):
    """
    start and end are datetime.date objects
    """
    logger.debug(f'Query prices from {start} to {end}')

    # Make start timestamp being at 01:00, as the query seems to be
    # inclusive. If we simply queried by start and end dates, we'd get back 25
    # items, where the first one belongs to previous day.
    #
    # The series labels are timestamps, and are apparently the end-side of the
    # time range. So "2024-01-01 02:00" is for time range 01:00-02:00.
    start = datetime.datetime.combine(start, datetime.time(1, 0))

    start = pd.Timestamp(start, tz=TZ)
    end = pd.Timestamp(end, tz=TZ)

    series = client.query_day_ahead_prices(country_code, start=start, end=end)

    if len(series) != 24:
        # Something's wrong, we didn't get proper dataset
        logger.error(f'Received only {len(series)} items, not storing data')
        return

    # Convert €/MWh -> cnt/kWh
    series /= 10

    # Convert to UTC
    series = series.tz_convert(pytz.utc)
                           
    store_prices(series)

def store_prices(series):
    with db.get_session() as session:
        for ts, value in series.items():
            existing_price = session.query(db.Price).filter_by(time=ts).first()

            if not existing_price:
                # insert a new row into the Price table
                price = db.Price(time=ts, price=value)
                logger.debug(f'Store value {value:.3f} for {ts}')
                session.add(price)
        session.commit()

def publish(topic, data, persist=False):
    # Create a MQTT client object
    client = mqtt.Client()

    # Connect to MQTT broker
    client.connect(MQTT_BROKER_HOST)

    # Publish the message to the topic
    client.publish(topic, data)

    # Disconnect from MQTT broker
    client.disconnect()

def update_tomorrow():
    update_prices(tomorrow(), day_after())
    
def publish_hourly():
    now = datetime.datetime.utcnow()
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    next_hour = current_hour + datetime.timedelta(hours=1)
    
    with db.get_session() as session:
        current_price = session.query(db.Price).filter_by(time=next_hour).first().price

    logger.debug(f'Publish hourly price {current_price}')

    publish(MQTT_TOPIC_HOURLY, current_price, persist=True)

def publish_daily():
    now = datetime.datetime.now()
    today_start = datetime.datetime.combine(
        now.date(), datetime.time(0, 0)
    ).replace(tzinfo=zoneinfo.ZoneInfo(TZ))

    # Convert start time to utc for db access
    today_start = today_start.astimezone(datetime.timezone.utc)

    # Get end time (automatically uses same timezone)
    today_end = today_start + datetime.timedelta(days=1)

    with db.get_session() as session:
        items = session.query(db.Price).filter(db.Price.time > today_start).filter(db.Price.time <= today_end)
        
    data = {
        'date': now.date().strftime('%Y-%m-%d'),
        'items': [],
    }

    for item in items:
        ts = item.time.replace(tzinfo=datetime.timezone.utc)
        ts = ts.astimezone(zoneinfo.ZoneInfo(TZ))
        ts -= datetime.timedelta(hours=1)
        data['items'].append({'hour': ts.hour, 'price': item.price})

    logger.debug(f'Publish daily prices ({len(data["items"])} items)')
        
    publish(MQTT_TOPIC_TODAY, json.dumps(data), persist=True)

if __name__ == '__main__':
    # Always update today's price when starting up
    update_prices(today(), tomorrow())

    # If past 14:00, update tomorrow's prices as well
    now = datetime.datetime.now()
    if now.time() > datetime.time(14, 1):
        time.sleep(5)  # Give the API a break
        update_tomorrow()

    schedule.every().day.at("14:01", TZ).do(update_tomorrow)
    schedule.every().hour.at(":00").do(publish_hourly)
    schedule.every().day.at("00:00").do(publish_daily)

    while True:
        schedule.run_pending()
        next_wait = schedule.idle_seconds()
        logger.debug(f'Sleeping {int(next_wait)}s')
        time.sleep(next_wait)


