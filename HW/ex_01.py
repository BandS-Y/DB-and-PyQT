"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
 Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
 В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
 («Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции
 ip_address(). (Внимание! Аргументом сабпроцеса должен быть список, а не строка!!!
 Крайне желательно использование потоков.)
"""

import platform
import subprocess
import threading
from ipaddress import ip_address

# out_ip_ping = {'Reachable': "", 'Unreachable': ""} # таблица результатов сканирования
out_ip_ping = []

def test_ipaddr(value):
    """
    Проверка является ли введённое значение IP адресом
    """
    try:
        ip_addr = ip_address(value)
    except ValueError:
        raise Exception('не является ip адресом')
    return ip_addr


def ping(ip_addr):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    response = subprocess.Popen(["ping", param, '1', str(ip_addr)], stdout=subprocess.PIPE)
    if response.wait() == 0:
        out_ip_ping.append({'Reachable': str(ip_addr)})
    else:
        out_ip_ping.append({'Unreachable': str(ip_addr)})
        # pass



def host_ping(hosts_list):
    """
    Функция проверки доступности узлов.
    """
    threads = []
    for host in hosts_list:
        try:
            ip_addr = test_ipaddr(host)
        except Exception as e:
            print(f'{host} - {e} - считаем доменным именем')
            ip_addr = host

        thread = threading.Thread(target=ping, args=(ip_addr, ), daemon=True)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    return out_ip_ping


if __name__ == '__main__':
    hosts_list = ['192.168.0.1', '8.8.8.8', 'yandex.ru', 'google.com', 'mail.ru',
                  '10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5']
    host_res_ping = host_ping(hosts_list)
    for host in host_res_ping:
        if 'Reachable' in host:
             print(f"{host.pop('Reachable')} - «Узел доступен»")
        else:
            print(f"{host.pop('Unreachable')} - «Узел НЕ доступен»")

