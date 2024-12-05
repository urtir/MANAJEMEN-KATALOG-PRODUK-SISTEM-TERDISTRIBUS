# MANAJEMEN KATALOG PRODUK SISTEM TERDISTRIBUSI

## Deskripsi
## dibuat oleh mahdy brata

Sistem manajemen katalog produk berbasis REST API yang memungkinkan akses dari berbagai perangkat dengan autentikasi API key.

## Teknologi yang Digunakan

* Python 3.10
* Flask 2.0.1
* MySQL
* Flask-CORS

## Langkah-langkah Implementasi

### 0. Persiapan Lingkungan

```
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Implementasi dimulai dengan menyiapkan lingkungan pengembangan yang terisolasi menggunakan Python virtual environment. Hal ini penting untuk menghindari konflik dependensi antar proyek. Virtual environment dibuat menggunakan perintah `python -m venv venv` dan diaktifkan melalui `.\venv\Scripts\activate` pada sistem Windows. Selanjutnya, instalasi dependensi dilakukan menggunakan `pip install -r requirements.txt` yang mencakup Flask 2.0.1, MySQL connector, dan pustaka pendukung lainnya.

### 1. Konfigurasi Database

```
-- Buat database
CREATE DATABASE product_catalog;
USE product_catalog;

-- Buat tabel products
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT
);

-- Buat tabel api_keys
CREATE TABLE api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_value VARCHAR(64) NOT NULL UNIQUE,
    client_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Struktur database dirancang untuk mendukung dua entitas utama: produk dan API key. Tabel `products` menyimpan informasi produk dengan kolom id (auto-increment), nama, kategori, harga (decimal untuk akurasi), dan deskripsi. Tabel `api_keys` dibuat untuk manajemen otentikasi dengan menyimpan key_value yang unik, nama klien, status aktif, dan timestamp pembuatan. Implementasi menggunakan MySQL sebagai RDBMS karena kemampuannya menangani transaksi dan relasi data.

### 2. Konfigurasi Environment

```
SECRET_KEY=your_secret_key_here
FLASK_DEBUG=True
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=product_catalog
```

Konfigurasi aplikasi menggunakan pendekatan environment variables melalui file `.env` untuk meningkatkan keamanan dan fleksibilitas deployment. Variabel konfigurasi mencakup SECRET_KEY untuk session Flask, kredensial database, dan mode debug. Implementasi menggunakan python-dotenv untuk memuat konfigurasi secara otomatis saat aplikasi dijalankan.

### 3. Menjalankan Server

```
python app.py
```

REST API diimplementasikan menggunakan Flask dengan prinsip-prinsip RESTful: stateless, resource-based URLs, dan penggunaan metode HTTP yang tepat. Endpoint API dibagi menjadi dua kategori utama: manajemen API key dan operasi CRUD produk. Setiap endpoint dilengkapi decorator `@require_api_key` untuk otentikasi dan `@db_connection` untuk manajemen koneksi database.

### 4. Mendapatkan API Key

Gunakan Postman atau curl untuk mendapatkan API key:

```
curl -X POST http://localhost:5000/api/keys \
-H "Content-Type: application/json" \
-d "{\"client_name\":\"client1\"}"
```

Klien API diimplementasikan dalam class `ProductAPI` yang menyediakan metode-metode untuk berinteraksi dengan server. Implementasi mencakup penanganan error, validasi response, dan konversi tipe data. Klien menggunakan requests library untuk komunikasi HTTP dan menyertakan API key dalam header setiap request

### 5. Mengakses API dari Perangkat Lain

#### a. Install Dependencies di Perangkat Client

```
pip install requests
```

Akses dari perangkat lain difasilitasi melalui client Python yang menggunakan library requests. Client dikonfigurasi dengan IP server dan API key, menyertakan header `X-API-Key` pada setiap request. Implementasi mencakup penanganan error dan validasi response

#### b. Gunakan Script Client

```
from client_api import ProductAPI

# Ganti dengan IP server dan API key yang diperoleh
SERVER_IP = '192.168.xxx.xxx'
API_KEY = 'your_api_key_here'

client = ProductAPI(SERVER_IP, API_KEY)

# Test koneksi
if client.test_connection():
    # Get all products
    products = client.get_products()
    print(products)
```

Pengujian dilakukan secara menyeluruh mencakup unit testing untuk komponen server dan client, serta integration testing untuk memverifikasi interaksi antar komponen. Framework pytest digunakan dengan fokus pada validasi autentikasi API key, operasi CRUD produk, dan penanganan error. Seluruh sistem menerapkan prinsip REST dengan endpoint terstruktur, autentikasi stateless, dan format data JSON.

## Endpoint API yang Tersedia

### 1. Manajemen API Key

* `POST /api/keys` - Membuat API key baru

### 2. Manajemen Produk

* `GET /api/products` - Mendapatkan semua produk
* `GET /api/products/<id>` - Mendapatkan produk spesifik
* `POST /api/products` - Menambah produk baru
* `PUT /api/products/<id>` - Memperbarui produk
* `DELETE /api/products/<id>` - Menghapus produk

## Format Request dan Response

### Contoh Request POST Product

```
{
    "name": "Produk Test",
    "category": "Elektronik",
    "price": 99.99,
    "description": "Deskripsi produk"
}
```

### Headers yang Diperlukan

```
Content-Type: application/json
X-API-Key: your_api_key_here
```

## Penanganan Error

* 401: API key tidak valid/tidak ada
* 404: Resource tidak ditemukan
* 500: Server error

## Keamanan

* Menggunakan API key untuk autentikasi
* CORS enabled untuk akses cross-origin
* Rate limiting (opsional)

Keamanan sistem ditangani melalui multiple layer: API key authentication, CORS policy untuk akses cross-origin, dan proper error handling. Logging diimplementasi untuk monitoring dan troubleshooting. Dokumentasi lengkap disediakan dalam README.md, mencakup setup, penggunaan API, dan panduan troubleshooting.

## Pengujian

```
# Jalankan unit tests
python -m pytest tests/
```

## Troubleshooting

1. Pastikan server MySQL berjalan
2. Periksa konfigurasi firewall untuk port 5000
3. Validasi API key pada header request
4. Periksa log server untuk error detail

## Kontribusi

Silakan buat pull request untuk kontribusi.

## Lisensi

MIT License
