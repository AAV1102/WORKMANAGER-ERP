import sqlite3

conn = sqlite3.connect('workmanager_erp.db')
c = conn.cursor()

columns_to_add = [
    ('telefono', 'TEXT', '""'),
    ('email', 'TEXT', '""'),
    ('salario', 'REAL', '0'),
    ('departamento', 'TEXT', '""'),
    ('performance', 'INTEGER', '0')
]

for col_name, col_type, default_val in columns_to_add:
    try:
        c.execute(f'ALTER TABLE empleados ADD COLUMN {col_name} {col_type} DEFAULT {default_val}')
        print(f'Columna {col_name} agregada exitosamente')
    except sqlite3.OperationalError as e:
        print(f'Columna {col_name} ya existe o error: {e}')

conn.commit()
conn.close()
print('Proceso completado')
