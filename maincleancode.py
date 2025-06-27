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
    filename='scraper_error.log',             # File log output
    level=logging.DEBUG,                      
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S'
)

# Nonaktifkan log internal dari selenium agar tidak mengganggu
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


# Fungsi untuk menyimpan hasil scraping ke file CSV
def simpan_ke_csv(hasil, nama_file="bps_all_tables.csv"):
    kolom = ["subjek", "kategori", "judul_tabel", "webapi_url"]
    with open(nama_file, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=kolom)
        writer.writeheader()
        writer.writerows(hasil)


# Fungsi menunggu hingga loading spinner hilang
def tunggu_loading(driver, timeout=35):
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".mantine-Loader-root"))
        )
    except TimeoutException:
        logging.warning(" Spinner loading masih muncul setelah timeout, lanjutkan...")
        print(" [WARNING] Spinner loading masih muncul setelah timeout, lanjutkan...")

# Fungsi untuk menunggu tabel benar-benar stabil (tidak berubah jumlahnya)
def tunggu_tabel_stabil(driver, selector, min_jumlah=1, max_tunggu=45, detik_stabil=4):
    mulai = time.time()
    jumlah_terakhir = -1
    terakhir_berubah = time.time()
    while True:
        elemen = driver.find_elements(By.CSS_SELECTOR, selector)
        jumlah = len(elemen)
        sekarang = time.time()

        if jumlah != jumlah_terakhir:
            terakhir_berubah = sekarang
            jumlah_terakhir = jumlah

        if (sekarang - terakhir_berubah > detik_stabil) and (jumlah >= min_jumlah or jumlah == 0):
            return elemen

        if sekarang - mulai > max_tunggu:
            return elemen

        time.sleep(1.0)

# Fungsi klik nomor halaman pada pagination
def klik_halaman(driver, wait, nomor_halaman, maksimal_coba=4):
    error_terakhir = ""
    for percobaan in range(1, maksimal_coba + 1):
        try:
            try:
                driver.find_element(By.XPATH, f"//button[normalize-space(text())='{nomor_halaman}']")
            except:
                if nomor_halaman > 1:
                    logging.info(f"Halaman {nomor_halaman} belum muncul, klik dulu halaman {nomor_halaman - 1}")
                    print(f"[INFO] Halaman {nomor_halaman} belum muncul, klik dulu halaman {nomor_halaman - 1}")
                    klik_halaman(driver, wait, nomor_halaman - 1)
                    time.sleep(2)
                    tunggu_loading(driver)

            tombol = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//button[@type='button' and normalize-space(text())='{nomor_halaman}']")
                )
            )

            if tombol.get_attribute('data-active') == 'true' or tombol.get_attribute('aria-current') == 'page':
                logging.info(f"Halaman {nomor_halaman} sudah aktif, lewati klik.")
                print(f"[INFO] Halaman {nomor_halaman} sudah aktif, lewati klik.")
                return

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tombol)
            time.sleep(0.4)

            try:
                tombol_tutup = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']")
                if tombol_tutup.is_displayed():
                    tombol_tutup.click()
                    time.sleep(0.4)
            except:
                pass

            wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//button[@type='button' and normalize-space(text())='{nomor_halaman}']")
            ))

            try:
                tombol.click()
            except:
                driver.execute_script("arguments[0].click();", tombol)

            logging.info(f"Klik halaman {nomor_halaman} (percobaan ke-{percobaan})")
            print(f"[INFO] Klik halaman {nomor_halaman} (percobaan ke-{percobaan})")
            time.sleep(2.2)
            tunggu_loading(driver, timeout=20)
            time.sleep(1.2)
            return

        except Exception as e:
            error_terakhir = str(e)
            logging.warning(f"Gagal klik halaman {nomor_halaman} (coba ke-{percobaan}): {e}")
            print(f"[WARNING]Gagal klik halaman {nomor_halaman} (coba ke-{percobaan}): {e}")
            time.sleep(2)

    logging.error(f"Gagal klik halaman {nomor_halaman} setelah {maksimal_coba} kali: {error_terakhir}")
    print(f"[ERORR] Gagal klik halaman {nomor_halaman} setelah {maksimal_coba} kali: {error_terakhir}")

