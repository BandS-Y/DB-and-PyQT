"""
2. Написать функцию host_range_ping() (возможности которой основаны на функции из примера 1) для перебора ip-адресов
из заданного диапазона. Меняться должен только последний октет каждого адреса. По результатам проверки должно
выводиться соответствующее сообщение.
"""
from ex_01 import host_ping, test_ipaddr


def block_host_ping():
    while True:
        start_ip = input("Введите стартовый адрес: ")
        try:
            ip_start = test_ipaddr(start_ip)
            break
        except Exception as e:
            print(e)

    while True:
        end_ip = input("Укажите количество адресов для проверки?: ")
        if not end_ip.isnumeric():
            print("Необходимо ввести число")
        else:
            last_oct = int(start_ip.split('.')[3])  # вычисляем последний октет
            end_ip = int(end_ip)
            if (last_oct + end_ip) > 256:  # тестируем октет на переполнение
                print(f"максимальное число хостов может быть не более {256 - last_oct}")
            else:
                break

    host_list = []
    [host_list.append(ip_start + x) for x in range(end_ip)]

    return host_ping(host_list)

if __name__ == "__main__":

    host_res_ping = block_host_ping()
    for host in host_res_ping:
        if 'Reachable' in host:
            print(f"{host.pop('Reachable')} - «Узел доступен»")
        else:
            print(f"{host.pop('Unreachable')} - «Узел НЕ доступен»")
