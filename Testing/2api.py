import requests
import json

url = "https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/domain/0000/var/457/th/1,2/key/79452e4c302f8921ad36cd2bf55f0630/"
response = requests.get(url, timeout=10)
data = response.json()
with open("bps_hls_sample.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Sukses simpan file data BPS ke bps_hls_sample.json")
