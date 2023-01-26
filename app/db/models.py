import datetime

import peewee

from db import BaseModel, database


class Profession(BaseModel):
    id = peewee.AutoField()
    name = peewee.CharField()


class User(BaseModel):
    teleg_id = peewee.CharField(primary_key=True)
    teleg_username = peewee.CharField(null=True)
    is_admin = peewee.BooleanField(default=False)
    is_active = peewee.BooleanField(default=False)
    is_hr = peewee.BooleanField(default=False)
    first_name = peewee.CharField(null=True)
    last_name = peewee.CharField(null=True)
    _profession = peewee.ForeignKeyField(
        Profession, backref="users", null=True, on_delete="SET_NULL"
    )
    register_date = peewee.DateTimeField(default=datetime.datetime.now)
    last_matching_date = peewee.DateTimeField(default=datetime.datetime.now)

    @property
    def pairs(self) -> peewee.ModelSelect:
        return Pair.select().where(
            Pair.hr == self if self.is_hr else Pair.respondent == self
        )

    @property
    def profession(self) -> str:
        match self:
            case User(is_admin=True):
                return "Администратор этого бота"
            case User(is_hr=True):
                return "IT-рекрутер"
            case User(_profession=Profession() as profession):
                return profession.name
        return "Профессия не указана"

    @profession.setter
    def profession(self, profession: Profession | int):
        match profession:
            case Profession():
                self._profession = profession
            case int(pk):
                self._profession = Profession.get_by_id(pk)
            case _:
                raise ValueError(
                    f'Profession must be a "int" or "Profession", not {type(profession).__name__}'
                )

    @property
    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.teleg_username

    @full_name.setter
    def full_name(self, value: str):
        match value := value.split():
            case first_name, last_name:
                self.first_name, self.last_name = first_name, last_name
            case first_name,:
                self.first_name, self.last_name = first_name, None

    @property
    def mention(self):
        return f'<a href="tg://user?id={self.teleg_id}">{self.teleg_username or self.full_name}</a>'

    def __repr__(self) -> str:
        return f"<{type(self).__name__} @{self.teleg_username}>"

    def __str__(self):
        return f"@{self.teleg_username}"


class Pair(BaseModel):
    id = peewee.AutoField()
    hr = peewee.ForeignKeyField(User)
    respondent = peewee.ForeignKeyField(User, on_delete="CASCADE")
    match_date = peewee.DateField(default=datetime.datetime.now)
    complete = peewee.BooleanField(default=False)
    date_complete = peewee.DateField(null=True)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.hr} to {self.respondent}>"

    def __str__(self):
        return f"{self.hr} to {self.respondent}"


def create_tables() -> None:
    database.create_tables((User, Pair, Profession))
