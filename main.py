import tkinter as tk
from tkinter import messagebox
from tkinter.font import Font
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from fpdf import FPDF
from twilio.rest import Client
import requests

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
import matplotlib.gridspec as gridspec

import sqlite3

# Fungsi untuk membuat database
def buat_database():
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
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

buat_database()




# Fungsi untuk menampilkan dashboard
def tampil_dashboard():
    for widget in konten_frame.winfo_children():
        widget.destroy()
    
    dashboard_label = tk.Label(konten_frame, text="Selamat Datang di Aplikasi Persediaan Barang", font=("Helvetica", 16))
    dashboard_label.pack(pady=20)

# Fungsi untuk format angka menjadi RP
def format_rp(value, tick_number=None):  # Tambahkan tick_number sebagai argumen opsional
    if value is None:  # Menangani nilai None
        return "RP 0"
    return f"RP {value:,.0f}".replace(',', '.').replace('.', ',', 1)

# Fungsi untuk menampilkan grafik pendapatan
def format_func(value, tick_number):
    """Format angka menjadi format Rupiah."""
    if value is None:  # Menangani nilai None
        return "Rp 0"
    return f"Rp {value:,.0f}".replace(',', '.').replace('.', ',', 1)

def tampil_grafik_pendapatan():
    # Mengambil data pendapatan harian dan bulanan
    tanggal_harian = []
    pendapatan_harian = []
    
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    
    # Mendapatkan 7 hari terakhir
    for i in range(7):
        tanggal = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        tanggal_harian.append(tanggal)
        
        cursor.execute('''
            SELECT SUM(jumlah * harga_jual) FROM barang_keluar 
            JOIN stok_barang ON barang_keluar.id_barang = stok_barang.id 
            WHERE tanggal = ?
        ''', (tanggal,))
        row = cursor.fetchone()
        pendapatan_harian.append(row[0] if row[0] is not None else 0)

    # Format tanggal untuk sumbu X (hanya tanggal dan bulan)
    tanggal_harian_formatted = [datetime.strptime(t, '%Y-%m-%d').strftime('%d-%m') for t in tanggal_harian]

    # Mengambil pendapatan bulanan untuk 6 bulan terakhir
    cursor.execute('''
        SELECT strftime("%m", tanggal), SUM(jumlah * harga_jual) 
        FROM barang_keluar 
        JOIN stok_barang ON barang_keluar.id_barang = stok_barang.id 
        WHERE tanggal >= date('now', '-6 months') 
        GROUP BY strftime("%m", tanggal)
        ORDER BY strftime("%m", tanggal)
    ''')

    # Mengisi pendapatan bulanan
    pendapatan_dict = {str(i).zfill(2): 0 for i in range(1, 13)}  # Inisialisasi dengan 0 untuk semua bulan
    for row in cursor.fetchall():
        pendapatan_dict[row[0]] = row[1] if row[1] is not None else 0

    # Daftar bulan dengan singkatan 3 huruf
    bulan = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']

    # Mengambil bulan saat ini
    bulan_sekarang = datetime.now().month

    # Mengambil data untuk bulan sekarang dan 5 bulan sebelumnya
    pendapatan_bulanan = []
    for i in range(6):
        bulan_ke = (bulan_sekarang - i) % 12
        if bulan_ke == 0:  # Jika hasilnya 0, artinya itu bulan Desember
            bulan_ke = 12
        pendapatan_bulanan.append(pendapatan_dict[str(bulan_ke).zfill(2)])

    # Mengambil nama bulan untuk 6 bulan terakhir
    bulan_terakhir = [bulan[(bulan_sekarang - i - 1) % 12] for i in range(6)]

    # Membuat grafik dengan gridspec
    fig = plt.figure(figsize=(14, 5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[2, 1])  # Atur rasio lebar

    # Grafik Pendapatan Harian (Area Chart)
    axs0 = fig.add_subplot(gs[0])  # Menambahkan subplot untuk pendapatan harian
    axs0.fill_between(tanggal_harian_formatted, pendapatan_harian, color='blue', alpha=0.5)
    axs0.plot(tanggal_harian_formatted, pendapatan_harian, marker='o', color='blue')  # Tambahkan titik
    axs0.set_title('Pendapatan Harian')
    axs0.set_xlabel('Tanggal')
    axs0.set_ylabel('Pendapatan')

    # Menambahkan garis horizontal di sumbu Y
    for y in range(0, int(max(pendapatan_harian)) + 1, 100000):  # Ganti 100000 sesuai kebutuhan
        axs0.axhline(y=y, color='gray', linestyle='--', linewidth=0.5)

    # Menambahkan grid hanya pada sumbu Y
    axs0.yaxis.grid(True, linestyle='--', alpha=0.7)  # Hanya grid pada sumbu Y

    # Mengatur format sumbu y untuk menampilkan RP dan pemisah ribuan
    axs0.yaxis.set_major_formatter(FuncFormatter(format_func))

    # Grafik Pendapatan Bulanan
    axs1 = fig.add_subplot(gs[1])
    axs1.bar(bulan_terakhir[::-1], pendapatan_bulanan[::-1], color='orange')  # Balik urutan bulan dan pendapatan
    axs1.set_title('Pendapatan Bulanan')
    axs1.set_xlabel('Bulan')
    axs1.set_ylabel('Pendapatan')

    # Menambahkan garis horizontal di sumbu Y
    for y in range(0, int(max(pendapatan_bulanan)) + 1, 100000):  # Ganti 100000 sesuai kebutuhan
        axs1.axhline(y=y, color='gray', linestyle='--', linewidth=0.5)

    # Menambahkan grid hanya pada sumbu Y
    axs1.yaxis.grid(True, linestyle='--', alpha=0.7)  # Hanya grid pada sumbu Y

    axs1.yaxis.set_major_formatter(FuncFormatter(format_func))

    # Menambahkan ruang di sebelah kiri grafik bulanan
    plt.subplots_adjust(wspace=0.6)  # Sesuaikan nilai wspace untuk menggeser grafik

    # Menampilkan grafik di dalam Tkinter
    canvas = FigureCanvasTkAgg(fig, master=konten_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()


    # Fungsi untuk menampilkan dashboard
def tampil_dashboard():
    for widget in konten_frame.winfo_children():
        widget.destroy()
    
    dashboard_label = tk.Label(konten_frame, text="Selamat Datang di Aplikasi Persediaan Barang", font=("Helvetica", 16))
    dashboard_label.pack(pady=20)

    # Memanggil fungsi untuk menampilkan grafik
    tampil_grafik_pendapatan()

def format_rp(value):
    """Format angka menjadi format Rupiah"""
    return f"RP {int(value):,.0f}".replace(',', '.').replace('.', ',', 1)

def format_input_harga(value):
    """Format input harga menjadi format ribuan"""
    # Menghapus semua karakter non-digit
    value = ''.join(filter(str.isdigit, value))
    if value:
        return '{:,.0f}'.format(int(value)).replace(',', '.')
    return value


# Fungsi untuk menampilkan data barang
def tampil_data_barang(cari=None):
    for widget in konten_frame.winfo_children():
        widget.destroy()
    label = tk.Label(konten_frame, text="Data Stok Barang", font=("Helvetica", 16))
    label.pack(pady=20)

    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    search_frame = tk.Frame(tabel_frame, bg="#ECF0F1")
    search_frame.pack(pady=10)

    tk.Label(search_frame, text="Cari Barang:", bg="#ECF0F1").grid(row=0, column=0, pady=5)
    entry_search = tk.Entry(search_frame)
    entry_search.grid(row=0, column=1, pady=5)

    # Listbox untuk menampilkan rekomendasi
    listbox_rekomendasi = tk.Listbox(search_frame, height=0)  # Awalnya tinggi 0
    listbox_rekomendasi.grid(row=1, column=1, pady=5)  # Tempatkan di bawah entry
    listbox_rekomendasi.grid_forget()  # Sembunyikan Listbox dari awal
    listbox_rekomendasi.bind("<ButtonRelease-1>", lambda event: select_recommendation(event, entry_search, listbox_rekomendasi))

    search_btn = tk.Button(search_frame, text="Cari", command=lambda: tampil_data_barang(entry_search.get()))
    search_btn.grid(row=0, column=2, padx=5)  # Tempatkan tombol di sebelah kanan entry

    # Tambahkan tombol Refresh
    refresh_btn = tk.Button(search_frame, text="Refresh", command=lambda: tampil_data_barang())
    refresh_btn.grid(row=0, column=3, padx=5)  # Tempatkan tombol Refresh di sebelah kanan tombol Cari

    def update_nama_barang(event):
        search_term = entry_search.get()
        listbox_rekomendasi.delete(0, tk.END)  # Kosongkan Listbox

        if search_term:
            conn = sqlite3.connect('stok_barang.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nama_barang FROM stok_barang WHERE nama_barang LIKE ?', ('%' + search_term + '%',))
            results = cursor.fetchall()
            conn.close()

            # Tambahkan rekomendasi ke Listbox
            for row in results:
                listbox_rekomendasi.insert(tk.END, row[0])  # Tambahkan nama barang ke Listbox
            
            # Sesuaikan tinggi Listbox
            adjust_listbox_height(listbox_rekomendasi)

            # Tampilkan Listbox jika ada rekomendasi
            if listbox_rekomendasi.size() > 0:
                listbox_rekomendasi.grid(row=1, column=1)  # Tampilkan Listbox
            else:
                listbox_rekomendasi.grid_forget()  # Sembunyikan Listbox jika tidak ada rekomendasi
        else:
            listbox_rekomendasi.grid_forget()  # Sembunyikan Listbox jika input kosong

    def adjust_listbox_height(listbox):
        item_count = listbox.size()  # Hitung jumlah item
        max_visible_items = 5  # Jumlah maksimum item yang ingin ditampilkan
        height = min(item_count, max_visible_items)  # Atur tinggi berdasarkan jumlah item
        listbox.config(height=height)  # Set tinggi Listbox

    entry_search.bind("<KeyRelease>", update_nama_barang)  # Bind event saat mengetik

    def select_recommendation(event, entry, listbox):
        try:
            selection = listbox.curselection()  # Ambil item yang dipilih
            if selection:
                entry.delete(0, tk.END)  # Hapus isi Entry
                entry.insert(0, listbox.get(selection))  # Masukkan item yang dipilih ke Entry
                listbox.delete(0, tk.END)  # Kosongkan Listbox
                listbox.grid_forget()  # Sembunyikan Listbox setelah memilih
        except Exception as e:
            print(e)

    # Treeview untuk menampilkan data barang
    tree = ttk.Treeview(tabel_frame, columns=("ID", "Nama Barang", "Brand", "Stok", "Harga Jual"), show='headings')
    tree.heading("ID", text="ID")
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Brand", text="Brand")
    tree.heading("Stok", text="Stok")
    tree.heading("Harga Jual", text="Harga Jual")

    tree.column("ID", width=50, anchor='center')
    tree.column("Nama Barang", width=150)
    tree.column("Brand", width=100)
    tree.column("Stok", width=50, anchor='center')
    tree.column("Harga Jual", width=100)

    tree.pack()

    # Mengambil data barang dari database
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    
    if cari:
        cursor.execute('SELECT * FROM stok_barang WHERE nama_barang LIKE ? ORDER BY stok ASC', ('%' + cari + '%',))
    else:
        cursor.execute('SELECT * FROM stok_barang ORDER BY stok ASC')

    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        row = list(row)  # Konversi tuple ke list agar bisa dimodifikasi
        try:
            row[4] = format_rp(float(row[4]))  # Format harga jual
        except ValueError:
            row[4] = "RP 0"  # Jika terjadi kesalahan konversi

        tree.insert("", tk.END, values=row)


    def tambah_data_form():
        for widget in konten_frame.winfo_children():
            widget.destroy()
        label = tk.Label(konten_frame, text="Tambahkan Data Stok Barang", font=("Helvetica", 16))
        label.pack(pady=20)

        form_frame = tk.Frame(konten_frame, bg="#ECF0F1")
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Nama Barang:", bg="#ECF0F1").grid(row=0, column=0, pady=5)
        entry_nama_barang = tk.Entry(form_frame)
        entry_nama_barang.grid(row=0, column=1, pady=5)
        
        tk.Label(form_frame, text="Brand:", bg="#ECF0F1").grid(row=1, column=0, pady=5)
        entry_brand = tk.Entry(form_frame)
        entry_brand.grid(row=1, column=1, pady=5)
        
        tk.Label(form_frame, text="Stok:", bg="#ECF0F1").grid(row=2, column=0, pady=5)
        entry_stok = tk.Entry(form_frame)
        entry_stok.grid(row=2, column=1, pady=5)
        
        tk.Label(form_frame, text="Harga Jual:", bg="#ECF0F1").grid(row=3, column=0, pady=5)
        entry_harga_jual = tk.Entry(form_frame)
        entry_harga_jual.grid(row=3, column=1, pady=5)

        # Format input harga jual saat mengetik
        def on_price_change(*args):
            value = entry_harga_jual.get()
            formatted_value = format_input_harga(value)
            entry_harga_jual.delete(0, tk.END)
            entry_harga_jual.insert(0, formatted_value)

        entry_harga_jual.bind("<KeyRelease>", on_price_change)

        def tambah_barang():
            nama_barang = entry_nama_barang.get()
            brand = entry_brand.get()
            stok = entry_stok.get()
            harga_jual = entry_harga_jual.get().replace('.', '').replace(',', '.')  # Hapus titik dan ganti koma dengan titik
            
            if nama_barang and brand and stok and harga_jual:
                conn = sqlite3.connect('stok_barang.db')
                cursor = conn.cursor()
                
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 FROM stok_barang')
                new_id = cursor.fetchone()[0]
                
                cursor.execute('''
                    INSERT INTO stok_barang (id, nama_barang, brand, stok, harga_jual)
                    VALUES (?, ?, ?, ?, ?)
                ''', (new_id, nama_barang, brand, stok, harga_jual))
                conn.commit()
                conn.close()
                messagebox.showinfo("Sukses", "Barang berhasil ditambahkan!")
                tampil_data_barang()
            else:
                messagebox.showwarning("Peringatan", "Semua field harus diisi!")
        
        tambah_btn = tk.Button(form_frame, text="Tambah Barang", command=tambah_barang)
        tambah_btn.grid(row=4, column=0, pady=10)

        kembali_btn = tk.Button(form_frame, text="Kembali", command=tampil_data_barang)
        kembali_btn.grid(row=4, column=1, pady=10)

    tambah_data_btn = tk.Button(tabel_frame, text="Tambah Data", command=tambah_data_form)
    tambah_data_btn.pack(side=tk.RIGHT, padx=5, pady=10)

    def edit_hapus_data():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Peringatan", "Silakan pilih data yang akan diedit atau dihapus!")
            return
        
        item_id = tree.item(selected_item)["values"][0]

        def edit_barang_form():
            for widget in konten_frame.winfo_children():
                widget.destroy()
            label = tk.Label(konten_frame, text="Edit Data Stok Barang", font=("Helvetica", 16))
            label.pack(pady=20)

            form_frame = tk.Frame(konten_frame, bg="#ECF0F1")
            form_frame.pack(pady=20)

            tk.Label(form_frame, text="Nama Barang:", bg="#ECF0F1").grid(row=0, column=0, pady=5)
            entry_nama_barang = tk.Entry(form_frame)
            entry_nama_barang.grid(row=0, column=1, pady=5)

            tk.Label(form_frame, text="Brand:", bg="#ECF0F1").grid(row=1, column=0, pady=5)
            entry_brand = tk.Entry(form_frame)
            entry_brand.grid(row=1, column=1, pady=5)

            tk.Label(form_frame, text="Stok:", bg="#ECF0F1").grid(row=2, column=0, pady=5)
            entry_stok = tk.Entry(form_frame)
            entry_stok.grid(row=2, column=1, pady=5)

            tk.Label(form_frame, text="Harga Jual:", bg="#ECF0F1").grid(row=3, column=0, pady=5)
            entry_harga_jual = tk.Entry(form_frame)
            entry_harga_jual.grid(row=3, column=1, pady=5)

            # Format input harga jual saat mengetik
            def on_price_change(*args):
                value = entry_harga_jual.get()
                formatted_value = format_input_harga(value)
                entry_harga_jual.delete(0, tk.END)
                entry_harga_jual.insert(0, formatted_value)

            entry_harga_jual.bind("<KeyRelease>", on_price_change)

            def update_barang():
                nama_barang = entry_nama_barang.get()
                brand = entry_brand.get()
                stok = entry_stok.get()
                harga_jual = entry_harga_jual.get().replace('.', '').replace(',', '.')

                if nama_barang and brand and stok and harga_jual:
                    conn = sqlite3.connect('stok_barang.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE stok_barang
                        SET nama_barang = ?, brand = ?, stok = ?, harga_jual = ?
                        WHERE id = ?
                    ''', (nama_barang, brand, stok, harga_jual, item_id))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Sukses", "Barang berhasil diupdate!")
                    tampil_data_barang()
                else:
                    messagebox.showwarning("Peringatan", "Semua field harus diisi!")

            update_btn = tk.Button(form_frame, text="Update Barang", command=update_barang)
            update_btn.grid(row=4, column=0, pady=10)

            kembali_btn = tk.Button(form_frame, text="Kembali", command=tampil_data_barang)
            kembali_btn.grid(row=4, column=1, pady=10)

            conn = sqlite3.connect('stok_barang.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nama_barang, brand, stok, harga_jual FROM stok_barang WHERE id = ?', (item_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                entry_nama_barang.insert(0, row[0])
                entry_brand.insert(0, row[1])
                entry_stok.insert(0, row[2])
                entry_harga_jual.insert(0, row[3])

        def hapus_barang():
            result = messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin menghapus barang ini?")
            if result:
                conn = sqlite3.connect('stok_barang.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM stok_barang WHERE id = ?', (item_id,))
                conn.commit()

                # Mengupdate ID barang setelah penghapusan
                cursor.execute('''
                    UPDATE stok_barang
                    SET id = id - 1
                    WHERE id > ?
                ''', (item_id,))
                conn.commit()
                
                conn.close()
                messagebox.showinfo("Sukses", "Barang berhasil dihapus!")
                tampil_data_barang()

        edit_btn = tk.Button(tabel_frame, text="Edit Data", command=edit_barang_form)
        edit_btn.pack(side=tk.LEFT, padx=5, pady=10)

        hapus_btn = tk.Button(tabel_frame, text="Hapus Data", command=hapus_barang)
        hapus_btn.pack(side=tk.LEFT, padx=5, pady=10)

    edit_hapus_btn = tk.Button(tabel_frame, text="Edit/Hapus Data", command=edit_hapus_data)
    edit_hapus_btn.pack(side=tk.LEFT, padx=5, pady=10)

def barang_masuk():
    for widget in konten_frame.winfo_children():
        widget.destroy()
    
    label = tk.Label(konten_frame, text="Barang Masuk", font=("Helvetica", 16))
    label.pack(pady=20)

    # Tabel untuk menampilkan barang masuk
    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    tree = ttk.Treeview(tabel_frame, columns=("Nama Barang", "Tanggal", "Jumlah"), show='headings')
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Tanggal", text="Tanggal")
    tree.heading("Jumlah", text="Jumlah")

    tree.column("Nama Barang", width=150)
    tree.column("Tanggal", width=100)
    tree.column("Jumlah", width=100)

    tree.pack()

    # Tampilkan data barang masuk yang ada
    tampil_barang_masuk(tree)

    # Tombol untuk menambah barang masuk
    tambah_btn = tk.Button(konten_frame, text="Tambah Barang Masuk", command=lambda: tambah_barang_masuk(tree))
    tambah_btn.pack(pady=10)

    # Tombol untuk menghapus barang masuk
    hapus_btn = tk.Button(konten_frame, text="Hapus Barang Masuk", command=lambda: hapus_barang_masuk(tree))
    hapus_btn.pack(pady=10)

def hapus_barang_masuk(tree):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Peringatan", "Silakan pilih data yang akan dihapus!")
        return

    item_values = tree.item(selected_item)["values"]
    nama_barang = item_values[0]
    jumlah = item_values[2]

    result = messagebox.askyesno("Konfirmasi", f"Apakah Anda yakin ingin menghapus barang masuk '{nama_barang}'?")
    if result:
        conn = sqlite3.connect('stok_barang.db')
        cursor = conn.cursor()

        # Menghapus data dari tabel barang_masuk
        cursor.execute('''
            DELETE FROM barang_masuk
            WHERE id_barang = (SELECT id FROM stok_barang WHERE nama_barang = ?) AND tanggal = ? AND jumlah = ?
        ''', (nama_barang, item_values[1], jumlah))

        # Mengupdate stok di tabel stok_barang
        cursor.execute('''
            UPDATE stok_barang
            SET stok = stok - ?
            WHERE id = (SELECT id FROM stok_barang WHERE nama_barang = ?)
        ''', (jumlah, nama_barang))

        conn.commit()
        conn.close()
        messagebox.showinfo("Sukses", "Barang masuk berhasil dihapus!")
        tampil_barang_masuk(tree)


    # Tampilkan data barang masuk yang ada
    tampil_barang_masuk(tree)


def tambah_barang_masuk(tree):
    for widget in konten_frame.winfo_children():
        widget.destroy()
    label = tk.Label(konten_frame, text="Tambah Data Barang Masuk", font=("Helvetica", 16))
    label.pack(pady=20)

    form_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    form_frame.pack(pady=20)

    tk.Label(form_frame, text="Nama Barang:", bg="#ECF0F1").grid(row=0, column=0, pady=5)
    
    entry_nama_barang = tk.Entry(form_frame)
    entry_nama_barang.grid(row=0, column=1, pady=5)

    # Listbox untuk menampilkan rekomendasi
    listbox_rekomendasi = tk.Listbox(form_frame, height=0)  # Awalnya tinggi 0
    listbox_rekomendasi.grid(row=1, column=1)  # Grid di sini tetapi akan disembunyikan
    listbox_rekomendasi.grid_forget()  # Sembunyikan Listbox dari awal
    listbox_rekomendasi.bind("<ButtonRelease-1>", lambda event: select_recommendation(event, entry_nama_barang, listbox_rekomendasi))

    tk.Label(form_frame, text="Tanggal:", bg="#ECF0F1").grid(row=2, column=0, pady=5)
    entry_tanggal = tk.Entry(form_frame)
    entry_tanggal.grid(row=2, column=1, pady=5)
    entry_tanggal.insert(0, datetime.now().strftime("%Y-%m-%d"))  # Set tanggal otomatis

    tk.Label(form_frame, text="Jumlah Barang:", bg="#ECF0F1").grid(row=3, column=0, pady=5)
    entry_jumlah_barang = tk.Entry(form_frame)
    entry_jumlah_barang.grid(row=3, column=1, pady=5)

    def update_nama_barang(event):
        search_term = entry_nama_barang.get()
        listbox_rekomendasi.delete(0, tk.END)  # Kosongkan Listbox

        if search_term:
            conn = sqlite3.connect('stok_barang.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nama_barang FROM stok_barang WHERE nama_barang LIKE ?', ('%' + search_term + '%',))
            results = cursor.fetchall()
            conn.close()

            # Tambahkan rekomendasi ke Listbox
            for row in results:
                listbox_rekomendasi.insert(tk.END, row[0])  # Tambahkan nama barang ke Listbox
            
            # Sesuaikan tinggi Listbox
            adjust_listbox_height(listbox_rekomendasi)

            # Tampilkan Listbox jika ada rekomendasi
            if listbox_rekomendasi.size() > 0:
                listbox_rekomendasi.grid(row=1, column=1)  # Tampilkan Listbox
            else:
                listbox_rekomendasi.grid_forget()  # Sembunyikan Listbox jika tidak ada rekomendasi
        else:
            listbox_rekomendasi.grid_forget()  # Sembunyikan Listbox jika input kosong

    def adjust_listbox_height(listbox):
        item_count = listbox.size()  # Hitung jumlah item
        max_visible_items = 5  # Jumlah maksimum item yang ingin ditampilkan
        height = min(item_count, max_visible_items)  # Atur tinggi berdasarkan jumlah item
        listbox.config(height=height)  # Set tinggi Listbox

    entry_nama_barang.bind("<KeyRelease>", update_nama_barang)  # Bind event saat mengetik

    def select_recommendation(event, entry, listbox):
        try:
            selection = listbox.curselection()  # Ambil item yang dipilih
            if selection:
                entry.delete(0, tk.END)  # Hapus isi Entry
                entry.insert(0, listbox.get(selection))  # Masukkan item yang dipilih ke Entry
                listbox.delete(0, tk.END)  # Kosongkan Listbox
                listbox.grid_forget()  # Sembunyikan Listbox setelah memilih
        except Exception as e:
            print(e)

    def simpan_barang_masuk():
        nama_barang = entry_nama_barang.get()
        tanggal = entry_tanggal.get()
        jumlah = entry_jumlah_barang.get()

        if nama_barang and tanggal and jumlah:
            conn = sqlite3.connect('stok_barang.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO barang_masuk (id_barang, jumlah, tanggal)
                VALUES ((SELECT id FROM stok_barang WHERE nama_barang = ?), ?, ?)
            ''', (nama_barang, jumlah, tanggal))

            cursor.execute('''
                UPDATE stok_barang
                SET stok = stok + ?
                WHERE id = (SELECT id FROM stok_barang WHERE nama_barang = ?)
            ''', (jumlah, nama_barang))

            conn.commit()
            conn.close()
            messagebox.showinfo("Sukses", "Barang masuk berhasil ditambahkan!")
            barang_masuk()
        else:
            messagebox.showwarning("Peringatan", "Semua field harus diisi!")

    simpan_btn = tk.Button(form_frame, text="Simpan Barang Masuk", command=simpan_barang_masuk)
    simpan_btn.grid(row=4, column=0, pady=10)

    kembali_btn = tk.Button(form_frame, text="Kembali", command=barang_masuk)
    kembali_btn.grid(row=4, column=1, pady=10)


def tampil_barang_masuk(tree):
    # Menghapus semua item di tabel sebelum menampilkan data baru
    for item in tree.get_children():
        tree.delete(item)

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sb.nama_barang, bm.tanggal, bm.jumlah
        FROM barang_masuk bm
        JOIN stok_barang sb ON bm.id_barang = sb.id
        ORDER BY bm.tanggal DESC  -- Mengurutkan berdasarkan tanggal terbaru
    ''')
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        tree.insert("", tk.END, values=row)



# tampil menu barang keluar
def barang_keluar():
    for widget in konten_frame.winfo_children():
        widget.destroy()
    label = tk.Label(konten_frame, text="Barang Keluar", font=("Helvetica", 16))
    label.pack(pady=20)

    # Tabel untuk menampilkan barang keluar
    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    tree = ttk.Treeview(tabel_frame, columns=("Nama Barang", "Tanggal", "Jumlah"), show='headings')
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Tanggal", text="Tanggal")
    tree.heading("Jumlah", text="Jumlah")

    tree.column("Nama Barang", width=150)
    tree.column("Tanggal", width=100)
    tree.column("Jumlah", width=100)

    tree.pack()

    # Tampilkan data barang keluar yang ada
    tampil_barang_keluar(tree)

    # Tombol untuk menambah barang keluar
    tambah_btn = tk.Button(konten_frame, text="Tambah Barang Keluar", command=lambda: tambah_barang_keluar(tree))
    tambah_btn.pack(pady=10)

    # Tombol untuk menghapus barang keluar
    hapus_btn = tk.Button(konten_frame, text="Hapus Barang Keluar", command=lambda: hapus_barang_keluar(tree))
    hapus_btn.pack(pady=10)

def hapus_barang_keluar(tree):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Peringatan", "Silakan pilih data yang akan dihapus!")
        return

    item_values = tree.item(selected_item)["values"]
    nama_barang = item_values[0]
    jumlah = item_values[2]

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()

    # Menghapus dari tabel barang_keluar
    cursor.execute('''
        DELETE FROM barang_keluar
        WHERE id_barang = (SELECT id FROM stok_barang WHERE nama_barang = ?) AND jumlah = ?
    ''', (nama_barang, jumlah))

    # Mengembalikan stok barang di tabel stok_barang
    cursor.execute('''
        UPDATE stok_barang
        SET stok = stok + ?
        WHERE id = (SELECT id FROM stok_barang WHERE nama_barang = ?)
    ''', (jumlah, nama_barang))

    conn.commit()
    conn.close()
    messagebox.showinfo("Sukses", "Barang keluar berhasil dihapus!")
    tampil_barang_keluar(tree)

def tambah_barang_keluar(tree):
    for widget in konten_frame.winfo_children():
        widget.destroy()
    label = tk.Label(konten_frame, text="Tambah Data Barang Keluar", font=("Helvetica", 16))
    label.pack(pady=20)

    form_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    form_frame.pack(pady=20)

    tk.Label(form_frame, text="Nama Barang:", bg="#ECF0F1").grid(row=0, column=0, pady=5)
    entry_nama_barang = tk.Entry(form_frame)
    entry_nama_barang.grid(row=0, column=1, pady=5)

    # Listbox untuk menampilkan rekomendasi
    listbox_rekomendasi = tk.Listbox(form_frame, height=0)  # Awalnya tinggi 0
    listbox_rekomendasi.grid(row=1, column=1)  # Grid di sini tetapi akan disembunyikan
    listbox_rekomendasi.grid_forget()  # Sembunyikan Listbox dari awal
    listbox_rekomendasi.bind("<ButtonRelease-1>", lambda event: select_recommendation(event, entry_nama_barang, listbox_rekomendasi))

    tk.Label(form_frame, text="Tanggal:", bg="#ECF0F1").grid(row=2, column=0, pady=5)
    entry_tanggal = tk.Entry(form_frame)
    entry_tanggal.grid(row=2, column=1, pady=5)
    entry_tanggal.insert(0, datetime.now().strftime("%Y-%m-%d"))  # Set tanggal otomatis

    tk.Label(form_frame, text="Jumlah Barang:", bg="#ECF0F1").grid(row=3, column=0, pady=5)
    entry_jumlah_barang = tk.Entry(form_frame)
    entry_jumlah_barang.grid(row=3, column=1, pady=5)

    def update_nama_barang(event):
        search_term = entry_nama_barang.get()
        listbox_rekomendasi.delete(0, tk.END)  # Kosongkan Listbox

        if search_term:
            conn = sqlite3.connect('stok_barang.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nama_barang FROM stok_barang WHERE nama_barang LIKE ?', ('%' + search_term + '%',))
            results = cursor.fetchall()
            conn.close()

            # Tambahkan rekomendasi ke Listbox
            for row in results:
                listbox_rekomendasi.insert(tk.END, row[0])  # Tambahkan nama barang ke Listbox
            
            # Sesuaikan tinggi Listbox
            adjust_listbox_height(listbox_rekomendasi)

            # Tampilkan Listbox jika ada rekomendasi
            if listbox_rekomendasi.size() > 0:
                listbox_rekomendasi.grid(row=1, column=1)  # Tampilkan Listbox
            else:
                listbox_rekomendasi.grid_forget()  # Sembunyikan Listbox jika tidak ada rekomendasi
        else:
            listbox_rekomendasi.grid_forget()  # Sembunyikan Listbox jika input kosong

    def adjust_listbox_height(listbox):
        item_count = listbox.size()  # Hitung jumlah item
        max_visible_items = 5  # Jumlah maksimum item yang ingin ditampilkan
        height = min(item_count, max_visible_items)  # Atur tinggi berdasarkan jumlah item
        listbox.config(height=height)  # Set tinggi Listbox

    entry_nama_barang.bind("<KeyRelease>", update_nama_barang)  # Bind event saat mengetik

    def select_recommendation(event, entry, listbox):
        try:
            selection = listbox.curselection()  # Ambil item yang dipilih
            if selection:
                entry.delete(0, tk.END)  # Hapus isi Entry
                entry.insert(0, listbox.get(selection))  # Masukkan item yang dipilih ke Entry
                listbox.delete(0, tk.END)  # Kosongkan Listbox
                listbox.grid_forget()  # Sembunyikan Listbox setelah memilih
        except Exception as e:
            print(e)

    def simpan_barang_keluar():
        nama_barang = entry_nama_barang.get()
        tanggal = entry_tanggal.get()
        jumlah = entry_jumlah_barang.get()

        if nama_barang and tanggal and jumlah:
            conn = sqlite3.connect('stok_barang.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO barang_keluar (id_barang, jumlah, tanggal)
                VALUES ((SELECT id FROM stok_barang WHERE nama_barang = ?), ?, ?)
            ''', (nama_barang, jumlah, tanggal))

            cursor.execute('''
                UPDATE stok_barang
                SET stok = stok - ?
                WHERE id = (SELECT id FROM stok_barang WHERE nama_barang = ?)
            ''', (jumlah, nama_barang))

            conn.commit()
            conn.close()
            messagebox.showinfo("Sukses", "Barang keluar berhasil ditambahkan!")
            barang_keluar()
        else:
            messagebox.showwarning("Peringatan", "Semua field harus diisi!")

    simpan_btn = tk.Button(form_frame, text="Simpan Barang Keluar", command=simpan_barang_keluar)
    simpan_btn.grid(row=4, column=0, pady=10)

    kembali_btn = tk.Button(form_frame, text="Kembali", command=barang_keluar)
    kembali_btn.grid(row=4, column=1, pady=10)


def tampil_barang_keluar(tree):
    # Menghapus semua item di tabel sebelum menampilkan data baru
    for item in tree.get_children():
        tree.delete(item)

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sb.nama_barang, bk.tanggal, bk.jumlah
        FROM barang_keluar bk
        JOIN stok_barang sb ON bk.id_barang = sb.id
        ORDER BY bk.tanggal DESC  -- Mengurutkan berdasarkan tanggal terbaru
    ''')
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        tree.insert("", tk.END, values=row)


# Fungsi untuk menampilkan laporan barang masuk
# Fungsi untuk menampilkan laporan barang masuk dengan filter tanggal
# Global variables to store filter dates
filter_applied = False
filtered_dates = (None, None)

# Initialize tree variable for global access
tree = None

def tampil_lap_barang_masuk():
    global filter_frame, pdf_btn, entry_tanggal_awal, entry_tanggal_akhir, tree  # Declare as global to use in other functions
    for widget in konten_frame.winfo_children():
        widget.destroy()

    laporan_label = tk.Label(konten_frame, text="Laporan Barang Masuk", font=("Helvetica", 16))
    laporan_label.pack(pady=20)

    # Frame untuk filter tanggal
    filter_frame = tk.Frame(konten_frame)
    filter_frame.pack(pady=10)

    tk.Label(filter_frame, text="Tanggal Awal:").pack(side=tk.LEFT)
    entry_tanggal_awal = tk.Entry(filter_frame)
    entry_tanggal_awal.pack(side=tk.LEFT, padx=5)
    entry_tanggal_awal.insert(0, datetime.now().strftime("%Y-%m-%d"))

    tk.Label(filter_frame, text="Tanggal Akhir:").pack(side=tk.LEFT)
    entry_tanggal_akhir = tk.Entry(filter_frame)
    entry_tanggal_akhir.pack(side=tk.LEFT, padx=5)
    entry_tanggal_akhir.insert(0, datetime.now().strftime("%Y-%m-%d"))

    filter_btn = tk.Button(filter_frame, text="Filter", command=filter_data)
    filter_btn.pack(side=tk.LEFT, padx=5)

    reset_btn = tk.Button(filter_frame, text="Reset", command=reset_filter)
    reset_btn.pack(side=tk.LEFT, padx=5)

    # Tombol untuk menyimpan sebagai PDF di atas tabel
    pdf_btn = tk.Button(konten_frame, text="Simpan sebagai PDF", command=simpan_pdf_barang_masuk)
    pdf_btn.pack(pady=10)

    # Tabel untuk menampilkan laporan barang masuk
    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    tree = ttk.Treeview(tabel_frame, columns=("Nama Barang", "Tanggal", "Jumlah"), show='headings')
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Tanggal", text="Tanggal")
    tree.heading("Jumlah", text="Jumlah")

    tree.column("Nama Barang", width=150)
    tree.column("Tanggal", width=100)
    tree.column("Jumlah", width=100)

    tree.pack()

    # Tampilkan data barang masuk yang ada
    tampil_barang_masuk(tree)

def tampil_barang_masuk(tree, tanggal_awal=None, tanggal_akhir=None):
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()

    if tanggal_awal and tanggal_akhir:
        cursor.execute('''
            SELECT sb.nama_barang, bm.tanggal, bm.jumlah
            FROM barang_masuk bm
            JOIN stok_barang sb ON bm.id_barang = sb.id
            WHERE bm.tanggal BETWEEN ? AND ?
            ORDER BY bm.tanggal DESC
        ''', (tanggal_awal, tanggal_akhir))
    else:
        cursor.execute('''
            SELECT sb.nama_barang, bm.tanggal, bm.jumlah
            FROM barang_masuk bm
            JOIN stok_barang sb ON bm.id_barang = sb.id
            ORDER BY bm.tanggal DESC
        ''')

    rows = cursor.fetchall()
    conn.close()

    for row in tree.get_children():
        tree.delete(row)

    for row in rows:
        tree.insert("", tk.END, values=row)

def filter_data():
    tanggal_awal = entry_tanggal_awal.get()
    tanggal_akhir = entry_tanggal_akhir.get()

    if tanggal_awal and tanggal_akhir:
        tampil_barang_masuk(tree, tanggal_awal, tanggal_akhir)
        global filter_applied, filtered_dates
        filter_applied = True
        filtered_dates = (tanggal_awal, tanggal_akhir)
    else:
        messagebox.showwarning("Peringatan", "Silakan masukkan kedua tanggal untuk memfilter!")

def reset_filter():
    global filter_applied, filtered_dates
    # Reset filter state
    filter_applied = False
    filtered_dates = (None, None)

    # Reset entry fields
    entry_tanggal_awal.delete(0, tk.END)
    entry_tanggal_akhir.delete(0, tk.END)
    entry_tanggal_awal.insert(0, datetime.now().strftime("%Y-%m-%d"))
    entry_tanggal_akhir.insert(0, datetime.now().strftime("%Y-%m-%d"))

    # Tampilkan kembali semua data
    tampil_barang_masuk(tree)

def simpan_pdf_barang_masuk():
    # Membuat objek PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Judul
    pdf.cell(200, 10, txt="Laporan Barang Masuk", ln=True, align='C')
    pdf.cell(200, 10, txt="", ln=True)  # Space

    # Header tabel
    pdf.cell(50, 10, 'Nama Barang', border=1)
    pdf.cell(40, 10, 'Tanggal', border=1)
    pdf.cell(30, 10, 'Jumlah', border=1)
    pdf.ln()  # Pindah ke baris berikutnya

    # Mengambil data dari database
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()

    if filter_applied:
        cursor.execute('''
            SELECT sb.nama_barang, bm.tanggal, bm.jumlah
            FROM barang_masuk bm
            JOIN stok_barang sb ON bm.id_barang = sb.id
            WHERE bm.tanggal BETWEEN ? AND ?
            ORDER BY bm.tanggal DESC
        ''', filtered_dates)
    else:
        cursor.execute('''
            SELECT sb.nama_barang, bm.tanggal, bm.jumlah
            FROM barang_masuk bm
            JOIN stok_barang sb ON bm.id_barang = sb.id
            ORDER BY bm.tanggal DESC
        ''')

    rows = cursor.fetchall()
    conn.close()

    # Menambahkan data ke PDF
    for row in rows:
        pdf.cell(50, 10, row[0], border=1)  # Nama Barang
        pdf.cell(40, 10, row[1], border=1)  # Tanggal
        pdf.cell(30, 10, str(row[2]), border=1)  # Jumlah
        pdf.ln()  # Pindah ke baris berikutnya

    # Menyimpan PDF
    pdf.output("laporan_barang_masuk.pdf")
    messagebox.showinfo("Sukses", "Laporan berhasil disimpan sebagai PDF!")

# Global variables to store filter dates
filter_applied_barang_keluar = False
filtered_dates_barang_keluar = (None, None)

# Initialize tree variable for global access
tree = None
# Fungsi untuk menampilkan laporan barang keluar
# Global variables to track filter state
filter_applied_barang_keluar = False
filtered_dates_barang_keluar = (None, None)

def tampil_lap_barang_keluar():
    global filter_frame, pdf_btn, entry_tanggal_awal, entry_tanggal_akhir, tree  # Declare as global to use in other functions
    for widget in konten_frame.winfo_children():
        widget.destroy()

    laporan_label = tk.Label(konten_frame, text="Laporan Barang Keluar", font=("Helvetica", 16))
    laporan_label.pack(pady=20)

    # Frame untuk filter tanggal
    filter_frame = tk.Frame(konten_frame)
    filter_frame.pack(pady=10)

    tk.Label(filter_frame, text="Tanggal Awal:").pack(side=tk.LEFT)
    entry_tanggal_awal = tk.Entry(filter_frame)
    entry_tanggal_awal.pack(side=tk.LEFT, padx=5)
    entry_tanggal_awal.insert(0, datetime.now().strftime("%Y-%m-%d"))

    tk.Label(filter_frame, text="Tanggal Akhir:").pack(side=tk.LEFT)
    entry_tanggal_akhir = tk.Entry(filter_frame)
    entry_tanggal_akhir.pack(side=tk.LEFT, padx=5)
    entry_tanggal_akhir.insert(0, datetime.now().strftime("%Y-%m-%d"))

    filter_btn = tk.Button(filter_frame, text="Filter", command=filter_data_barang_keluar)
    filter_btn.pack(side=tk.LEFT, padx=5)

    reset_btn = tk.Button(filter_frame, text="Reset", command=reset_filter_barang_keluar)
    reset_btn.pack(side=tk.LEFT, padx=5)

    # Tombol untuk menyimpan sebagai PDF di atas tabel
    pdf_btn = tk.Button(konten_frame, text="Simpan sebagai PDF", command=simpan_pdf_barang_keluar)
    pdf_btn.pack(pady=10)

    belanja_btn = tk.Button(konten_frame, text="Belanja Barang PDF", command=belanja_barang_pdf)
    belanja_btn.pack(pady=10)

    # Tabel untuk menampilkan laporan barang keluar
    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    tree = ttk.Treeview(tabel_frame, columns=("Nama Barang", "Tanggal", "Jumlah"), show='headings')
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Tanggal", text="Tanggal")
    tree.heading("Jumlah", text="Jumlah")

    tree.column("Nama Barang", width=150)
    tree.column("Tanggal", width=100)
    tree.column("Jumlah", width=100)

    tree.pack()

    # Tampilkan data barang keluar yang ada
    tampil_barang_keluar(tree)

def tampil_barang_keluar(tree, tanggal_awal=None, tanggal_akhir=None):
    global filter_applied_barang_keluar, filtered_dates_barang_keluar
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()

    if tanggal_awal and tanggal_akhir:
        cursor.execute('''
            SELECT sb.nama_barang, bk.tanggal, bk.jumlah
            FROM barang_keluar bk
            JOIN stok_barang sb ON bk.id_barang = sb.id
            WHERE bk.tanggal BETWEEN ? AND ?
            ORDER BY bk.tanggal DESC
        ''', (tanggal_awal, tanggal_akhir))
        filter_applied_barang_keluar = True
        filtered_dates_barang_keluar = (tanggal_awal, tanggal_akhir)
    else:
        cursor.execute('''
            SELECT sb.nama_barang, bk.tanggal, bk.jumlah
            FROM barang_keluar bk
            JOIN stok_barang sb ON bk.id_barang = sb.id
            ORDER BY bk.tanggal DESC
        ''')
        filter_applied_barang_keluar = False
        filtered_dates_barang_keluar = (None, None)

    rows = cursor.fetchall()
    conn.close()

    # Menghapus semua item di tabel sebelum menampilkan data baru
    for item in tree.get_children():
        tree.delete(item)

    for row in rows:
        tree.insert("", tk.END, values=row)

def filter_data_barang_keluar():
    tanggal_awal = entry_tanggal_awal.get()
    tanggal_akhir = entry_tanggal_akhir.get()

    if tanggal_awal and tanggal_akhir:
        tampil_barang_keluar(tree, tanggal_awal, tanggal_akhir)
    else:
        messagebox.showwarning("Peringatan", "Silakan masukkan kedua tanggal untuk memfilter!")

def reset_filter_barang_keluar():
    entry_tanggal_awal.delete(0, tk.END)
    entry_tanggal_akhir.delete(0, tk.END)
    entry_tanggal_awal.insert(0, datetime.now().strftime("%Y-%m-%d"))
    entry_tanggal_akhir.insert(0, datetime.now().strftime("%Y-%m-%d"))
    tampil_barang_keluar(tree)

def simpan_pdf_barang_keluar():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Laporan Barang Keluar", ln=True, align='C')
    pdf.cell(200, 10, txt="", ln=True)  # Space

    pdf.cell(50, 10, 'Nama Barang', border=1)
    pdf.cell(40, 10, 'Tanggal', border=1)
    pdf.cell(30, 10, 'Jumlah', border=1)
    pdf.ln()

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()

    if filter_applied_barang_keluar:
        cursor.execute('''
            SELECT sb.nama_barang, bk.tanggal, bk.jumlah
            FROM barang_keluar bk
            JOIN stok_barang sb ON bk.id_barang = sb.id
            WHERE bk.tanggal BETWEEN ? AND ?
            ORDER BY bk.tanggal DESC
        ''', filtered_dates_barang_keluar)
    else:
        cursor.execute('''
            SELECT sb.nama_barang, bk.tanggal, bk.jumlah
            FROM barang_keluar bk
            JOIN stok_barang sb ON bk.id_barang = sb.id
            ORDER BY bk.tanggal DESC
        ''')

    rows = cursor.fetchall()
    conn.close()


    for row in rows:
        pdf.cell(50, 10, row[0], border=1)
        pdf.cell(40, 10, row[1], border=1)
        pdf.cell(30, 10, str(row[2]), border=1)
        pdf.ln()

    pdf.output("laporan_barang_keluar.pdf")
    messagebox.showinfo("Sukses", "Laporan berhasil disimpan sebagai PDF!")
    

def belanja_barang_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Belanja Barang PDF", ln=True, align='C')
    pdf.cell(200, 10, txt="", ln=True)  # Space

    pdf.cell(50, 10, 'Nama Barang', border=1)
    pdf.cell(30, 10, 'Total Jumlah', border=1)
    pdf.ln()

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()

    if filter_applied_barang_keluar:
        # Jika filter diterapkan, gunakan tanggal dari filtered_dates_barang_keluar
        cursor.execute('''
            SELECT sb.nama_barang, SUM(bk.jumlah) as total_jumlah
            FROM barang_keluar bk
            JOIN stok_barang sb ON bk.id_barang = sb.id
            WHERE bk.tanggal BETWEEN ? AND ?
            GROUP BY sb.nama_barang
            ORDER BY total_jumlah DESC
        ''', filtered_dates_barang_keluar)
    else:
        # Jika tidak ada filter, ambil semua data
        cursor.execute('''
            SELECT sb.nama_barang, SUM(bk.jumlah) as total_jumlah
            FROM barang_keluar bk
            JOIN stok_barang sb ON bk.id_barang = sb.id
            GROUP BY sb.nama_barang
            ORDER BY total_jumlah DESC
        ''')

    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        pdf.cell(50, 10, row[0], border=1)
        pdf.cell(30, 10, f'{row[1]} pcs', border=1)
        pdf.ln()

    pdf.output("laporan_Belanja.pdf")
    messagebox.showinfo("Sukses", "Laporan berhasil disimpan sebagai PDF!")


def tampil_lap_stok_barang():
    global filter_frame, pdf_btn, tree  # Declare tree as global
    for widget in konten_frame.winfo_children():
        widget.destroy()
    
    laporan_label = tk.Label(konten_frame, text="Laporan Stok Barang", font=("Helvetica", 16))
    laporan_label.pack(pady=20)

    # Frame untuk filter pencarian
    filter_frame = tk.Frame(konten_frame)
    filter_frame.pack(pady=10)

    tk.Label(filter_frame, text="Cari Barang:").pack(side=tk.LEFT)
    entry_search = tk.Entry(filter_frame)
    entry_search.pack(side=tk.LEFT, padx=5)

    search_btn = tk.Button(filter_frame, text="Cari", command=lambda: tampil_stok_barang_filtered(entry_search.get()))
    search_btn.pack(side=tk.LEFT)

    # Tambahkan tombol Refresh
    refresh_btn = tk.Button(filter_frame, text="Refresh", command=lambda: tampil_stok_barang(tree))
    refresh_btn.pack(side=tk.LEFT, padx=5)

    # Tombol untuk menyimpan sebagai PDF di atas tabel
    pdf_btn = tk.Button(konten_frame, text="Simpan sebagai PDF", command=simpan_pdf_stok_barang)
    pdf_btn.pack(pady=10)

    # Tabel untuk menampilkan laporan stok barang
    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    tree = ttk.Treeview(tabel_frame, columns=("ID", "Nama Barang", "Brand", "Stok", "Harga Jual"), show='headings')
    tree.heading("ID", text="ID")
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Brand", text="Brand")
    tree.heading("Stok", text="Stok")
    tree.heading("Harga Jual", text="Harga Jual")

    tree.column("ID", width=50, anchor='center')
    tree.column("Nama Barang", width=150)
    tree.column("Brand", width=100)
    tree.column("Stok", width=50, anchor='center')
    tree.column("Harga Jual", width=100)

    tree.pack()

    # Tampilkan data stok barang yang ada
    tampil_stok_barang(tree)

def tampil_stok_barang(tree):
    # Menghapus semua item di tabel sebelum menampilkan data baru
    for item in tree.get_children():
        tree.delete(item)

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    # Mengambil data dan mengurutkan berdasarkan ID
    cursor.execute('SELECT * FROM stok_barang ORDER BY id ASC')  # Pastikan 'id' adalah nama kolom ID di database
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        tree.insert("", tk.END, values=row)

def tampil_stok_barang_filtered(cari):
    global tree  # Declare tree as global to access it
    # Menghapus semua item di tabel sebelum menampilkan data baru
    for item in tree.get_children():
        tree.delete(item)

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    
    # Mengambil data berdasarkan pencarian
    cursor.execute('SELECT * FROM stok_barang WHERE nama_barang LIKE ?', ('%' + cari + '%',))
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        tree.insert("", tk.END, values=row)

def simpan_pdf_stok_barang():
    # Membuat objek PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Judul
    pdf.cell(200, 10, txt="Laporan Stok Barang", ln=True, align='C')
    pdf.cell(200, 10, txt="", ln=True)  # Space

    # Header tabel
    pdf.cell(20, 10, 'ID', border=1)
    pdf.cell(60, 10, 'Nama Barang', border=1)
    pdf.cell(40, 10, 'Brand', border=1)
    pdf.cell(30, 10, 'Stok', border=1)
    pdf.cell(40, 10, 'Harga Jual', border=1)
    pdf.ln()  # Pindah ke baris berikutnya

    # Mengambil data dari database
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stok_barang ORDER BY stok ASC')
    rows = cursor.fetchall()
    conn.close()

    # Menambahkan data ke PDF
    for row in rows:
        pdf.cell(20, 10, str(row[0]), border=1)  # ID
        pdf.cell(60, 10, row[1], border=1)  # Nama Barang
        pdf.cell(40, 10, row[2], border=1)  # Brand
        pdf.cell(30, 10, str(row[3]), border=1)  # Stok
        pdf.cell(40, 10, str(row[4]), border=1)  # Harga Jual
        pdf.ln()  # Pindah ke baris berikutnya

    # Menyimpan PDF
    pdf.output("laporan_stok_barang.pdf")
    messagebox.showinfo("Sukses", "Laporan berhasil disimpan sebagai PDF!")


def format_rp(value):
    """Format angka menjadi string dengan awalan 'RP' dan pemisah ribuan."""
    return f"RP {value:,.0f}".replace(',', '.').replace('.', ',', 1)

# Fungsi untuk menampilkan laporan pendapatan
def tampil_lap_pendapatan():
    global filter_frame, pdf_btn  # Declare as global to use in other functions
    for widget in konten_frame.winfo_children():
        widget.destroy()
    
    # Mendapatkan tahun saat ini
    current_year = datetime.now().year

    # Menampilkan label dengan tahun saat ini
    laporan_label = tk.Label(konten_frame, text=f"Laporan Pendapatan Tahun{current_year}", font=("Helvetica", 16))
    laporan_label.pack(pady=20)

    # Frame untuk filter pencarian
    filter_frame = tk.Frame(konten_frame)
    filter_frame.pack(pady=10)

    tk.Label(filter_frame, text="Cari Nama Barang:").pack(side=tk.LEFT)
    entry_search = tk.Entry(filter_frame)
    entry_search.pack(side=tk.LEFT, padx=5)

    search_btn = tk.Button(filter_frame, text="Cari", command=lambda: tampil_pendapatan_filtered(entry_search.get()))
    search_btn.pack(side=tk.LEFT)

    # Tombol untuk menyimpan sebagai PDF di atas tabel
    pdf_btn = tk.Button(konten_frame, text="Simpan sebagai PDF", command=simpan_pdf_pendapatan)
    pdf_btn.pack(pady=10)

    # Tabel untuk menampilkan laporan pendapatan
    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    tree = ttk.Treeview(tabel_frame, columns=("Tanggal", "Nama Barang", "Qty", "Harga Jual", "Total"), show='headings')
    tree.heading("Tanggal", text="Tanggal")
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Qty", text="Qty")
    tree.heading("Harga Jual", text="Harga Jual")
    tree.heading("Total", text="Total")

    tree.column("Tanggal", width=100)
    tree.column("Nama Barang", width=150)
    tree.column("Qty", width=50, anchor='center')
    tree.column("Harga Jual", width=100)
    tree.column("Total", width=100)

    tree.pack()

    # Tampilkan data pendapatan yang ada
    tampil_pendapatan(tree)

def tampil_pendapatan(tree):
    # Menghapus semua item di tabel sebelum menampilkan data baru
    for item in tree.get_children():
        tree.delete(item)

    total_pendapatan = 0

    # Dapatkan tahun saat ini
    current_year = datetime.now().year

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    
    # Ambil data pendapatan untuk tahun saat ini
    cursor.execute('''
        SELECT b.tanggal, s.nama_barang, b.jumlah, s.harga_jual
        FROM barang_keluar b
        JOIN stok_barang s ON b.id_barang = s.id
        WHERE strftime('%Y', b.tanggal) = ?
    ''', (str(current_year),))  # Filter berdasarkan tahun saat ini

    rows = cursor.fetchall()
    conn.close()

    # Cek jika ada data yang diambil
    if not rows:
        print("Tidak ada data untuk tahun ini.")  # Menampilkan pesan jika tidak ada data

    for row in rows:
        tanggal, nama_barang, jumlah, harga_jual = row
        # Remove thousands separator before converting to float
        harga_jual_float = float(harga_jual.replace('.', '').replace(',', '.'))
        total_harga = jumlah * harga_jual_float  # Calculate total based on quantity and price
        total_pendapatan += total_harga
        # Format the values for display
        tree.insert("", tk.END, values=(tanggal, nama_barang, jumlah, format_rp(harga_jual_float), format_rp(total_harga)))

    # Menambahkan total pendapatan ke baris baru di bawah tabel
    tree.insert("", tk.END, values=("", "Total Pendapatan", "", "", format_rp(total_pendapatan)))

    # Optionally, you can format the total row differently if needed
    total_row = tree.get_children()[-1]  # Get the last inserted row (total row)
    tree.item(total_row, tags=('total_row',))  # Tag the total row for styling if needed


def tampil_lap_pendapatan():
    global filter_frame, pdf_btn  # Declare as global to use in other functions
    for widget in konten_frame.winfo_children():
        widget.destroy()
    
    # Mendapatkan tahun saat ini
    current_year = datetime.now().year

    # Menampilkan label dengan tahun saat ini
    laporan_label = tk.Label(konten_frame, text=f"Laporan Pendapatan Tahun {current_year}", font=("Helvetica", 16))
    laporan_label.pack(pady=20)

    # Frame untuk filter pencarian
    filter_frame = tk.Frame(konten_frame)
    filter_frame.pack(pady=10)

    # Tombol untuk menyimpan sebagai PDF di atas tabel
    pdf_btn = tk.Button(konten_frame, text="Simpan sebagai PDF", command=simpan_pdf_pendapatan)
    pdf_btn.pack(pady=10)

    # Tabel untuk menampilkan laporan pendapatan
    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    tree = ttk.Treeview(tabel_frame, columns=("Tanggal", "Nama Barang", "Qty", "Harga Jual", "Total"), show='headings')
    tree.heading("Tanggal", text="Tanggal")
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Qty", text="Qty")
    tree.heading("Harga Jual", text="Harga Jual")
    tree.heading("Total", text="Total")

    tree.column("Tanggal", width=100)
    tree.column("Nama Barang", width=150)
    tree.column("Qty", width=50, anchor='center')
    tree.column("Harga Jual", width=100)
    tree.column("Total", width=100)

    tree.pack()

    # Tampilkan data pendapatan yang ada
    tampil_pendapatan(tree)

    # Menambahkan tombol untuk pendapatan harian, mingguan, dan bulanan
    button_frame = tk.Frame(konten_frame)
    button_frame.pack(side=tk.TOP, padx=10, pady=10)

    btn_harian = tk.Button(button_frame, text="Pendapatan Harian", command=tampil_pendapatan_harian)
    btn_harian.pack(side=tk.LEFT, padx=5)

    btn_mingguan = tk.Button(button_frame, text="Pendapatan Mingguan", command=tampil_pendapatan_mingguan)
    btn_mingguan.pack(side=tk.LEFT, padx=5)

    btn_bulanan = tk.Button(button_frame, text="Pendapatan Bulanan", command=tampil_pendapatan_bulanan)
    btn_bulanan.pack(side=tk.LEFT, padx=5)

def tampil_pendapatan(tree):
    # Menghapus semua item di tabel sebelum menampilkan data baru
    for item in tree.get_children():
        tree.delete(item)

    total_pendapatan = 0

    # Dapatkan bulan dan tahun saat ini
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    
    # Modifikasi query untuk mengambil data berdasarkan bulan dan tahun saat ini
    cursor.execute('''
        SELECT b.tanggal, s.nama_barang, b.jumlah, s.harga_jual
        FROM barang_keluar b
        JOIN stok_barang s ON b.id_barang = s.id
        WHERE strftime('%Y', b.tanggal) = ?
    ''', (str(current_year),))  # Format bulan dengan dua digit

    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        tanggal, nama_barang, jumlah, harga_jual = row
        # Remove thousands separator before converting to float
        harga_jual_float = float(harga_jual.replace('.', '').replace(',', '.'))
        total_harga = jumlah * harga_jual_float  # Calculate total based on quantity and price
        total_pendapatan += total_harga
        # Format the values for display
        tree.insert("", tk.END, values=(tanggal, nama_barang, jumlah, format_rp(harga_jual_float), format_rp(total_harga)))

    # Menambahkan total pendapatan ke baris baru di bawah tabel
    tree.insert("", tk.END, values=("", f"Total Pendapatan {current_year}", "", "", format_rp(total_pendapatan)))


    # Optionally, you can format the total row differently if needed
    total_row = tree.get_children()[-1]  # Get the last inserted row (total row)
    tree.item(total_row, tags=('total_row',))  # Tag the total row for styling if needed


def tampil_pendapatan_harian():
    for widget in konten_frame.winfo_children():
        widget.destroy()

    laporan_label = tk.Label(konten_frame, text="Pendapatan Harian", font=("Helvetica", 16))
    laporan_label.pack(pady=20)

    date_frame = tk.Frame(konten_frame)
    date_frame.pack(pady=10)

    tk.Label(date_frame, text="Pilih Tanggal:").pack(side=tk.LEFT)
    selected_date = DateEntry(date_frame, date_pattern='yyyy-mm-dd')
    selected_date.pack(side=tk.LEFT, padx=5)

    btn_tampilkan = tk.Button(date_frame, text="Tampilkan", command=lambda: tampil_pendapatan_berdasarkan_tanggal(selected_date.get_date()))
    btn_tampilkan.pack(side=tk.LEFT, padx=5)

    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    global tree
    tree = ttk.Treeview(tabel_frame, columns=("Tanggal", "Nama Barang", "Qty", "Harga Jual", "Total"), show='headings')
    tree.heading("Tanggal", text="Tanggal")
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Qty", text="Qty")
    tree.heading("Harga Jual", text="Harga Jual")
    tree.heading("Total", text="Total")

    tree.column("Tanggal", width=100)
    tree.column("Nama Barang", width=150)
    tree.column("Qty", width=50, anchor='center')
    tree.column("Harga Jual", width=100)
    tree.column("Total", width=100)

    tree.pack()

    # Tampilkan data untuk hari ini secara default
    today = datetime.now().strftime("%Y-%m-%d")
    tampil_pendapatan_berdasarkan_tanggal(today)

    # Tambahkan tombol kembali
    back_btn = tk.Button(konten_frame, text="Kembali", command=tampil_lap_pendapatan)
    back_btn.pack(pady=10)

    # Tambahkan tombol simpan sebagai PDF
    pdf_btn = tk.Button(konten_frame, text="Simpan sebagai PDF", command=lambda: simpan_pdf_pendapatan_harian(selected_date.get_date()))
    pdf_btn.pack(pady=10)


def tampil_pendapatan_berdasarkan_tanggal(tanggal):
    # Menghapus konten tabel sebelumnya
    for item in tree.get_children():
        tree.delete(item)

    total_pendapatan = 0

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()

    query = '''
    SELECT tanggal, nama_barang, jumlah, harga_jual, (jumlah * harga_jual) AS total
    FROM barang_keluar
    JOIN stok_barang ON barang_keluar.id_barang = stok_barang.id
    WHERE DATE(tanggal) = ?
    '''
    cursor.execute(query, (tanggal,))
    data = cursor.fetchall()

    # Menampilkan data ke dalam tabel
    for row in data:
        tree.insert("", tk.END, values=row)
        total_pendapatan += row[4]  # Menambahkan total dari kolom total (indeks 4)

    # Menambahkan total pendapatan ke baris baru di bawah tabel
    tree.insert("", tk.END, values=("", "Total Pendapatan", "", "", format_rp(total_pendapatan)))

    # Optionally, you can format the total row differently if needed
    total_row = tree.get_children()[-1]  # Get the last inserted row (total row)
    tree.item(total_row, tags=('total_row',))  # Tag the total row for styling if needed

    conn.close()

def simpan_pdf_pendapatan_harian(selected_date):
    # Membuat objek PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Mengambil tanggal yang dipilih
    formatted_date = selected_date.strftime("%d %B %Y")  # Format tanggal menjadi "DD Bulan YYYY"

    # Judul dengan tanggal yang dipilih
    pdf.cell(200, 10, txt=f"Laporan Pendapatan Harian - {formatted_date}", ln=True, align='C')
    pdf.cell(200, 10, txt="", ln=True)  # Space

    # Header tabel
    pdf.cell(30, 10, 'Tanggal', border=1)
    pdf.cell(50, 10, 'Nama Barang', border=1)
    pdf.cell(30, 10, 'Qty', border=1)
    pdf.cell(40, 10, 'Harga Jual', border=1)
    pdf.cell(40, 10, 'Total', border=1)
    pdf.ln()  # Pindah ke baris berikutnya

    # Mengambil data dari tabel
    total_pendapatan = 0  # Inisialisasi total pendapatan

    for row in tree.get_children():
        values = tree.item(row, 'values')

        # Pastikan nilai tidak kosong sebelum konversi
        qty = values[2] if values[2] else '0'
        harga_jual_str = values[3] if values[3] else '0'
        total_str = values[4] if values[4] else '0'

        # Konversi harga_jual dan total ke float
        try:
            harga_jual_float = float(harga_jual_str.replace('.', '').replace(',', '').replace('RP ', '').strip())
            total_float = float(total_str.replace('.', '').replace(',', '').replace('RP ', '').strip())
        except ValueError:
            messagebox.showerror("Error", f"Format nilai tidak valid: Harga Jual - {harga_jual_str}, Total - {total_str}")
            return

        pdf.cell(30, 10, values[0], border=1)  # Tanggal
        pdf.cell(50, 10, values[1], border=1)  # Nama Barang
        pdf.cell(30, 10, str(qty), border=1)  # Qty
        pdf.cell(40, 10, format_rp(harga_jual_float), border=1)  # Harga Jual
        pdf.cell(40, 10, format_rp(total_float), border=1)  # Total
        pdf.ln()  # Pindah ke baris berikutnya

        # Hitung total pendapatan
        total_pendapatan = total_float

    # Menambahkan total pendapatan di bawah tabel
    pdf.cell(200, 10, txt="", ln=True)  # Space
    pdf.cell(200, 10, txt=f"Total Pendapatan: {format_rp(total_pendapatan)}", ln=True, align='C')

    # Menyimpan PDF
    pdf.output("pendapatan_harian.pdf")
    messagebox.showinfo("Sukses", "Laporan harian berhasil disimpan PDF")

    return "pendapatan_harian.pdf"


def tampil_pendapatan_mingguan():
    for widget in konten_frame.winfo_children():
        widget.destroy()

    laporan_label = tk.Label(konten_frame, text="Pendapatan Mingguan", font=("Helvetica", 16))
    laporan_label.pack(pady=20)

    week_frame = tk.Frame(konten_frame)
    week_frame.pack(pady=10)

    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    current_week = (current_date.day - 1) // 7 + 1

    total_weeks = 5

    tk.Label(week_frame, text="Pilih Minggu:").pack(side=tk.LEFT)

    week_number = tk.StringVar(value=current_week)
    week_combobox = ttk.Combobox(week_frame, textvariable=week_number, state="readonly")
    week_combobox['values'] = [i for i in range(1, total_weeks + 1)]
    week_combobox.pack(side=tk.LEFT, padx=5)
    
    tk.Label(week_frame, text="Pilih Bulan:").pack(side=tk.LEFT)
    
    month_names = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    month_number = tk.StringVar(value=month_names[current_month - 1])
    month_combobox = ttk.Combobox(week_frame, textvariable=month_number, state="readonly")
    month_combobox['values'] = month_names
    month_combobox.pack(side=tk.LEFT, padx=5)

    btn_tampilkan = tk.Button(week_frame, text="Tampilkan", command=lambda: tampil_pendapatan_berdasarkan_minggu(int(week_number.get()), month_names.index(month_number.get()) + 1))
    btn_tampilkan.pack(side=tk.LEFT, padx=5)

    pdf_btn = tk.Button(week_frame, text="Simpan sebagai PDF", command=lambda: simpan_pdf_pendapatan_mingguan(int(week_number.get()), month_names.index(month_number.get()) + 1))
    pdf_btn.pack(pady=5)

    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    global tree
    tree = ttk.Treeview(tabel_frame, columns=("Tanggal", "Nama Barang", "Qty", "Harga Jual", "Total"), show='headings')
    tree.heading("Tanggal", text="Tanggal")
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Qty", text="Qty")
    tree.heading("Harga Jual", text="Harga Jual")
    tree.heading("Total", text="Total")

    tree.column("Tanggal", width=100)
    tree.column("Nama Barang", width=150)
    tree.column("Qty", width=50, anchor='center')
    tree.column("Harga Jual", width=100)
    tree.column("Total", width=100)

    tree.pack()

    tampil_pendapatan_berdasarkan_minggu(int(week_number.get()), current_month)

    back_btn = tk.Button(konten_frame, text="Kembali", command=tampil_lap_pendapatan)
    back_btn.pack(padx=5, pady=10)

def tampil_pendapatan_berdasarkan_minggu(week, month):
    if week < 1 or week > 5 or month < 1 or month > 12:
        messagebox.showerror("Input Salah", "Minggu harus antara 1-5 dan bulan antara 1-12.")
        return

    for item in tree.get_children():
        tree.delete(item)

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()

    current_year = datetime.now().year
    start_date = datetime.strptime(f'{current_year}-{month}-1', '%Y-%m-%d') + timedelta(weeks=week-1)
    end_date = start_date + timedelta(days=6)

    query = '''
    SELECT tanggal, nama_barang, jumlah, harga_jual, (jumlah * harga_jual) AS total
    FROM barang_keluar
    JOIN stok_barang ON barang_keluar.id_barang = stok_barang.id
    WHERE DATE(tanggal) BETWEEN ? AND ?
    '''
    cursor.execute(query, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    data = cursor.fetchall()

    total_pendapatan = 0

    if not data:
        messagebox.showinfo("Tidak Ada Data", "Tidak ada data untuk minggu ini.")
    else:
        for row in data:
            tree.insert("", tk.END, values=row)
            total_pendapatan += row[4]

    tree.insert("", tk.END, values=("", "Total Pendapatan", "", "", format_rp(total_pendapatan)))

    conn.close()

def simpan_pdf_pendapatan_mingguan(week, month):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    month_names = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    month_name = month_names[month - 1]

    pdf.cell(200, 10, txt=f"Laporan Pendapatan Minggu Ke-{week} Bulan {month_name}", ln=True, align='C')
    pdf.cell(200, 10, txt="", ln=True)

    pdf.cell(30, 10, 'Tanggal', border=1)
    pdf.cell(50, 10, 'Nama Barang', border=1)
    pdf.cell(30, 10, 'Qty', border=1)
    pdf.cell(40, 10, 'Harga Jual', border=1)
    pdf.cell(40, 10, 'Total', border=1)
    pdf.ln()

    total_pendapatan = 0

    for row in tree.get_children():
        values = tree.item(row, 'values')

        # Pastikan nilai tidak kosong sebelum konversi
        qty = values[2] if values[2] else '0'
        harga_jual = values[3] if values[3] else '0'
        total = values[4] if values[4] else '0'

        # Konversi harga_jual dan total ke float
        harga_jual_float = float(harga_jual.replace('.', '').replace(',', '').replace('RP ', '').strip())
        total_float = float(total.replace('.', '').replace(',', '').replace('RP ', '').strip())

        pdf.cell(30, 10, values[0], border=1)  # Tanggal
        pdf.cell(50, 10, values[1], border=1)  # Nama Barang
        pdf.cell(30, 10, str(qty), border=1)  # Qty
        pdf.cell(40, 10, format_rp(harga_jual_float), border=1)  # Harga Jual
        pdf.cell(40, 10, format_rp(total_float), border=1)  # Total
        pdf.ln()

        # Hitung total pendapatan
        total_pendapatan = total_float

    pdf.cell(200, 10, txt="", ln=True)  # Space
    pdf.cell(200, 10, txt=f"Total Pendapatan: {format_rp(total_pendapatan)}", ln=True, align='C')

    # Menyimpan PDF
    pdf.output("pendapatan_mingguan.pdf")
    messagebox.showinfo("Sukses", "Laporan mingguan berhasil disimpan sebagai PDF!")


def tampil_pendapatan_bulanan():
    for widget in konten_frame.winfo_children():
        widget.destroy()

    laporan_label = tk.Label(konten_frame, text="Pendapatan Bulanan", font=("Helvetica", 16))
    laporan_label.pack(pady=20)

    # Frame untuk input bulan dan tombol
    input_frame = tk.Frame(konten_frame)
    input_frame.pack(pady=10)

    # Menghitung bulan saat ini
    current_month = datetime.now().month  # Mengambil bulan saat ini

    tk.Label(input_frame, text="Pilih Bulan:").pack(side=tk.LEFT, padx=5)

    # Menggunakan Combobox untuk memilih bulan dengan nama
    month_names = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    month_number = tk.StringVar(value=month_names[current_month - 1])  # Set default ke bulan saat ini
    month_combobox = ttk.Combobox(input_frame, textvariable=month_number, state="readonly")
    month_combobox['values'] = month_names  # Menggunakan nama bulan
    month_combobox.pack(side=tk.LEFT, padx=5)

    btn_tampilkan = tk.Button(input_frame, text="Tampilkan", command=lambda: tampil_pendapatan_berdasarkan_bulanan(month_names.index(month_number.get()) + 1))
    btn_tampilkan.pack(side=tk.LEFT, padx=5)

    # Tambahkan tombol simpan sebagai PDF
    pdf_btn = tk.Button(input_frame, text="Simpan sebagai PDF", command=lambda: simpan_pdf_pendapatan_bulanan(month_names.index(month_number.get()) + 1))
    pdf_btn.pack(side=tk.LEFT, padx=5)

    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    global tree
    tree = ttk.Treeview(tabel_frame, columns=("Tanggal", "Nama Barang", "Qty", "Harga Jual", "Total"), show='headings')
    tree.heading("Tanggal", text="Tanggal")
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Qty", text="Qty")
    tree.heading("Harga Jual", text="Harga Jual")
    tree.heading("Total", text="Total")

    tree.column("Tanggal", width=100)
    tree.column("Nama Barang", width=150)
    tree.column("Qty", width=50, anchor='center')
    tree.column("Harga Jual", width=100)
    tree.column("Total", width=100)

    tree.pack()

    # Tampilkan data untuk bulan saat ini secara default
    tampil_pendapatan_berdasarkan_bulanan(current_month)

    # Tambahkan tombol kembali
    back_btn = tk.Button(konten_frame, text="Kembali", command=tampil_lap_pendapatan)
    back_btn.pack(padx=5, pady=10)


def tampil_pendapatan_berdasarkan_bulanan(month):
    # Validasi input
    if month < 1 or month > 12:
        messagebox.showerror("Input Salah", "Bulan harus antara 1-12.")
        return

    # Menghapus konten tabel sebelumnya
    for item in tree.get_children():
        tree.delete(item)

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()

    # Mendapatkan tahun saat ini
    current_year = datetime.now().year

    # Menghitung tanggal awal dan akhir bulan
    start_date = datetime(current_year, month, 1)
    if month == 12:
        end_date = datetime(current_year + 1, 1, 1)  # 1 Januari tahun depan
    else:
        end_date = datetime(current_year, month + 1, 1)  # 1 bulan depan

    query = '''
    SELECT tanggal, nama_barang, jumlah, harga_jual, (jumlah * harga_jual) AS total
    FROM barang_keluar
    JOIN stok_barang ON barang_keluar.id_barang = stok_barang.id
    WHERE DATE(tanggal) BETWEEN ? AND ?
    '''
    cursor.execute(query, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    data = cursor.fetchall()

    total_pendapatan = 0  # Inisialisasi total pendapatan

    # Menampilkan data ke dalam tabel
    if not data:
        messagebox.showinfo("Tidak Ada Data", "Tidak ada data untuk bulan ini.")
    else:
        for row in data:
            tree.insert("", tk.END, values=row)
            total_pendapatan += row[4]  # Menambahkan total dari kolom total (indeks 4)

    # Menambahkan total pendapatan ke baris baru di bawah tabel
    tree.insert("", tk.END, values=("", "Total Pendapatan", "", "", format_rp(total_pendapatan)))

    conn.close()


def simpan_pdf_pendapatan_bulanan(month):
    # Membuat objek PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Format nama bulan
    month_names = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    month_name = month_names[month - 1]  # Mengambil nama bulan berdasarkan index

    # Judul
    pdf.cell(200, 10, txt=f"Laporan Pendapatan Bulan {month_name}", ln=True, align='C')
    pdf.cell(200, 10, txt="", ln=True)  # Space

    # Header tabel
    pdf.cell(30, 10, 'Tanggal', border=1)
    pdf.cell(50, 10, 'Nama Barang', border=1)
    pdf.cell(30, 10, 'Qty', border=1)
    pdf.cell(40, 10, 'Harga Jual', border=1)
    pdf.cell(40, 10, 'Total', border=1)
    pdf.ln()  # Pindah ke baris berikutnya

    total_pendapatan = 0  # Inisialisasi total pendapatan

    # Mengambil data dari tabel
    for row in tree.get_children():
        values = tree.item(row, 'values')

        # Pastikan nilai tidak kosong sebelum konversi
        qty = values[2] if values[2] else '0'
        harga_jual_str = values[3] if values[3] else '0'
        total_str = values[4] if values[4] else '0'

        # Konversi harga_jual dan total ke float
        try:
            harga_jual_float = float(harga_jual_str.replace('.', '').replace(',', '').replace('RP ', '').strip())
            total_float = float(total_str.replace('.', '').replace(',', '').replace('RP ', '').strip())
        except ValueError:
            messagebox.showerror("Error", f"Format nilai tidak valid: Harga Jual - {harga_jual_str}, Total - {total_str}")
            return

        pdf.cell(30, 10, values[0], border=1)  # Tanggal
        pdf.cell(50, 10, values[1], border=1)  # Nama Barang
        pdf.cell(30, 10, str(qty), border=1)  # Qty
        pdf.cell(40, 10, format_rp(harga_jual_float), border=1)  # Harga Jual
        pdf.cell(40, 10, format_rp(total_float), border=1)  # Total
        pdf.ln()  # Pindah ke baris berikutnya

        # Hitung total pendapatan
        total_pendapatan = total_float

    # Menambahkan total pendapatan di bawah tabel
    pdf.cell(200, 10, txt="", ln=True)  # Space
    pdf.cell(200, 10, txt=f"Total Pendapatan: {format_rp(total_pendapatan)}", ln=True, align='C')

    # Menyimpan PDF
    pdf.output("pendapatan_bulanan.pdf")
    messagebox.showinfo("Sukses", "Laporan bulanan berhasil disimpan sebagai PDF!")




def tampil_pendapatan_filtered(cari):
    for widget in konten_frame.winfo_children():
        if widget not in [filter_frame, pdf_btn]:
            widget.destroy()

    laporan_label = tk.Label(konten_frame, text="Laporan Pendapatan", font=("Helvetica", 16))
    laporan_label.pack(pady=20)

    # Frame untuk filter pencarian
    filter_frame = tk.Frame(konten_frame)
    filter_frame.pack(pady=10)

    tk.Label(filter_frame, text="Cari Nama Barang:").pack(side=tk.LEFT)
    entry_search = tk.Entry(filter_frame)
    entry_search.pack(side=tk.LEFT, padx=5)

    search_btn = tk.Button(filter_frame, text="Cari", command=lambda: tampil_pendapatan_filtered(entry_search.get()))
    search_btn.pack(side=tk.LEFT)

    # Tombol untuk menyimpan sebagai PDF di atas tabel
    pdf_btn = tk.Button(konten_frame, text="Simpan sebagai PDF", command=simpan_pdf_pendapatan)
    pdf_btn.pack(pady=10)

    # Tabel untuk menampilkan laporan pendapatan
    tabel_frame = tk.Frame(konten_frame, bg="#ECF0F1")
    tabel_frame.pack(pady=20)

    tree = ttk.Treeview(tabel_frame, columns=("Tanggal", "Nama Barang", "Satuan", "Harga Jual", "Jumlah"), show='headings')
    tree.heading("Tanggal", text="Tanggal")
    tree.heading("Nama Barang", text="Nama Barang")
    tree.heading("Satuan", text="Satuan")
    tree.heading("Harga Jual", text="Harga Jual")
    tree.heading("Jumlah", text="Jumlah")

    tree.column("Tanggal", width=100)
    tree.column("Nama Barang", width=150)
    tree.column("Satuan", width=50, anchor='center')
    tree.column("Harga Jual", width=100)
    tree.column("Jumlah", width=100)

    tree.pack()

    # Keterangan Total Pendapatan
    total_label = tk.Label(konten_frame, text="Total Pendapatan: Rp 0", font=("Helvetica", 14))
    total_label.pack(pady=10)

    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.tanggal, s.nama_barang, b.jumlah, s.harga_jual
        FROM barang_keluar b
        JOIN stok_barang s ON b.id_barang = s.id
        WHERE s.nama_barang LIKE ?
    ''', ('%' + cari + '%',))
    
    rows = cursor.fetchall()
    conn.close()

    total_pendapatan = 0

    for row in rows:
        tanggal, nama_barang, jumlah, harga_jual = row
        total_harga = jumlah * float(harga_jual)
        total_pendapatan += total_harga
        tree.insert("", tk.END, values=(tanggal, nama_barang, jumlah, harga_jual, total_harga))

    # Menambahkan total pendapatan ke baris baru di bawah tabel
    tree.insert("", tk.END, values=("", "Total Pendapatan", "", "", total_pendapatan))

    total_label.config(text=f"Total Pendapatan: Rp {total_pendapatan}")

