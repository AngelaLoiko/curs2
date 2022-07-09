import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

import settings

Base = declarative_base()
if settings.params['use_database']:
    with open('tokens/database.txt') as conf:
        engine = sa.create_engine(conf.read(), echo=True, future=True)


def get_dic() -> dict:
    return {
                  "sex": {
                      "1": "женский",
                      "2": "мужской"
                   },
                  "relation": {
                       "1": "не женат/не замужем",
                       "2": "есть друг/есть подруга",
                       "3": "помолвлен/помолвлена",
                       "4": "женат/замужем",
                       "5": "всё сложно",
                       "6": "в активном поиске",
                       "7": "влюблён/влюблена",
                       "8": "в гражданском браке"
                   }
                 }


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


def get_user_by_vk(id_vk: int, session=None) -> object:
    """
    Получает объект user из users по имеющемуся id_vk
    :param session:
    :param id_vk:
    :return: User object
    """
    if session:
        stmt = sa.select(Users).where(Users.id_vk == id_vk)
        user = session.scalars(stmt).one_or_none()
    else:
        with Session(engine) as session:
            stmt = sa.select(Users).where(Users.id_vk == id_vk)
            user = session.scalars(stmt).one_or_none()
    return user


def get_user_by_id(id_user: int, session=None) -> object:
    """
    Получает объект user из users по имеющемуся id_user
    :param session:
    :param id_user:
    :return: user
    """
    if session:
        stmt = sa.select(Users).where(Users.id_user == id_user)
        user = session.scalars(stmt).one()
    else:
        with Session(engine) as session:
            stmt = sa.select(Users).where(Users.id_user == id_user)
            user = session.scalars(stmt).one()
    return user


def select_photos(id_user: int) -> dict:
    """
    Выбирает до 3 фото с максимальным количеством лайков из таблицы photo для пользователя с id_user
    :return: list of `photo` objects
    """
    res_dict = {'photos': []}
    with Session(engine) as session:
        user = get_user_by_vk(id_user, session=session)
        stmt = sa.select(Photo).where(Photo.id_user == user.id_user).limit(3)
        photo_list = session.scalars(stmt).all()
        for ph in photo_list:
            res_dict['photos'].append({'photo_id': ph.id_photo_vk, 'owner_id': ph.id_user, 'likes': ph.likes_count})
        return res_dict


def get_offset(id_user: int) -> int:
    """
    Получает сдвиг для функции поиска в ВК
    :param id_user: идентификатор ВК текущего пользователя
    :return:
    """
    with Session(engine) as session:
        user = get_user_by_vk(id_user, session=session)
        if user:
            stmt = sa.select(UserCandidate).where(UserCandidate.id_user == user.id_user)
            offset = len(session.scalars(stmt).all())
        else:
            offset = 0
    return offset


def session_start():
    return Session(engine)


def session_end(session):
    session.commit()
    session.close()


def select_candidates(id_vk_user: int) -> dict:
    """
    Возвращает словарь со списком кандидатов для пользователя
    :param id_vk_user: Идентификатор ВК пользователя
    :return: словарь со списком кандидатов
    """
    res_dict = {'count': 0, 'items': []}
    with Session(engine) as session:
        stmt = sa.select(Users).where(Users.id_vk == id_vk_user)
        user = session.scalars(stmt).one_or_none()
        if not user:
            # Пользователь отсутствует в users, значит, и кандидатов у него не будет
            return res_dict
        old_date = datetime.now() - timedelta(days=7)
        stmt = sa.select(UserCandidate).where(UserCandidate.id_user == user.id_user,
                                              sa.or_(UserCandidate.id_status == 0,
                                                     sa.and_(UserCandidate.id_status == 1,
                                                             UserCandidate.search_date < old_date.isoformat())))
        candidate_couples = session.scalars(stmt).all()
        for couple in candidate_couples:
            stmt = sa.select(Users).where(Users.id_user == couple.id_candidate)
            candidate = session.scalars(stmt).one_or_none()
            if candidate:
                # Кандидат есть в users, добавляем в выдачу
                res_dict['count'] += 1
                res_dict['items'].append({'id': candidate.id_vk,
                                          'bdate': candidate.bdate.strftime('%d.%m.%Y'),
                                          'city': {'id': candidate.id_city, 'title': ''},
                                          'relation': candidate.id_relation,
                                          'sex': candidate.id_sex,
                                          'screen_name': candidate.id_vk_str,
                                          'first_name': candidate.first_name,
                                          'last_name': candidate.last_name})
        return res_dict