# Fungsi utama scraping
def main():
    driver = webdriver.Chrome()
    tunggu = WebDriverWait(driver, 40)
    hasil = []
    kategori_kosong = []

    try:
        driver.get('https://www.bps.go.id/id/statistics-table?subject=528')

        data_kategori = []

        for tombol in driver.find_elements(By.CSS_SELECTOR, "button.transition-all"):
            try:
                tombol.click()
                time.sleep(0.5)
            except:
                pass

        blok_subjek = tunggu.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.flex.flex-col.gap-y-1 > div.w-full.rounded-lg.bg-white")
        ))

        for blok in blok_subjek:
            try:
                btn = blok.find_element(By.CSS_SELECTOR, "button[type='button']")
                subjek = btn.find_element(By.TAG_NAME, "p").text.strip()
            except:
                continue

            if not subjek:
                continue

            panel = blok.find_element(By.CSS_SELECTOR, "div.accordion-content")
            if not panel.is_displayed():
                btn.click()
                time.sleep(0.5)

            for tautan in blok.find_elements(By.CSS_SELECTOR, "div.accordion-content a.mx-2.px-3.py-2.inline-block"):
                kategori = tautan.text.strip()
                if not kategori or len(kategori) < 3:
                    continue
                data_kategori.append({
                    "subjek": subjek,
                    "kategori": kategori,
                    "url": tautan.get_attribute("href")
                })

        for entri in data_kategori:
            subjek = entri["subjek"]
            kategori = entri["kategori"]
            url = entri["url"]

            print(f"\n>> SUBJEK: {subjek} | KATEGORI: {kategori}")
            driver.get(url)
            time.sleep(3)
            tunggu_loading(driver)
            time.sleep(2)

            try:
                paginasi = driver.find_elements(By.CSS_SELECTOR, "button.mantine-Pagination-control")
                halaman_terakhir = 1
                for btn in paginasi:
                    try:
                        angka = int(btn.text.strip())
                        if angka > halaman_terakhir:
                            halaman_terakhir = angka
                    except:
                        continue
            except:
                halaman_terakhir = 1

            halaman = 1
            while halaman <= halaman_terakhir:
                if halaman != 1:
                    klik_halaman(driver, tunggu, halaman)

                tunggu_loading(driver)
                time.sleep(2)

                tabels = tunggu_tabel_stabil(driver, "td.mantine-1s8spa1 > div.text-black", 1)
                total = len(tabels)
                if total == 0:
                    break

                indeks = 0
                while indeks < total:
                    if halaman != 1:
                        klik_halaman(driver, tunggu, halaman)

                    tunggu_loading(driver)
                    time.sleep(1.5)
                    tabels = tunggu_tabel_stabil(driver, "td.mantine-1s8spa1 > div.text-black", 1)
                    if indeks >= len(tabels):
                        indeks += 1
                        continue

                    sel = tabels[indeks]
                    try:
                        judul_ringkas = sel.text.strip() or f"UNKNOWN_TABEL_{indeks+1}"
                        print(f"  [hal {halaman}][{indeks+1}/{total}] {judul_ringkas}")
                    except Exception as e:
                        logging.warning(f"(TABEL MACET ke-{indeks+1}): {e}")
                        print(f"([WARNING]TABEL MACET ke-{indeks+1}): {e}")
                        indeks += 1
                        continue

                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sel)
                        time.sleep(0.7)
                    except:
                        pass

                    try:
                        tombol_tutup = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']")
                        if tombol_tutup.is_displayed():
                            tombol_tutup.click()
                            print("    (Tutup overlay sebelum klik tabel)")
                            time.sleep(0.7)
                    except:
                        pass

                    try:
                        ActionChains(driver).move_to_element(sel).click().perform()
                        time.sleep(2.2)
                    except Exception as e:
                        logging.warning(f"(Gagal klik tabel ke-{indeks+1}: {e})")
                        print(f"([WARNING]Gagal klik tabel ke-{indeks+1}: {e})")
                        indeks += 1
                        continue

                    gagal_detail = False
                    try:
                        judul_lengkap = WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.font-bold.text-xl.text-main-primary.mb-4"))
                        ).text.strip()
                    except:
                        logging.error("Gagal ambil judul lengkap, reload halaman.")
                        print("[ERORR]Gagal ambil judul lengkap, reload halaman.")
                        gagal_detail = True

                    endpoint = ""
                    if not gagal_detail:
                        try:
                            tombol_json = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'JSON')]"))
                            )
                            tombol_json.click()
                            time.sleep(1.0)
                            endpoint = WebDriverWait(driver, 5).until(
                                EC.visibility_of_element_located(
                                    (By.XPATH, "//input[@readonly and contains(@value, 'webapi.bps.go.id')]")
                                )
                            ).get_attribute("value")
                        except:
                            logging.error(" Tidak menemukan endpoint JSON.")
                            print("[ERORR]Tidak menemukan endpoint JSON.")
                            gagal_detail = True

                    if gagal_detail:
                        hasil.append({
                            "subjek": subjek,
                            "kategori": kategori,
                            "judul_tabel": judul_lengkap if not gagal_detail else judul_ringkas,
                            "webapi_url": ""
                        })
                        simpan_ke_csv(hasil)
                        logging.info(" Reload kategori (skip tabel ini).")
                        print("[INFO] Reload kategori (skip tabel ini).")
                        driver.get(url)
                        time.sleep(3)
                        tunggu_loading(driver)
                        if halaman != 1:
                            klik_halaman(driver, tunggu, halaman)
                        time.sleep(1.5)
                        indeks += 1
                        continue

                    for tutup in [
                        (By.CSS_SELECTOR, "button svg.fa-xmark"),
                        (By.XPATH, "//button[contains(., 'Kembali')]")
                    ]:
                        try:
                            tombol = tunggu.until(EC.element_to_be_clickable(tutup))
                            tombol.click()
                            time.sleep(0.9)
                        except:
                            pass

                    hasil.append({
                        "subjek": subjek,
                        "kategori": kategori,
                        "judul_tabel": judul_lengkap if not gagal_detail else judul_ringkas,
                        "webapi_url": endpoint.replace("[WebAPI_KEY]", "921504506b78d644648e514971ac0d28")
                    })
                    simpan_ke_csv(hasil)
                    print(f"    → {judul_lengkap}")
                    print(f"    → {endpoint}")
                    time.sleep(1.6)

                    indeks += 1

                try:
                    klik_halaman(driver, tunggu, halaman)
                    time.sleep(2)
                    tunggu_loading(driver)
                except Exception as e:
                    logging.warning(f" Gagal klik ulang halaman {halaman}: {e}")
                    print(f"[WARNING] Gagal klik ulang halaman {halaman}: {e}")

                halaman += 1

        print   ("\nSelesai! Kategori kosong:", kategori_kosong)

    except KeyboardInterrupt:
        logging.info("\n[INFO] Dihentikan oleh user. Simpan hasil...")
        print("\n[INFO] Dihentikan oleh user. Simpan hasil...")
        simpan_ke_csv(hasil)
    except Exception as e:
        logging.error(f"\nTerjadi kesalahan: {e}. Simpan hasil sebelum keluar...")
        print(f"\n[ERORR]Terjadi kesalahan: {e}. Simpan hasil sebelum keluar...")
        simpan_ke_csv(hasil)
        raise
    finally:
        driver.quit()

# Jalankan program utama
if __name__ == "__main__":
    main()
