from peewee import Model, TextField, SqliteDatabase, ForeignKeyField, IntegerField, FloatField, OperationalError
from hashlib import sha256
import random

database = SqliteDatabase('selection_test.db', threadlocals=True)


class SplitTestBase(Model):
    class Meta:
        database = database


class Test(SplitTestBase):
    name = TextField()


class Option(SplitTestBase):
    test = ForeignKeyField(Test, related_name='options')
    clicks = IntegerField()
    shows = IntegerField()
    weight = FloatField()
    hash = TextField()


class NewTest:
    def __init__(self, name, options):
        self.test, _ = Test.create_or_get(name=name)
        self.name = name
        self.options = {}
        self.add_option(*options)

    def add_option(self, *values):
        # we get a bunch of what are essentially HTML values
        # (different options) then we add them to the DB
        for value in values:
            m = sha256()
            m.update(value.encode('utf-8'))
            hash_string = m.hexdigest()
            clicks, shows, weight = 1, 1, 1
            option, created = Option.get_or_create(hash=hash_string, test=self.test,
                                                   defaults={'clicks': clicks, 'shows': shows, 'weight': weight,
                                                             'test': self.test})
            self.options[hash_string] = {
                'value': value.format(hash=hash_string),
                'data': {'clicks': option.clicks, 'shows': option.shows, 'weight': option.weight}
            }

    def set_weight(self, hash_string):
        self.options[hash_string]['data']['weight'] = (self.options[hash_string]['data']['clicks'] /
                                                       self.options[hash_string]['data']['shows'])

    def show_option(self, hash_string):
        self.options[hash_string]['data']['shows'] += 1
        self.set_weight(hash_string)
        Option.update(**self.options[hash_string]['data']).where(Option.hash == hash_string)

    def click_option(self, hash_string):
        if hash_string in self.options:
            self.options[hash_string]['data']['clicks'] += 1
            self.set_weight(hash_string)
            Option.update(**self.options[hash_string]['data']).where(Option.hash == hash_string)

    def get_option(self):
        if random.randint(0, 0) < 1:
            hash_string = random.choice(list(self.options.keys()))
        else:
            options = self.test.options.order_by(Option.weight.desc())
            hash_string = options.get().hash
        self.show_option(hash_string)
        value = self.options[hash_string]['value']
        return value


def create_tables():
    database.connect()
    tables = [Test, Option]
    for table in tables:
        try:
            database.create_table(table)
        except OperationalError:
            pass


create_tables()