def add_candidates(vk_user: dict, candidate_list: dict) -> None:
    """
    Добавляет кандидатов из ВК в users и user_candidate. Если такой кандидат уже есть - обновляет информацию. Если
    самого пользователя ещё нет в базе - добавляет и его.
    :param vk_user: Словарь с данными пользователя из ВК, для которого найдены кандидаты
    :param candidate_list: Словарь со списком кандидатов из ВК
    :return: None
    """
    '''Процедура пытается смержить эту информацию с той которая есть в базе - по айдишнику искать, есть ли такой
    кандидат в списке, если такого кандидата нет- добавить, если есть, если флаг он был просмотрен- вообще ничего
    делать не надо- можем скипнуть эту запись, это может быть если что -то с офсетом пошло не так. А если флаг стоит, 
    что он еще не просмотрен, то эту запись нужно обновить- используя полученную информацию'''
    with Session(engine) as session:
        db_user = get_user_by_vk(vk_user['id'])
        if not db_user:
            # Пользователя нет в базе, надо добавить
            db_user = Users(vk_user['id'],
                            vk_user['screen_name'],
                            vk_user['first_name'],
                            vk_user['last_name'],
                            vk_user['sex'],
                            vk_user.get('city').get('id', 0),
                            vk_user['bdate'],
                            vk_user.get('relation', 0),
                            'https://vk.com/' + vk_user['screen_name'])
            db_user.insert(session=session)
            session.commit()

        for candidate in candidate_list['items']:
            db_cand = get_user_by_vk(candidate['id'], session=session)
            if db_cand:
                # Кандидат уже есть в users
                couple = UserCandidate(db_user, db_cand)
                couple = couple.find_couple(couple.id_user, couple.id_candidate, session=session)
                if couple:
                    # Уже есть пара с этим кандидатом. Если статус не 0 - идём дальше
                    if couple.id_status != 0:
                        continue
                    # else: если 0, то вроде нечего с ней делать
                else:
                    # Добавляем пару
                    couple = UserCandidate(db_user, db_cand)
                    couple.insert(session=session)
            else:
                # Кандидата ещё нет, надо добавить его и пару с ним
                db_cand = Users(candidate['id'],
                                candidate['screen_name'],
                                candidate['first_name'],
                                candidate['last_name'],
                                candidate['sex'],
                                candidate.get('city').get('id', 0),
                                candidate['bdate'],
                                candidate.get('relation', 0),
                                'https://vk.com/' + candidate['screen_name'])
                db_cand.insert(session=session)
                session.commit()
                couple = UserCandidate(db_user, db_cand)
                couple.insert(session=session)
        session.commit()


def couple_update(id_vk_user: int, id_vk_cand: int, new_status: int) -> None:
    """
    Обновление статуса пары
    :param id_vk_user:
    :param id_vk_cand:
    :param new_status:
    :return:
    """
    with Session(engine) as session:
        db_user = get_user_by_vk(id_vk_user, session=session)
        db_cand = get_user_by_vk(id_vk_cand, session=session)
        if db_cand and db_user:
            db_couple = UserCandidate(db_user, db_cand)
            db_couple = db_couple.find_couple(db_couple.id_user, db_couple.id_candidate, session=session)
            db_couple.update(id_status=new_status, session=session)


