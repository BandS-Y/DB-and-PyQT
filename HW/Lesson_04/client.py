"""Программа-клиент"""


import sys
import json
import socket
import time
import argparse
import logging
import threading
# import logs.config_client_log
from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS, ACTION, \
    TIME, USER, ACCOUNT_NAME, SENDER, PRESENCE, RESPONSE, \
    ERROR, MESSAGE, MESSAGE_TEXT, DESTINATION, EXIT
from common.utils import get_message, send_message
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from decos import log
from metaclasses import ClientVerifier
import dis

# Инициализация клиентского логера
LOGGER = logging.getLogger('client')

"""
Класс формирования и отправки сообщений на сервер и взаимодействия с пользователем.
"""
class ClientSender(threading.Thread, metaclass=ClientVerifier):


    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def create_exit_message(self):
        """
        Функция создаёт словарь с сообщением о выходе
        """

        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    def create_message(self):
        """
        Функция запрашивает кому отправить сообщение и само сообщение,
        и отправляет полученные данные на сервер

        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
        except Exception as e:
            print(e)
            LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    def run(self):
        """
        Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения
        """

        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                send_message(self.sock, self.create_exit_message())
                print('Завершение соединения.')
                LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    def print_help(self):
        """
        Функция выводящяя справку по использованию
        """

        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')


    """
    Класс-приёмник сообщений с сервера. Принимает сообщения, выводит в консоль.
    """
class ClientReader(threading.Thread, metaclass=ClientVerifier):


    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        """
        Функция - обработчик сообщений других пользователей, поступающих с сервера
        Принимает сообщения, выводит в консоль. Завершается при потере соединения.
        """
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                          f'\n{message[MESSAGE_TEXT]}')
                    LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                f'\n{message[MESSAGE_TEXT]}')
                else:
                    LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                LOGGER.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                LOGGER.critical(f'Потеряно соединение с сервером.')
                break


@log
def create_presence(account_name):
    """
    Функция генерирует запрос о присутствии клиента
    """

    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


@log
def process_response_ans(message):
    """
    Функция разбирает ответ сервера на сообщение о присутствии,
    возвращает 200 если все ОК или генерирует исключение при ошибке
    :param message:
    :return:
    """
    LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def arg_parser():
    """
    Парсер аргументов коммандной строки
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        LOGGER.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    return server_address, server_port, client_name


def main():
    # Загружаем параметы коммандной строки
    server_address, server_port, client_name = arg_parser()

    """Сообщаем о запуске"""
    print(f'Консольный месседжер. Клиентский модуль. Имя пользователя: {client_name}')

    # Если имя пользователя не было задано, необходимо запросить пользователя.
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    LOGGER.info(
        f'Запущен клиент с параметрами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_ans(get_message(transport))
        LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        LOGGER.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except ServerError as error:
        LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        sys.exit(1)
    except (ConnectionRefusedError, ConnectionError):
        LOGGER.critical(
            f'Не удалось подключиться к серверу {server_address}:{server_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    else:
        # Если соединение с сервером установлено корректно,
        # запускаем клиентский процесс приёма сообщений
        # receiver = threading.Thread(target=message_from_server, args=(transport, client_name))
        receiver = ClientReader(client_name, transport)
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        # user_interface = threading.Thread(target=user_interactive, args=(transport, client_name))
        user_interface = ClientSender(client_name, transport)
        user_interface.daemon = True
        user_interface.start()

        LOGGER.debug('Запущены процессы')

        # Watchdog основной цикл, если один из потоков завершён,
        # то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках,
        # достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
