"""
3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
 (использовать модуль tabulate). Таблица должна состоять из двух колонок и выглядеть примерно так:

Reachable
10.0.0.1
10.0.0.2

Unreachable
10.0.0.3
10.0.0.4
"""

from ex_02 import block_host_ping
from tabulate import tabulate

res = {'Reachable': "", "Unreachable": ""}

def host_in_tab():
    global ip_table
    ip_table = block_host_ping()
    print(ip_table)


if __name__ == "__main__":
    host_res_ping = block_host_ping()
    for host in host_res_ping:
        if 'Reachable' in host:
            res["Reachable"] += f"{host.pop('Reachable')}\n"
        else:
            res["Unreachable"] += f"{host.pop('Unreachable')}\n"
    print(tabulate([res], headers='keys'))
