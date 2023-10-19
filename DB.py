import peewee
import os

import Constants

db_path = os.environ['CDEM_SQLITE_PATH']

if os.environ.get('CDEM_WIPE_DATA', 'False').lower() == 'True'.lower():
    print('CDEM_WIPE_DATA is True, dropping data')
    try:
        os.remove(db_path)
        print(f'Successfully removed file')

    except Exception:
        print('Failed to remove DB file')

database = peewee.SqliteDatabase(db_path)


class BaseModel(peewee.Model):
    class Meta:
        database = database


class CalendarEvents(BaseModel):
    drupal_id = peewee.CharField(primary_key=True)
    start_datetime = peewee.DateTimeField()
    end_datetime = peewee.DateTimeField()
    title = peewee.TextField()
    activity_type = peewee.CharField()
    location = peewee.TextField()
    description = peewee.TextField()
    eligibility = peewee.TextField(null=True)
    requirements = peewee.TextField(null=True)
    addition_requirements = peewee.TextField(null=True)
    info_link = peewee.TextField(null=True)
    video_link = peewee.TextField(null=True)
    image_link = peewee.TextField(null=True)


class Config(BaseModel):
    key = peewee.CharField(primary_key=True)
    value = peewee.TextField()


def set_latest_url(url: str) -> None:
    try:
        Config.create(key='latest_url', value=url)

    except peewee.IntegrityError:
        Config.update({Config.value: url}).where(Config.key == 'latest_url').execute()


def get_latest_url() -> str:
    row = Config.get_or_none(Config.key == 'latest_url')
    if row is None:
        return Constants.EVENTS_FEED

    else:
        return row.value


CalendarEvents.create_table()
Config.create_table()
