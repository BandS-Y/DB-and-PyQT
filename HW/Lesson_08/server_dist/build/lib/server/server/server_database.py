"""
ORM с помощью SQLAalchemy.

SQLAalchemy требует предварительной установки:
у меня необходимо было ещё обновить утилиты
sudo apt-get install python3-distutils
pip install sqlalchemy

Декларативный стиль
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime


class ServerDB:
    """
    Класс - серверная база данных
    """
    Base = declarative_base()

    class AllUsers(Base):
        """
        Класс - отображение таблицы всех пользователей
        """
        # Создаём таблицу пользователей
        __tablename__ = 'all_users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        last_conn = Column(DateTime)
        passwd_hash = Column(String)
        pubkey = Column(Text)

        # Экземпляр этого класса - запись в таблице AllUsers
        def __init__(self, login, passwd_hash):
            self.login = login
            self.last_conn = datetime.datetime.now()
            self.passwd_hash = passwd_hash
            self.pubkey = None

    class ActiveUsers(Base):
        """
        Класс - отображение таблицы активных пользователей:
        """
        # Создаём таблицу активностей пользователей
        __tablename__ = 'active_users'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('all_users.id'), unique=True)
        ip = Column(String)
        port = Column(Integer)
        time_conn = Column(DateTime)

        #  Экземпляр этого класса - запись в таблице ActiveUsers
        def __init__(self, user, ip, port, time_conn):
            self.user = user
            self.ip = ip
            self.port = port
            self.time_conn = time_conn

    class LoginHistory(Base):
        """
        Класс - отображение таблицы истории входов
        """
        # Создаём таблицу истории входов в приложение
        __tablename__ = 'login_history'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('all_users.id'))
        ip = Column(String)
        port = Column(Integer)
        last_conn = Column(DateTime)

        # Экземпляр этого класса - запись в таблице LoginHistory
        def __init__(self, user, ip, port, last_conn):
            self.user = user
            self.ip = ip
            self.port = port
            self.last_conn = last_conn

    class UsersContacts(Base):
        """
        Класс - отображение таблицы контактов пользователей
        """
        # Создаём таблицу контактов пользователей
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('all_users.id'))
        contact = Column(String, ForeignKey('all_users.id'))

        # Экземпляр класса - запись в таблице UsersContacts
        def __init__(self, user, contact):
            self.user = user
            self.contact = contact

    class UsersHistory(Base):
        """
        Класс отображение таблицы истории действий
        """
        # Создаём таблицу истории пользователей
        __tablename__ = 'history'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('all_users.id'))
        sent = Column(Integer)
        accepted = Column(Integer)

        # Экземпляр класса - запись в таблице UsersHistory
        def __init__(self, user):
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        """
        Создаём движок базы данных
        SERVER_DATABASE - sqlite:///server_base_pre.db3
        echo=False - отключает вывод на экран sql-запросов
        pool_recycle - по умолчанию соединение с БД через 8 часов простоя обрывается
        Чтобы этого не случилось необходимо добавить pool_recycle=7200 (переустановка
        соединения через каждые 2 часа)
        """
        self.engine = create_engine(
            f'sqlite:///{path}',
            echo=False,
            pool_recycle=7200,
            connect_args={
                'check_same_thread': False})

        # Создаём таблицы
        self.Base.metadata.create_all(self.engine)

        # Создаём сессию
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Если в таблице активных пользователей есть записи, то их необходимо удалить
        # Когда устанавливаем соединение, очищаем таблицу активных пользователей
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip, port, key):
        """
        Функция выполняется при входе пользователя, фиксирует в базе сам факт входа
        обновляет открытый ключ пользователя при его изменении.
        :param username:
        :param ip:
        :param port:
        :return:
        """
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        rez = self.session.query(self.AllUsers).filter_by(login=username)
        # print(type(rez))
        # Если имя пользователя уже присутствует в таблице, обновляем время
        # последнего входа
        if rez.count():
            user = rez.first()
            user.last_conn = datetime.datetime.now()
            if user.pubkey != key:
                user.pubkey = key

        # Если нет, то создаём нового пользователя
        else:
            raise ValueError('Пользователь не зарегистрирован.')
            # # Создаем экземпляр класса self.AllUsers, через который передаем данные в таблицу
            # user = self.AllUsers(username)
            # self.session.add(user)
            # # Коммит здесь нужен, чтобы в db записался ID
            # self.session.commit()
            # user_in_history = self.UsersHistory(user.id)
            # self.session.add(user_in_history)

        # Теперь можно создать запись в таблицу активных пользователей о факте входа.
        # Создаем экземпляр класса self.ActiveUsers, через который передаем данные в таблицу
        new_active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)

        # и сохранить в историю входов
        # Создаем экземпляр класса self.LoginHistory, через который передаем данные в таблицу
        history = self.LoginHistory(user.id, ip, port, datetime.datetime.now())
        self.session.add(history)

        # Сохраняем изменения
        self.session.commit()

    def user_logout(self, username):
        """
        Функция фиксирует отключение пользователя
        и удаляет его из активных пользователей.
        :param username:
        :return:
        """
        # Запрашиваем пользователя, что покидает нас
        # получаем запись из таблицы AllUsers
        user = self.session.query(self.AllUsers).filter_by(login=username).first()

        # Удаляем его из таблицы активных пользователей.
        # Удаляем запись из таблицы ActiveUsers
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()

        # Применяем изменения
        self.session.commit()

    def add_user(self, name, passwd_hash):
        """
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        :param name:
        :param passwd_hash:
        :return:
        """

        user_row = self.AllUsers(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.UsersHistory(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        """
        Метод удаляющий пользователя из базы.
        :param name:
        :return:
        """

        user = self.session.query(self.AllUsers).filter_by(login=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(id=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(user=user.id).delete()
        self.session.query(
            self.UsersContacts).filter_by(
            contact=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user=user.id).delete()
        self.session.query(self.AllUsers).filter_by(login=name).delete()
        self.session.commit()

    def get_hash(self, name):
        """
        Метод получения хэша пароля пользователя.
        :param name:
        :return:
        """

        user = self.session.query(self.AllUsers).filter_by(login=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        """
        Метод получения публичного ключа пользователя.
        :param name:
        :return:
        """

        user = self.session.query(self.AllUsers).filter_by(login=name).first()
        return user.pubkey

    def check_user(self, name):
        """
        Метод проверяющий существование пользователя.
        :param name:
        :return:
        """

        if self.session.query(self.AllUsers).filter_by(login=name).count():
            return True
        else:
            return False

    def users_list(self):
        """
        Функция возвращает список известных пользователей со временем последнего входа.
        :return:
        """
        # Запрос строк таблицы пользователей.
        query = self.session.query(
            self.AllUsers.login,
            self.AllUsers.last_conn,
        )
        # Возвращаем список кортежей
        return query.all()

    def active_users_list(self):
        """
        Функция возвращает список активных пользователей
        :return:
        """
        # Запрашиваем соединение таблиц и собираем кортежи - имя, адрес, порт, время.
        query = self.session.query(
            self.AllUsers.login,
            self.ActiveUsers.ip,
            self.ActiveUsers.port,
            self.ActiveUsers.time_conn
        ).join(self.AllUsers)

        # Возвращаем список кортежей
        return query.all()

    def login_history(self, username=None):
        """
        Функция возвращает историю входов по пользователю или по всем пользователям
        :param username:
        :return:
        """
        # Запрашиваем историю входа
        query = self.session.query(self.AllUsers.login,
                                   self.LoginHistory.last_conn,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)

        # Если было указано имя пользователя, то фильтруем по нему
        if username:
            query = query.filter(self.AllUsers.login == username)
        return query.all()

    def process_message(self, sender, recipient):
        """
        Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
        :param sender:
        :param recipient:
        :return:
        """
        # Получаем ID отправителя и получателя
        sender = self.session.query(self.AllUsers).filter_by(login=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(login=recipient).first().id

        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        """
        Функция добавляет контакт для пользователя.
        :param user:
        :param contact:
        :return:
        """
        # Получаем ID пользователей
        user = self.session.query(self.AllUsers).filter_by(login=user).first()
        contact = self.session.query(self.AllUsers).filter_by(login=contact).first()

        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return

        # Создаём объект и заносим его в базу
        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        """
        Функция удаляет контакт из базы данных
        :param user:
        :param contact:
        :return:
        """
        # Получаем ID пользователей
        user = self.session.query(self.AllUsers).filter_by(login=user).first()
        contact = self.session.query(self.AllUsers).filter_by(login=contact).first()

        # Проверяем что контакт может существовать (полю пользователь мы доверяем)
        if not contact:
            return

        # Удаляем требуемое
        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete()
        self.session.commit()

    def get_contacts(self, username):
        """
        Функция возвращает список контактов пользователя.
        :param username:
        :return:
        """
        # Запрашиваем указанного пользователя
        user = self.session.query(self.AllUsers).filter_by(login=username).one()

        # Запрашиваем его список контактов
        query = self.session.query(self.UsersContacts, self.AllUsers.login). \
            filter_by(user=user.id). \
            join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)

        # выбираем только имена пользователей и возвращаем их.
        return [contact[1] for contact in query.all()]

    def message_history(self):
        """
        Функция возвращает количество переданных и полученных сообщений.
        :return:
        """
        query = self.session.query(
            self.AllUsers.login,
            self.AllUsers.last_conn,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)

        # Возвращаем список кортежей
        return query.all()


# Отладка
if __name__ == '__main__':
    db = ServerDB('../server/server_database.db3')

    # Выполняем "подключение" пользователя
    db.user_login('client_1', '192.168.1.4', 7778)
    db.user_login('client_2', '192.168.1.5', 7777)

    # выводим список кортежей - активных пользователей
    print(db.active_users_list())

    # выполняем 'отключение' пользователя
    db.user_logout('client_1')
    print(db.users_list())

    # выводим список активных пользователей
    print(db.active_users_list())
    db.user_logout('client_2')
    print(db.users_list())
    print(db.active_users_list())

    # запрашиваем историю входов по пользователю
    db.login_history('client_1')

    # выводим список известных пользователей
    print(db.users_list())
