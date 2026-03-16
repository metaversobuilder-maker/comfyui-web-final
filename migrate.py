import sqlite3
import json
from datetime import datetime

# Leer datos
with open('C:/Users/moncl/.openclaw/workspace/comfyui-web/migrate_jobs.json', 'r') as f:
    jobs = json.load(f)

# Conectar a la nueva DB
new_conn = sqlite3.connect('C:/Users/moncl/.openclaw/workspace/comfyui-web/backend/comfyui.db')
new_cursor = new_conn.cursor()

# Insertar cada job
inserted = 0
errors = 0
for job in jobs:
    try:
        prompt = ""
        if job.get('payload'):
            try:
                p = json.loads(job['payload'])
                prompt = p.get('prompt', '')
            except:
                prompt = job.get('payload', '')
        
        new_cursor.execute('''
            INSERT INTO jobs (type, status, payload, prompt, image_path, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            job['type'],
            job['status'],
            job.get('payload', ''),
            prompt,
            job.get('image_path'),
            job.get('created_at', datetime.now().isoformat()),
            job.get('completed_at')
        ))
        inserted += 1
    except Exception as e:
        print(f'Error: {e}')
        errors += 1

new_conn.commit()

# Verificar
new_cursor.execute('SELECT COUNT(*) FROM jobs')
count = new_cursor.fetchone()[0]

new_conn.close()

print(f'Migrados {inserted} jobs')
print(f'Errores: {errors}')
print(f'Total en nueva DB: {count}')
