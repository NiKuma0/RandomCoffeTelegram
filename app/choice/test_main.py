"""
Testing matching algorithms 
"""
from email.policy import default
import os
import datetime
from pprint import pprint
import random
import tempfile
from itertools import zip_longest

import pytest
import peewee

COUNT_USERS = 4
COUNT_HRS = 7
COUNT_WEEK = 7


class User(peewee.Model):
    id = peewee.AutoField()
    name = peewee.CharField()
    is_hr = peewee.BooleanField(default=False)
    __queue = peewee.IntegerField(default=-1)

    @property
    def queue(self):
        return self.__queue

    @queue.setter
    def queue(self, value):
        self.__queue = value % (User.select().where(User.is_hr == self.is_hr).count())

    @classmethod
    def make_queue(cls):
        arr = []
        hrs = cls.select().where(cls.is_hr == False).order_by(peewee.fn.Random())
        users = cls.select().where(cls.is_hr == True).order_by(peewee.fn.Random())
        for i, hr in enumerate(hrs):
            hr.queue = i
            arr.append(hr)
        for i, user in enumerate(users):
            user.queue = i
            arr.append(user)
        return cls.bulk_update(arr, fields=(cls.__queue,))

    def __repr__(self):
        return f"<{self.name} {self.queue}>"


class Pair(peewee.Model):
    hr = peewee.ForeignKeyField(User)
    respondent = peewee.ForeignKeyField(User)


@pytest.fixture
def db():
    fd, name = tempfile.mkstemp()
    database = peewee.SqliteDatabase(name)
    User._meta.database = database
    Pair._meta.database = database
    database.create_tables((User, Pair))
    yield database
    os.close(fd)
    os.unlink(name)


@pytest.fixture
def create(db):
    users = [
        User(
            name=f"user{i}",
        )
        for i in range(COUNT_USERS)
    ]
    hrs = [
        User(
            name=f"hr{i}",
            is_hr=True,
        )
        for i in range(COUNT_HRS)
    ]
    User.bulk_create(users)
    User.bulk_create(hrs)
    User.make_queue()


@pytest.fixture
def get_random_pairs(create):
    pairs = []
    loners = []
    for _ in range(COUNT_WEEK):
        hrs = User.select().where(User.is_hr == True).order_by(peewee.fn.Random())
        users = User.select().where(User.is_hr == False).order_by(peewee.fn.Random())
        for hr, user in zip_longest(hrs, users):
            if hr and user:
                pairs.append(hr.name + user.name)
            else:
                loners.append((hr or user).name)
    return pairs, loners


@pytest.fixture
def get_pairs(create):
    pairs = []
    loners = []
    for _ in range(COUNT_WEEK):
        hrs = User.select().where(User.is_hr == True).order_by(+User._User__queue)
        users = User.select().where(User.is_hr == False).order_by(+User._User__queue)
        which_queue_to_move = True if hrs.count() > users.count() else False
        updated_models = []
        for hr, user in zip_longest(hrs, users):
            if which_queue_to_move and hr:
                hr.queue += 1
                updated_models.append(hr)
            elif user:
                user.queue += 1
                updated_models.append(user)
            if user and hr:
                pairs.append(str(hr) + str(user))
                continue
            loners.append((hr or user).name)
        User.bulk_update(updated_models, fields=(User._User__queue,))
    return pairs, loners


def __get_choice_arr_and_user(greater, lesser):
    coeff = round(greater.count() / lesser.count(), 5)
    remainder = 0
    index = 0
    greater_list = list(greater)
    for user in lesser:
        choices_arr = []
        count_choices = coeff + remainder
        int_count = int(count_choices)
        remainder = count_choices - int_count
        for i in range(int_count):
            choices_arr.append(greater_list[index])
            index += 1
        yield choices_arr, user
    updated = []
    for user1, user2 in zip_longest(lesser, greater):
        # if user1:
        #     user1.queue += int(coeff) + 1
        #     updated.append(user1)
        user2.queue += int(coeff) + 1
        updated.append(user2)
    User.bulk_update(updated, fields=(User._User__queue,))


@pytest.fixture
def get_smart_queue(create):
    pairs = []
    loners = []
    for _ in range(COUNT_WEEK):
        users = User.select().where(User.is_hr == False).order_by(User._User__queue)
        hrs = User.select().where(User.is_hr == True).order_by(User._User__queue)
        greater, lesser = (users, hrs) if users.count() > hrs.count() else (hrs, users)
        for choice_arr, user in __get_choice_arr_and_user(greater, lesser):
            random.shuffle(choice_arr)
            user_pair_field, other_pair_field = (
                (Pair.hr, Pair.respondent) if user.is_hr else (Pair.respondent, Pair.hr)
            )
            _pairs = Pair.select().where(user_pair_field == user)
            new_pair = None
            for choice in choice_arr:
                if new_pair or _pairs.where(other_pair_field == choice).exists():
                    loners.append(choice)
                    continue
                pairs.append(str(choice) + str(user))
                Pair.create(
                    **{
                        user_pair_field.column_name: user,
                        other_pair_field.column_name: choice,
                    }
                )
    return pairs, loners


def test_random(get_random_pairs):
    pairs, loners = get_random_pairs
    pprint(f"len pairs = {len(pairs)}")
    pprint(f"len set of pairs = {len(set(pairs))}")
    pprint(f"len loners = {len(loners)}")
    pprint(f"len set of loners = {len(set(loners))}")
    assert False


def test_queue(get_pairs):
    pairs, loners = get_pairs
    pprint(f"len pairs = {len(pairs)}")
    pprint(f"len set of pairs = {len(set(pairs))}")
    pprint(f"len loners = {len(loners)}")
    pprint(f"len set of loners = {len(set(loners))}")
    assert False


def test_smart_queue(get_smart_queue):
    pairs, loners = get_smart_queue
    pprint(f"len pairs = {len(pairs)}")
    pprint(f"len set of pairs = {len(set(pairs))}")
    pprint(f"len loners = {len(loners)}")
    pprint(f"len set of loners = {len(set(loners))}")
    assert False
