import requests
from bs4 import BeautifulSoup

response = requests.get('https://www.scrapethissite.com/pages/simple/')
soup = BeautifulSoup(response.text, "html.parser")

country_blocks = soup.find_all("div", class_="col-md-4 country")

result = []
for block in country_blocks:
    # Ambil nama negara
    name_element = block.find("h3", class_="country-name")
    country_name = name_element.get_text(strip=True) if name_element else ""

    # Ambil ibu kota
    capital_element = block.find("span", class_="country-capital")
    capital_name = capital_element.get_text(strip=True) if capital_element else ""

    # Ambil populasi
    population_element = block.find("span", class_="country-population")
    population_name = population_element.get_text(strip=True) if population_element else ""

    result.append({"name": country_name, "capital": capital_name, "population": population_name })

for item in result:
    print(f"Country: {item['name']} - Capital {item['capital']} - Population: : {item['population']}" )