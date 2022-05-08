"""
ORM для клиента
Декларативный стиль
"""

import sys
import logging

sys.path.append('../')
from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from common.variables import *
import datetime


class ClientDatabase:
    """
    Класс - база данных сервера.
    """
    Base = declarative_base()

    class KnownUsers(Base):
        """
        # Класс - отображение таблицы известных пользователей.
        """
        # Создаём таблицу известных пользователей
        __tablename__ = 'known_users'
        id = Column(Integer, primary_key=True)
        username = Column(String)

        # Создаём экземпляр класса KnownUsers
        def __init__(self, user):
            self.username = user

    class MessageHistory(Base):
        """
        Класс - отображение таблицы истории сообщений
        """
        # Создаём таблицу истории сообщений
        __tablename__ = 'message_history'
        id = Column(Integer, primary_key=True)
        from_user = Column(String)
        to_user = Column(String)
        message = Column(Text)
        date = Column(DateTime)

        # Создаём экземпляр класса message_history
        def __init__(self, from_user, to_user, message):
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts(Base):
        """
        Класс - отображение списка контактов
        """
        # Создаём таблицу контактов
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True)

        # Создаём экземпляр класса contacts
        def __init__(self, contact):
            self.id = None
            self.name = contact

    # Конструктор класса:
    def __init__(self, name):
        """
        Создаём движок базы данных, поскольку разрешено несколько клиентов одновременно,
        каждый должен иметь свою БД.
        Поскольку клиент мультипоточный, то необходимо отключить проверки на подключения
        с разных потоков, иначе sqlite3.ProgrammingError
        echo=False - отключает вывод на экран sql-запросов
        pool_recycle - по умолчанию соединение с БД через 8 часов простоя обрывается
        Чтобы этого не случилось необходимо добавить pool_recycle=7200 (переустановка
        соединения через каждые 2 часа)
        """
        self.engine = create_engine(f'sqlite:///client_{name}.db3',
                                    echo=False,
                                    pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        # Создаём таблицы
        self.Base.metadata.create_all(self.engine)

        # Создаём сессию
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Необходимо очистить таблицу контактов, т.к. при запуске они подгружаются с сервера.
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        """
        Функция добавления контактов
        :param contact:
        :return:
        """
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def contacts_clear(self):
        """
        Метод, очищающий таблицу со списком контактов.
        :return:
        """
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def del_contact(self, contact):
        """
        Функция удаления контакта
        :param contact:
        :return:
        """
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    def add_users(self, users_list):
        """
        Функция добавления известных пользователей.
        Пользователи получаются только с сервера, поэтому таблица очищается.
        :param users_list:
        :return:
        """
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        """
        Функция сохраняет сообщения
        :param from_user:
        :param to_user:
        :param message:
        :return:
        """
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        """
        Функция возвращает контакты.
        :return:
        """
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        """
        Функция возвращает список известных пользователей.
        :return:
        """
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def check_user(self, user):
        """
        Функция проверяет наличие пользователя в таблице Известных Пользователей
        :param user:
        :return:
        """
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        """
        Функция проверяет наличие пользователя в таблице Контактов
        :param contact:
        :return:
        """
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, from_who=None, to_who=None):
        """
        Функция возвращает историю переписки
        :param from_who:
        :param to_who:
        :return:
        """
        query = self.session.query(self.MessageHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(to_user=to_who)
        return [(history_row.from_user, history_row.to_user, history_row.message, history_row.date)
                for history_row in query.all()]


# отладка
if __name__ == '__main__':
    test_db = ClientDatabase('test1')
    for i in ['test3', 'test4', 'test5']:
        test_db.add_contact(i)
    test_db.add_contact('test4')
    test_db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])
    test_db.save_message('test1', 'test2',
                         f'Привет! я тестовое сообщение от {datetime.datetime.now()}!')
    test_db.save_message('test2', 'test1',
                         f'Привет! я другое тестовое сообщение от {datetime.datetime.now()}!')
    print(test_db.get_contacts())
    print(test_db.get_users())
    print(test_db.check_user('test1'))
    print(test_db.check_user('test10'))
    print(test_db.get_history('test2'))
    print(test_db.get_history(to_who='test2'))
    print(test_db.get_history('test3'))
    test_db.del_contact('test4')
    print(test_db.get_contacts())
