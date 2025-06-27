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


## Flow Script
┌────────────────────┐
│     Start Script   │
└────────┬───────────┘
         │
         ▼
1. Buka halaman:
   https://www.bps.go.id/id/statistics-table?subject=528
         │
         ▼
2. Expand seluruh tombol accordion untuk menampilkan subjek
         │
         ▼
3. Loop setiap subjek:
   └─ Ambil nama subjek
   └─ Loop kategori di dalamnya:
      └─ Ambil nama kategori & URL
         │
         ▼
4. Untuk setiap kategori:
   └─ Kunjungi URL kategori
   └─ Tunggu loading selesai
   └─ Periksa apakah ada pagination
         │
         ▼
5. Loop setiap halaman:
   └─ Jika bukan halaman pertama, klik pagination
   └─ Tunggu loading selesai
   └─ Tunggu tabel stabil (jumlah tidak berubah dalam durasi tertentu)
         │
         ▼
6. Loop setiap tabel di halaman:
   └─ Scroll ke tabel
   └─ Tutup popup jika muncul
   └─ Klik tabel untuk buka detail
         ├─ Jika gagal klik:
         │   └─ Logging dan lanjut ke tabel berikutnya
         │
         └─ Jika berhasil:
             └─ Ambil judul tabel (h1)
             └─ Klik tombol `JSON`
             └─ Ambil URL WebAPI
                 ├─ Jika gagal:
                 │   └─ Reload halaman kategori
                 │   └─ Simpan hasil kosong
                 │
                 └─ Jika berhasil:
                     └─ Simpan ke hasil (CSV)
                     └─ Kembali ke halaman kategori
         │
         ▼
7. Simpan hasil ke CSV setiap kali data berhasil diambil
         │
         ▼
8. Setelah semua kategori selesai:
   └─ Cetak informasi kategori kosong (jika ada)
         │
         ▼
9. Simpan semua hasil akhir
         │
         ▼
    ┌──────────────┐
    │ End of Script│
    └──────────────┘


## Error Handling dan Safety Check
Jenis Error	Solusi di Script
**1. Loading Spinner terlalu lama**	
Timeout ditangani dengan warning → lanjut proses
**2. Tombol pagination tidak bisa diklik**	
Retry klik hingga 4 kali → log warning/error
**3. Judul tabel kosong / error**
klik	Lewati dengan logging, tanpa hentikan proses
**4. Gagal ambil endpoint JSON**
Dianggap gagal → reload halaman → skip satu tabel
**5. Popup muncul saat klik tabel**
Script otomatis close popup dulu
**6. KeyboardInterrupt (Ctrl+C)**
Tangkap KeyboardInterrupt → hasil tetap disimpan

## Update hasil
- **WebAPI URL**: Hasil pada [WebAPI_KEY] sudah otomatis diupdate dengan URL yang baru dengan BPS APIs provides programmatic access to read BPS data
- **Hasil Scraping**: Sudah di Uji Coba secara Berkala dapat Mengambil seluruh secara 100% Valid 
- **Testi Tabel**: berasil mengambil 1000 Tabel dengan 1000 Subjek,katagori,Judul,web Url Tabel yang Valid


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

