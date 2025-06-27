## Struktur File

- **main.py**  
  Menjawab soal nomor 1 (scraping judul tabel dan WebAPI URL).
- **2.py**  
  Menjawab soal nomor 2 (mengambil data dari WebAPI dan menyimpannya ke CSV).

---

## Penjelasan Script

### 1. `main.py` — Scraping Judul Tabel dan WebAPI URL


## Flow Scraping

1. **Buka halaman utama statistik BPS**  
   URL: `https://www.bps.go.id/id/statistics-table?subject=528`

2. **Expand semua subjek (accordion)**  
   Klik semua tombol untuk menampilkan kategori di setiap subjek.

3. **Loop semua subjek dan kategori**
   - Ambil nama subjek (misalnya: *Pendidikan*)
   - Ambil semua kategori di dalamnya (misalnya: *Angka Partisipasi Sekolah*) dan URL-nya

4. **Kunjungi setiap kategori**
   - Buka URL kategori
   - Tunggu hingga loading selesai
   - Periksa apakah ada pagination

5. **Loop per halaman (jika ada pagination)**
   - Klik nomor halaman (jika bukan halaman pertama)
   - Tunggu loading spinner hilang
   - Tunggu sampai jumlah tabel stabil (tidak berubah-ubah)

6. **Loop setiap tabel dalam halaman**
   - Scroll ke elemen tabel
   - Tutup pop-up (jika muncul)
   - Klik sel tabel untuk masuk ke halaman detail

7. **Ambil detail tabel**
   - Ambil `Judul Tabel` dari `<h1>`
   - Klik tombol `JSON`
   - Ambil nilai URL WebAPI dari input field readonly

8. **Error handling**
   - Jika gagal klik tabel atau gagal ambil detail:
     - Reload ulang halaman kategori
     - Skip dan tetap simpan data kosong (dengan `WebAPI URL` kosong)

9. **Simpan ke file CSV (`bps_all_tables.csv`)**
   - Data disimpan setiap kali 1 tabel berhasil diambil
   - Kolom CSV: `Subjek`, `Kategori`, `Judul Tabel`, `WebAPI URL`

10. **Selesai**
    - Cetak log kategori tanpa tabel
    - Tutup browser dan simpan hasil akhir



## Error Handling dan Safety Check

| Jenis Error                               | Solusi dalam Script                                               |
|-------------------------------------------|-------------------------------------------------------------------|
| **1. Loading spinner terlalu lama**       | Timeout otomatis → diberikan peringatan (`warning`) lalu lanjut. |
| **2. Tombol pagination tidak bisa diklik**| Retry klik hingga 4 kali → jika tetap gagal, log sebagai error.   |
| **3. Judul tabel kosong atau error klik** | Melewati indeks tabel tersebut → logging dan lanjut ke berikutnya.|
| **4. Gagal ambil endpoint JSON**          | Reload halaman kategori → skip tabel tersebut dan log hasil kosong.|
| **5. Popup muncul saat klik tabel**       | Script mendeteksi dan menutup popup sebelum klik dilakukan.       |
| **6. KeyboardInterrupt (Ctrl + C)**       | Tangkap interupsi pengguna → simpan hasil sementara sebelum keluar.|

Semua error ditangani dengan aman agar proses scraping tidak berhenti total, dan data tetap disimpan secara bertahap.
 
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

