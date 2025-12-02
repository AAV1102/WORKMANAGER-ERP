import sqlite3

conn = sqlite3.connect('workmanager_erp.db')
c = conn.cursor()
c.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = c.fetchall()
print('Tables:', [t[0] for t in tables])
conn.close()
