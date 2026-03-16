import sqlite3
conn = sqlite3.connect('C:/Users/moncl/.openclaw/workspace/comfyui-web/backend/comfyui.db')
cursor = conn.cursor()
cursor.execute("UPDATE jobs SET type='image' WHERE type='imagen'")
conn.commit()
print('Actualizado')
cursor.execute('SELECT type, status, COUNT(*) FROM jobs GROUP BY type, status')
for row in cursor.fetchall():
    print(row)
conn.close()
