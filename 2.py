from flask import Flask, render_template, Response
import requests
import pandas as pd
import io
import re

app = Flask(__name__)

def get_bps_data():
    url = "https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/domain/0000/var/457/th/1,2/key/79452e4c302f8921ad36cd2bf55f0630/"
    response = requests.get(url, timeout=10)
    data = response.json()
    if response.status_code != 200 or 'datacontent' not in data:
        raise Exception("Gagal mengambil data dari API BPS.")

    # --- PARSING PROVINSI & KABUPATEN/KOTA ---
    wilayah = {}
    current_prov = ""
    for item in data["vervar"]:
        label = item["label"]
        label_clean = re.sub(r"</?b>", "", label, flags=re.IGNORECASE).strip()
        if re.search(r"<\s*b\s*>", label, flags=re.IGNORECASE):
            current_prov = label_clean
        else:
            wilayah[str(item["val"])] = {
                "provinsi": current_prov,
                "kabupaten_kota": label_clean
            }

    # --- TAHUN & KODE GENDER ---
    tahun_map = {str(item["val"]): item["label"] for item in data["tahun"]}
    kode_tahun_2024 = None
    for k, v in tahun_map.items():
        if v == "2024":
            kode_tahun_2024 = k
            break
    if kode_tahun_2024 is None:
        raise ValueError("Tahun 2024 tidak ditemukan di metadata tahun.")

    kode_laki = "211"
    kode_perempuan = "212"

    # --- BANGUN DATAFRAME ---
    data_rows = {}
    for k, v in data["datacontent"].items():
        wilayah_id = k[:4]
        kode_gender = k[7:10]
        kode_tahun = k[10:13]
        if kode_tahun != kode_tahun_2024:
            continue
        if wilayah_id in wilayah:
            row_key = (wilayah_id, kode_tahun)
            if row_key not in data_rows:
                data_rows[row_key] = {
                    "provinsi": wilayah[wilayah_id]["provinsi"],
                    "kabupaten_kota": wilayah[wilayah_id]["kabupaten_kota"],
                    "laki_laki": "",
                    "perempuan": "",
                    "tahun": tahun_map[kode_tahun]
                }
            if kode_gender == kode_laki:
                data_rows[row_key]["laki_laki"] = v
            elif kode_gender == kode_perempuan:
                data_rows[row_key]["perempuan"] = v

    df = pd.DataFrame(list(data_rows.values()))
    df = df[df['provinsi'].str.lower() != df['kabupaten_kota'].str.lower()]
    df = df[df['laki_laki'].astype(str) != '']
    df = df[df['perempuan'].astype(str) != '']

    # Format angka
    df['laki_laki'] = df['laki_laki'].apply(lambda x: str(x).replace('.', ','))
    df['perempuan'] = df['perempuan'].apply(lambda x: str(x).replace('.', ','))

    df = df.sort_values(['provinsi', 'kabupaten_kota']).reset_index(drop=True)
    return df

@app.route('/')
def index():
    df = get_bps_data()
    print("Jumlah baris data:", len(df))
    table_html = df.to_html(index=False, classes="table table-bordered")
    return render_template("index.html", table_html=table_html)

@app.route('/bps-hls-csv')
def get_bps_hls_csv():
    df = get_bps_data()
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return Response(buffer, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=bps_hls_2024.csv"})

if __name__ == "__main__":
    app.run(debug=True)