def simpan_pdf_pendapatan():
    # Membuat objek PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Dapatkan tahun saat ini
    current_year = datetime.now().year
    # Judul
    pdf.cell(200, 10, txt=f"Laporan Pendapatan Tahun {current_year}", ln=True, align='C')
    pdf.cell(200, 10, txt="", ln=True)  # Space

    # Header tabel
    pdf.cell(30, 10, 'Tanggal', border=1)
    pdf.cell(50, 10, 'Nama Barang', border=1)
    pdf.cell(30, 10, 'Qty', border=1)
    pdf.cell(40, 10, 'Harga Jual', border=1)
    pdf.cell(40, 10, 'Total', border=1)
    pdf.ln()  # Pindah ke baris berikutnya

    # Mengambil data dari database
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.tanggal, s.nama_barang, b.jumlah, s.harga_jual
        FROM barang_keluar b
        JOIN stok_barang s ON b.id_barang = s.id
    ''')
    rows = cursor.fetchall()
    conn.close()

    total_pendapatan = 0

    # Menambahkan data ke PDF
    for row in rows:
        tanggal, nama_barang, jumlah, harga_jual = row
        # Clean the harga_jual string before converting to float
        harga_jual_float = float(harga_jual.replace('.', '').replace(',', '.'))

        # Hitung total harga berdasarkan jumlah
        total_harga = jumlah * harga_jual_float
        total_pendapatan += total_harga

        # Menambahkan baris ke PDF
        pdf.cell(30, 10, tanggal, border=1)  # Tanggal
        pdf.cell(50, 10, nama_barang, border=1)  # Nama Barang
        pdf.cell(30, 10, str(jumlah), border=1)  # Jumlah
        pdf.cell(40, 10, format_rp(harga_jual_float), border=1)  # Harga Jual
        pdf.cell(40, 10, format_rp(total_harga), border=1)  # Total Pendapatan
        pdf.ln()  # Pindah ke baris berikutnya

    # Menambahkan total pendapatan di bawah tabel
    pdf.cell(200, 10, txt="", ln=True)  # Space
    pdf.cell(200, 10, txt=f"Total Pendapatan : {format_rp(total_pendapatan)}", ln=True, align='C')

    # Menyimpan PDF
    pdf.output("laporan_pendapatan.pdf")
    messagebox.showinfo("Sukses", "Laporan berhasil disimpan sebagai PDF!")


# Fungsi untuk menutup toko
def tutup_toko():
    # Cek koneksi internet
    try:
        requests.get('https://www.google.com', timeout=5)
        internet_connected = True
    except requests.ConnectionError:
        internet_connected = False

    if not internet_connected:
        messagebox.showwarning("Tidak Terhubung ke Internet", "Anda tidak dapat menutup toko karena tidak ada koneksi internet.")
        return

    # Jika terhubung ke internet, kirim laporan
    kirim_laporan_ke_whatsapp()

    # Tampilkan pesan sukses
    messagebox.showinfo("Sukses", "Toko berhasil ditutup dan laporan telah dikirim.")

    # Tutup aplikasi (jika menggunakan Tkinter)
    # Tutup aplikasi
    app.quit()


def kirim_laporan_ke_whatsapp():
    # Konfigurasi Twilio
    account_sid = 'AC1f43e5d3c0880523ec627d243e2710f1'
    auth_token = '12b3a93525d237630db202278c07bd65'
    client = Client(account_sid, auth_token)

    # Nomor pengirim dan penerima
    from_whatsapp_number = 'whatsapp:+14155238886'  # Ganti dengan nomor WhatsApp Twilio Anda
    to_whatsapp_number = 'whatsapp:+6288223210054'  # Ganti dengan nomor WhatsApp Anda

    # Ambil tanggal hari ini
    today = datetime.now().strftime('%Y-%m-%d')

    # Ambil laporan barang keluar hari ini
    conn = sqlite3.connect('stok_barang.db')
    cursor = conn.cursor()
    
    # Ambil data barang keluar
    cursor.execute('''
        SELECT sb.nama_barang, bk.tanggal, bk.jumlah
        FROM barang_keluar bk
        JOIN stok_barang sb ON bk.id_barang = sb.id
        WHERE bk.tanggal = ?
    ''', (today,))
    rows_barang_keluar = cursor.fetchall()

    # Ambil data pendapatan hari ini
    cursor.execute('''
        SELECT b.tanggal, s.nama_barang, b.jumlah, s.harga_jual
        FROM barang_keluar b
        JOIN stok_barang s ON b.id_barang = s.id
        WHERE DATE(b.tanggal) = ?
    ''', (today,))
    rows_pendapatan = cursor.fetchall()
    conn.close()

    # Format pesan untuk barang keluar
    pesan_barang_keluar = f"*Laporan Barang Keluar Hari Ini Tanggal:* {today}\n\n"
    if not rows_barang_keluar:
        pesan_barang_keluar += "Tidak ada barang keluar hari ini.\n\n"
    else:
        for row in rows_barang_keluar:
            nama_barang, tanggal, jumlah = row
            pesan_barang_keluar += f"Nama Barang: {nama_barang}, Jumlah: {jumlah}\n"

    # Mengirim pesan laporan barang keluar
    client.messages.create(
        body=pesan_barang_keluar,
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )

    # Format pesan untuk pendapatan
    pesan_pendapatan = f"*Laporan Pendapatan Hari Ini Tanggal:* {today}\n\n"
    total_pendapatan = 0
    if not rows_pendapatan:
        pesan_pendapatan += "Tidak ada pendapatan hari ini.\n"
    else:
        for index, row in enumerate(rows_pendapatan, start=1):
            tanggal, nama_barang, jumlah, harga_jual = row
            harga_jual_float = float(harga_jual.replace('.', '').replace(',', '.'))
            total_harga = jumlah * harga_jual_float
            total_pendapatan += total_harga
            pesan_pendapatan += f"{index}. Nama Barang: {nama_barang}, Jumlah: {jumlah}, Harga Jual: {format_rp(harga_jual_float)}, Total: {format_rp(total_harga)}\n"

    # Tambahkan total pendapatan ke pesan
    pesan_pendapatan += f"\nTotal Pendapatan Hari Ini: {format_rp(total_pendapatan)}"

    # Mengirim pesan laporan pendapatan
    client.messages.create(
        body=pesan_pendapatan,
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )

    messagebox.showinfo("Info", "Laporan telah dikirim ke WhatsApp!")




# Membuat aplikasi utama
app = tk.Tk()
app.title("Aplikasi Persediaan Barang")
app.geometry("1024x600")

# Font untuk menu
menu_font = Font(family="Helvetica", size=12, weight="bold")

# Frame menu
menu_frame = tk.Frame(app, bg="#2C3E50", width=200)
menu_frame.pack(side="left", fill="y")

# Frame konten
konten_frame = tk.Frame(app, bg="#ECF0F1")
konten_frame.pack(side="right", expand=True, fill="both")

# Logo
logo_img = Image.open(r'D:\Aplikasi Stok Barang\assets\logo.png')
logo_img = logo_img.resize((150, 150), Image.LANCZOS)
logo_photo = ImageTk.PhotoImage(logo_img)
logo_label = tk.Label(menu_frame, image=logo_photo, bg="#2C3E50")
logo_label.pack(pady=20)

# Memuat ikon untuk menu
dashboard_icon = Image.open(r'D:\Aplikasi Stok Barang\assets\computer.png')  # Ganti dengan path ke ikon Anda
dashboard_icon = dashboard_icon.resize((20, 20), Image.LANCZOS)  # Ukuran ikon
dashboard_icon_tk = ImageTk.PhotoImage(dashboard_icon)

data_barang_icon = Image.open(r'D:\Aplikasi Stok Barang\assets\box.png')  # Ganti dengan path ke ikon Anda
data_barang_icon = data_barang_icon.resize((20, 20), Image.LANCZOS)  # Ukuran ikon
data_barang_icon_tk = ImageTk.PhotoImage(data_barang_icon)

transaksi_icon = Image.open(r'D:\Aplikasi Stok Barang\assets\cash-flow.png')  # Ganti dengan path ke ikon Anda
transaksi_icon = transaksi_icon.resize((20, 20), Image.LANCZOS)
transaksi_icon_tk = ImageTk.PhotoImage(transaksi_icon)

laporan_icon = Image.open(r'D:\Aplikasi Stok Barang\assets\report.png')  # Ganti dengan path ke ikon Anda
laporan_icon = laporan_icon.resize((20, 20), Image.LANCZOS)
laporan_icon_tk = ImageTk.PhotoImage(laporan_icon)

tutup_toko_icon = Image.open(r'D:\Aplikasi Stok Barang\assets\closed.png')  # Ganti dengan path ke ikon Anda
tutup_toko_icon = tutup_toko_icon.resize((20, 20), Image.LANCZOS)
tutup_toko_icon_tk = ImageTk.PhotoImage(tutup_toko_icon)

# Menu items
menu_items = [
    ("Dashboard", tampil_dashboard, dashboard_icon_tk),
    ("Data Barang", tampil_data_barang, data_barang_icon_tk),
]


# Tampilkan dashboard pada awal aplikasi
tampil_dashboard()

# Menambahkan menu utama
for item in menu_items:
    menu_btn = tk.Button(menu_frame, text=item[0], font=("Helvetica", 12), fg="white", bg="#2980B9", 
                         activebackground="#3498DB", bd=0, padx=20, pady=10, anchor="w", 
                         command=item[1], image=item[2], compound=tk.LEFT)
    menu_btn.pack(fill="x")

# Menambahkan menu Transaksi
transaksi_menu_btn = tk.Menubutton(menu_frame, text="Transaksi", font=menu_font, relief="raised", bg="#2980B9", fg="white")
transaksi_menu_btn.menu = tk.Menu(transaksi_menu_btn, tearoff=0)
transaksi_menu_btn["menu"] = transaksi_menu_btn.menu

# Menambahkan submenu untuk Barang Masuk dan Barang Keluar
transaksi_menu_btn.menu.add_command(label="Barang Masuk", command=barang_masuk)
transaksi_menu_btn.menu.add_command(label="Barang Keluar", command=barang_keluar)

transaksi_menu_btn.pack(fill="x")
transaksi_menu_btn.config(image=transaksi_icon_tk, compound=tk.LEFT)


# Menambahkan menu Laporan
laporan_menu_btn = tk.Menubutton(menu_frame, text="Laporan", font=menu_font, relief="raised", bg="#2980B9", fg="white")
laporan_menu_btn.menu = tk.Menu(laporan_menu_btn, tearoff=0)
laporan_menu_btn["menu"] = laporan_menu_btn.menu

# Menambahkan submenu untuk laporan
laporan_menu_btn.menu.add_command(label="Lap Barang Masuk", command=lambda: tampil_lap_barang_masuk())
laporan_menu_btn.menu.add_command(label="Lap Barang Keluar", command=lambda: tampil_lap_barang_keluar())
laporan_menu_btn.menu.add_command(label="Lap Stok Barang", command=lambda: tampil_lap_stok_barang())
laporan_menu_btn.menu.add_command(label="Lap Pendapatan", command=tampil_lap_pendapatan)

laporan_menu_btn.pack(fill="x")
laporan_menu_btn.config(image=laporan_icon_tk, compound=tk.LEFT)

# Menambahkan menu Transaksi
tutup_toko_btn = tk.Button(menu_frame, text="Tutup Toko", font=("Helvetica", 12), fg="white", bg="#c0392b", 
                            activebackground="#e74c3c", bd=0, padx=20, pady=10, anchor="w", 
                            command=tutup_toko, image=tutup_toko_icon_tk, compound=tk.LEFT)
tutup_toko_btn.pack(fill="x")

# Tampilkan dashboard pada awal aplikasi


# Menjalankan aplikasi
app.mainloop()  