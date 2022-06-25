import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from datetime import date, datetime


Base = declarative_base()
with open('tokens/database.txt') as conf:
    engine = sa.create_engine(conf.read(), echo=True, future=True)


def get_id_user(user: object) -> int:
    """
    В передаваемых объектах пустое поле id_user, его надо получать из таблицы users
    :param user: объект типа Users
    :return: id_user
    """
    with Session(engine) as session:
        stmt = sa.select(Users).where(Users.id_vk == user.id_vk)
        user = session.scalars(stmt).one()
    return user.id_user


def get_id_user_from_vk(id_vk: int) -> int:
    """
    Получает id_user из users, если в передаваемом объекте в этом поле содержится id_vk
    :param id_vk:
    :return: id_user
    """
    with Session(engine) as session:
        stmt = sa.select(Users).where(Users.id_vk == id_vk)
        user = session.scalars(stmt).one()
    return user.id_user


class Status(Base):
    """
    Справочник статуса кандидатов. 0 - не просмотрено, 1 - просмотрено, 2 - в избранном, 3 - в чёрном списке.
    """
    __tablename__ = 'status'
    id_status = sa.Column(sa.SmallInteger, primary_key=True)
    status = sa.Column(sa.String(20))

    def __repr__(self):
        return f'Status(id={self.id_status}, status={self.status})'


class Relation(Base):
    """
    Справочник статуса отношений пользователя.
    1 - свободен(-на), 2 - встречается, 3 - помолвка, 4 - в браке, 5 - всё сложно, 6 - в активном поиске,
    7 - влюблён(-а), 8 - гражданский брак, 0 - не указано (любой).
    """
    __tablename__ = 'relation'
    id_relation = sa.Column(sa.SmallInteger, primary_key=True)
    relation = sa.Column(sa.String(40))

    users = relationship('Users')  # , back_populates='relation')
    req_params = relationship('ReqParams')  # , back_populates='relation')

    def __repr__(self):
        return f'Relation(id={self.id_relation}, relation={self.relation})'


class Sex(Base):
    """
    Справочник полов. 1 - женский, 2 - мужской, 0 - любой (не указан)
    """
    __tablename__ = 'sex'
    id_sex = sa.Column(sa.SmallInteger, primary_key=True)
    sex = sa.Column(sa.String(10))

    users = relationship('Users')  # , back_populates='sex')
    req_params = relationship('ReqParams')  # , back_populates='sex')

    def __repr__(self):
        return f'Sex(id={self.id_sex}, sex={self.sex})'


class DataBase:
    """ Базовый класс для взаимодействия с БД """
    def insert(self):
        """
        Вставка записи в таблицу
        :return: None
        """
        with Session(engine) as session:
            session.add(self)
            session.commit()
        return None


class Users(DataBase, Base):
    """
    Основная таблица пользователей и кандидатов. Содержит идентификаторы ВК (цифровой и строковый), имя и фамилию,
    дату рождения, пол, статус отношений, город, а также ссылку на аккаунт
    """
    __tablename__ = 'users'
    id_user = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    id_vk = sa.Column(sa.Integer)
    id_vk_str = sa.Column(sa.String(80))
    first_name = sa.Column(sa.String(80))
    last_name = sa.Column(sa.String(80))
    id_sex = sa.Column(sa.SmallInteger, sa.ForeignKey('sex.id_sex'))
    id_city = sa.Column(sa.Integer)
    bdate = sa.Column(sa.Date)
    id_relation = sa.Column(sa.SmallInteger, sa.ForeignKey('relation.id_relation'))
    url = sa.Column(sa.String(160))

    sex = relationship('Sex', back_populates='users')
    relation = relationship('Relation', back_populates='users')
    # us_user = relationship('UserCandidate', back_populates='users')
    # uc_candidate = relationship('UserCandidate', back_populates='candidate')
    photo = relationship('Photo', back_populates='users')
    req_params = relationship('ReqParams')  # , back_populates='users')

    def __init__(self, id_vk, id_vk_str, first_name, last_name, id_sex, id_city, bdate, id_relation, url):
        """ Инициализация объекта Users """
        self.id_vk = id_vk
        self.id_vk_str = id_vk_str
        self.first_name = first_name
        self.last_name = last_name
        self.id_sex = id_sex
        self.id_city = id_city
        self.bdate = bdate
        self.id_relation = id_relation
        self.url = url

    def __repr__(self):
        return f'Users(id={self.id_user}, id_vk={self.id_vk}, name={" ".join((self.first_name, self.last_name))} ' \
               f'sex={self.id_sex}, bdate={self.bdate}, relation={self.id_relation}, city={self.id_city})'

    def update(self):
        """
        Обновление информации о существующем пользователе. Может изменить имя, пол, дату рождения, город, статус
        отношений, урл. Остаются идентификаторы в таблице и ВК.
        :return:
        """
        with Session(engine) as session:
            stmt = sa.select(Users).where(Users.id_vk == self.id_vk)
            user = session.scalars(stmt).one()
            user.first_name = self.first_name
            user.last_name = self.last_name
            user.id_sex = self.id_sex
            user.id_city = self.id_city
            user.bdate = self.bdate
            user.id_relation = self.id_relation
            user.url = self.url
            session.commit()


