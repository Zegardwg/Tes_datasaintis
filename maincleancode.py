from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import csv
import logging

# Konfigurasi logging utama
logging.basicConfig( 
    filename='scraper_error.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S'
)

# Nonaktifkan log internal dari selenium
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

def simpan_hasil_ke_csv(hasil, nama_file="bps_all_tables.csv"):
    """Menyimpan hasil scraping ke file CSV"""
    kolom = ["subjek", "kategori", "Judul Tabel", "WebAPI URL"]
    with open(nama_file, "w", newline='', encoding="utf-8") as f:
        penulis = csv.DictWriter(f, fieldnames=kolom)
        penulis.writeheader()
        penulis.writerows(hasil)

def tunggu_loading_selesai(driver, timeout=35):
    """Menunggu hingga loading spinner menghilang"""
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".mantine-Loader-root"))
        )
    except TimeoutException:
        logging.warning("Spinner loading masih ada setelah timeout")
        print("[PERINGATAN] Spinner loading masih ada setelah timeout")

def tunggu_tabel_stabil(driver, selector, min_jumlah=1, max_tunggu=45, detik_stabil=4):
    """Menunggu hingga jumlah tabel stabil"""
    waktu_mulai = time.time()
    jumlah_terakhir = -1
    waktu_terakhir_berubah = time.time()

    # Temukan elemen menggunakan selector
    while True:
        tabel_tabel = driver.find_elements(By.CSS_SELECTOR, selector)
        jumlah_sekarang = len(tabel_tabel)
        waktu_sekarang = time.time()

        # Periksa apakah jumlah elemen berubah
        if jumlah_sekarang != jumlah_terakhir:
            waktu_terakhir_berubah = waktu_sekarang
            jumlah_terakhir = jumlah_sekarang

        # Kondisi return 1: Jumlah elemen stabil dan memenuhi syarat minimal
        if (waktu_sekarang - waktu_terakhir_berubah > detik_stabil) and (jumlah_sekarang >= min_jumlah or jumlah_sekarang == 0):
            return tabel_tabel

        # Kondisi return 2: Waktu penantian melebihi batas
        if waktu_sekarang - waktu_mulai > max_tunggu:
            return tabel_tabel

        time.sleep(1.0)

def klik_halaman_pagination(driver, wait, nomor_halaman, maksimal_percobaan=4):
    """Mengklik nomor halaman pada pagination"""
    pesan_error_terakhir = ""
    
    for percobaan in range(1, maksimal_percobaan + 1):
        try:
            # Jika halaman belum muncul, coba klik halaman sebelumnya
            try:
                driver.find_element(By.XPATH, f"//button[normalize-space(text())='{nomor_halaman}']")
            except:
                if nomor_halaman > 1:
                    print(f"[INFO] Halaman {nomor_halaman} belum muncul, mencoba halaman {nomor_halaman - 1}")
                    klik_halaman_pagination(driver, wait, nomor_halaman - 1)
                    time.sleep(2)
                    tunggu_loading_selesai(driver)

            # Tunggu dan dapatkan tombol halaman
            tombol_halaman = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//button[@type='button' and normalize-space(text())='{nomor_halaman}']")
                )
            )

            # Lewati jika halaman sudah aktif
            if tombol_halaman.get_attribute('data-active') == 'true' or tombol_halaman.get_attribute('aria-current') == 'page':
                print(f"[INFO] Halaman {nomor_halaman} sudah aktif")
                return

            # Scroll ke tombol
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tombol_halaman)
            time.sleep(0.4)

            # Tutup popup jika ada
            try:
                tombol_tutup = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']")
                if tombol_tutup.is_displayed():
                    tombol_tutup.click()
                    time.sleep(0.4)
            except:
                pass

            # Klik tombol halaman
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//button[@type='button' and normalize-space(text())='{nomor_halaman}']")
            ))

            try:
                tombol_halaman.click()
            except Exception:
                driver.execute_script("arguments[0].click();", tombol_halaman)

            print(f"[INFO] Mengklik halaman {nomor_halaman} (percobaan ke-{percobaan})")
            time.sleep(2.2)
            tunggu_loading_selesai(driver, timeout=20)
            time.sleep(1.2)
            return

        except Exception as e:
            pesan_error_terakhir = str(e)
            print(f"[PERINGATAN] Gagal klik halaman {nomor_halaman} (percobaan ke-{percobaan}): {e}")
            logging.warning(f"Gagal klik halaman {nomor_halaman}: {e}")
            time.sleep(2)

    print(f"[ERROR] Gagal klik halaman {nomor_halaman} setelah {maksimal_percobaan} percobaan: {pesan_error_terakhir}")
    logging.error(f"Gagal klik halaman {nomor_halaman}: {pesan_error_terakhir}")

