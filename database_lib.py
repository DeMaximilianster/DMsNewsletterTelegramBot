from os import listdir
import peewee
from playhouse.shortcuts import ThreadSafeDatabaseMetadata
from playhouse.migrate import SqliteMigrator, migrate


class MySqliteDatabase(peewee.SqliteDatabase):

    def __init__(self, database, *args, **kwargs):
        class BaseModel(peewee.Model):
            class Meta:
                # Instruct peewee to use our thread-safe metadata implementation.
                model_metadata_class = ThreadSafeDatabaseMetadata

        class User(BaseModel):
            user_id = peewee.IntegerField(primary_key=True)

            status = peewee.CharField()
            name = peewee.CharField()
            username = peewee.CharField()

        class Request(BaseModel):
            request_id = peewee.AutoField()
            user = peewee.ForeignKeyField(User, backref="requests")

            opened_at = peewee.DateTimeField()
            closed_at = peewee.DateTimeField(null=True)
            request_status = peewee.CharField(null=True)

        class Post(BaseModel):
            post_id = peewee.AutoField()

            copy_from_chat_id = peewee.IntegerField()
            copy_from_message_id = peewee.IntegerField()

        class PostWeeklySchedule(BaseModel):
            entry_id = peewee.AutoField()
            post = peewee.ForeignKeyField(Post, backref="schedule_entries")

            weekday = peewee.IntegerField()
            hour = peewee.IntegerField()
            minute = peewee.IntegerField()
            last_invoked = peewee.IntegerField()

        super().__init__(database, *args, **kwargs)
        self.User = User
        self.Request = Request
        self.Post = Post
        self.PostWeeklySchedule = PostWeeklySchedule
        self.all_tables = [self.User, self.Request, self.Post, self.PostWeeklySchedule]
        self.connections = 0

    def update_tables(self):
        self.connect()
        self.bind(self.all_tables)
        self.create_tables(self.all_tables)
        self.close()

    def connect(self, reuse_if_open=False):
        self.connections += 1
        if self.connections == 1:
            super().connect(reuse_if_open)

    def close(self):
        self.connections -= 1
        if self.connections == 0:
            super().close()


class DatabaseConnection:

    def __init__(self, database: MySqliteDatabase):
        self.database = database

    def __del__(self):
        self.database.close()

    def connect(self):
        self.database.connect()


def my_migrate():
    db_files = filter(lambda x: ".db" in x, listdir())
    for db_file in db_files:
        database = MySqliteDatabase(db_file)
        migrator = SqliteMigrator(database)
        migrate(
            migrator.add_column("model_name", "field_name", peewee.IntegerField(default=0))
        )


if __name__ == "__main__":
    my_migrate()
