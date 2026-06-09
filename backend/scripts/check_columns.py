import pg8000
conn = pg8000.connect(host='localhost', port=5432, database='ai4edu', user='ai4edu', password='ai4edu_password')
cursor = conn.cursor()

# notes 表列
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'notes' ORDER BY ordinal_position")
print("notes columns:")
for i, row in enumerate(cursor.fetchall(), 1):
    print(f"  {i}. {row[0]}")

print()

# resources 表列
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'resources' ORDER BY ordinal_position")
print("resources columns:")
for i, row in enumerate(cursor.fetchall(), 1):
    print(f"  {i}. {row[0]}")

conn.close()
