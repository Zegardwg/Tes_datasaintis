from flask import Flask, render_template, Response
import requests
import pandas as pd
import io
import re

app = Flask(__name__)

def get_bps_data():
    # Ambil data dari endpoint API BPS
    url = "https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/domain/0000/var/461/th/124/key/921504506b78d644648e514971ac0d28"
    response = requests.get(url, timeout=10)
    data = response.json()

    # pengecekan kondisi gagal
    if response.status_code != 200 or 'datacontent' not in data:
        raise Exception("Gagal mengambil data dari API BPS.")

    # Proses cleaning data
    wilayah = {}        # Mapping kode wilayah ke nama provinsi/kabupaten_kota
    current_prov = ""   # Menyimpan nama provinsi aktif
    for item in data["vervar"]:
        label = item["label"]
        # Hilangkan tag <b> dari label
        label_clean = re.sub(r"</?b>", "", label, flags=re.IGNORECASE).strip()
        # Kondisi: menyimpan tag <b> (nama provinsi), simpan ke current_prov
        if re.search(r"<\s*b\s*>", label, flags=re.IGNORECASE):
            current_prov = label_clean
        else:
            # jika bukan berarti kab/kota
            wilayah[str(item["val"])] = {
                "provinsi": current_prov,
                "kabupaten_kota": label_clean
            }

    # Mapping kode tahun ke label tahun
    tahun_map = {str(item["val"]): item["label"] for item in data["tahun"]}
    kode_tahun_2024 = None
    # Cari kode tahun yang labelnya "2024"
    for k, v in tahun_map.items():
        if v == "2023":
            kode_tahun_2024 = k
            break
    # Kondisi: Jika tidak ditemukan tahun 2024, erorr
    if kode_tahun_2024 is None:
        raise ValueError("Tahun 2024 tidak ditemukan di metadata tahun.")

    # Kode gender sudah fix (dari struktur BPS)
    kode_laki = "211"
    kode_perempuan = "212"

    data_rows = {}  # Simpan sementara row data
    for k, v in data["datacontent"].items():
        wilayah_id = k[:4]      # 4 digit pertama kode wilayah
        kode_gender = k[7:10]   # 3 digit gender
        kode_tahun = k[10:13]   # 3 digit tahun
        #Hanya proses data untuk tahun 2024
        if kode_tahun != kode_tahun_2024:
            continue
        # Hanya ambil wilayah yang ada di mapping wilayah
        if wilayah_id in wilayah:
            row_key = (wilayah_id, kode_tahun)
            # Inisialisasi row jika belum ada
            if row_key not in data_rows:
                data_rows[row_key] = {
                    "provinsi": wilayah[wilayah_id]["provinsi"],
                    "kabupaten_kota": wilayah[wilayah_id]["kabupaten_kota"],
                    "laki_laki": "",
                    "perempuan": "",
                    "tahun": tahun_map[kode_tahun]
                }
            # Isi kolom laki-laki/perempuan sesuai kode gender
            if kode_gender == kode_laki:
                data_rows[row_key]["laki_laki"] = v
            elif kode_gender == kode_perempuan:
                data_rows[row_key]["perempuan"] = v

    # Konversi ke DataFrame pandas
    df = pd.DataFrame(list(data_rows.values()))

    #filter data yang tidak valid
    # Kondisi: Hilangkan data duplikat provinsi (yang labelnya sama dengan kabupaten/kota)
    df = df[df['provinsi'].str.lower() != df['kabupaten_kota'].str.lower()]
    # Kondisi: Hanya baris yang sudah punya angka laki-laki & perempuan
    df = df[df['laki_laki'].astype(str) != '']
    df = df[df['perempuan'].astype(str) != '']

    # Ganti titik dengan koma pada data angka (standar lokal)
    df['laki_laki'] = df['laki_laki'].apply(lambda x: str(x).replace('.', ','))
    df['perempuan'] = df['perempuan'].apply(lambda x: str(x).replace('.', ','))

    # Urutkan berdasarkan provinsi lalu kabupaten/kota
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
    # Download DataFrame ke CSV
    df = get_bps_data()
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    # Response download file CSV
    return Response(buffer, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=bps_hls_2024.csv"})

if __name__ == "__main__":
    app.run(debug=True)
