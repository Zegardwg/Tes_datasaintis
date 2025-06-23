from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)
driver.get('https://www.bps.go.id/id/statistics-table?subject=528')

data = []
empty_cats = []

# Expand semua subjek utama di sidebar (accordion)
expand_buttons = driver.find_elements(By.CSS_SELECTOR, "button.transition-all")
for btn in expand_buttons:
    try:
        btn.click()
        time.sleep(0.2)
    except:
        pass

# === STEP 1: Kumpulkan semua subjek, kategori, dan URL kategori ke list (anti-stale) ===
subjek_kategori_list = []
subjek_bloks = wait.until(EC.presence_of_all_elements_located(
    (By.CSS_SELECTOR, "div.flex.flex-col.gap-y-1")
))

for blok in subjek_bloks:
    ps = blok.find_elements(By.CSS_SELECTOR, "p")
    if not ps:
        continue
    subjek_utama = ps[0].text.strip() or "UNKNOWN_SUBJEK"
    kategori_links = blok.find_elements(By.CSS_SELECTOR, "a.mx-2.px-3.py-2.inline-block")
    for kategori in kategori_links:
        kategori_nama = kategori.get_attribute('innerText').strip()
        # Atau bisa juga kategori.get_attribute('textContent').strip()
        # Tambahan filter: skip kategori kalau namanya pendek/kosong
        if not kategori_nama or len(kategori_nama) < 3:
            print(f"    [SKIP] Ada kategori tanpa nama di subjek '{subjek_utama}' (mungkin icon/empty): '{kategori_nama}'")
            continue
        kategori_url = kategori.get_attribute('href')
        subjek_kategori_list.append({
            "subjek": subjek_utama,
            "kategori": kategori_nama,
            "url": kategori_url
        })

# === STEP 2: Loop per kategori, scraping satu tabel pertama saja per kategori ===
for row in subjek_kategori_list:
    subjek_utama = row["subjek"]
    kategori_nama = row["kategori"]
    kategori_url = row["url"]
    print(f"== SUBJEK: {subjek_utama}  [KATEGORI] {kategori_nama}")
    driver.get(kategori_url)
    time.sleep(2)

    try:
        tabels = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "td.mantine-1s8spa1 > div.text-black")
        ))
    except Exception as e:
        print(f"   (TIDAK ADA TABEL di kategori '{kategori_nama}' subjek '{subjek_utama}')")
        empty_cats.append((subjek_utama, kategori_nama))
        continue

    if len(tabels) == 0:
        continue

    # -- HANYA SATU TABEL PERTAMA PER KATEGORI --
    tabel_judul = tabels[0].text.strip() or "UNKNOWN_TABEL"
    print(f"    > [TABEL] {tabel_judul}")

    try:
        tabels[0].click()
    except Exception as e:
        print(f"    (Gagal klik tabel pertama: {e})")
        continue

    try:
        judul_tabel = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "h1.font-bold.text-xl.text-main-primary.mb-4")
        )).text.strip()
    except:
        judul_tabel = tabel_judul

    try:
        btn_json = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'JSON')]")
        ))
        btn_json.click()
    except Exception as e:
        print(f"    (Tidak menemukan tombol JSON: {e})")
        try:
            btn_kembali = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Kembali')]")
            ))
            btn_kembali.click()
        except: pass
        continue

    try:
        input_api = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[@readonly and contains(@value, 'webapi.bps.go.id')]")
        ))
        endpoint = input_api.get_attribute('value')
    except:
        endpoint = ""
        print("    (Tidak menemukan endpoint)")

    try:
        btn_close = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button svg.fa-xmark")
        ))
        btn_close.find_element(By.XPATH, "./..").click()
    except: pass

    try:
        btn_kembali = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'Kembali')]")
        ))
        btn_kembali.click()
    except: pass

    # Simpan hasil
    data.append({
        "subjek": subjek_utama,
        "kategori": kategori_nama,
        "tabel": judul_tabel,
        "endpoint": endpoint
    })

    print(f"      [ENDPOINT] {endpoint}")
    time.sleep(1)

# === SAVE CSV ===
with open("bps_scraping_result.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["subjek", "kategori", "tabel", "endpoint"])
    writer.writeheader()
    writer.writerows(data)

print("\nSelesai scraping!")
print("Kategori tanpa tabel:", empty_cats)
driver.quit()