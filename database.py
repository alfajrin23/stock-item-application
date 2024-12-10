import sqlite3

# Function to create a database and the necessary tables
def create_database():
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(stok_barang)")
    columns = cursor.fetchall()
    print("Kolom dalam tabel stok_barang:")
    for column in columns:
        print(f"Nama: {column[1]}, Tipe: {column[2]}")  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stok_barang (
            id INTEGER PRIMARY KEY,
            nama_barang TEXT NOT NULL,
            brand TEXT NOT NULL,
            stok INTEGER NOT NULL,
            harga_jual TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS barang_masuk (
            id INTEGER PRIMARY KEY,
            id_barang INTEGER,
            jumlah INTEGER,
            tanggal TEXT,
            FOREIGN KEY (id_barang) REFERENCES stok_barang(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS barang_keluar (
            id INTEGER PRIMARY KEY,
            id_barang INTEGER,
            jumlah INTEGER,
            tanggal TEXT,
            FOREIGN KEY (id_barang) REFERENCES stok_barang(id)
        )
    ''')
    conn.commit()
    conn.close()

# Function to insert a new item into stok_barang
def insert_barang(nama_barang, brand, stok, harga_jual):
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stok_barang (nama_barang, brand, stok, harga_jual)
        VALUES (?, ?, ?, ?)
    ''', (nama_barang, brand, stok, harga_jual))
    conn.commit()
    conn.close()

# Function to fetch all items from stok_barang
def fetch_all_barang():
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stok_barang')
    rows = cursor.fetchall()
    conn.close()
    return rows

# Function to fetch barang masuk by date range
def fetch_barang_masuk_by_date(tanggal_awal, tanggal_akhir):
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sb.nama_barang, bm.tanggal, bm.jumlah
        FROM barang_masuk bm
        JOIN stok_barang sb ON bm.id_barang = sb.id
        WHERE bm.tanggal BETWEEN ? AND ?
    ''', (tanggal_awal, tanggal_akhir))
    rows = cursor.fetchall()
    conn.close()
    return rows

# Function to insert a new item into barang_masuk
def insert_barang_masuk(id_barang, jumlah, tanggal):
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO barang_masuk (id_barang, jumlah, tanggal)
        VALUES (?, ?, ?)
    ''', (id_barang, jumlah, tanggal))
    conn.commit()
    conn.close()

# Function to fetch all barang masuk
def fetch_all_barang_masuk():
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM barang_masuk')
    rows = cursor.fetchall()
    conn.close()
    return rows

# Function to fetch all barang keluar
def fetch_all_barang_keluar():
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM barang_keluar')
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_satuan_column():
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('ALTER TABLE stok_barang ADD COLUMN satuan TEXT')
    conn.commit()
    conn.close()



# Call the create_database function to ensure the database is created
create_database()
add_satuan_column()