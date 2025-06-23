from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv

def save_results_to_csv(results, filename="bps_all_tables.csv"):
    fieldnames = ["subjek","kategori","tabel_ringkas","tabel_lengkap","endpoint"]
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

def klik_pagination_page(driver, wait, page_num):
    try:
        page_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//button[@type='button' and normalize-space(text())='{page_num}']")
            )
        )
        page_btn.click()
        print(f"[INFO] Klik page {page_num}")
        time.sleep(2.5)
        tunggu_loading_selesai(driver, timeout=20)
        time.sleep(1.5)
    except Exception as e:
        print(f"[WARN] Tidak bisa klik page {page_num}: {e}")

def main():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 40)

    results = []
    empty_cats = []
    try:
        driver.get('https://www.bps.go.id/id/statistics-table?subject=528')

        # === STEP 1: Ambil mapping subjek → kategori → url ===
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

        for entry in data_links:
            subjek   = entry["subjek"]
            kategori = entry["kategori"]
            url      = entry["url"]

            print(f"\n>> SUBJEK: {subjek} | KATEGORI: {kategori}")
            driver.get(url)
            time.sleep(3)
            tunggu_loading_selesai(driver, timeout=30)
            time.sleep(2)

            # Cek jumlah halaman
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
                    # Pastikan selalu reload posisi
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
                        brief_title = cell.text.strip() or f"UNKNOWN_TABEL_{idx+1}"
                        print(f"  [hal {page_num}][{idx+1}/{total}] {brief_title}")
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
                        idx += 1
                        continue

                    error_or_reload = False
                    # --- Cek Judul
                    try:
                        full_title = WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.font-bold.text-xl.text-main-primary.mb-4"))
                        ).text.strip()
                    except Exception as e:
                        print("    [ERROR] Tidak bisa mengambil judul, reload halaman list!")
                        error_or_reload = True

                    # --- Cek JSON
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
                            error_or_reload = True

                    if error_or_reload:
                        # Catat tetap (endpoint kosong)
                        results.append({
                            "subjek": subjek,
                            "kategori": kategori,
                            "tabel_ringkas": brief_title,
                            "tabel_lengkap": "TIDAK BISA AMBIL DETAIL ATAU ENDPOINT",
                            "endpoint": ""
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

                    # --- Tutup popup JSON & kembali
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

                    # --- Simpan hasil
                    results.append({
                        "subjek": subjek,
                        "kategori": kategori,
                        "tabel_ringkas": brief_title,
                        "tabel_lengkap": full_title,
                        "endpoint": endpoint
                    })
                    save_results_to_csv(results)  # Auto-save setiap ada data baru
                    print(f"    → {full_title}")
                    print(f"    → {endpoint}")
                    time.sleep(1.6)

                    idx += 1

                page_num += 1

        print("\nSelesai! Kategori tanpa tabel:", empty_cats)

    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan user (Ctrl+C). Simpan data CSV sebelum keluar...")
        save_results_to_csv(results)
    except Exception as e:
        print(f"\n[ERROR] Terjadi error: {e}. Simpan data CSV sebelum keluar...")
        save_results_to_csv(results)
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
