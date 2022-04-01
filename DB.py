import peewee
import os

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


CalendarEvents.create_table()
