from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup browser
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://www.bps.go.id/id/statistics-table?subject=520"
driver.get(url)

wait = WebDriverWait(driver, 10)
time.sleep(5)

all_judul = []

def ambil_judul():
    time.sleep(2)
    judul_elements = driver.find_elements(By.XPATH, "//table[contains(@class, 'mantine-Table-root')]//div[@class='text-black']")
    return [el.text.strip() for el in judul_elements if el.text.strip()]

halaman = 1
while True:
    print(f"Halaman {halaman}")
    judul_saat_ini = ambil_judul()
    
    for j in judul_saat_ini:
        if j not in all_judul:
            all_judul.append(j)

    try:
        # Temukan tombol Next
        tombol_next = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next page']")))
        
        # Jika tombol next disable (halaman terakhir)
        if tombol_next.get_attribute("disabled"):
            print("Halaman terakhir tercapai.")
            break

        # Klik tombol Next dan tunggu table berubah
        ActionChains(driver).move_to_element(tombol_next).click().perform()
        halaman += 1
        time.sleep(2)

    except Exception as e:
        print("Tidak bisa klik tombol next:", str(e))
        break

# Print hasil
print("\nSemua Judul Tabel Pendidikan BPS:\n")
for i, judul in enumerate(all_judul, 1):
    print(f"{i}. {judul}")

driver.quit()
