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

def save_results_to_csv(results, filename="bps_all_tables.csv"):
    fieldnames = ["subjek", "kategori", "Judul Tabel", "WebAPI URL"]
    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def tunggu_loading_selesai(driver, timeout=35):
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".mantine-Loader-root"))
        )
    except TimeoutException:
        print("[WARN] Spinner loading masih ada setelah timeout, lanjutkan saja.")
        logging.warning(" Spinner loading masih muncul setelah timeout, lanjutkan...")

def tunggu_tabel_stabil(driver, selector, min_jumlah=1, max_wait=45, stable_seconds=4):
    start = time.time()
    last_count = -1
    last_change = time.time()
    while True:
        tabels = driver.find_elements(By.CSS_SELECTOR, selector)
        count = len(tabels)
        now = time.time()
        if count != last_count:
            last_change = now
            last_count = count
        if (now - last_change > stable_seconds) and (count >= min_jumlah or count == 0):
            return tabels
        if now - start > max_wait:
            return tabels
        time.sleep(1.0)

def klik_pagination_page(driver, wait, page_num, max_retry=4):
    last_error = ""
    for attempt in range(1, max_retry+1):
        try:
            # Jika page_num belum muncul, klik page_num - 1 terlebih dahulu
            try:
                driver.find_element(By.XPATH, f"//button[normalize-space(text())='{page_num}']")
            except:
                if page_num > 1:
                    print(f"[INFO] Halaman {page_num} belum muncul, klik dulu halaman {page_num - 1}")
                    klik_pagination_page(driver, wait, page_num - 1)
                    time.sleep(2)
                    tunggu_loading_selesai(driver)

            # Setelah muncul, baru lanjut klik seperti biasa
            page_btn = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//button[@type='button' and normalize-space(text())='{page_num}']")
                )
            )

            # Skip jika sudah aktif
            if page_btn.get_attribute('data-active') == 'true' or page_btn.get_attribute('aria-current') == 'page':
                print(f"[INFO] Page {page_num} sudah aktif, skip klik.")
                return

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", page_btn)
            time.sleep(0.4)

            try:
                close_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']")
                if close_btn.is_displayed():
                    close_btn.click()
                    time.sleep(0.4)
            except:
                pass

            wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//button[@type='button' and normalize-space(text())='{page_num}']")
            ))

            try:
                page_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", page_btn)

            print(f"[INFO] Klik page {page_num} (percobaan {attempt})")
            time.sleep(2.2)
            tunggu_loading_selesai(driver, timeout=20)
            time.sleep(1.2)
            return

        except Exception as e:
            last_error = str(e)
            print(f"[WARN] Gagal klik page {page_num} percobaan-{attempt}: {e}")
            logging.warning(f"[WARN] Gagal klik page {page_num} percobaan-{attempt}: {e}")
            time.sleep(2)

    print(f"[ERROR] Gagal klik page {page_num} setelah {max_retry} kali: {last_error}")
    logging.erorr(f"[ERROR] Gagal klik page {page_num} setelah {max_retry} kali: {last_error}")