def show_favorites(id_vk: int) -> list:
    """
    Возвращает словарь с избранными кандидатами для текущего пользователя
    :param: id_vk Идентификатор ВК текущего пользователя
    :return: list with dicts
    """
    res_list = []
    with Session(engine) as session:
        user = get_user_by_vk(id_vk, session=session)
        if user:
            stmt = sa.select(UserCandidate).where(UserCandidate.id_user == user.id_user,
                                                  UserCandidate.id_status == 2)
            favorites = session.scalars(stmt).all()
            for cand in favorites:
                stmt = sa.select(Users).where(Users.id_user == cand.id_candidate)
                candidate = session.scalars(stmt).one_or_none()
                if candidate:
                    res_list.append({'first_name': candidate.first_name,
                                     'last_name': candidate.last_name,
                                     'vk_id': candidate.id_vk,
                                     'elected': True})
    return res_list


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
    def insert(self, session=None):
        """
        Вставка записи в таблицу
        :return: None
        """
        if session:
            session.add(self)
        else:
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

    def select_pair(self, session=None) -> object:
        """
        Выбирает кандидата из таблицы user_candidate (при наличии)
        :return: объект UserCandidate
        """
        if session:
            old_date = datetime.now() - timedelta(days=7)
            stmt = sa.select(UserCandidate).where(UserCandidate.id_user == self.id_user,
                                                  sa.or_(UserCandidate.id_status == 0,
                                                         sa.and_(UserCandidate.id_status == 1,
                                                         UserCandidate.search_date < old_date.isoformat())))
            new_pair = session.scalars(stmt).first()
            return new_pair
        else:
            return None


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
        return f'UserCandidate(id={self.id_user_candidate}, pair={self.id_user}-{self.id_candidate}, ' \
               f'status={self.id_status}, searched={self.search_date})'

    def update(self, id_status: int, session=None) -> None:
        """
        Обновляет статус и дату модификации текущей пары.
        """
        if session:
            stmt = sa.select(UserCandidate).where(UserCandidate.id_user == self.id_user, UserCandidate.id_candidate ==
                                                  self.id_candidate)
            rec = session.scalars(stmt).one_or_none()
            rec.id_status = id_status
            rec.search_date = datetime.now().isoformat()
            session.commit()

    def find_couple(self, id_user, id_candidate, session=None):
        """
        Находит пару по двум идентификаторам
        :param id_user:
        :param id_candidate:
        :param session:
        :return:
        """
        if session:
            stmt = sa.select(UserCandidate).where(UserCandidate.id_user == id_user,
                                                  UserCandidate.id_candidate == id_candidate)
            couple = session.scalars(stmt).one_or_none()
            return couple
        else:
            with Session(engine) as session:
                stmt = sa.select(UserCandidate).where(UserCandidate.id_user == id_user,
                                                      UserCandidate.id_candidate == id_candidate)
                couple = session.scalars(stmt).one_or_none()
                return couple


class Photo(DataBase, Base):
    """
    Таблица фотографий пользователя. Содержит идентификар пользователя из таблицы users, идентификатор фото в ВК,
    количество лайков. Связь N-1 с users.
    """
    __tablename__ = 'photo'
    id_photo = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    id_user = sa.Column(sa.Integer, sa.ForeignKey('users.id_user'))
    id_photo_vk = sa.Column(sa.Integer)
    likes_count = sa.Column(sa.SmallInteger)

    users = relationship('Users')  # , back_populates='photo')

    def __init__(self, id_vk, id_photo_vk, likes_count):
        """ Инициализация объекта Photo """
        self.id_user = get_id_user(get_user_by_vk(id_vk))
        self.id_photo_vk = id_photo_vk
        self.likes_count = likes_count

    def __repr__(self):
        return f'Photo(id={self.id_photo}, user={self.id_user}, likes={self.likes_count}, ' \
               f'id_photo={self.id_photo_vk})'

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
