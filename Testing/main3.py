import requests
from bs4 import BeautifulSoup

# URL Kompas
url = "https://www.bps.go.id/id/statistics-table?subject=521"

# Kirim request ke halaman
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)

# Parsing HTML dengan BeautifulSoup
soup = BeautifulSoup(response.text, "html.parser")

# Cari semua elemen h1 dengan class hlTitle
headlines = soup.find_all("div", class_="text-black")

# Tampilkan hasilnya
for idx, headline in enumerate(headlines, start=1):
    print(f"{idx}. {headline.get_text(strip=True)}")