def main():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 40)
    results = []
    empty_cats = []

    try:
        driver.get('https://www.bps.go.id/id/statistics-table?subject=528')

        # Ambil mapping subjek - kategori - url
        data_links = []
        for btn in driver.find_elements(By.CSS_SELECTOR, "button.transition-all"):
            try:
                btn.click()
                time.sleep(0.5)
            except:
                pass

        subjek_bloks = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.flex.flex-col.gap-y-1 > div.w-full.rounded-lg.bg-white")
        ))

        for blok in subjek_bloks:
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

            for link in blok.find_elements(By.CSS_SELECTOR, "div.accordion-content a.mx-2.px-3.py-2.inline-block"):
                nama_kat = link.text.strip()
                if not nama_kat or len(nama_kat) < 3:
                    continue
                data_links.append({
                    "subjek": subjek,
                    "kategori": nama_kat,
                    "url": link.get_attribute("href")
                })

        # Loop per kategori
        for entry in data_links:
            subjek = entry["subjek"]
            kategori = entry["kategori"]
            url = entry["url"]

            print(f"\n>> SUBJEK: {subjek} | KATEGORI: {kategori}")
            driver.get(url)
            time.sleep(3)
            tunggu_loading_selesai(driver, timeout=30)
            time.sleep(2)

            # Cek jumlah halaman (pagination)
            try:
                paginations = driver.find_elements(By.CSS_SELECTOR, "button.mantine-Pagination-control")
                last_page = 1
                for btn in paginations:
                    try:
                        val = int(btn.text.strip())
                        if val > last_page:
                            last_page = val
                    except:
                        continue
            except:
                last_page = 1

            page_num = 1
            while page_num <= last_page:
                if page_num != 1:
                    klik_pagination_page(driver, wait, page_num)
                tunggu_loading_selesai(driver, timeout=30)
                time.sleep(2)
                tabels = tunggu_tabel_stabil(driver, "td.mantine-1s8spa1 > div.text-black", min_jumlah=1, max_wait=45, stable_seconds=4)
                total = len(tabels)
                if total == 0:
                    break

                table_indexes = list(range(len(tabels)))
                idx = 0
                while idx < len(table_indexes):
                    if page_num != 1:
                        klik_pagination_page(driver, wait, page_num)
                    tunggu_loading_selesai(driver, timeout=20)
                    time.sleep(1.5)
                    tabels = tunggu_tabel_stabil(driver, "td.mantine-1s8spa1 > div.text-black", min_jumlah=1, max_wait=45, stable_seconds=4)
                    if idx >= len(tabels):
                        idx += 1
                        continue
                    cell = tabels[idx]
                    try:
                        judul_tabel = cell.text.strip() or f"UNKNOWN_TABEL_{idx+1}"
                        print(f"  [hal {page_num}][{idx+1}/{total}] {judul_tabel}")
                    except Exception as e:
                        print(f"(STUCK TABLE ke-{idx+1}): {e}")
                        idx += 1
                        continue

                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cell)
                        time.sleep(0.7)
                    except:
                        pass

                    try:
                        close_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']")
                        if close_btn.is_displayed():
                            close_btn.click()
                            print("    (Tutup overlay pop-up sebelum klik tabel)")
                            time.sleep(0.7)
                    except:
                        pass

                    try:
                        ActionChains(driver).move_to_element(cell).click().perform()
                        time.sleep(2.2)
                    except Exception as e:
                        print(f"    (Gagal klik tabel ke-{idx+1}: {e})")
                        logging.erorr(f"    (Gagal klik tabel ke-{idx+1}: {e})")
                        idx += 1
                        continue

                    error_or_reload = False
                    try:
                        full_judul = WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.font-bold.text-xl.text-main-primary.mb-4"))
                        ).text.strip()
                    except Exception as e:
                        print("    [ERROR] Tidak bisa mengambil judul, reload halaman list!")
                        logging.error("    [ERROR] Tidak bisa mengambil judul, reload halaman list!")
                        error_or_reload = True

                    endpoint = ""
                    if not error_or_reload:
                        try:
                            btn_json = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'JSON')]"))
                            )
                            btn_json.click()
                            time.sleep(1.0)
                            endpoint = WebDriverWait(driver, 5).until(
                                EC.visibility_of_element_located(
                                    (By.XPATH, "//input[@readonly and contains(@value, 'webapi.bps.go.id')]"))
                            ).get_attribute("value")
                        except Exception as e:
                            print("    [ERROR] Tidak menemukan tombol JSON atau gagal ambil endpoint, reload halaman list!")
                            logging.error("    [ERROR] Tidak menemukan tombol JSON atau gagal ambil endpoint, reload halaman list!")
                            error_or_reload = True

                    if error_or_reload:
                        results.append({
                            "subjek": subjek,
                            "kategori": kategori,
                            "Judul Tabel": judul_tabel,
                            # "judul_detail": "TIDAK BISA AMBIL DETAIL ATAU ENDPOINT",
                            "WebAPI URL": "TIDAK BISA AMBIL DETAIL ATAU ENDPOINT"
                        })
                        save_results_to_csv(results)
                        print("    [INFO] Hard reload ke halaman kategori (skip tabel ini).")
                        driver.get(url)
                        time.sleep(3)
                        tunggu_loading_selesai(driver, timeout=20)
                        if page_num != 1:
                            klik_pagination_page(driver, wait, page_num)
                        time.sleep(1.5)
                        idx += 1
                        continue

                    for locator in [
                        (By.CSS_SELECTOR, "button svg.fa-xmark"),
                        (By.XPATH, "//button[contains(., 'Kembali')]")
                    ]:
                        try:
                            btn_close = wait.until(EC.element_to_be_clickable(locator))
                            btn_close.click()
                            time.sleep(0.9)
                        except:
                            pass

                    results.append({
                        "subjek": subjek,
                        "kategori": kategori,
                        "Judul Tabel": judul_tabel,
                        # "judul_detail": full_judul,
                        "WebAPI URL": endpoint.replace("[WebAPI_KEY]", "921504506b78d644648e514971ac0d28")
                    })
                    save_results_to_csv(results)
                    print(f"    → {full_judul}")
                    print(f"    → {endpoint}")
                    time.sleep(1.6)

                    idx += 1

                # Klik ulang halaman untuk refresh state sebelum lanjut
                try:
                    klik_pagination_page(driver, wait, page_num)
                    time.sleep(2)
                    tunggu_loading_selesai(driver, timeout=20)
                except Exception as e:
                    print(f"[WARN] Gagal klik ulang page {page_num}: {e}")
                    logging.warning(f"[WARN] Gagal klik ulang page {page_num}: {e}")

                page_num += 1

        print("\nSelesai! Kategori tanpa tabel:", empty_cats)

    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan user (Ctrl+C). Simpan data CSV sebelum keluar...")
        save_results_to_csv(results)
    except Exception as e:
        print(f"\n[ERROR] Terjadi error: {e}. Simpan data CSV sebelum keluar...")
        logging.erorr(f"\n[ERROR] Terjadi error: {e}. Simpan data CSV sebelum keluar...")
        save_results_to_csv(results)
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    main()