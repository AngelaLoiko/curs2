import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from datetime import date


Base = declarative_base()
with open('../tokens/database.txt') as conf:
    engine = sa.create_engine(conf.read(), echo=True, future=True)


class Status(Base):
    __tablename__ = 'status'
    id_status = sa.Column(sa.SmallInteger, primary_key=True)
    status = sa.Column(sa.String(20))

    def __repr__(self):
        return f'Status(id={self.id_status}, status={self.status})'


class Relation(Base):
    __tablename__ = 'relation'
    id_relation = sa.Column(sa.SmallInteger, primary_key=True)
    relation = sa.Column(sa.String(40))

    users = relationship('Users', back_populates='relation')
    req_params = relationship('ReqParams', back_populates='relation')

    def __repr__(self):
        return f'Relation(id={self.id_relation}, relation={self.relation})'


class Sex(Base):
    __tablename__ = 'sex'
    id_sex = sa.Column(sa.SmallInteger, primary_key=True)
    sex = sa.Column(sa.String(10))

    users = relationship('Users', back_populates='sex')
    req_params = relationship('ReqParams', back_populates='sex')

    def __repr__(self):
        return f'Sex(id={self.id_sex}, sex={self.sex})'


class Users(Base):
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
    req_params = relationship('ReqParams', back_populates='users')

    def __init__(self, id_vk, id_vk_str, first_name, last_name, id_sex, id_city, bdate, id_relation, url):
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

    def insert(self):
        with Session(engine) as session:
            session.add(self)
            session.commit()


class UserCandidate(Base):
    __tablename__ = 'user_candidate'
    id_user_candidate = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    id_user = sa.Column(sa.Integer, sa.ForeignKey('users.id_user'))
    id_candidate = sa.Column(sa.Integer, sa.ForeignKey('users.id_user'))
    id_status = sa.Column(sa.SmallInteger, sa.ForeignKey('status.id_status'))
    search_date = sa.Column(sa.TIMESTAMP)

    users = relationship('Users', foreign_keys=[id_user])
    candidate = relationship('Users', foreign_keys=[id_candidate])

    def __repr__(self):
        return f'UserCandidate(id={self.id_user_candidate}, pair={"-".join((self.id_user, self.id_candidate))}, ' \
               f'status={self.id_status}, searched={self.search_date})'


class Photo(Base):
    __tablename__ = 'photo'
    id_photo = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    id_user = sa.Column(sa.Integer, sa.ForeignKey('users.id_user'))
    url = sa.Column(sa.String(160))
    likes_count = sa.Column(sa.Integer)
    liked = sa.Column(sa.Boolean)

    users = relationship('Users', back_populates='photo')

    def __repr__(self):
        return f'Photo(id={self.id_photo}, user={self.id_user}, likes={self.likes_count}, liked={self.liked}, ' \
               f'url={self.url})'


class ReqParams(Base):
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

    def __repr__(self):
        return f'ReqParams(id={self.id_user}: sex={self.id_sex}, age from {self.age_from} to {self.age_to}, ' \
               f'city={self.id_city}, relation={self.id_relation})'


# def test_insert(rec):
#     with Session(engine) as session:
#         status4 = Status(id_status=4, status='Wow!')
#         session.add(status4)
#         session.commit()
me = Users(id_vk=560238635, id_vk_str='id560238635', first_name='Пётр', last_name='Кравцов', id_sex=2, id_city=312,
           bdate=date(1984, 11, 15), id_relation=6, url='https://vk.com/id4654256')
me.insert()
