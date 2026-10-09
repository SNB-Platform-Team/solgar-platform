# -*- coding: utf-8 -*-
import io
p = r'sales\pharmacy_simple_configs.py'
s = io.open(p, encoding='utf-8').read()

OLD = '"AZERIMED": _sv("AZERIMED", \'Наименование\', \'Адрес\', \'Продажи кол-vo\', \'\', \'Номер Аптеки\', \'\', \'\', \'\', \'Продажи кол-vo\'),'
NEW = '"AZERIMED": _sv("AZERIMED", \'Наименование\', \'Адрес\', \'Продажи кол-во\', \'\', \'Номер Аптеки\', \'\', \'\', \'\', \'Продажи кол-во\'),'

print('FOUND' if OLD in s else 'NOT FOUND')
if OLD in s:
    s = s.replace(OLD, NEW, 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('REPLACED')