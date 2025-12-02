import sqlite3

conn = sqlite3.connect('workmanager_erp.db')
c = conn.cursor()

# New columns for temporary user workflow
columns_to_add = [
    ('temp_user_flag', 'INTEGER', '0'),  # 0 = normal user, 1 = temporary user
    ('hr_completed', 'INTEGER', '0'),    # 0 = not completed, 1 = HR data filled
    ('tech_completed', 'INTEGER', '0'),  # 0 = not completed, 1 = technical data filled
    ('created_by_assignment', 'INTEGER', '0'),  # 0 = normal creation, 1 = created during assignment
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
