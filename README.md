# Jawaban Soal Scraping Web API BPS

Repositori ini berisi dua script Python untuk menyelesaikan soal berikut:

## Soal

### 1. **Scraping API URL dari web BPS**
Pada web bps.go.id lakukan pengambilan API URL JSON untuk mengambil judul data pada Tabel Statistik dengan klik Produk > Statistik menurut Subjek.  
Ambil scraping **semua judul data** di Tabel Statistik dan **ambil URL Web API** (dari tombol JSON).

**Hasil scraping:**
| Subjek                           | Kategori    | Judul Tabel                                                                              | WebAPI URL                                        |
|-----------------------------------|-------------|------------------------------------------------------------------------------------------|---------------------------------------------------|
| Statistik Demografi dan Sosial    | Pendidikan  | Angka Harapan Lama Sekolah (HLS) menurut Jenis Kelamin (Tahun), 2024                    | https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/domain/0000/var/457/key/WebAPI_KEY |

---

### 2. **Get data API URL dari web BPS ke CSV file**
Dari salah satu API URL yang diambil, lakukan pengambilan data JSON, lalu **modifikasi** data menjadi tabel berikut dan **simpan ke CSV**:

**Contoh hasil CSV yang diharapkan:**

| provinsi | kabupaten_kota | laki_laki | perempuan | tahun |
|----------|----------------|-----------|-----------|-------|
| Aceh     | Simeuleu       | 14,30     | 14,62     | 2024  |

---

## Struktur File

- **main.py**  
  Menjawab soal nomor 1 (scraping judul tabel dan WebAPI URL).
- **2.py**  
  Menjawab soal nomor 2 (mengambil data dari WebAPI dan menyimpannya ke CSV).

---

## Penjelasan Script

### 1. `main.py` — Scraping Judul Tabel dan WebAPI URL
Script ini melakukan scraping otomatis pada halaman statistik BPS untuk:

Mengambil seluruh daftar subjek, kategori, judul tabel statistik, dan WebAPI URL JSON (otomatis klik tombol JSON pada tiap tabel).

Data hasil scraping langsung disimpan ke file bps_all_tables.csv.

Script ini sudah diuji coba dan berhasil mengambil data lebih dari 500+ tabel BPS secara otomatis.

### 2. `2.py` — PARSING WebAPI URL

Script ini digunakan untuk:

Mengambil data statistik pendidikan dari WebAPI BPS (API JSON) untuk Angka Harapan Lama Sekolah (HLS) berdasarkan jenis kelamin tahun 2024.

Melakukan parsing dan transformasi data menjadi tabel dengan kolom: provinsi, kabupaten_kota, laki_laki, perempuan, tahun.

Menyajikan data dalam tampilan web (Flask), serta menyediakan fitur download CSV otomatis via endpoint /bps-hls-csv.

Script ini telah diuji coba dan berhasil mengambil serta memproses data seluruh Indonesia secara otomatis ke format yang siap simpan database atau diolah lebih lanjut.

## Dependensi

Pastikan sudah menginstall library berikut sebelum menjalankan script:
- `selenium`
- `flask`
- `requests`
- `pandas`


#### Cara menjalankan:

```bash
pip install -r requirements.txt
python main.py (No 1)
python 2.py (No 2)

