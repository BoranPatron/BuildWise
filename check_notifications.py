import sqlite3

conn = sqlite3.connect('buildwise.db')
cursor = conn.cursor()

# Check total count
cursor.execute('SELECT COUNT(*) FROM notifications')
count = cursor.fetchone()
print(f'Total notifications in DB: {count[0]}')

# Check recent notifications
cursor.execute('SELECT id, recipient_id, type, title, is_acknowledged, created_at FROM notifications ORDER BY id DESC LIMIT 10')
results = cursor.fetchall()
print('\nLatest notifications:')
for r in results:
    print(f'  ID={r[0]}, Recipient={r[1]}, Type={r[2]}, Title={r[3]}, Acknowledged={r[4]}, Created={r[5]}')

# Check resource allocations
cursor.execute('SELECT id, resource_id, trade_id, allocation_status, allocated_person_count FROM resource_allocations ORDER BY id DESC LIMIT 5')
allocs = cursor.fetchall()
print(f'\nRecent ResourceAllocations: {len(allocs)}')
for a in allocs:
    print(f'  ID={a[0]}, Resource={a[1]}, Trade={a[2]}, Status={a[3]}, PersonCount={a[4]}')

# Check resources
cursor.execute('SELECT id, service_provider_id, status, category FROM resources ORDER BY id DESC LIMIT 5')
resources = cursor.fetchall()
print(f'\nRecent Resources: {len(resources)}')
for res in resources:
    print(f'  ID={res[0]}, ServiceProvider={res[1]}, Status={res[2]}, Category={res[3]}')

conn.close()

