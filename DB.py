import peewee
import os

database = peewee.SqliteDatabase(os.environ['CDEM_SQLITE_PATH'])


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