def main():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 40)
    hasil_scraping = []
    kategori_kosong = []

    try:
        # Buka halaman utama
        driver.get('https://www.bps.go.id/id/statistics-table?subject=528')

        # Kumpulkan semua link kategori
        data_kategori = []
        
        # Buka semua panel expand subjek
        for tombol in driver.find_elements(By.CSS_SELECTOR, "button.transition-all"):
            try:
                tombol.click()
                time.sleep(0.5)
            except Exception:
                pass

        # Ambil semua blok subjek
        blok_subjek = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.flex.flex-col.gap-y-1 > div.w-full.rounded-lg.bg-white")
        ))

        for blok in blok_subjek:
            try:
                tombol_subjek = blok.find_element(By.CSS_SELECTOR, "button[type='button']")
                nama_subjek = tombol_subjek.find_element(By.TAG_NAME, "p").text.strip()
            except Exception:
                continue

            if not nama_subjek:
                continue

            # Buka panel jika tertutup
            panel = blok.find_element(By.CSS_SELECTOR, "div.accordion-content")
            if not panel.is_displayed():
                tombol_subjek.click()
                time.sleep(0.5)

            # Kumpulkan semua link kategori
            for link in blok.find_elements(By.CSS_SELECTOR, "div.accordion-content a.mx-2.px-3.py-2.inline-block"):
                nama_kategori = link.text.strip()
                if not nama_kategori or len(nama_kategori) < 3:
                    continue
                data_kategori.append({
                    "subjek": nama_subjek,
                    "kategori": nama_kategori,
                    "url": link.get_attribute("href")
                })

        # Proses scraping per kategori
        for kategori in data_kategori:
            subjek = kategori["subjek"]
            nama_kategori = kategori["kategori"]
            url_kategori = kategori["url"]

            print(f"\n>> SUBJEK: {subjek} | KATEGORI: {nama_kategori}")
            driver.get(url_kategori)
            time.sleep(3)
            tunggu_loading_selesai(driver)
            time.sleep(2)

            # Tentukan jumlah halaman
            try:
                tombol_pagination = driver.find_elements(By.CSS_SELECTOR, "button.mantine-Pagination-control")
                halaman_terakhir = 1
                for tombol in tombol_pagination:
                    try:
                        nomor = int(tombol.text.strip())
                        if nomor > halaman_terakhir:
                            halaman_terakhir = nomor
                    except Exception:
                        continue
            except Exception:
                halaman_terakhir = 1

            # Proses perpindahan per halaman
            halaman_sekarang = 1
            while halaman_sekarang <= halaman_terakhir:
                if halaman_sekarang != 1:
                    klik_halaman_pagination(driver, wait, halaman_sekarang)
                
                tunggu_loading_selesai(driver)
                time.sleep(2)

                # Dapatkan daftar tabel
                daftar_tabel = tunggu_tabel_stabil(driver, "td.mantine-1s8spa1 > div.text-black", 1)
                total_tabel = len(daftar_tabel)
                
                if total_tabel == 0:
                    kategori_kosong.append(f"{subjek} - {nama_kategori}")
                    break

                # Proses per tabel
                indeks_tabel = 0
                while indeks_tabel < total_tabel:
                    if halaman_sekarang != 1:
                        klik_halaman_pagination(driver, wait, halaman_sekarang)
                    
                    tunggu_loading_selesai(driver)
                    time.sleep(1.5)
                    
                    # Refresh daftar tabel dan Pengecekan Tabel yang tidak muncul
                    daftar_tabel = tunggu_tabel_stabil(driver, "td.mantine-1s8spa1 > div.text-black", 1)
                    if indeks_tabel >= len(daftar_tabel):
                        indeks_tabel += 1
                        continue

                    sel_tabel = daftar_tabel[indeks_tabel]
                    try:
                        judul_tabel = sel_tabel.text.strip() or f"TABEL_TIDAK_TERDEFINISI_{indeks_tabel+1}"
                        print(f"  [halaman {halaman_sekarang}][{indeks_tabel+1}/{total_tabel}] {judul_tabel}")
                    except Exception as e:
                        print(f"[PERINGATAN] Gagal baca judul tabel ke-{indeks_tabel+1}: {e}")
                        logging.warning(f"Gagal baca judul tabel: {e}")
                        indeks_tabel += 1
                        continue

                    # Scroll ke tabel
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sel_tabel)
                        time.sleep(0.7)
                    except Exception:
                        pass

                    # Tutup popup jika ada
                    try:
                        tombol_tutup = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']")
                        if tombol_tutup.is_displayed():
                            tombol_tutup.click()
                            print("    (Menutup popup sebelum klik tabel)")
                            time.sleep(0.7)
                    except Exception:
                        pass

                    #Kodnisi gagal Klik tabel ke
                    try:
                        ActionChains(driver).move_to_element(sel_tabel).click().perform()
                        time.sleep(2.2)
                    except Exception as e:
                        print(f"    [PERINGATAN] Gagal klik tabel ke-{indeks_tabel+1}: {e}")
                        logging.warning(f"Gagal klik tabel: {e}")
                        indeks_tabel += 1
                        continue

                    # Ambil detail tabel jika tidak ada erorr
                    error_terjadi = False
                    
                    # Ambil judul lengkap
                    try:
                        judul_lengkap = WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.font-bold.text-xl.text-main-primary.mb-4"))
                        ).text.strip()
                    except Exception as e:
                        print("    [ERROR] Gagal mengambil judul lengkap")
                        logging.error("Gagal mengambil judul lengkap")
                        error_terjadi = True

                    # Ambil endpoint API
                    endpoint_api = ""
                    if not error_terjadi:
                        try:
                            # Klik tombol JSON
                            tombol_json = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'JSON')]"))
                            )
                            tombol_json.click()
                            time.sleep(1.5)  # Tambah waktu tunggu
                            
                            # Ambil URL API
                            endpoint_api = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located(
                                    (By.XPATH, "//input[@readonly and contains(@value, 'webapi.bps.go.id')]")
                                )
                            ).get_attribute("value")
                        except Exception as e:
                            print("    [ERROR] Gagal mengambil endpoint API")
                            logging.error(f"Gagal mengambil endpoint API: {e}")
                            error_terjadi = True

                    # Jika error, simpan data yang ada dan reload
                    if error_terjadi:
                        hasil_scraping.append({
                            "subjek": subjek,
                            "kategori": nama_kategori,
                            "Judul Tabel": judul_tabel,
                            "WebAPI URL": "GAGAL_MENGAMBIL_DATA"
                        })
                        simpan_hasil_ke_csv(hasil_scraping)
                        print("    [INFO] Reload halaman kategori")
                        driver.get(url_kategori)
                        time.sleep(3)
                        tunggu_loading_selesai(driver)
                        if halaman_sekarang != 1:
                            klik_halaman_pagination(driver, wait, halaman_sekarang)
                        time.sleep(1.5)
                        indeks_tabel += 1
                        continue

                    # Tutup modal/popup
                    for lokator_tutup in [
                        (By.CSS_SELECTOR, "button svg.fa-xmark"),
                        (By.XPATH, "//button[contains(., 'Kembali')]")
                    ]:
                        try:
                            tombol = wait.until(EC.element_to_be_clickable(lokator_tutup))
                            tombol.click()
                            time.sleep(0.9)
                        except Exception:
                            pass

                    # Simpan hasil di ambil
                    hasil_scraping.append({
                        "subjek": subjek,
                        "kategori": nama_kategori,
                        "Judul Tabel": judul_lengkap,
                        "WebAPI URL": endpoint_api.replace("[WebAPI_KEY]", "921504506b78d644648e514971ac0d28")
                    })
                    simpan_hasil_ke_csv(hasil_scraping)
                    print(f"    → {judul_lengkap}")
                    print(f"    → {endpoint_api}")
                    time.sleep(1.6)

                    indeks_tabel += 1

                # Refresh halaman sebelum lanjut
                try:
                    klik_halaman_pagination(driver, wait, halaman_sekarang)
                    time.sleep(2)
                    tunggu_loading_selesai(driver)
                except Exception as e:
                    print(f"[PERINGATAN] Gagal refresh halaman {halaman_sekarang}: {e}")
                    logging.warning(f"Gagal refresh halaman: {e}")

                halaman_sekarang += 1

        print("\nSelesai! Kategori tanpa tabel:", kategori_kosong)

    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan oleh pengguna. Menyimpan data...")
        logging.info("Program dihentikan oleh pengguna")
        simpan_hasil_ke_csv(hasil_scraping)
    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}. Menyimpan data...")
        logging.error(f"Terjadi kesalahan: {e}")
        simpan_hasil_ke_csv(hasil_scraping)
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    main()