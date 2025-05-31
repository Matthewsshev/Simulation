import os
import sqlite3
from datetime import datetime

def connect_db(name):
    now = datetime.now()
    day, month, year = map(int, now.strftime("%d %m %Y").split())
    db_name = name + f'_{day}_{month}_{year}'
    for i in range(0, 19):
        temp = db_name + f'_{i}.db'
        if not os.path.isfile(temp):
            conn = sqlite3.connect(temp)
            dump_file = 'Instruction/dump.sql'
            with open(dump_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()
                conn.executescript(sql_script)
            return conn
    raise RuntimeError("No available DB slots found.")