class UserCandidate(DataBase, Base):
    """
    Таблица кандидатов для пользователя. Содержит идентификаторы пользователя, кандидатов, а также статус каждого
    кандидата для текущего пользователя и дату последней модификации (добавления) записи. Связь N-N с users.
    """
    __tablename__ = 'user_candidate'
    id_user_candidate = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    id_user = sa.Column(sa.Integer, sa.ForeignKey('users.id_user'))
    id_candidate = sa.Column(sa.Integer, sa.ForeignKey('users.id_user'))
    id_status = sa.Column(sa.SmallInteger, sa.ForeignKey('status.id_status'))
    search_date = sa.Column(sa.TIMESTAMP)

    users = relationship('Users', foreign_keys=[id_user])
    candidate = relationship('Users', foreign_keys=[id_candidate])

    def __init__(self, user, candidate):
        """ Инициализация объекта UserCandidate """
        self.id_user = get_id_user(user)
        self.id_candidate = get_id_user(candidate)
        self.id_status = 0
        self.search_date = datetime.now().isoformat()

    def __repr__(self):
        return f'UserCandidate(id={self.id_user_candidate}, pair={"-".join((self.id_user, self.id_candidate))}, ' \
               f'status={self.id_status}, searched={self.search_date})'

    def update(self, candidate: object, id_status: int) -> None:
        """
        Обновляет статус и дату модификации кандидата для текущего пользователя.
        """
        with Session(engine) as session:
            stmt = sa.select(Users).where(Users.id_vk == self.id_vk)
            user = session.scalars(stmt).one()
            stmt = sa.select(Users).where(Users.id_vk == candidate.id_vk)
            cand = session.scalars(stmt).one()
            stmt = sa.select(UserCandidate).where(UserCandidate.id_user == user.id_user, UserCandidate.id_candidate ==
                                                  cand.id_user)
            rec = session.scalars(stmt).one()
            rec.id_status = id_status
            rec.search_date = datetime.now().isoformat()
            session.commit()

    def is_exists(self) -> bool:
        """
        Проверяет наличие непоказанных кандидатов для пользователя
        :return: True - есть кандидаты в БД; False - нет кандидатов
        """
        with Session(engine) as session:
            if sa.exists().where(UserCandidate.id_user == self.id_user, UserCandidate.id_status == 0):
                return True
            else:
                return False


class Photo(DataBase, Base):
    """
    Таблица фотографий пользователя. Содержит идентификар пользователя из таблицы users, ссылку на фото, количество
    лайков. Связь N-1 с users.
    """
    __tablename__ = 'photo'
    id_photo = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    id_user = sa.Column(sa.Integer, sa.ForeignKey('users.id_user'))
    url = sa.Column(sa.String(160))
    likes_count = sa.Column(sa.Integer)

    users = relationship('Users')  # , back_populates='photo')

    def __init__(self, user, url, likes_count):
        """ Инициализация объекта Photo """
        self.id_user = get_id_user(user)
        self.url = url
        self.likes_count = likes_count

    def __repr__(self):
        return f'Photo(id={self.id_photo}, user={self.id_user}, likes={self.likes_count}, liked={self.liked}, ' \
               f'url={self.url})'

    def update(self, user: object) -> None:
        """
        Обновляет количество лайков в таблице Photo либо добавляет новую запись, если фото там ещё не было
        """
        # TODO check if it works
        self.id_user = get_id_user(user)
        with Session(engine) as session:
            # если фото уже есть - обновляем количество лайков
            if sa.exists().where(Photo.id_user == self.id_user, Photo.url == self.url):
                stmt = sa.select(Photo).where(Photo.id_user == self.id_user, Photo.url == self.url)
                ph = session.scalars(stmt).one()
                ph.likes_count = self.likes_count
            # если нет - добавляем в таблицу
            else:
                self.insert()
            session.commit()


class ReqParams(DataBase, Base):
    """
    Таблица с текущим поисковым запросом пользователя. Содержит параметры запроса: город, пол, диапазон возраста,
    статус отношений. Связь 1-1 с users.
    """
    __tablename__ = 'req_params'
    id_user = sa.Column(sa.Integer, sa.ForeignKey('users.id_user'), primary_key=True)
    id_sex = sa.Column(sa.SmallInteger, sa.ForeignKey('sex.id_sex'))
    id_city = sa.Column(sa.Integer)
    age_from = sa.Column(sa.SmallInteger)
    age_to = sa.Column(sa.SmallInteger)
    id_relation = sa.Column(sa.SmallInteger, sa.ForeignKey('relation.id_relation'))

    users = relationship('Users', back_populates='req_params')
    sex = relationship('Sex', back_populates='req_params')
    relation = relationship('Relation', back_populates='req_params')

    def __init__(self, user: object, id_sex: int, age_from: int, age_to: int, id_city: int, id_relation: int) -> None:
        """ Инициализация объекта ReqParams"""
        self.id_user = get_id_user(user)
        self.id_sex = id_sex
        self.id_city = id_city
        self.age_from = age_from
        self.age_to = age_to
        self.id_relation = id_relation

    def __repr__(self):
        return f'ReqParams(id={self.id_user}: sex={self.id_sex}, age from {self.age_from} to {self.age_to}, ' \
               f'city={self.id_city}, relation={self.id_relation})'
