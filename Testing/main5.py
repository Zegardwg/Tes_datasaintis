from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
import time
import csv

def main():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 30)  # Sedikit lebih lama

    driver.get('https://www.bps.go.id/id/statistics-table?subject=528')

    # === STEP 1: Ambil mapping subjek → kategori → url ===
    data_links = []
    for btn in driver.find_elements(By.CSS_SELECTOR, "button.transition-all"):
        try:
            btn.click()
            time.sleep(0.2)
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
            time.sleep(0.2)

        for link in blok.find_elements(By.CSS_SELECTOR, "div.accordion-content a.mx-2.px-3.py-2.inline-block"):
            nama_kat = link.text.strip()
            if not nama_kat or len(nama_kat) < 3:
                continue
            data_links.append({
                "subjek": subjek,
                "kategori": nama_kat,
                "url": link.get_attribute("href")
            })

    # === STEP 2: Ambil semua judul tabel per kategori ===
    results = []
    empty_cats = []
    for entry in data_links:
        subjek   = entry["subjek"]
        kategori = entry["kategori"]
        url      = entry["url"]

        print(f"\n>> SUBJEK: {subjek} | KATEGORI: {kategori}")
        driver.get(url)
        time.sleep(2)

        try:
            tabels = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "td.mantine-1s8spa1 > div.text-black")
            ))
        except TimeoutException:
            print(f"   (Tidak ada tabel di '{kategori}')")
            empty_cats.append((subjek, kategori))
            continue

        total = len(tabels)
        if total == 0:
            empty_cats.append((subjek, kategori))
            continue

        # loop berdasarkan index, re-find setiap kali
        for i in range(total):
            # re-find dan tunggu visible
            try:
                tabels = wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "td.mantine-1s8spa1 > div.text-black")
                ))
                cell = tabels[i]
                brief_title = cell.text.strip() or f"UNKNOWN_TABEL_{i+1}"
                print(f"  [{i+1}/{total}] {brief_title}")
            except TimeoutException:
                print(f"    (Timeout tabel ke-{i+1}, skip...)")
                continue

            # --- Scroll ke elemen sebelum klik
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cell)
                time.sleep(0.3)
            except:
                pass

            # --- Handle overlay/pop-up kalau ada
            try:
                close_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']")
                if close_btn.is_displayed():
                    close_btn.click()
                    print("    (Tutup overlay pop-up sebelum klik tabel)")
            except:
                pass

            # --- Coba klik
            try:
                ActionChains(driver).move_to_element(cell).click().perform()
            except ElementClickInterceptedException as e:
                print(f"    (Klik tabel ke-{i+1} terhalang overlay/sticky. Skip.)")
                continue
            except Exception as e:
                print(f"    (Gagal klik tabel ke-{i+1}: {e})")
                continue

            # --- Ambil judul lengkap
            try:
                full_title = wait.until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "h1.font-bold.text-xl.text-main-primary.mb-4")
                )).text.strip()
            except:
                full_title = brief_title

            # --- Klik JSON dan ambil endpoint
            endpoint = ""
            try:
                btn_json = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'JSON')]")
                ))
                btn_json.click()
                endpoint = wait.until(EC.visibility_of_element_located(
                    (By.XPATH, "//input[@readonly and contains(@value, 'webapi.bps.go.id')]")
                )).get_attribute("value")
            except Exception as e:
                print(f"    (Gagal ambil JSON/endpoint tabel ke-{i+1}: {e})")

            # --- Tutup popup JSON & kembali
            for locator in [
                (By.CSS_SELECTOR, "button svg.fa-xmark"),
                (By.XPATH, "//button[contains(., 'Kembali')]")
            ]:
                try:
                    btn_close = wait.until(EC.element_to_be_clickable(locator))
                    btn_close.click()
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
            print(f"    → {full_title}")
            print(f"    → {endpoint}")
            time.sleep(0.4)

    # === STEP 3: simpan ke CSV ===
    with open("bps_all_tables.csv", "w", newline='', encoding="utf-8") as f:
        fieldnames = ["subjek","kategori","tabel_ringkas","tabel_lengkap","endpoint"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\nSelesai! Kategori tanpa tabel:", empty_cats)
    driver.quit()

if __name__ == "__main__":
    main()